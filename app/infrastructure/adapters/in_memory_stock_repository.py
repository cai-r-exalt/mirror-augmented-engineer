from typing import Dict

from app.domain.ports.stock_repository import StockRepository


class InMemoryStockRepository(StockRepository):
    def __init__(
        self,
        initial_stock: Dict[str, int] | None = None,
        initial_prepared_stock: Dict[str, int] | None = None,
    ):
        self.stock: Dict[str, int] = dict(initial_stock or {})
        self.prepared_stock: Dict[str, int] = dict(initial_prepared_stock or {})

    def is_in_stock(self, item_name: str, quantity: int) -> bool:
        return self.stock.get(item_name, 0) >= quantity

    def item_exists(self, item_name: str) -> bool:
        return item_name in self.stock

    def decrement(self, item_name: str, quantity: int) -> None:
        current = self.stock.get(item_name, 0)
        if current < quantity:
            raise ValueError("Insufficient stock")
        self.stock[item_name] = current - quantity

    def increment(self, item_name: str, quantity: int) -> None:
        self.stock[item_name] = self.stock.get(item_name, 0) + quantity

    def is_prepared_in_stock(self, item_name: str, quantity: int) -> bool:
        return self.prepared_stock.get(item_name, 0) >= quantity

    def decrement_prepared(self, item_name: str, quantity: int) -> None:
        current = self.prepared_stock.get(item_name, 0)
        if current < quantity:
            raise ValueError("Insufficient prepared stock")
        self.prepared_stock[item_name] = current - quantity
