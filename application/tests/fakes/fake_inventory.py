from typing import Any


class FakeInventoryRepository:
    def is_in_stock(self, item_name: str, quantity: int) -> bool:
        return True

    def decrement(self, item_name: str, quantity: int) -> None:
        # No-op for application-layer tests
        return None
