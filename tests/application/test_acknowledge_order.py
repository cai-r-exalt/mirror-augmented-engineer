"""Application integration tests for POST /orders/{order_id}/acknowledge.

These tests exercise the full wiring through controller → use case → in-memory
adapters and verify correct HTTP status codes, response shapes, and token deduction.
"""


from app.application.controllers.acknowledge_order_controller import AcknowledgeOrderController
from app.application.dto.acknowledge_order import AcknowledgeOrderRequest
from app.domain.entities.commande import Article, Commande, ContributorContribution, LigneCommande
from app.domain.ports.item_catalog_repository import (
    ITEM_TYPE_MEAL,
    ITEM_TYPE_NON_ALCOHOLIC_DRINK,
    ITEM_TYPE_NORMAL_ALCOHOLIC_DRINK,
    ITEM_TYPE_PREMIUM_ALCOHOLIC_DRINK,
    ITEM_TYPE_SNACK,
    ItemCost,
)
from app.domain.use_cases.acknowledge_order import AcknowledgeOrderUseCase
from app.domain.value_objects.token_contribution import TokenContribution
from app.infrastructure.adapters.in_memory_festivalier_repository import InMemoryFestivalierRepository
from app.infrastructure.adapters.in_memory_item_catalog_repository import InMemoryItemCatalogRepository
from app.infrastructure.adapters.in_memory_order_repository import InMemoryOrderRepository
from app.infrastructure.adapters.in_memory_stock_repository import InMemoryStockRepository
from app.infrastructure.adapters.mock_notification_adapter import MockNotificationAdapter


def _build_infrastructure(stock: dict | None = None, balances: dict | None = None):
    order_repo = InMemoryOrderRepository()
    stock_repo = InMemoryStockRepository(stock or {"Bière": 10, "Whisky": 5, "Chips": 10, "Burger": 10, "Eau": 10})
    catalog_repo = InMemoryItemCatalogRepository()
    catalog_repo.register(ItemCost("Eau", drink_tokens_per_unit=0, item_type=ITEM_TYPE_NON_ALCOHOLIC_DRINK))
    catalog_repo.register(ItemCost("Bière", drink_tokens_per_unit=1, item_type=ITEM_TYPE_NORMAL_ALCOHOLIC_DRINK))
    catalog_repo.register(ItemCost("Whisky", drink_tokens_per_unit=2, item_type=ITEM_TYPE_PREMIUM_ALCOHOLIC_DRINK))
    catalog_repo.register(ItemCost("Chips", food_tokens_per_unit=1, item_type=ITEM_TYPE_SNACK))
    catalog_repo.register(ItemCost("Burger", food_tokens_per_unit=3, item_type=ITEM_TYPE_MEAL))
    festivalier_repo = InMemoryFestivalierRepository(
        balances or {"f-1": {"drink_tokens": 20, "food_tokens": 20}}
    )
    notifications = MockNotificationAdapter()

    use_case = AcknowledgeOrderUseCase(
        order_repository=order_repo,
        stock_repository=stock_repo,
        item_catalog_repository=catalog_repo,
        festivalier_repository=festivalier_repo,
        notification_port=notifications,
    )
    controller = AcknowledgeOrderController(acknowledge_order_use_case=use_case)
    return controller, order_repo, stock_repo, festivalier_repo, notifications


def _pending_order(order_id: str, festivalier_id: str, items: list) -> Commande:
    lignes = [
        LigneCommande(article=Article(name=item["name"]), quantite=item["quantity"])
        for item in items
    ]
    return Commande(id=order_id, festivalier_id=festivalier_id, lignes=lignes, status="EN_ATTENTE")


class TestAcknowledgeOrderEndpoint:
    """Integration tests for the acknowledge order controller."""

    def setup_method(self):
        self.controller, self.order_repo, self.stock_repo, self.festivalier_repo, self.notifications = (
            _build_infrastructure()
        )

    # ── Success cases ────────────────────────────────────────────────────────

    def test_returns_200_with_acknowledged_status_and_eta(self):
        """
        Given a pending order with mixed drinks and meals
        When bartender acknowledges it
        Then response is 200 with ACKNOWLEDGED status and calculated eta_minutes
        """
        order = _pending_order("order-1", "f-1", [
            {"name": "Bière", "quantity": 2},
            {"name": "Burger", "quantity": 1},
        ])
        self.order_repo.save(order)

        response = self.controller.acknowledge_order(AcknowledgeOrderRequest("order-1"))

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ACKNOWLEDGED"
        assert body["orderId"] == "order-1"
        assert body["etaMinutes"] == 16  # 2×2=4 (normal alc) + 10+2=12 (meal + longest_drink=2)
        assert body["acknowledgedAt"] is not None

    def test_returns_200_for_non_alcoholic_only_order(self):
        """Non-alcoholic only order: 1 type → 1 minute ETA."""
        order = _pending_order("order-1", "f-1", [{"name": "Eau", "quantity": 3}])
        self.order_repo.save(order)

        response = self.controller.acknowledge_order(AcknowledgeOrderRequest("order-1"))

        assert response.status_code == 200
        assert response.json()["etaMinutes"] == 1

    def test_token_deduction_occurs_at_acknowledgement(self):
        """
        Given a solo order for 2 Bière (1 drink token each) + 1 Chips (1 food token)
        When bartender acknowledges it
        Then festivalier's drink balance is reduced by 2 and food balance by 1
        """
        order = _pending_order("order-1", "f-1", [
            {"name": "Bière", "quantity": 2},
            {"name": "Chips", "quantity": 1},
        ])
        self.order_repo.save(order)

        before = self.festivalier_repo.get_balance("f-1")
        self.controller.acknowledge_order(AcknowledgeOrderRequest("order-1"))
        after = self.festivalier_repo.get_balance("f-1")

        assert after.drink_tokens == before.drink_tokens - 2
        assert after.food_tokens == before.food_tokens - 1

    def test_notification_sent_after_acknowledgement(self):
        """Festivalier is notified with the ETA after acknowledgement."""
        order = _pending_order("order-1", "f-1", [{"name": "Whisky", "quantity": 1}])
        self.order_repo.save(order)

        self.controller.acknowledge_order(AcknowledgeOrderRequest("order-1"))

        assert len(self.notifications.acknowledgement_notifications) == 1
        notif = self.notifications.acknowledgement_notifications[0]
        assert notif["order_id"] == "order-1"
        assert notif["festivalier_id"] == "f-1"
        assert notif["eta_minutes"] == 3  # 1 premium × 3

    # ── Error cases ──────────────────────────────────────────────────────────

    def test_returns_404_when_order_not_found(self):
        response = self.controller.acknowledge_order(AcknowledgeOrderRequest("nonexistent"))
        assert response.status_code == 404
        assert "not found" in response.json()["error"].lower()

    def test_returns_422_when_order_already_acknowledged(self):
        order = _pending_order("order-1", "f-1", [{"name": "Bière", "quantity": 1}])
        order.status = "ACKNOWLEDGED"
        self.order_repo.save(order)

        response = self.controller.acknowledge_order(AcknowledgeOrderRequest("order-1"))
        assert response.status_code == 422

    def test_returns_422_when_order_is_cancelled(self):
        order = _pending_order("order-1", "f-1", [{"name": "Bière", "quantity": 1}])
        order.status = "ANNULEE"
        self.order_repo.save(order)

        response = self.controller.acknowledge_order(AcknowledgeOrderRequest("order-1"))
        assert response.status_code == 422

    def test_returns_422_when_stock_insufficient_at_acknowledge(self):
        """Prevent acknowledgement when stock is no longer sufficient."""
        controller, order_repo, stock_repo, _, _ = _build_infrastructure(
            stock={"Bière": 2}
        )
        order = _pending_order("order-1", "f-1", [{"name": "Bière", "quantity": 5}])
        order_repo.save(order)

        response = controller.acknowledge_order(AcknowledgeOrderRequest("order-1"))
        assert response.status_code == 422

    def test_no_token_deduction_when_stock_check_fails(self):
        """Tokens must remain unchanged when acknowledgement is blocked by insufficient stock."""
        controller, order_repo, _, festivalier_repo, _ = _build_infrastructure(
            stock={"Bière": 2},
            balances={"f-1": {"drink_tokens": 10, "food_tokens": 0}},
        )
        order = _pending_order("order-1", "f-1", [{"name": "Bière", "quantity": 5}])
        order_repo.save(order)

        before = festivalier_repo.get_balance("f-1")
        controller.acknowledge_order(AcknowledgeOrderRequest("order-1"))
        after = festivalier_repo.get_balance("f-1")

        assert after.drink_tokens == before.drink_tokens


class TestAcknowledgeGroupOrderTokenDeduction:
    """Integration test showing token deduction for group orders at acknowledgement."""

    def test_group_order_deducts_pledged_amounts(self):
        """
        Given a group order with two contributors
        When bartender acknowledges it
        Then each contributor's pledged tokens are deducted from their balance
        """
        controller, order_repo, _, festivalier_repo, _ = _build_infrastructure(
            balances={
                "f-1": {"drink_tokens": 10, "food_tokens": 0},
                "f-2": {"drink_tokens": 8, "food_tokens": 0},
            }
        )
        order = Commande(
            id="order-grp",
            festivalier_id="GROUP",
            lignes=[LigneCommande(article=Article(name="Bière"), quantite=3)],
            status="EN_ATTENTE",
            contributors=[
                ContributorContribution(
                    festivalier_id="f-1",
                    contribution=TokenContribution(drink_tokens=2, food_tokens=0),
                ),
                ContributorContribution(
                    festivalier_id="f-2",
                    contribution=TokenContribution(drink_tokens=1, food_tokens=0),
                ),
            ],
        )
        order_repo.save(order)

        before_f1 = festivalier_repo.get_balance("f-1")
        before_f2 = festivalier_repo.get_balance("f-2")

        response = controller.acknowledge_order(AcknowledgeOrderRequest("order-grp"))

        assert response.status_code == 200
        assert response.json()["status"] == "ACKNOWLEDGED"

        after_f1 = festivalier_repo.get_balance("f-1")
        after_f2 = festivalier_repo.get_balance("f-2")

        assert after_f1.drink_tokens == before_f1.drink_tokens - 2
        assert after_f2.drink_tokens == before_f2.drink_tokens - 1
