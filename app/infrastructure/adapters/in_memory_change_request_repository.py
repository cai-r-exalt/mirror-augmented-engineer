from typing import Dict, List, Optional

from app.domain.entities.change_request import ChangeRequest
from app.domain.ports.change_request_repository import ChangeRequestRepository


class InMemoryChangeRequestRepository(ChangeRequestRepository):
    """In-memory implementation of the ChangeRequestRepository port.

    Stores change requests by id. Used in tests and local runs.
    """

    def __init__(self) -> None:
        self._store: Dict[str, ChangeRequest] = {}

    def save(self, change_request: ChangeRequest) -> None:
        self._store[change_request.id] = change_request

    def get_by_id(self, request_id: str) -> Optional[ChangeRequest]:
        return self._store.get(request_id)

    def find_by_order_id(self, order_id: str) -> List[ChangeRequest]:
        return [cr for cr in self._store.values() if cr.order_id == order_id]

    def find_pending_by_order_id(self, order_id: str) -> List[ChangeRequest]:
        return [
            cr
            for cr in self._store.values()
            if cr.order_id == order_id and cr.status == "EN_ATTENTE_REVIEW"
        ]
