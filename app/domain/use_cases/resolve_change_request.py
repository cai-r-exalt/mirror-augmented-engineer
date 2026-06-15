from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.domain.entities.change_request import ChangeRequest
from app.domain.entities.commande import Article, Commande, LigneCommande
from app.domain.exceptions import (
    ChangeRequestNotFoundException,
    OrderNotFoundException,
)
from app.domain.ports.change_request_repository import ChangeRequestRepository
from app.domain.ports.item_catalog_repository import ItemCatalogRepository
from app.domain.ports.notification_port import NotificationPort
from app.domain.ports.order_repository import OrderRepository
from app.domain.ports.stock_repository import StockRepository
from app.domain.services.eta_calculator import calculate_eta


@dataclass
class ResolveChangeRequestCommand:
    """Command for a bartender to accept or reject a pending change request."""

    order_id: str
    request_id: str
    accept: bool
    resolver_id: Optional[str] = field(default=None)
    rejection_reason: Optional[str] = field(default=None)


@dataclass
class ResolveChangeRequestResult:
    """Result returned by ``ResolveChangeRequestUseCase.execute``.

    Carries both the updated change request and the newly computed ETA (when
    the request was accepted).  Having a dedicated result type avoids the need
    for the controller to reach into the use case's internal repository.
    """

    change_request: ChangeRequest
    new_eta_minutes: Optional[int]


class ResolveChangeRequestUseCase:
    """Domain use case for a bartender to resolve (accept or reject) a change request.

    On acceptance:
    - Checks which proposed items are already available in prepared stock.
    - Items fully covered by prepared stock are "transferred" and require no
      additional preparation time.
    - ETA is recomputed for the remaining items that still need preparation.
    - The order's items and ``eta_minutes`` are updated.
    - The festivalier is notified with the new ETA.

    On rejection:
    - The rejection reason is recorded and the festivalier is notified.
    - The original order is left unchanged.

    In both cases the audit fields ``resolver_id`` and ``resolved_at`` are
    persisted on the change request.
    """

    def __init__(
        self,
        order_repository: OrderRepository,
        change_request_repository: ChangeRequestRepository,
        notification_port: NotificationPort,
        stock_repository: StockRepository,
        item_catalog_repository: ItemCatalogRepository,
    ) -> None:
        self.order_repository = order_repository
        self.change_request_repository = change_request_repository
        self.notification_port = notification_port
        self.stock_repository = stock_repository
        self.item_catalog_repository = item_catalog_repository

    def execute(self, command: ResolveChangeRequestCommand) -> ResolveChangeRequestResult:
        order = self.order_repository.get_by_id(command.order_id)
        if order is None:
            raise OrderNotFoundException(command.order_id)

        change_request = self.change_request_repository.get_by_id(command.request_id)
        if change_request is None or change_request.order_id != command.order_id:
            raise ChangeRequestNotFoundException(command.request_id)

        # Audit fields
        change_request.resolver_id = command.resolver_id
        change_request.resolved_at = datetime.now(timezone.utc).isoformat()

        new_eta_minutes: Optional[int] = None

        if command.accept:
            new_eta_minutes = self._apply_accepted_change(order, change_request)
        else:
            self._apply_rejected_change(change_request, command.rejection_reason)

        self.notification_port.notify_festivalier_change_resolved(
            festivalier_id=order.festivalier_id,
            order_id=command.order_id,
            accepted=command.accept,
            rejection_reason=command.rejection_reason,
            new_eta_minutes=new_eta_minutes,
        )

        return ResolveChangeRequestResult(
            change_request=change_request,
            new_eta_minutes=new_eta_minutes,
        )

    # ── Private helpers ──────────────────────────────────────────────────────

    def _apply_accepted_change(self, order: Commande, change_request: ChangeRequest) -> int:
        """Apply the proposed items to the order, reuse prepared items where possible.

        Returns the newly computed ETA in minutes.
        """
        new_lignes: List[LigneCommande] = [
            LigneCommande(
                article=Article(name=item["name"]),
                quantite=item["quantity"],
            )
            for item in change_request.proposed_items
        ]
        order.lignes = new_lignes

        # Determine which items still need preparation after accounting for
        # prepared stock that can be transferred to the new composition.
        needs_preparation = self._items_needing_preparation(change_request.proposed_items)

        new_eta = calculate_eta(needs_preparation, self.item_catalog_repository) if needs_preparation else 0
        order.eta_minutes = new_eta

        self.order_repository.save(order)

        change_request.status = "ACCEPTEE"
        self.change_request_repository.save(change_request)

        return new_eta

    def _apply_rejected_change(
        self, change_request: ChangeRequest, rejection_reason: Optional[str]
    ) -> None:
        change_request.status = "REJETEE"
        change_request.rejection_reason = rejection_reason
        self.change_request_repository.save(change_request)

    def _items_needing_preparation(
        self, proposed_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Return the subset of proposed items whose quantity is not fully covered
        by the existing prepared stock.

        For each item the transferable quantity is ``min(proposed_qty, prepared_qty)``.
        Only items with a remaining (non-covered) quantity are returned.
        """
        needs_preparation = []
        for item in proposed_items:
            name = item["name"]
            qty = item["quantity"]
            prepared_qty = self.stock_repository.get_prepared_quantity(name)
            remaining_qty = max(0, qty - prepared_qty)
            if remaining_qty > 0:
                needs_preparation.append({"name": name, "quantity": remaining_qty})
        return needs_preparation
