import uuid
from dataclasses import dataclass
from typing import Any, Dict, List

from app.domain.entities.change_request import ChangeRequest
from app.domain.exceptions import (
    OrderNotEligibleForChangeRequestException,
    OrderNotFoundException,
)
from app.domain.ports.change_request_repository import ChangeRequestRepository
from app.domain.ports.notification_port import NotificationPort
from app.domain.ports.order_repository import OrderRepository

_STATUSES_ELIGIBLE_FOR_CHANGE_REQUEST = {"ACQUITTEE", "PRÊTE"}


@dataclass
class CreateChangeRequestCommand:
    """Command to request a modification on an already-acknowledged order."""

    order_id: str
    proposed_items: List[Dict[str, Any]]


class CreateChangeRequestUseCase:
    """Domain use case to create a change request for an acknowledged order.

    Does not mutate the original order. Instead it records the proposed
    modification and notifies the bartender(s) for review.
    """

    def __init__(
        self,
        order_repository: OrderRepository,
        change_request_repository: ChangeRequestRepository,
        notification_port: NotificationPort,
    ) -> None:
        self.order_repository = order_repository
        self.change_request_repository = change_request_repository
        self.notification_port = notification_port

    def execute(self, command: CreateChangeRequestCommand) -> ChangeRequest:
        order = self.order_repository.get_by_id(command.order_id)
        if order is None:
            raise OrderNotFoundException(command.order_id)

        if order.status not in _STATUSES_ELIGIBLE_FOR_CHANGE_REQUEST:
            raise OrderNotEligibleForChangeRequestException(command.order_id, order.status)

        change_request = ChangeRequest(
            id=str(uuid.uuid4()),
            order_id=command.order_id,
            proposed_items=list(command.proposed_items),
        )
        self.change_request_repository.save(change_request)

        self.notification_port.notify_bartender_change_requested(
            order_id=command.order_id,
            change_request_id=change_request.id,
        )

        return change_request
