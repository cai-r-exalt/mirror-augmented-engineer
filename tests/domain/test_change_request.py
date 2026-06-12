"""Domain unit tests for the change-request workflow.

Covers:
- CreateChangeRequestUseCase: happy path and failure cases
- ListChangeRequestsUseCase: listing pending requests
- ResolveChangeRequestUseCase: accept and reject flows, notifications,
  prepared-item transfer, ETA recomputation, and audit trail
"""

import pytest

from app.domain.entities.commande import Article, Commande, LigneCommande
from app.domain.exceptions import (
    ChangeRequestNotFoundException,
    OrderNotFoundException,
    OrderNotEligibleForChangeRequestException,
)
from app.domain.ports.item_catalog_repository import (
    ITEM_TYPE_NORMAL_ALCOHOLIC_DRINK,
    ItemCost,
)
from app.domain.use_cases.create_change_request import (
    CreateChangeRequestCommand,
    CreateChangeRequestUseCase,
)
from app.domain.use_cases.list_change_requests import (
    ListChangeRequestsCommand,
    ListChangeRequestsUseCase,
)
from app.domain.use_cases.resolve_change_request import (
    ResolveChangeRequestCommand,
    ResolveChangeRequestUseCase,
)
from app.infrastructure.adapters.in_memory_change_request_repository import (
    InMemoryChangeRequestRepository,
)
from app.infrastructure.adapters.in_memory_item_catalog_repository import (
    InMemoryItemCatalogRepository,
)
from app.infrastructure.adapters.in_memory_order_repository import InMemoryOrderRepository
from app.infrastructure.adapters.in_memory_stock_repository import InMemoryStockRepository
from app.infrastructure.adapters.mock_notification_adapter import MockNotificationAdapter


def _make_acknowledged_order(order_id: str = "order-1", festivalier_id: str = "f-1") -> Commande:
    return Commande(
        id=order_id,
        festivalier_id=festivalier_id,
        lignes=[LigneCommande(article=Article(name="Mojito"), quantite=2)],
        status="ACQUITTEE",
    )


def _make_catalog(*item_names: str) -> InMemoryItemCatalogRepository:
    """Return a catalog with the given items registered as normal alcoholic drinks."""
    catalog = InMemoryItemCatalogRepository()
    for name in item_names:
        catalog.register(ItemCost(name=name, item_type=ITEM_TYPE_NORMAL_ALCOHOLIC_DRINK))
    return catalog


class TestCreateChangeRequestUseCase:
    def setup_method(self):
        self.order_repo = InMemoryOrderRepository()
        self.change_request_repo = InMemoryChangeRequestRepository()
        self.notifications = MockNotificationAdapter()

        self.use_case = CreateChangeRequestUseCase(
            order_repository=self.order_repo,
            change_request_repository=self.change_request_repo,
            notification_port=self.notifications,
        )

    # ── Happy path ───────────────────────────────────────────────────────────

    def test_create_change_request_on_acknowledged_order_returns_request(self):
        """
        Given an acknowledged order
        When festivalier requests changes
        Then a change request is created with pending review status
        """
        self.order_repo.save(_make_acknowledged_order())

        cmd = CreateChangeRequestCommand(
            order_id="order-1",
            proposed_items=[{"name": "Bière", "quantity": 1}],
        )
        result = self.use_case.execute(cmd)

        assert result is not None
        assert result.id is not None
        assert result.order_id == "order-1"
        assert result.status == "EN_ATTENTE_REVIEW"
        assert result.proposed_items == [{"name": "Bière", "quantity": 1}]

    def test_create_change_request_is_persisted(self):
        """Created change request can be retrieved from the repository."""
        self.order_repo.save(_make_acknowledged_order())

        cmd = CreateChangeRequestCommand(
            order_id="order-1",
            proposed_items=[{"name": "Bière", "quantity": 2}],
        )
        result = self.use_case.execute(cmd)

        saved = self.change_request_repo.get_by_id(result.id)
        assert saved is not None
        assert saved.order_id == "order-1"

    def test_create_change_request_notifies_bartender(self):
        """
        Given an acknowledged order
        When festivalier requests changes
        Then a bartender notification is created and the change is pending review
        """
        self.order_repo.save(_make_acknowledged_order())

        cmd = CreateChangeRequestCommand(
            order_id="order-1",
            proposed_items=[{"name": "Bière", "quantity": 1}],
        )
        result = self.use_case.execute(cmd)

        assert len(self.notifications.bartender_notifications) == 1
        notification = self.notifications.bartender_notifications[0]
        assert notification["order_id"] == "order-1"
        assert notification["change_request_id"] == result.id

    def test_create_change_request_does_not_mutate_original_order(self):
        """The original order's items remain unchanged after creating a change request."""
        order = _make_acknowledged_order()
        self.order_repo.save(order)

        cmd = CreateChangeRequestCommand(
            order_id="order-1",
            proposed_items=[{"name": "Bière", "quantity": 5}],
        )
        self.use_case.execute(cmd)

        updated_order = self.order_repo.get_by_id("order-1")
        assert len(updated_order.lignes) == 1
        assert updated_order.lignes[0].article.name == "Mojito"
        assert updated_order.lignes[0].quantite == 2

    def test_create_change_request_works_for_prete_status(self):
        """A change request can also be created for orders that are ready (PRÊTE)."""
        order = _make_acknowledged_order()
        order.status = "PRÊTE"
        self.order_repo.save(order)

        cmd = CreateChangeRequestCommand(
            order_id="order-1",
            proposed_items=[{"name": "Bière", "quantity": 1}],
        )
        result = self.use_case.execute(cmd)

        assert result.status == "EN_ATTENTE_REVIEW"

    # ── Failure: order not found ─────────────────────────────────────────────

    def test_raises_order_not_found_when_order_does_not_exist(self):
        cmd = CreateChangeRequestCommand(
            order_id="ghost-99",
            proposed_items=[{"name": "Bière", "quantity": 1}],
        )
        with pytest.raises(OrderNotFoundException) as exc_info:
            self.use_case.execute(cmd)
        assert exc_info.value.order_id == "ghost-99"

    # ── Failure: wrong status ────────────────────────────────────────────────

    def test_raises_not_eligible_when_order_is_pending(self):
        """EN_ATTENTE orders should be modified directly via PATCH, not change requests."""
        order = _make_acknowledged_order()
        order.status = "EN_ATTENTE"
        self.order_repo.save(order)

        cmd = CreateChangeRequestCommand(
            order_id="order-1",
            proposed_items=[{"name": "Bière", "quantity": 1}],
        )
        with pytest.raises(OrderNotEligibleForChangeRequestException) as exc_info:
            self.use_case.execute(cmd)
        assert exc_info.value.order_id == "order-1"
        assert exc_info.value.current_status == "EN_ATTENTE"

    def test_raises_not_eligible_when_order_is_cancelled(self):
        """Cancelled orders are not eligible for change requests."""
        order = _make_acknowledged_order()
        order.status = "ANNULEE"
        self.order_repo.save(order)

        cmd = CreateChangeRequestCommand(
            order_id="order-1",
            proposed_items=[{"name": "Bière", "quantity": 1}],
        )
        with pytest.raises(OrderNotEligibleForChangeRequestException):
            self.use_case.execute(cmd)


class TestListChangeRequestsUseCase:
    def setup_method(self):
        self.order_repo = InMemoryOrderRepository()
        self.change_request_repo = InMemoryChangeRequestRepository()
        self.notifications = MockNotificationAdapter()

        self.create_use_case = CreateChangeRequestUseCase(
            order_repository=self.order_repo,
            change_request_repository=self.change_request_repo,
            notification_port=self.notifications,
        )
        self.list_use_case = ListChangeRequestsUseCase(
            order_repository=self.order_repo,
            change_request_repository=self.change_request_repo,
        )

    def test_list_returns_pending_change_requests_for_order(self):
        """Pending change requests are listed for the bartender UI."""
        self.order_repo.save(_make_acknowledged_order())

        self.create_use_case.execute(
            CreateChangeRequestCommand(
                order_id="order-1",
                proposed_items=[{"name": "Bière", "quantity": 1}],
            )
        )
        self.create_use_case.execute(
            CreateChangeRequestCommand(
                order_id="order-1",
                proposed_items=[{"name": "Eau plate", "quantity": 3}],
            )
        )

        result = self.list_use_case.execute(ListChangeRequestsCommand(order_id="order-1"))

        assert len(result) == 2
        assert all(cr.status == "EN_ATTENTE_REVIEW" for cr in result)

    def test_list_returns_empty_when_no_pending_requests(self):
        """An order with no change requests returns an empty list."""
        self.order_repo.save(_make_acknowledged_order())
        result = self.list_use_case.execute(ListChangeRequestsCommand(order_id="order-1"))
        assert result == []

    def test_list_raises_order_not_found_for_unknown_order(self):
        with pytest.raises(OrderNotFoundException):
            self.list_use_case.execute(ListChangeRequestsCommand(order_id="ghost"))

    def test_list_does_not_include_resolved_requests(self):
        """Resolved change requests (accepted/rejected) are not returned."""
        from app.domain.entities.change_request import ChangeRequest

        self.order_repo.save(_make_acknowledged_order())

        resolved = ChangeRequest(
            id="req-resolved",
            order_id="order-1",
            proposed_items=[{"name": "Bière", "quantity": 1}],
            status="ACCEPTEE",
        )
        self.change_request_repo.save(resolved)

        pending_cr = self.create_use_case.execute(
            CreateChangeRequestCommand(
                order_id="order-1",
                proposed_items=[{"name": "Eau plate", "quantity": 2}],
            )
        )

        result = self.list_use_case.execute(ListChangeRequestsCommand(order_id="order-1"))
        assert len(result) == 1
        assert result[0].id == pending_cr.id


class TestResolveChangeRequestUseCase:
    def setup_method(self):
        self.order_repo = InMemoryOrderRepository()
        self.change_request_repo = InMemoryChangeRequestRepository()
        self.notifications = MockNotificationAdapter()
        # Catalog with proposed items so ETA can be computed
        self.catalog_repo = _make_catalog("Mojito", "Bière")
        self.stock_repo = InMemoryStockRepository()

        create_use_case = CreateChangeRequestUseCase(
            order_repository=self.order_repo,
            change_request_repository=self.change_request_repo,
            notification_port=self.notifications,
        )
        self.resolve_use_case = ResolveChangeRequestUseCase(
            order_repository=self.order_repo,
            change_request_repository=self.change_request_repo,
            notification_port=self.notifications,
            stock_repository=self.stock_repo,
            item_catalog_repository=self.catalog_repo,
        )

        # Place an acknowledged order and a pending change request
        order = _make_acknowledged_order()
        self.order_repo.save(order)
        self.change_request = create_use_case.execute(
            CreateChangeRequestCommand(
                order_id="order-1",
                proposed_items=[{"name": "Bière", "quantity": 3}],
            )
        )

    # ── Accept ───────────────────────────────────────────────────────────────

    def test_accepting_change_request_updates_order_items(self):
        """
        Scenario: Bartender accepts change request
        Given a pending change request
        When bartender accepts
        Then the order's items are updated with the proposed items
        """
        cmd = ResolveChangeRequestCommand(
            order_id="order-1",
            request_id=self.change_request.id,
            accept=True,
        )
        self.resolve_use_case.execute(cmd)

        updated_order = self.order_repo.get_by_id("order-1")
        assert len(updated_order.lignes) == 1
        assert updated_order.lignes[0].article.name == "Bière"
        assert updated_order.lignes[0].quantite == 3

    def test_accepting_change_request_marks_it_as_accepted(self):
        cmd = ResolveChangeRequestCommand(
            order_id="order-1",
            request_id=self.change_request.id,
            accept=True,
        )
        self.resolve_use_case.execute(cmd)

        updated_cr = self.change_request_repo.get_by_id(self.change_request.id)
        assert updated_cr.status == "ACCEPTEE"

    def test_accepting_change_request_notifies_festivalier(self):
        cmd = ResolveChangeRequestCommand(
            order_id="order-1",
            request_id=self.change_request.id,
            accept=True,
        )
        self.resolve_use_case.execute(cmd)

        festivalier_notifications = self.notifications.festivalier_notifications
        assert len(festivalier_notifications) == 1
        notif = festivalier_notifications[0]
        assert notif["festivalier_id"] == "f-1"
        assert notif["order_id"] == "order-1"
        assert notif["accepted"] is True
        assert notif["rejection_reason"] is None
        assert isinstance(notif["new_eta_minutes"], int)

    # ── Reject ───────────────────────────────────────────────────────────────

    def test_rejecting_change_request_does_not_change_order_items(self):
        """
        Scenario: Bartender rejects change request
        Given a pending change request
        When bartender rejects with a reason
        Then the original order items remain unchanged
        """
        cmd = ResolveChangeRequestCommand(
            order_id="order-1",
            request_id=self.change_request.id,
            accept=False,
            rejection_reason="Items already prepared",
        )
        self.resolve_use_case.execute(cmd)

        unchanged_order = self.order_repo.get_by_id("order-1")
        assert len(unchanged_order.lignes) == 1
        assert unchanged_order.lignes[0].article.name == "Mojito"
        assert unchanged_order.lignes[0].quantite == 2

    def test_rejecting_change_request_marks_it_as_rejected(self):
        cmd = ResolveChangeRequestCommand(
            order_id="order-1",
            request_id=self.change_request.id,
            accept=False,
            rejection_reason="Already started",
        )
        self.resolve_use_case.execute(cmd)

        updated_cr = self.change_request_repo.get_by_id(self.change_request.id)
        assert updated_cr.status == "REJETEE"
        assert updated_cr.rejection_reason == "Already started"

    def test_rejecting_change_request_notifies_festivalier_with_reason(self):
        cmd = ResolveChangeRequestCommand(
            order_id="order-1",
            request_id=self.change_request.id,
            accept=False,
            rejection_reason="Bière out of stock",
        )
        self.resolve_use_case.execute(cmd)

        festivalier_notifications = self.notifications.festivalier_notifications
        assert len(festivalier_notifications) == 1
        notif = festivalier_notifications[0]
        assert notif["accepted"] is False
        assert notif["rejection_reason"] == "Bière out of stock"

    # ── Failure cases ────────────────────────────────────────────────────────

    def test_raises_order_not_found_when_order_does_not_exist(self):
        cmd = ResolveChangeRequestCommand(
            order_id="ghost",
            request_id=self.change_request.id,
            accept=True,
        )
        with pytest.raises(OrderNotFoundException):
            self.resolve_use_case.execute(cmd)

    def test_raises_change_request_not_found_when_request_does_not_exist(self):
        cmd = ResolveChangeRequestCommand(
            order_id="order-1",
            request_id="ghost-req",
            accept=True,
        )
        with pytest.raises(ChangeRequestNotFoundException) as exc_info:
            self.resolve_use_case.execute(cmd)
        assert exc_info.value.request_id == "ghost-req"

    def test_raises_change_request_not_found_when_request_belongs_to_different_order(self):
        """A change request from another order cannot be resolved for this order."""
        other_order = _make_acknowledged_order(order_id="order-99", festivalier_id="f-99")
        self.order_repo.save(other_order)

        other_notifications = MockNotificationAdapter()
        other_cr_repo = InMemoryChangeRequestRepository()
        other_create = CreateChangeRequestUseCase(
            order_repository=self.order_repo,
            change_request_repository=other_cr_repo,
            notification_port=other_notifications,
        )
        other_cr = other_create.execute(
            CreateChangeRequestCommand(
                order_id="order-99",
                proposed_items=[{"name": "Eau plate", "quantity": 1}],
            )
        )

        # Save into the same repo (simulates cross-contamination attempt)
        self.change_request_repo.save(other_cr)

        cmd = ResolveChangeRequestCommand(
            order_id="order-1",  # different order
            request_id=other_cr.id,
            accept=True,
        )
        with pytest.raises(ChangeRequestNotFoundException):
            self.resolve_use_case.execute(cmd)


class TestResolveChangeRequestTransferAndETA:
    """Tests for prepared-item transfer logic and ETA recomputation on acceptance.

    Acceptance criteria from the issue:
    - When accepting and prepared items can be transferred, the order ETA is
      reduced to cover only the items that still need preparation.
    - When accepting and no prepared items are reusable, the full ETA for all
      proposed items is computed.
    - Audit fields (resolver_id, resolved_at) are always persisted.
    """

    def setup_method(self):
        self.order_repo = InMemoryOrderRepository()
        self.change_request_repo = InMemoryChangeRequestRepository()
        self.notifications = MockNotificationAdapter()
        # Catalog: Mojito and Bière are normal alcoholic drinks (2 min × qty)
        self.catalog_repo = _make_catalog("Mojito", "Bière")
        # Start with no prepared stock; individual tests can add prepared items
        self.stock_repo = InMemoryStockRepository()

        create_use_case = CreateChangeRequestUseCase(
            order_repository=self.order_repo,
            change_request_repository=self.change_request_repo,
            notification_port=self.notifications,
        )
        self.resolve_use_case = ResolveChangeRequestUseCase(
            order_repository=self.order_repo,
            change_request_repository=self.change_request_repo,
            notification_port=self.notifications,
            stock_repository=self.stock_repo,
            item_catalog_repository=self.catalog_repo,
        )

        # Acknowledged order: Mojito x2 (originally placed)
        order = _make_acknowledged_order()
        order.eta_minutes = 4  # 2 min × 2 Mojitos
        self.order_repo.save(order)

        # Festivalier requests: Mojito x1 + Bière x2 (modified composition)
        self.change_request = create_use_case.execute(
            CreateChangeRequestCommand(
                order_id="order-1",
                proposed_items=[
                    {"name": "Mojito", "quantity": 1},
                    {"name": "Bière", "quantity": 2},
                ],
            )
        )

    # ── Scenario: Accept when transfer possible ───────────────────────────────

    def test_accept_with_prepared_transfer_reduces_eta(self):
        """
        Scenario: Accept change when transfer possible
        Given an acknowledged order and Mojito x1 is already prepared
        When bartender accepts the change request
        Then ETA covers only Bière x2 (the item not yet prepared)
        """
        # Mojito x1 is already in prepared stock → transferable
        self.stock_repo.prepared_stock["Mojito"] = 1

        cmd = ResolveChangeRequestCommand(
            order_id="order-1",
            request_id=self.change_request.id,
            accept=True,
            resolver_id="bartender-1",
        )
        self.resolve_use_case.execute(cmd)

        updated_order = self.order_repo.get_by_id("order-1")
        # Only Bière x2 still needs preparation → 2 min × 2 = 4 min
        assert updated_order.eta_minutes == 4

    def test_accept_with_full_transfer_gives_zero_eta(self):
        """
        Given all proposed items are in prepared stock
        When bartender accepts the change request
        Then ETA is 0 (nothing left to prepare)
        """
        # Both Mojito x1 and Bière x2 are already prepared
        self.stock_repo.prepared_stock["Mojito"] = 1
        self.stock_repo.prepared_stock["Bière"] = 2

        cmd = ResolveChangeRequestCommand(
            order_id="order-1",
            request_id=self.change_request.id,
            accept=True,
            resolver_id="bartender-1",
        )
        self.resolve_use_case.execute(cmd)

        updated_order = self.order_repo.get_by_id("order-1")
        assert updated_order.eta_minutes == 0

    def test_accept_with_full_transfer_notifies_with_new_eta(self):
        """Festivalier is notified with the updated (reduced) ETA on acceptance."""
        self.stock_repo.prepared_stock["Mojito"] = 1

        cmd = ResolveChangeRequestCommand(
            order_id="order-1",
            request_id=self.change_request.id,
            accept=True,
            resolver_id="bartender-1",
        )
        self.resolve_use_case.execute(cmd)

        notif = self.notifications.festivalier_notifications[0]
        assert notif["accepted"] is True
        assert isinstance(notif["new_eta_minutes"], int)
        # Mojito x1 transferred; only Bière x2 needs preparation → 4 min
        assert notif["new_eta_minutes"] == 4

    # ── Scenario: Accept when no transfer possible ────────────────────────────

    def test_accept_without_prepared_transfer_computes_full_eta(self):
        """
        Given no prepared items exist for any proposed item
        When bartender accepts the change request
        Then ETA covers the full proposed composition (Mojito x1 + Bière x2 = 6 min)
        """
        # No prepared stock at all
        cmd = ResolveChangeRequestCommand(
            order_id="order-1",
            request_id=self.change_request.id,
            accept=True,
            resolver_id="bartender-1",
        )
        self.resolve_use_case.execute(cmd)

        updated_order = self.order_repo.get_by_id("order-1")
        # Mojito x1 (2 min) + Bière x2 (4 min) = 6 min
        assert updated_order.eta_minutes == 6

    def test_accept_without_transfer_notifies_with_full_eta(self):
        """Festivalier is notified with the full ETA when no transfer is possible."""
        cmd = ResolveChangeRequestCommand(
            order_id="order-1",
            request_id=self.change_request.id,
            accept=True,
            resolver_id="bartender-1",
        )
        self.resolve_use_case.execute(cmd)

        notif = self.notifications.festivalier_notifications[0]
        assert notif["accepted"] is True
        assert notif["new_eta_minutes"] == 6

    # ── Audit trail ───────────────────────────────────────────────────────────

    def test_accept_persists_resolver_id_and_resolved_at(self):
        """
        Audit trail: resolver_id and resolved_at are stored on the change request
        when the bartender accepts.
        """
        cmd = ResolveChangeRequestCommand(
            order_id="order-1",
            request_id=self.change_request.id,
            accept=True,
            resolver_id="bartender-42",
        )
        self.resolve_use_case.execute(cmd)

        saved_cr = self.change_request_repo.get_by_id(self.change_request.id)
        assert saved_cr.resolver_id == "bartender-42"
        assert saved_cr.resolved_at is not None

    def test_reject_persists_resolver_id_and_resolved_at(self):
        """
        Audit trail: resolver_id and resolved_at are stored on the change request
        when the bartender rejects.
        """
        cmd = ResolveChangeRequestCommand(
            order_id="order-1",
            request_id=self.change_request.id,
            accept=False,
            resolver_id="bartender-42",
            rejection_reason="Items already prepared",
        )
        self.resolve_use_case.execute(cmd)

        saved_cr = self.change_request_repo.get_by_id(self.change_request.id)
        assert saved_cr.resolver_id == "bartender-42"
        assert saved_cr.resolved_at is not None
        assert saved_cr.status == "REJETEE"

    def test_reject_does_not_include_eta_in_notification(self):
        """On rejection, new_eta_minutes in the notification is None."""
        cmd = ResolveChangeRequestCommand(
            order_id="order-1",
            request_id=self.change_request.id,
            accept=False,
            rejection_reason="Already started",
        )
        self.resolve_use_case.execute(cmd)

        notif = self.notifications.festivalier_notifications[0]
        assert notif["accepted"] is False
        assert notif["new_eta_minutes"] is None

    def test_partial_prepared_transfer_computes_remaining_eta(self):
        """
        Given Mojito x1 is prepared but the order requires Mojito x1 (fully covered)
        and Bière x2 (not covered at all), only Bière x2 contributes to ETA.
        """
        # Partially prepare: only Mojito x1 available (covers full Mojito request)
        self.stock_repo.prepared_stock["Mojito"] = 5  # more than enough

        cmd = ResolveChangeRequestCommand(
            order_id="order-1",
            request_id=self.change_request.id,
            accept=True,
        )
        self.resolve_use_case.execute(cmd)

        updated_order = self.order_repo.get_by_id("order-1")
        # Mojito fully covered; Bière x2 still needs prep → 2 × 2 = 4 min
        assert updated_order.eta_minutes == 4
