from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class PlaceOrderCommand:
    festivalier_id: str
    items: List[Dict[str, Any]]


class PlaceOrder:
    """Application layer use case to place an order.

    This class was extracted from tests to live in production code so the
    behaviour can be reused by the application layer.
    """

    def __init__(self, order_repository, inventory_repository):
        self.order_repository = order_repository
        self.inventory_repository = inventory_repository

    def execute(self, command: PlaceOrderCommand):
        for item in command.items:
            if not self.inventory_repository.is_in_stock(item["name"], item["quantity"]):
                raise ValueError("Item out of stock")
        return self.order_repository.create_order(command.festivalier_id, command.items)
