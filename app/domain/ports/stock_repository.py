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
