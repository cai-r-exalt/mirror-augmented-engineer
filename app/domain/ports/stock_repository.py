from abc import ABC, abstractmethod


class StockRepository(ABC):
    @abstractmethod
    def is_in_stock(self, item_name: str, quantity: int) -> bool:
        raise NotImplementedError

    @abstractmethod
    def item_exists(self, item_name: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def decrement(self, item_name: str, quantity: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def increment(self, item_name: str, quantity: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def is_prepared_in_stock(self, item_name: str, quantity: int) -> bool:
        raise NotImplementedError

    @abstractmethod
    def decrement_prepared(self, item_name: str, quantity: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_prepared_quantity(self, item_name: str) -> int:
        """Return the current quantity available in prepared stock for the given item."""
        raise NotImplementedError

    @abstractmethod
    def get_quantity(self, item_name: str) -> int:
        """Return the current stock quantity for the given item (0 if not present)."""
        raise NotImplementedError

    @abstractmethod
    def set_quantity(self, item_name: str, quantity: int) -> None:
        """Set the stock quantity for the given item to an exact value."""
        raise NotImplementedError
