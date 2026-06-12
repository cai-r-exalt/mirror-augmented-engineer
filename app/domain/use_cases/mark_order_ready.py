from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List

from app.domain.entities.commande import Commande
from app.domain.exceptions import (
    OrderNotFoundException,
    OrderNotReadyTransitionableException,
    PreparedStockInsuffisantException,
)
from app.domain.ports.notification_port import NotificationPort
from app.domain.ports.order_repository import OrderRepository
from app.domain.ports.stock_repository import StockRepository

DEFAULT_PICKUP_DETAILS = "Pickup at the bartender counter"


@dataclass
class MarkOrderReadyCommand:
    order_id: str
    pickup_details: str = DEFAULT_PICKUP_DETAILS


class MarkOrderReadyUseCase:
    """Transition an acknowledged order to READY when prepared stock is sufficient."""

    def __init__(
        self,
        order_repository: OrderRepository,
        stock_repository: StockRepository,
        notification_port: NotificationPort,
    ) -> None:
        self.order_repository = order_repository
        self.stock_repository = stock_repository
        self.notification_port = notification_port

    def execute(self, command: MarkOrderReadyCommand) -> Commande:
        order = self.order_repository.get_by_id(command.order_id)
        if order is None:
            raise OrderNotFoundException(command.order_id)

        if order.status != "ACKNOWLEDGED":
            raise OrderNotReadyTransitionableException(command.order_id, order.status)

        for line in order.lignes:
            item_name = line.article.name
            quantity = line.quantite
            if not self.stock_repository.is_prepared_in_stock(item_name, quantity):
                raise PreparedStockInsuffisantException(command.order_id, item_name)

        for line in order.lignes:
            self.stock_repository.decrement_prepared(line.article.name, line.quantite)

        order.status = "READY"
        order.ready_at = datetime.now(timezone.utc).isoformat()
        self.order_repository.save(order)

        for festivalier_id in self._resolve_notification_recipients(order):
            self.notification_port.notify_festivalier_order_ready(
                festivalier_id=festivalier_id,
                order_id=order.id,
                pickup_details=command.pickup_details,
            )

        return order

    def _resolve_notification_recipients(self, order: Commande) -> List[str]:
        if order.contributors:
            return [contributor.festivalier_id for contributor in order.contributors]
        return [order.festivalier_id]
