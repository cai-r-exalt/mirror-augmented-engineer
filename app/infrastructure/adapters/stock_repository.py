from typing import Dict


class InMemoryStockRepository:
    def __init__(self, initial_stock: Dict[str, int] | None = None):
        self.stock: Dict[str, int] = dict(initial_stock or {})

    def is_in_stock(self, item_name: str, quantity: int) -> bool:
        return self.stock.get(item_name, 0) >= quantity

    def decrement(self, item_name: str, quantity: int) -> None:
        current = self.stock.get(item_name, 0)
        if current < quantity:
            raise ValueError("Insufficient stock")
        self.stock[item_name] = current - quantity
