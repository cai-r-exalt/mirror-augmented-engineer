"""InventoryController — handles admin inventory management endpoints.

Access: Admin-only.  Role/auth gating (e.g. HTTP Basic Auth or JWT admin
claim) will be added in a future iteration; this controller documents the
admin-only intent in its class docstring and HTTP mapping comments.
"""

from app.application.dto.inventory import UpdateStockRequest, UpdateStockResponse
from app.domain.exceptions import InvalidStockQuantityException, ItemNotFoundException
from app.domain.use_cases.update_stock import UpdateStockCommand, UpdateStockUseCase


class InventoryController:
    """Controller handling PATCH /inventory/{item_id}.

    Admin-only endpoint — access control to be enforced by an auth middleware
    in a future iteration.

    HTTP status mapping:
    - 200  — stock quantity updated successfully
    - 400  — missing or non-integer quantity in request body
    - 404  — item not found in the stock repository
    - 422  — quantity is negative
    """

    def __init__(self, update_stock_use_case: UpdateStockUseCase) -> None:
        self.update_stock_use_case = update_stock_use_case

    def update_stock(self, req: UpdateStockRequest) -> UpdateStockResponse:
        """Admin sets the stock quantity for a given item.

        Args:
            req: Contains the item identifier and the desired quantity.

        Returns:
            An UpdateStockResponse with the HTTP status code and response body.
        """
        if req.quantity is None:
            return UpdateStockResponse(400, {"error": "quantity is required"})

        if not isinstance(req.quantity, int) or isinstance(req.quantity, bool):
            return UpdateStockResponse(400, {"error": "quantity must be an integer"})

        try:
            self.update_stock_use_case.execute(
                UpdateStockCommand(item_id=req.item_id, quantity=req.quantity)
            )
        except InvalidStockQuantityException as exc:
            return UpdateStockResponse(422, {"error": str(exc)})
        except ItemNotFoundException as exc:
            return UpdateStockResponse(404, {"error": str(exc)})

        return UpdateStockResponse(200, {"itemId": req.item_id, "quantity": req.quantity})
