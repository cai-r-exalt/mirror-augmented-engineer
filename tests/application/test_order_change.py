"""Application integration tests for the order-change and change-request endpoints.

These tests exercise the full wiring through controller → use cases → in-memory
adapters and verify correct HTTP status codes and response shapes.
"""

import pytest

from app.application.controllers.order_change_controller import OrderChangeController
from app.application.dto.order_change import (
    CreateChangeRequestRequest,
    ModifyOrderRequest,
    ResolveChangeRequestRequest,
)
from app.domain.entities.commande import Article, Commande, LigneCommande
from app.domain.use_cases.create_change_request import CreateChangeRequestUseCase
from app.domain.use_cases.list_change_requests import ListChangeRequestsUseCase
from app.domain.use_cases.modify_order import ModifyOrderUseCase
from app.domain.use_cases.resolve_change_request import ResolveChangeRequestUseCase
from app.infrastructure.adapters.in_memory_change_request_repository import (
    InMemoryChangeRequestRepository,
)
from app.infrastructure.adapters.in_memory_order_repository import InMemoryOrderRepository
from app.infrastructure.adapters.in_memory_stock_repository import InMemoryStockRepository
from app.infrastructure.adapters.mock_notification_adapter import MockNotificationAdapter


def _build_controller():
    order_repo = InMemoryOrderRepository()
    stock_repo = InMemoryStockRepository({"Mojito": 10, "Bière": 8, "Eau plate": 20})
    change_request_repo = InMemoryChangeRequestRepository()
    notifications = MockNotificationAdapter()

    modify_uc = ModifyOrderUseCase(order_repository=order_repo, stock_repository=stock_repo)
    create_cr_uc = CreateChangeRequestUseCase(
        order_repository=order_repo,
        change_request_repository=change_request_repo,
        notification_port=notifications,
    )
    list_cr_uc = ListChangeRequestsUseCase(
        order_repository=order_repo,
        change_request_repository=change_request_repo,
    )
    resolve_cr_uc = ResolveChangeRequestUseCase(
        order_repository=order_repo,
        change_request_repository=change_request_repo,
        notification_port=notifications,
    )

    controller = OrderChangeController(
        modify_order_use_case=modify_uc,
        create_change_request_use_case=create_cr_uc,
        list_change_requests_use_case=list_cr_uc,
        resolve_change_request_use_case=resolve_cr_uc,
    )

    return controller, order_repo, stock_repo, change_request_repo, notifications


# ── PATCH /orders/{order_id} ──────────────────────────────────────────────────

class TestModifyOrderEndpoint:
    def setup_method(self):
        self.controller, self.order_repo, self.stock_repo, self.cr_repo, self.notifications = (
            _build_controller()
        )
        # Place a pending order (Mojito x2, stock decremented to 8)
        self.stock_repo.decrement("Mojito", 2)
        self.order = Commande(
            id="order-1",
            festivalier_id="f-1",
            lignes=[LigneCommande(article=Article(name="Mojito"), quantite=2)],
            status="EN_ATTENTE",
        )
        self.order_repo.save(self.order)

    def test_returns_200_and_updated_order_when_modification_succeeds(self):
        """
        Given an unacknowledged order and sufficient tokens/stock
        When festivalier requests modifications via PATCH
        Then modifications are accepted and tokens/stock validated
        """
        req = ModifyOrderRequest(
            order_id="order-1", items=[{"name": "Bière", "quantity": 2}]
        )
        response = self.controller.modify_order(req)

        assert response.status_code == 200
        body = response.json()
        assert body["orderId"] == "order-1"
        assert body["status"] == "EN_ATTENTE"

    def test_returns_400_when_items_missing(self):
        req = ModifyOrderRequest(order_id="order-1", items=None)
        response = self.controller.modify_order(req)
        assert response.status_code == 400

    def test_returns_400_when_items_is_empty_list(self):
        req = ModifyOrderRequest(order_id="order-1", items=[])
        response = self.controller.modify_order(req)
        assert response.status_code == 400

    def test_returns_400_when_item_missing_quantity(self):
        req = ModifyOrderRequest(order_id="order-1", items=[{"name": "Bière"}])
        response = self.controller.modify_order(req)
        assert response.status_code == 400

    def test_returns_404_when_order_not_found(self):
        req = ModifyOrderRequest(
            order_id="ghost-99", items=[{"name": "Bière", "quantity": 1}]
        )
        response = self.controller.modify_order(req)
        assert response.status_code == 404

    def test_returns_422_when_order_is_already_acknowledged(self):
        self.order.status = "ACQUITTEE"
        self.order_repo.save(self.order)

        req = ModifyOrderRequest(
            order_id="order-1", items=[{"name": "Bière", "quantity": 1}]
        )
        response = self.controller.modify_order(req)
        assert response.status_code == 422

    def test_returns_409_when_item_is_out_of_stock(self):
        req = ModifyOrderRequest(
            order_id="order-1", items=[{"name": "Bière", "quantity": 99}]
        )
        response = self.controller.modify_order(req)
        assert response.status_code == 409

    def test_returns_409_when_item_is_unknown(self):
        req = ModifyOrderRequest(
            order_id="order-1", items=[{"name": "Champagne", "quantity": 1}]
        )
        response = self.controller.modify_order(req)
        assert response.status_code == 409


# ── POST /orders/{order_id}/change-requests ───────────────────────────────────

class TestCreateChangeRequestEndpoint:
    def setup_method(self):
        self.controller, self.order_repo, self.stock_repo, self.cr_repo, self.notifications = (
            _build_controller()
        )
        self.order = Commande(
            id="order-1",
            festivalier_id="f-1",
            lignes=[LigneCommande(article=Article(name="Mojito"), quantite=2)],
            status="ACQUITTEE",
        )
        self.order_repo.save(self.order)

    def test_returns_201_with_change_request_id(self):
        """
        Given an acknowledged order
        When festivalier requests changes
        Then a bartender notification is created and the change is pending review
        """
        req = CreateChangeRequestRequest(
            order_id="order-1",
            proposed_items=[{"name": "Bière", "quantity": 1}],
        )
        response = self.controller.create_change_request(req)

        assert response.status_code == 201
        body = response.json()
        assert "changeRequestId" in body
        assert body["status"] == "EN_ATTENTE_REVIEW"

    def test_returns_400_when_proposed_items_missing(self):
        req = CreateChangeRequestRequest(order_id="order-1", proposed_items=None)
        response = self.controller.create_change_request(req)
        assert response.status_code == 400

    def test_returns_404_when_order_not_found(self):
        req = CreateChangeRequestRequest(
            order_id="ghost", proposed_items=[{"name": "Bière", "quantity": 1}]
        )
        response = self.controller.create_change_request(req)
        assert response.status_code == 404

    def test_returns_422_when_order_is_pending(self):
        """EN_ATTENTE orders should use PATCH, not change requests."""
        self.order.status = "EN_ATTENTE"
        self.order_repo.save(self.order)

        req = CreateChangeRequestRequest(
            order_id="order-1",
            proposed_items=[{"name": "Bière", "quantity": 1}],
        )
        response = self.controller.create_change_request(req)
        assert response.status_code == 422


# ── GET /orders/{order_id}/change-requests ────────────────────────────────────

class TestListChangeRequestsEndpoint:
    def setup_method(self):
        self.controller, self.order_repo, self.stock_repo, self.cr_repo, self.notifications = (
            _build_controller()
        )
        self.order = Commande(
            id="order-1",
            festivalier_id="f-1",
            lignes=[LigneCommande(article=Article(name="Mojito"), quantite=2)],
            status="ACQUITTEE",
        )
        self.order_repo.save(self.order)

    def test_returns_200_with_pending_change_requests(self):
        # Create two change requests first
        self.controller.create_change_request(
            CreateChangeRequestRequest(
                order_id="order-1", proposed_items=[{"name": "Bière", "quantity": 1}]
            )
        )
        self.controller.create_change_request(
            CreateChangeRequestRequest(
                order_id="order-1", proposed_items=[{"name": "Eau plate", "quantity": 2}]
            )
        )

        response = self.controller.list_change_requests("order-1")

        assert response.status_code == 200
        body = response.json()
        assert "changeRequests" in body
        assert len(body["changeRequests"]) == 2

    def test_returns_200_with_empty_list_when_no_requests(self):
        response = self.controller.list_change_requests("order-1")
        assert response.status_code == 200
        assert response.json()["changeRequests"] == []

    def test_returns_404_when_order_not_found(self):
        response = self.controller.list_change_requests("ghost")
        assert response.status_code == 404


# ── POST /orders/{order_id}/change-requests/{req_id}/resolve ─────────────────

class TestResolveChangeRequestEndpoint:
    def setup_method(self):
        self.controller, self.order_repo, self.stock_repo, self.cr_repo, self.notifications = (
            _build_controller()
        )
        self.order = Commande(
            id="order-1",
            festivalier_id="f-1",
            lignes=[LigneCommande(article=Article(name="Mojito"), quantite=2)],
            status="ACQUITTEE",
        )
        self.order_repo.save(self.order)

        create_response = self.controller.create_change_request(
            CreateChangeRequestRequest(
                order_id="order-1", proposed_items=[{"name": "Bière", "quantity": 3}]
            )
        )
        self.change_request_id = create_response.json()["changeRequestId"]

    def test_returns_200_when_bartender_accepts(self):
        req = ResolveChangeRequestRequest(
            order_id="order-1", request_id=self.change_request_id, accept=True
        )
        response = self.controller.resolve_change_request(req)

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ACCEPTEE"

    def test_returns_200_when_bartender_rejects_with_reason(self):
        req = ResolveChangeRequestRequest(
            order_id="order-1",
            request_id=self.change_request_id,
            accept=False,
            rejection_reason="Items already prepared",
        )
        response = self.controller.resolve_change_request(req)

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "REJETEE"
        assert body["rejectionReason"] == "Items already prepared"

    def test_returns_404_when_order_not_found(self):
        req = ResolveChangeRequestRequest(
            order_id="ghost", request_id=self.change_request_id, accept=True
        )
        response = self.controller.resolve_change_request(req)
        assert response.status_code == 404

    def test_returns_404_when_change_request_not_found(self):
        req = ResolveChangeRequestRequest(
            order_id="order-1", request_id="ghost-req", accept=True
        )
        response = self.controller.resolve_change_request(req)
        assert response.status_code == 404

    def test_returns_400_when_accept_is_none(self):
        req = ResolveChangeRequestRequest(
            order_id="order-1", request_id=self.change_request_id, accept=None
        )
        response = self.controller.resolve_change_request(req)
        assert response.status_code == 400
