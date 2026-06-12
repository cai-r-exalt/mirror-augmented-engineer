from typing import Any

import pytest

from app.domain.entities.commande import Article, Commande, ContributorContribution, LigneCommande
from app.domain.exceptions import (
    OrderNotReadyTransitionableException,
    PreparedStockInsufficientException,
)
from app.domain.use_cases.mark_order_ready import MarkOrderReadyCommand, MarkOrderReadyUseCase
from app.domain.value_objects.token_contribution import TokenContribution
from app.infrastructure.adapters.in_memory_order_repository import InMemoryOrderRepository
from app.infrastructure.adapters.in_memory_stock_repository import InMemoryStockRepository
from app.infrastructure.adapters.mock_notification_adapter import MockNotificationAdapter


def _acknowledged_order(order_id: str, festivalier_id: str, items: list[dict[str, Any]]) -> Commande:
    lignes = [LigneCommande(article=Article(name=item["name"]), quantite=item["quantity"]) for item in items]
    return Commande(id=order_id, festivalier_id=festivalier_id, lignes=lignes, status="ACKNOWLEDGED")


class TestMarkOrderReadyUseCase:
    def test_marks_order_ready_and_notifies_festivalier(self):
        order_repo = InMemoryOrderRepository()
        stock_repo = InMemoryStockRepository(initial_prepared_stock={"Bière": 2})
        notifications = MockNotificationAdapter()
        use_case = MarkOrderReadyUseCase(order_repo, stock_repo, notifications)
        order_repo.save(_acknowledged_order("order-1", "f-1", [{"name": "Bière", "quantity": 2}]))

        result = use_case.execute(MarkOrderReadyCommand(order_id="order-1"))

        assert result.status == "READY"
        assert result.ready_at is not None
        assert stock_repo.prepared_stock["Bière"] == 0
        assert len(notifications.ready_notifications) == 1
        assert notifications.ready_notifications[0]["festivalier_id"] == "f-1"
        assert notifications.ready_notifications[0]["order_id"] == "order-1"

    def test_raises_when_prepared_items_are_insufficient(self):
        order_repo = InMemoryOrderRepository()
        stock_repo = InMemoryStockRepository(initial_prepared_stock={"Bière": 1})
        notifications = MockNotificationAdapter()
        use_case = MarkOrderReadyUseCase(order_repo, stock_repo, notifications)
        order_repo.save(_acknowledged_order("order-1", "f-1", [{"name": "Bière", "quantity": 2}]))

        with pytest.raises(PreparedStockInsufficientException):
            use_case.execute(MarkOrderReadyCommand(order_id="order-1"))

        persisted = order_repo.get_by_id("order-1")
        assert persisted is not None
        assert persisted.status == "ACKNOWLEDGED"
        assert persisted.ready_at is None
        assert notifications.ready_notifications == []

    def test_notifies_all_contributors_for_group_order(self):
        order_repo = InMemoryOrderRepository()
        stock_repo = InMemoryStockRepository(initial_prepared_stock={"Bière": 2})
        notifications = MockNotificationAdapter()
        use_case = MarkOrderReadyUseCase(order_repo, stock_repo, notifications)
        order = _acknowledged_order("order-grp", "GROUP", [{"name": "Bière", "quantity": 2}])
        order.contributors = [
            ContributorContribution(
                festivalier_id="f-1",
                contribution=TokenContribution(drink_tokens=1, food_tokens=0),
            ),
            ContributorContribution(
                festivalier_id="f-2",
                contribution=TokenContribution(drink_tokens=1, food_tokens=0),
            ),
        ]
        order_repo.save(order)

        use_case.execute(MarkOrderReadyCommand(order_id="order-grp"))

        notified_festivalier_ids = sorted(
            notif["festivalier_id"] for notif in notifications.ready_notifications
        )
        assert notified_festivalier_ids == ["f-1", "f-2"]

    def test_raises_when_order_not_acknowledged(self):
        order_repo = InMemoryOrderRepository()
        stock_repo = InMemoryStockRepository(initial_prepared_stock={"Bière": 2})
        notifications = MockNotificationAdapter()
        use_case = MarkOrderReadyUseCase(order_repo, stock_repo, notifications)
        order = _acknowledged_order("order-1", "f-1", [{"name": "Bière", "quantity": 1}])
        order.status = "EN_ATTENTE"
        order_repo.save(order)

        with pytest.raises(OrderNotReadyTransitionableException):
            use_case.execute(MarkOrderReadyCommand(order_id="order-1"))
