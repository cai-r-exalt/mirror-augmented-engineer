"""Domain unit tests for AcknowledgeOrderUseCase.

Covers:
- ETA calculation for multiple item type combinations (deterministic)
- Token deduction for solo and group orders
- Stock validation at acknowledge time
- Status and acknowledged_at persistence
- Notification sent to festivalier
- Error cases (order not found, wrong status, insufficient stock)
"""

import pytest

from app.domain.entities.commande import Article, Commande, ContributorContribution, LigneCommande
from app.domain.exceptions import (
    OrderAlreadyAcknowledgedException,
    OrderNotAcknowledgeableException,
    OrderNotFoundException,
)
from app.domain.ports.item_catalog_repository import (
    ITEM_TYPE_MEAL,
    ITEM_TYPE_NON_ALCOHOLIC_DRINK,
    ITEM_TYPE_NORMAL_ALCOHOLIC_DRINK,
    ITEM_TYPE_PREMIUM_ALCOHOLIC_DRINK,
    ITEM_TYPE_SNACK,
    ItemCost,
)
from app.domain.use_cases.acknowledge_order import AcknowledgeOrderCommand, AcknowledgeOrderUseCase
from app.domain.value_objects.token_contribution import TokenContribution
from app.infrastructure.adapters.in_memory_festivalier_repository import InMemoryFestivalierRepository
from app.infrastructure.adapters.in_memory_item_catalog_repository import InMemoryItemCatalogRepository
from app.infrastructure.adapters.in_memory_order_repository import InMemoryOrderRepository
from app.infrastructure.adapters.in_memory_stock_repository import InMemoryStockRepository
from app.infrastructure.adapters.mock_notification_adapter import MockNotificationAdapter


def _make_use_case(order_repo, stock_repo, catalog_repo, festivalier_repo, notifications):
    return AcknowledgeOrderUseCase(
        order_repository=order_repo,
        stock_repository=stock_repo,
        item_catalog_repository=catalog_repo,
        festivalier_repository=festivalier_repo,
        notification_port=notifications,
    )


def _pending_order(order_id: str, festivalier_id: str, items: list) -> Commande:
    lignes = [
        LigneCommande(article=Article(name=item["name"]), quantite=item["quantity"])
        for item in items
    ]
    return Commande(id=order_id, festivalier_id=festivalier_id, lignes=lignes, status="EN_ATTENTE")


class TestAcknowledgeOrderETACalculation:
    """Deterministic unit tests for ETA computation rules."""

    def setup_method(self):
        self.order_repo = InMemoryOrderRepository()
        self.stock_repo = InMemoryStockRepository({
            "Eau": 20,
            "Jus d'orange": 20,
            "Bière": 20,
            "Mojito": 20,
            "Whisky": 20,
            "Chips": 20,
            "Nachos": 20,
            "Burger": 20,
            "Pizza": 20,
        })
        self.catalog_repo = InMemoryItemCatalogRepository()
        reg = self.catalog_repo.register
        reg(ItemCost("Eau", item_type=ITEM_TYPE_NON_ALCOHOLIC_DRINK))
        reg(ItemCost("Jus d'orange", item_type=ITEM_TYPE_NON_ALCOHOLIC_DRINK))
        reg(ItemCost("Bière", drink_tokens_per_unit=1, item_type=ITEM_TYPE_NORMAL_ALCOHOLIC_DRINK))
        reg(ItemCost("Mojito", drink_tokens_per_unit=1, item_type=ITEM_TYPE_NORMAL_ALCOHOLIC_DRINK))
        reg(ItemCost("Whisky", drink_tokens_per_unit=2, item_type=ITEM_TYPE_PREMIUM_ALCOHOLIC_DRINK))
        reg(ItemCost("Chips", food_tokens_per_unit=1, item_type=ITEM_TYPE_SNACK))
        reg(ItemCost("Nachos", food_tokens_per_unit=1, item_type=ITEM_TYPE_SNACK))
        reg(ItemCost("Burger", food_tokens_per_unit=3, item_type=ITEM_TYPE_MEAL))
        reg(ItemCost("Pizza", food_tokens_per_unit=3, item_type=ITEM_TYPE_MEAL))
        self.festivalier_repo = InMemoryFestivalierRepository({
            "f-1": {"drink_tokens": 20, "food_tokens": 20},
        })
        self.notifications = MockNotificationAdapter()
        self.use_case = _make_use_case(
            self.order_repo, self.stock_repo, self.catalog_repo, self.festivalier_repo, self.notifications
        )

    def _ack(self, order_id: str) -> Commande:
        return self.use_case.execute(AcknowledgeOrderCommand(order_id=order_id))

    # ── Non-alcoholic only ──────────────────────────────────────────────────

    def test_eta_one_non_alcoholic_type(self):
        """1 type of non-alcoholic drink → 1 minute."""
        order = _pending_order("o-1", "f-1", [{"name": "Eau", "quantity": 3}])
        self.order_repo.save(order)
        result = self._ack("o-1")
        assert result.eta_minutes == 1

    def test_eta_three_different_non_alcoholic_types(self):
        """3 different non-alcoholic drinks → 3 minutes (1 per type)."""
        # Need to add a 3rd non-alc item and stock
        self.stock_repo.stock["Limonade"] = 20
        self.catalog_repo.register(ItemCost("Limonade", item_type=ITEM_TYPE_NON_ALCOHOLIC_DRINK))
        order = _pending_order("o-1", "f-1", [
            {"name": "Eau", "quantity": 2},
            {"name": "Jus d'orange", "quantity": 1},
            {"name": "Limonade", "quantity": 3},
        ])
        self.order_repo.save(order)
        result = self._ack("o-1")
        assert result.eta_minutes == 3

    def test_eta_same_non_alcoholic_type_multiple_times_counts_once(self):
        """Multiple quantities of a single non-alcoholic drink → 1 minute."""
        order = _pending_order("o-1", "f-1", [{"name": "Eau", "quantity": 5}])
        self.order_repo.save(order)
        result = self._ack("o-1")
        assert result.eta_minutes == 1

    # ── Normal alcoholic drinks ─────────────────────────────────────────────

    def test_eta_normal_alcoholic_per_drink_quantity(self):
        """3 normal alcoholic drinks → 2 × 3 = 6 minutes."""
        order = _pending_order("o-1", "f-1", [{"name": "Bière", "quantity": 3}])
        self.order_repo.save(order)
        result = self._ack("o-1")
        assert result.eta_minutes == 6

    def test_eta_two_different_normal_alcoholic_drinks(self):
        """2 Bière + 1 Mojito → 2×2 + 2×1 = 6 minutes."""
        order = _pending_order("o-1", "f-1", [
            {"name": "Bière", "quantity": 2},
            {"name": "Mojito", "quantity": 1},
        ])
        self.order_repo.save(order)
        result = self._ack("o-1")
        assert result.eta_minutes == 6

    # ── Premium alcoholic drinks ────────────────────────────────────────────

    def test_eta_premium_alcoholic_per_drink_quantity(self):
        """2 premium alcoholic drinks → 3 × 2 = 6 minutes."""
        order = _pending_order("o-1", "f-1", [{"name": "Whisky", "quantity": 2}])
        self.order_repo.save(order)
        result = self._ack("o-1")
        assert result.eta_minutes == 6

    # ── Snacks ──────────────────────────────────────────────────────────────

    def test_eta_one_snack_type(self):
        """1 type of snack → 2 minutes."""
        order = _pending_order("o-1", "f-1", [{"name": "Chips", "quantity": 3}])
        self.order_repo.save(order)
        result = self._ack("o-1")
        assert result.eta_minutes == 2

    def test_eta_two_different_snack_types(self):
        """2 different snack types → 2 × 2 = 4 minutes."""
        order = _pending_order("o-1", "f-1", [
            {"name": "Chips", "quantity": 1},
            {"name": "Nachos", "quantity": 2},
        ])
        self.order_repo.save(order)
        result = self._ack("o-1")
        assert result.eta_minutes == 4

    # ── Meals ────────────────────────────────────────────────────────────────

    def test_eta_meal_only_no_drinks(self):
        """1 type of meal with no drinks → 10 + 0 = 10 minutes."""
        order = _pending_order("o-1", "f-1", [{"name": "Burger", "quantity": 1}])
        self.order_repo.save(order)
        result = self._ack("o-1")
        assert result.eta_minutes == 10

    def test_eta_meal_with_non_alcoholic_drink(self):
        """1 meal type + 1 non-alc type → non_alc=1, meal=10+1=11 → total=12."""
        order = _pending_order("o-1", "f-1", [
            {"name": "Burger", "quantity": 1},
            {"name": "Eau", "quantity": 1},
        ])
        self.order_repo.save(order)
        result = self._ack("o-1")
        assert result.eta_minutes == 12  # 1 (non-alc) + (10 (meal base) + 1 (longest_drink)) = 12

    def test_eta_meal_with_normal_alcoholic_drink(self):
        """1 meal type + 2 normal alc → normal_alc=4, meal=10+2=12 → total=16."""
        order = _pending_order("o-1", "f-1", [
            {"name": "Burger", "quantity": 1},
            {"name": "Bière", "quantity": 2},
        ])
        self.order_repo.save(order)
        result = self._ack("o-1")
        assert result.eta_minutes == 16  # 4 (normal alc) + 12 (meal + longest_drink=2)

    def test_eta_meal_with_premium_alcoholic_drink(self):
        """1 meal type + 1 premium alc → premium_alc=3, meal=10+3=13 → total=16."""
        order = _pending_order("o-1", "f-1", [
            {"name": "Burger", "quantity": 1},
            {"name": "Whisky", "quantity": 1},
        ])
        self.order_repo.save(order)
        result = self._ack("o-1")
        assert result.eta_minutes == 16  # 3 (premium) + 13 (meal + longest_drink=3)

    def test_eta_two_meal_types_with_premium_drink(self):
        """2 meal types + 1 premium alc → premium=3, meal=20+3=23 → total=26."""
        order = _pending_order("o-1", "f-1", [
            {"name": "Burger", "quantity": 1},
            {"name": "Pizza", "quantity": 1},
            {"name": "Whisky", "quantity": 1},
        ])
        self.order_repo.save(order)
        result = self._ack("o-1")
        assert result.eta_minutes == 26  # 3 + (10*2 + 3)

    # ── Mixed orders ─────────────────────────────────────────────────────────

    def test_eta_mixed_non_alc_and_snack(self):
        """2 non-alc types + 1 snack type → 2 + 2 = 4 minutes."""
        order = _pending_order("o-1", "f-1", [
            {"name": "Eau", "quantity": 1},
            {"name": "Jus d'orange", "quantity": 1},
            {"name": "Chips", "quantity": 2},
        ])
        self.order_repo.save(order)
        result = self._ack("o-1")
        assert result.eta_minutes == 4

    def test_eta_mixed_normal_alc_and_snack(self):
        """3 normal alc + 2 snack types → 6 + 4 = 10 minutes."""
        order = _pending_order("o-1", "f-1", [
            {"name": "Bière", "quantity": 3},
            {"name": "Chips", "quantity": 1},
            {"name": "Nachos", "quantity": 1},
        ])
        self.order_repo.save(order)
        result = self._ack("o-1")
        assert result.eta_minutes == 10  # 6 + 4

    def test_eta_mixed_all_types(self):
        """2 non-alc + 3 normal_alc + 1 premium + 1 snack + 1 meal.

        non_alc = 2
        normal_alc = 6
        premium = 3
        snack = 2
        longest_drink = max(1, 2, 3) = 3
        meal = 10 + 3 = 13
        total = 2 + 6 + 3 + 2 + 13 = 26
        """
        order = _pending_order("o-1", "f-1", [
            {"name": "Eau", "quantity": 1},
            {"name": "Jus d'orange", "quantity": 1},
            {"name": "Bière", "quantity": 3},
            {"name": "Whisky", "quantity": 1},
            {"name": "Chips", "quantity": 1},
            {"name": "Burger", "quantity": 1},
        ])
        self.order_repo.save(order)
        result = self._ack("o-1")
        assert result.eta_minutes == 26


class TestAcknowledgeOrderStatusAndPersistence:
    """Tests that status, eta_minutes, and acknowledged_at are persisted correctly."""

    def setup_method(self):
        self.order_repo = InMemoryOrderRepository()
        self.stock_repo = InMemoryStockRepository({"Bière": 10})
        self.catalog_repo = InMemoryItemCatalogRepository()
        self.catalog_repo.register(
            ItemCost("Bière", drink_tokens_per_unit=1, item_type=ITEM_TYPE_NORMAL_ALCOHOLIC_DRINK)
        )
        self.festivalier_repo = InMemoryFestivalierRepository({"f-1": {"drink_tokens": 10, "food_tokens": 0}})
        self.notifications = MockNotificationAdapter()
        self.use_case = _make_use_case(
            self.order_repo, self.stock_repo, self.catalog_repo, self.festivalier_repo, self.notifications
        )

    def test_order_status_becomes_acknowledged(self):
        order = _pending_order("o-1", "f-1", [{"name": "Bière", "quantity": 1}])
        self.order_repo.save(order)
        result = self.use_case.execute(AcknowledgeOrderCommand("o-1"))
        assert result.status == "ACKNOWLEDGED"

    def test_order_eta_minutes_set(self):
        order = _pending_order("o-1", "f-1", [{"name": "Bière", "quantity": 2}])
        self.order_repo.save(order)
        result = self.use_case.execute(AcknowledgeOrderCommand("o-1"))
        assert result.eta_minutes == 4  # 2 × 2

    def test_order_acknowledged_at_set(self):
        order = _pending_order("o-1", "f-1", [{"name": "Bière", "quantity": 1}])
        self.order_repo.save(order)
        result = self.use_case.execute(AcknowledgeOrderCommand("o-1"))
        assert result.acknowledged_at is not None

    def test_notification_sent_with_eta(self):
        order = _pending_order("o-1", "f-1", [{"name": "Bière", "quantity": 1}])
        self.order_repo.save(order)
        self.use_case.execute(AcknowledgeOrderCommand("o-1"))
        assert len(self.notifications.acknowledgement_notifications) == 1
        notif = self.notifications.acknowledgement_notifications[0]
        assert notif["order_id"] == "o-1"
        assert notif["festivalier_id"] == "f-1"
        assert notif["eta_minutes"] == 2


class TestAcknowledgeOrderTokenDeduction:
    """Tests for token deduction at acknowledgement time."""

    def setup_method(self):
        self.order_repo = InMemoryOrderRepository()
        self.stock_repo = InMemoryStockRepository({"Bière": 10, "Whisky": 10, "Chips": 10})
        self.catalog_repo = InMemoryItemCatalogRepository()
        reg = self.catalog_repo.register
        reg(ItemCost("Bière", drink_tokens_per_unit=1, item_type=ITEM_TYPE_NORMAL_ALCOHOLIC_DRINK))
        reg(ItemCost("Whisky", drink_tokens_per_unit=2, item_type=ITEM_TYPE_PREMIUM_ALCOHOLIC_DRINK))
        reg(ItemCost("Chips", food_tokens_per_unit=1, item_type=ITEM_TYPE_SNACK))
        self.festivalier_repo = InMemoryFestivalierRepository({
            "f-1": {"drink_tokens": 10, "food_tokens": 5},
            "f-2": {"drink_tokens": 8, "food_tokens": 3},
        })
        self.notifications = MockNotificationAdapter()
        self.use_case = _make_use_case(
            self.order_repo, self.stock_repo, self.catalog_repo, self.festivalier_repo, self.notifications
        )

    def test_solo_order_deducts_drink_tokens(self):
        """Acknowledging a solo order deducts computed item costs from festivalier."""
        order = _pending_order("o-1", "f-1", [{"name": "Bière", "quantity": 3}])
        self.order_repo.save(order)

        before = self.festivalier_repo.get_balance("f-1")
        self.use_case.execute(AcknowledgeOrderCommand("o-1"))
        after = self.festivalier_repo.get_balance("f-1")

        assert after.drink_tokens == before.drink_tokens - 3  # 1 token × 3

    def test_solo_order_deducts_food_tokens(self):
        order = _pending_order("o-1", "f-1", [{"name": "Chips", "quantity": 2}])
        self.order_repo.save(order)

        before = self.festivalier_repo.get_balance("f-1")
        self.use_case.execute(AcknowledgeOrderCommand("o-1"))
        after = self.festivalier_repo.get_balance("f-1")

        assert after.food_tokens == before.food_tokens - 2  # 1 token × 2

    def test_solo_mixed_order_deducts_both_token_types(self):
        order = _pending_order("o-1", "f-1", [
            {"name": "Whisky", "quantity": 1},
            {"name": "Chips", "quantity": 2},
        ])
        self.order_repo.save(order)

        before = self.festivalier_repo.get_balance("f-1")
        self.use_case.execute(AcknowledgeOrderCommand("o-1"))
        after = self.festivalier_repo.get_balance("f-1")

        assert after.drink_tokens == before.drink_tokens - 2  # 2 per Whisky × 1
        assert after.food_tokens == before.food_tokens - 2    # 1 per Chips × 2

    def test_group_order_deducts_pledged_amounts_from_each_contributor(self):
        """Group order deducts each contributor's pledged tokens, not item cost."""
        order = Commande(
            id="o-grp",
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
        self.order_repo.save(order)

        before_f1 = self.festivalier_repo.get_balance("f-1")
        before_f2 = self.festivalier_repo.get_balance("f-2")
        self.use_case.execute(AcknowledgeOrderCommand("o-grp"))
        after_f1 = self.festivalier_repo.get_balance("f-1")
        after_f2 = self.festivalier_repo.get_balance("f-2")

        assert after_f1.drink_tokens == before_f1.drink_tokens - 2
        assert after_f2.drink_tokens == before_f2.drink_tokens - 1


class TestAcknowledgeOrderErrorCases:
    """Tests for error handling in AcknowledgeOrderUseCase."""

    def setup_method(self):
        self.order_repo = InMemoryOrderRepository()
        self.stock_repo = InMemoryStockRepository({"Bière": 5})
        self.catalog_repo = InMemoryItemCatalogRepository()
        self.catalog_repo.register(
            ItemCost("Bière", drink_tokens_per_unit=1, item_type=ITEM_TYPE_NORMAL_ALCOHOLIC_DRINK)
        )
        self.festivalier_repo = InMemoryFestivalierRepository({"f-1": {"drink_tokens": 10, "food_tokens": 0}})
        self.notifications = MockNotificationAdapter()
        self.use_case = _make_use_case(
            self.order_repo, self.stock_repo, self.catalog_repo, self.festivalier_repo, self.notifications
        )

    def test_raises_when_order_not_found(self):
        with pytest.raises(OrderNotFoundException) as exc_info:
            self.use_case.execute(AcknowledgeOrderCommand("nonexistent"))
        assert exc_info.value.order_id == "nonexistent"

    def test_raises_when_order_already_acknowledged(self):
        order = _pending_order("o-1", "f-1", [{"name": "Bière", "quantity": 1}])
        order.status = "ACKNOWLEDGED"
        self.order_repo.save(order)
        with pytest.raises(OrderAlreadyAcknowledgedException):
            self.use_case.execute(AcknowledgeOrderCommand("o-1"))

    def test_raises_when_order_not_in_pending_status(self):
        order = _pending_order("o-1", "f-1", [{"name": "Bière", "quantity": 1}])
        order.status = "ANNULEE"
        self.order_repo.save(order)
        with pytest.raises(OrderNotAcknowledgeableException):
            self.use_case.execute(AcknowledgeOrderCommand("o-1"))

    def test_raises_when_stock_insufficient_at_acknowledge_time(self):
        """If stock drops below required after placement, acknowledgement should fail."""
        order = _pending_order("o-1", "f-1", [{"name": "Bière", "quantity": 10}])
        self.order_repo.save(order)
        with pytest.raises(OrderNotAcknowledgeableException) as exc_info:
            self.use_case.execute(AcknowledgeOrderCommand("o-1"))
        assert "stock" in exc_info.value.reason

    def test_no_tokens_deducted_when_stock_fails(self):
        """Token balances must not change when acknowledgement fails."""
        order = _pending_order("o-1", "f-1", [{"name": "Bière", "quantity": 10}])
        self.order_repo.save(order)
        before = self.festivalier_repo.get_balance("f-1")
        with pytest.raises(OrderNotAcknowledgeableException):
            self.use_case.execute(AcknowledgeOrderCommand("o-1"))
        after = self.festivalier_repo.get_balance("f-1")
        assert after.drink_tokens == before.drink_tokens
