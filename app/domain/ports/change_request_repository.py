from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entities.change_request import ChangeRequest


class ChangeRequestRepository(ABC):
    """Port for persisting and querying change requests."""

    @abstractmethod
    def save(self, change_request: ChangeRequest) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, request_id: str) -> Optional[ChangeRequest]:
        raise NotImplementedError

    @abstractmethod
    def find_by_order_id(self, order_id: str) -> List[ChangeRequest]:
        raise NotImplementedError

    @abstractmethod
    def find_pending_by_order_id(self, order_id: str) -> List[ChangeRequest]:
        raise NotImplementedError
