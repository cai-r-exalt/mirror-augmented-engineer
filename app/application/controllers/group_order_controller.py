from typing import Any

from app.application.dto.group_order import GroupOrderRequest, GroupOrderResponse
from app.domain.exceptions import (
    ArticleInconnuException,
    ContributorBalanceExceededException,
    FestivalierInconnuException,
    InsufficientPooledFundsException,
    StockInsuffisantException,
)
from app.domain.use_cases.place_group_order import ContributorInput, PlaceGroupOrderCommand


class GroupOrderController:
    """Controller for the POST /group-orders endpoint.

    Accepts a GroupOrderRequest, validates it, maps to the domain command,
    and delegates to the injected use case.

    HTTP status mapping:
    - 400 — malformed request (missing/invalid fields)
    - 402 — insufficient pooled funds
    - 409 — stock unavailable or contributor balance exceeded
    - 201 — order created successfully
    """

    def __init__(self, use_case: Any) -> None:
        self.use_case = use_case

    def create_group_order(self, req: GroupOrderRequest) -> GroupOrderResponse:
        errors = self._validate(req)
        if errors:
            return GroupOrderResponse(400, {"errors": errors})

        command = PlaceGroupOrderCommand(
            items=[
                {
                    "name": item.get("id") or item.get("name"),
                    "quantity": item.get("quantity") if item.get("quantity") is not None else item.get("quantite"),
                }
                for item in req.items
            ],
            contributors=[
                ContributorInput(
                    festivalier_id=c.festivalier_id,
                    drink_tokens=c.contribution.drink_tokens,
                    food_tokens=c.contribution.food_tokens,
                )
                for c in req.contributors
            ],
        )

        try:
            result = self.use_case.execute(command)
        except (StockInsuffisantException, ArticleInconnuException) as exc:
            return GroupOrderResponse(409, {"error": str(exc)})
        except (ContributorBalanceExceededException, FestivalierInconnuException) as exc:
            return GroupOrderResponse(409, {"error": str(exc)})
        except InsufficientPooledFundsException as exc:
            return GroupOrderResponse(402, {"error": str(exc)})

        order_id = getattr(result, "id", None)
        return GroupOrderResponse(201, {"orderId": order_id})

    # ── Private helpers ─────────────────────────────────────────────────────

    def _validate(self, req: GroupOrderRequest) -> list:
        errors = []

        if not req.items or not isinstance(req.items, list):
            errors.append({"field": "items", "message": "items must be a non-empty list"})

        if not req.contributors or not isinstance(req.contributors, list):
            errors.append({"field": "contributors", "message": "contributors must be a non-empty list"})
            return errors

        for item in req.items or []:
            if not (item.get("id") or item.get("name")):
                errors.append({"field": "items[].id", "message": "each item must have an id or name"})
            qty = item.get("quantity") or item.get("quantite")
            if qty is None or not isinstance(qty, int) or qty <= 0:
                errors.append({"field": "items[].quantity", "message": "each item must have a positive quantity"})

        for contributor in req.contributors:
            if not contributor.festivalier_id:
                errors.append({"field": "contributors[].festivalier_id", "message": "festivalier_id is required"})
            contrib = contributor.contribution
            if not isinstance(contrib.drink_tokens, int) or contrib.drink_tokens < 0:
                errors.append(
                    {"field": "contributors[].contribution.drink_tokens", "message": "must be a non-negative integer"}
                )
            if not isinstance(contrib.food_tokens, int) or contrib.food_tokens < 0:
                errors.append(
                    {"field": "contributors[].contribution.food_tokens", "message": "must be a non-negative integer"}
                )

        return errors
