from dataclasses import dataclass
from typing import Any, Dict, List

from app.domain.entities.commande import Article, Commande, LigneCommande
from app.domain.exceptions import (
    ArticleInconnuException,
    OrderNotFoundException,
    OrderNotModifiableException,
    StockInsuffisantException,
)
from app.domain.ports.order_repository import OrderRepository
from app.domain.ports.stock_repository import StockRepository


@dataclass
class ModifyOrderCommand:
    """Command to modify an unacknowledged order's items."""

    order_id: str
    items: List[Dict[str, Any]]


class ModifyOrderUseCase:
    """Domain use case to modify an order that is still pending (EN_ATTENTE).

    Applies changes immediately: restores stock committed by the original items,
    validates the new items against available stock, then updates the order's
    composition in the repository.
    """

    def __init__(self, order_repository: OrderRepository, stock_repository: StockRepository) -> None:
        self.order_repository = order_repository
        self.stock_repository = stock_repository

    def execute(self, command: ModifyOrderCommand) -> Commande:
        order = self.order_repository.get_by_id(command.order_id)
        if order is None:
            raise OrderNotFoundException(command.order_id)

        if order.status != "EN_ATTENTE":
            raise OrderNotModifiableException(command.order_id, order.status)

        old_items: Dict[str, int] = {ligne.article.name: ligne.quantite for ligne in order.lignes}
        new_items: Dict[str, int] = {item["name"]: item["quantity"] for item in command.items}

        # Validate all new items exist in the catalog before touching any stock
        for name in new_items:
            if not self.stock_repository.item_exists(name):
                raise ArticleInconnuException(name)

        # Validate sufficient stock for the net additional quantities needed.
        # The old items' stock will be restored, so we only need to check
        # the incremental demand beyond what the original order already reserved.
        for name, new_qty in new_items.items():
            old_qty = old_items.get(name, 0)
            net_needed = new_qty - old_qty
            if net_needed > 0 and not self.stock_repository.is_in_stock(name, net_needed):
                raise StockInsuffisantException(name)

        # Release stock committed by the original items
        for name, qty in old_items.items():
            self.stock_repository.increment(name, qty)

        # Commit stock for the new items
        for name, qty in new_items.items():
            self.stock_repository.decrement(name, qty)

        # Replace the order's lines with the new items
        new_lignes: List[LigneCommande] = [
            LigneCommande(article=Article(name=item["name"]), quantite=item["quantity"])
            for item in command.items
        ]
        order.lignes = new_lignes
        self.order_repository.save(order)

        return order
