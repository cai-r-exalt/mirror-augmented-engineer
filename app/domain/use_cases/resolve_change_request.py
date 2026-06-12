from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.domain.entities.change_request import ChangeRequest
from app.domain.entities.commande import Article, Commande, LigneCommande
from app.domain.exceptions import (
    ChangeRequestNotFoundException,
    OrderNotFoundException,
)
from app.domain.ports.change_request_repository import ChangeRequestRepository
from app.domain.ports.notification_port import NotificationPort
from app.domain.ports.order_repository import OrderRepository


@dataclass
class ResolveChangeRequestCommand:
    """Command for a bartender to accept or reject a pending change request."""

    order_id: str
    request_id: str
    accept: bool
    rejection_reason: Optional[str] = field(default=None)


class ResolveChangeRequestUseCase:
    """Domain use case for a bartender to resolve (accept or reject) a change request.

    On acceptance: the order's items are updated with the proposed items.
    On rejection: the rejection reason is recorded and the festivalier is notified.
    In both cases, the festivalier receives a notification with the decision.
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

    def execute(self, command: ResolveChangeRequestCommand) -> ChangeRequest:
        order = self.order_repository.get_by_id(command.order_id)
        if order is None:
            raise OrderNotFoundException(command.order_id)

        change_request = self.change_request_repository.get_by_id(command.request_id)
        if change_request is None or change_request.order_id != command.order_id:
            raise ChangeRequestNotFoundException(command.request_id)

        if command.accept:
            self._apply_accepted_change(order, change_request)
        else:
            self._apply_rejected_change(change_request, command.rejection_reason)

        self.notification_port.notify_festivalier_change_resolved(
            festivalier_id=order.festivalier_id,
            order_id=command.order_id,
            accepted=command.accept,
            rejection_reason=command.rejection_reason,
        )

        return change_request

    # ── Private helpers ──────────────────────────────────────────────────────

    def _apply_accepted_change(self, order: Commande, change_request: ChangeRequest) -> None:
        new_lignes: List[LigneCommande] = [
            LigneCommande(
                article=Article(name=item["name"]),
                quantite=item["quantity"],
            )
            for item in change_request.proposed_items
        ]
        order.lignes = new_lignes
        self.order_repository.save(order)

        change_request.status = "ACCEPTEE"
        self.change_request_repository.save(change_request)

    def _apply_rejected_change(
        self, change_request: ChangeRequest, rejection_reason: Optional[str]
    ) -> None:
        change_request.status = "REJETEE"
        change_request.rejection_reason = rejection_reason
        self.change_request_repository.save(change_request)
