from typing import Dict


class FakeInventoryRepository:
    def __init__(self, stock: Dict[str, int]):
        self.stock = dict(stock)

    def is_in_stock(self, item_name: str, quantity: int) -> bool:
        return self.stock.get(item_name, 0) >= quantity

    def decrement(self, item_name: str, quantity: int) -> None:
        self.stock[item_name] = self.stock.get(item_name, 0) - quantity
