from typing import Any

from app.application.dto.order_change import (
    CreateChangeRequestRequest,
    ModifyOrderRequest,
    OrderChangeResponse,
    ResolveChangeRequestRequest,
)
from app.domain.exceptions import (
    ArticleInconnuException,
    ChangeRequestNotFoundException,
    OrderNotEligibleForChangeRequestException,
    OrderNotFoundException,
    OrderNotModifiableException,
    StockInsuffisantException,
)
from app.domain.use_cases.create_change_request import (
    CreateChangeRequestCommand,
    CreateChangeRequestUseCase,
)
from app.domain.use_cases.list_change_requests import (
    ListChangeRequestsCommand,
    ListChangeRequestsUseCase,
)
from app.domain.use_cases.modify_order import ModifyOrderCommand, ModifyOrderUseCase
from app.domain.use_cases.resolve_change_request import (
    ResolveChangeRequestCommand,
    ResolveChangeRequestUseCase,
)


class OrderChangeController:
    """Controller handling order-modification and change-request endpoints.

    HTTP status mapping:
    - 200  — successful modification or change request resolution
    - 201  — change request created
    - 400  — malformed request (missing/invalid fields)
    - 404  — order or change request not found
    - 409  — stock unavailable or unknown item
    - 422  — order state prevents the operation
    """

    def __init__(
        self,
        modify_order_use_case: ModifyOrderUseCase,
        create_change_request_use_case: CreateChangeRequestUseCase,
        list_change_requests_use_case: ListChangeRequestsUseCase,
        resolve_change_request_use_case: ResolveChangeRequestUseCase,
    ) -> None:
        self.modify_order_use_case = modify_order_use_case
        self.create_change_request_use_case = create_change_request_use_case
        self.list_change_requests_use_case = list_change_requests_use_case
        self.resolve_change_request_use_case = resolve_change_request_use_case

    # ── PATCH /orders/{order_id} ──────────────────────────────────────────────

    def modify_order(self, req: ModifyOrderRequest) -> OrderChangeResponse:
        """Directly modify a pending (EN_ATTENTE) order's items."""
        errors = self._validate_items(req.items)
        if errors:
            return OrderChangeResponse(400, {"errors": errors})

        try:
            result = self.modify_order_use_case.execute(
                ModifyOrderCommand(order_id=req.order_id, items=req.items)
            )
        except OrderNotFoundException as exc:
            return OrderChangeResponse(404, {"error": str(exc)})
        except OrderNotModifiableException as exc:
            return OrderChangeResponse(422, {"error": str(exc)})
        except ArticleInconnuException as exc:
            return OrderChangeResponse(409, {"error": str(exc)})
        except StockInsuffisantException as exc:
            return OrderChangeResponse(409, {"error": str(exc)})

        return OrderChangeResponse(200, {"orderId": result.id, "status": result.status})

    # ── POST /orders/{order_id}/change-requests ───────────────────────────────

    def create_change_request(self, req: CreateChangeRequestRequest) -> OrderChangeResponse:
        """Create a change request for an acknowledged order."""
        errors = self._validate_items(req.proposed_items)
        if errors:
            return OrderChangeResponse(400, {"errors": errors})

        try:
            result = self.create_change_request_use_case.execute(
                CreateChangeRequestCommand(
                    order_id=req.order_id,
                    proposed_items=req.proposed_items,
                )
            )
        except OrderNotFoundException as exc:
            return OrderChangeResponse(404, {"error": str(exc)})
        except OrderNotEligibleForChangeRequestException as exc:
            return OrderChangeResponse(422, {"error": str(exc)})

        return OrderChangeResponse(201, {"changeRequestId": result.id, "status": result.status})

    # ── GET /orders/{order_id}/change-requests ────────────────────────────────

    def list_change_requests(self, order_id: str) -> OrderChangeResponse:
        """List all pending change requests for the given order."""
        try:
            results = self.list_change_requests_use_case.execute(
                ListChangeRequestsCommand(order_id=order_id)
            )
        except OrderNotFoundException as exc:
            return OrderChangeResponse(404, {"error": str(exc)})

        return OrderChangeResponse(
            200,
            {
                "changeRequests": [
                    {
                        "id": cr.id,
                        "orderId": cr.order_id,
                        "proposedItems": cr.proposed_items,
                        "status": cr.status,
                    }
                    for cr in results
                ]
            },
        )

    # ── POST /orders/{order_id}/change-requests/{req_id}/resolve ─────────────

    def resolve_change_request(self, req: ResolveChangeRequestRequest) -> OrderChangeResponse:
        """Bartender accepts or rejects a pending change request."""
        if req.accept is None:
            return OrderChangeResponse(400, {"errors": [{"field": "accept", "message": "accept is required"}]})

        try:
            result = self.resolve_change_request_use_case.execute(
                ResolveChangeRequestCommand(
                    order_id=req.order_id,
                    request_id=req.request_id,
                    accept=req.accept,
                    rejection_reason=req.rejection_reason,
                )
            )
        except OrderNotFoundException as exc:
            return OrderChangeResponse(404, {"error": str(exc)})
        except ChangeRequestNotFoundException as exc:
            return OrderChangeResponse(404, {"error": str(exc)})

        return OrderChangeResponse(
            200,
            {
                "changeRequestId": result.id,
                "status": result.status,
                "rejectionReason": result.rejection_reason,
            },
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    def _validate_items(self, items: Any) -> list:
        errors = []
        if not items or not isinstance(items, list):
            errors.append({"field": "items", "message": "items must be a non-empty list"})
            return errors

        for item in items:
            if not item.get("name"):
                errors.append({"field": "items[].name", "message": "each item must have a name"})
            qty = item.get("quantity")
            if qty is None or not isinstance(qty, int) or qty <= 0:
                errors.append(
                    {"field": "items[].quantity", "message": "each item must have a positive quantity"}
                )

        return errors
