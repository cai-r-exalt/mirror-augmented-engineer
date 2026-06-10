from typing import Optional

from app.domain.ports.order_repository import OrderRepository


class CancelOrderUseCase:
    """Domain use case to cancel an order.

    Cancels an order only if it is currently pending (`EN_ATTENTE`). The
    implementation is intentionally minimal to match test expectations.
    """

    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository

    def execute(self, order_id: str) -> None:
        order = self.order_repository.get_by_id(order_id)
        if order is None:
            return
        if getattr(order, "status", None) == "EN_ATTENTE":
            self.order_repository.update_status(order_id, "ANNULEE")
