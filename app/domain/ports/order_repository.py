from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from app.domain.entities.commande import Commande


class OrderRepository(ABC):
    @abstractmethod
    def create_order(self, festivalier_id: str, items: List[Dict[str, Any]]) -> Commande:
        raise NotImplementedError

    @abstractmethod
    def save(self, commande: Commande) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, order_id: str) -> Optional[Commande]:
        raise NotImplementedError

    @abstractmethod
    def update_status(self, order_id: str, status: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def find_by_festivalier_and_status(self, festivalier_id: str, status: str) -> List[Commande]:
        raise NotImplementedError
