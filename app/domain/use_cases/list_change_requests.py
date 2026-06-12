from dataclasses import dataclass
from typing import List

from app.domain.entities.change_request import ChangeRequest
from app.domain.exceptions import OrderNotFoundException
from app.domain.ports.change_request_repository import ChangeRequestRepository
from app.domain.ports.order_repository import OrderRepository


@dataclass
class ListChangeRequestsCommand:
    """Command to list pending change requests for an order."""

    order_id: str


class ListChangeRequestsUseCase:
    """Domain use case to list all pending change requests for an order.

    Intended for the bartender UI to review outstanding modification requests.
    """

    def __init__(
        self,
        order_repository: OrderRepository,
        change_request_repository: ChangeRequestRepository,
    ) -> None:
        self.order_repository = order_repository
        self.change_request_repository = change_request_repository

    def execute(self, command: ListChangeRequestsCommand) -> List[ChangeRequest]:
        order = self.order_repository.get_by_id(command.order_id)
        if order is None:
            raise OrderNotFoundException(command.order_id)

        return self.change_request_repository.find_pending_by_order_id(command.order_id)
