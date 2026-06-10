from dataclasses import dataclass
from typing import List, Dict, Any

from app.domain.ports.stock_repository import StockRepository
from app.domain.ports.order_repository import OrderRepository
from app.domain.exceptions import StockInsuffisantException, ArticleInconnuException


@dataclass
class PasserCommandeCommand:
    festivalier_id: str
    items: List[Dict[str, Any]]


class PasserCommandeUseCase:
    """Domain use case to place an order with inventory validation.

    This class encapsulates stock validation and delegation to the order
    repository. It depends on a `StockRepository` port.
    """

    def __init__(self, order_repository: OrderRepository, stock_repository: StockRepository):
        self.order_repository: OrderRepository = order_repository
        self.stock_repository = stock_repository

    def execute(self, command: PasserCommandeCommand):
        # Validate items exist and have sufficient stock
        for item in command.items:
            name = item["name"]
            qty = item["quantity"]

            stock_map = getattr(self.stock_repository, "stock", None)
            if isinstance(stock_map, dict) and name not in stock_map:
                raise ArticleInconnuException(name)

            if not self.stock_repository.is_in_stock(name, qty):
                raise StockInsuffisantException(name)

        # Decrement stock and create order
        for item in command.items:
            self.stock_repository.decrement(item["name"], item["quantity"])

        return self.order_repository.create_order(command.festivalier_id, command.items)
