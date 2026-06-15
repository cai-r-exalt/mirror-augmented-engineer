"""Domain unit tests for HydrationSchedulerUseCase.

Covers:
- Heavy-drinker detection (>3 alcoholic units in the last hour)
- Notification sent to heavy drinkers on every scheduler run (30-min frequency)
- Notification sent to regular drinkers only on full-hour runs (60-min frequency)
- No notifications outside the 11:00–19:00 festival window
- Integration scenario: scheduler decisioning with mixed users
"""

from datetime import datetime, timezone

from app.domain.ports.item_catalog_repository import (
    ITEM_TYPE_NON_ALCOHOLIC_DRINK,
    ITEM_TYPE_NORMAL_ALCOHOLIC_DRINK,
    ITEM_TYPE_PREMIUM_ALCOHOLIC_DRINK,
    ItemCost,
)
from app.domain.use_cases.hydration_scheduler import (
    HydrationSchedulerUseCase,
)
from app.infrastructure.adapters.in_memory_festivalier_repository import (
    InMemoryFestivalierRepository,
)
from app.infrastructure.adapters.in_memory_item_catalog_repository import (
    InMemoryItemCatalogRepository,
)
from app.infrastructure.adapters.in_memory_order_repository import (
    InMemoryOrderRepository,
)
from app.infrastructure.adapters.mock_notification_adapter import (
    MockNotificationAdapter,
)

# ── Helpers ───────────────────────────────────────────────────────────────────


def _dt(hour: int, minute: int = 0) -> datetime:
    """Return a UTC datetime on a fixed calendar day at the given time."""
    return datetime(2024, 7, 15, hour, minute, 0, tzinfo=timezone.utc)


def _make_acknowledged_order(
    repo: InMemoryOrderRepository,
    festivalier_id: str,
    items: list[dict],
    acknowledged_at: datetime,
) -> None:
    """Create and store an acknowledged order with the given items and timestamp."""
    order = repo.create_order(festivalier_id, items)
    order.status = "ACKNOWLEDGED"
    order.acknowledged_at = acknowledged_at.isoformat()
    repo.save(order)


def _build_use_case(
    festivalier_ids: list[str] | None = None,
    catalog_items: list[ItemCost] | None = None,
) -> tuple[HydrationSchedulerUseCase, InMemoryOrderRepository, MockNotificationAdapter]:
    """Return a fully wired use case with in-memory adapters."""
    order_repo = InMemoryOrderRepository()

    festivalier_repo = InMemoryFestivalierRepository(
        {fid: {"drink_tokens": 10, "food_tokens": 10} for fid in (festivalier_ids or [])}
    )

    catalog_repo = InMemoryItemCatalogRepository()
    for item in catalog_items or []:
        catalog_repo.register(item)

    notif = MockNotificationAdapter()
    use_case = HydrationSchedulerUseCase(
        order_repository=order_repo,
        item_catalog_repository=catalog_repo,
        festivalier_repository=festivalier_repo,
        notification_port=notif,
    )
    return use_case, order_repo, notif


# ── Heavy-drinker detection unit tests ────────────────────────────────────────


class TestHeavyDrinkerDetection:
    """Unit tests focused on the alcohol-counting logic."""

    def setup_method(self):
        self.use_case, self.order_repo, self.notif = _build_use_case(
            festivalier_ids=["f-1"],
            catalog_items=[
                ItemCost("Bière", drink_tokens_per_unit=1, item_type=ITEM_TYPE_NORMAL_ALCOHOLIC_DRINK),
                ItemCost("Whisky", drink_tokens_per_unit=2, item_type=ITEM_TYPE_PREMIUM_ALCOHOLIC_DRINK),
                ItemCost("Eau", item_type=ITEM_TYPE_NON_ALCOHOLIC_DRINK),
            ],
        )

    def test_exactly_threshold_drinks_is_not_heavy(self):
        """
        Given a user who consumed exactly 3 alcoholic drinks in the last hour
        When the scheduler runs at a full-hour mark
        Then the user is notified (hourly reminder, not heavy-drinker frequency)
        And no heavy-drinker tips are included
        """
        now = _dt(14, 0)
        one_hour_ago = _dt(13, 0)
        _make_acknowledged_order(
            self.order_repo, "f-1",
            [{"name": "Bière", "quantity": 3}],
            acknowledged_at=one_hour_ago.replace(minute=30),
        )

        result = self.use_case.execute(now)

        assert "f-1" in result.notified_festivalier_ids
        reminder = self.notif.hydration_reminders[0]
        assert reminder["festivalier_id"] == "f-1"
        assert reminder["tips"] is None

    def test_more_than_threshold_drinks_is_heavy(self):
        """
        Given a user who consumed 4 alcoholic drinks in the last hour
        When the scheduler runs at the half-hour mark
        Then the user receives a heavy-drinker reminder with tips
        """
        now = _dt(14, 30)
        _make_acknowledged_order(
            self.order_repo, "f-1",
            [{"name": "Bière", "quantity": 4}],
            acknowledged_at=_dt(14, 0),
        )

        result = self.use_case.execute(now)

        assert "f-1" in result.notified_festivalier_ids
        reminder = self.notif.hydration_reminders[0]
        assert reminder["tips"] is not None

    def test_non_alcoholic_drinks_not_counted(self):
        """
        Given a user who consumed 10 non-alcoholic drinks in the last hour
        When the scheduler runs at the half-hour mark (no full-hour run)
        Then the user is NOT notified (not a heavy drinker, not a full-hour run)
        """
        now = _dt(14, 30)
        _make_acknowledged_order(
            self.order_repo, "f-1",
            [{"name": "Eau", "quantity": 10}],
            acknowledged_at=_dt(14, 0),
        )

        result = self.use_case.execute(now)

        assert result.notified_festivalier_ids == []

    def test_premium_alcoholic_drinks_are_counted(self):
        """
        Given a user who consumed 4 premium alcoholic drinks in the last hour
        When the scheduler runs at the half-hour mark
        Then the user is identified as a heavy drinker and notified
        """
        now = _dt(14, 30)
        _make_acknowledged_order(
            self.order_repo, "f-1",
            [{"name": "Whisky", "quantity": 4}],
            acknowledged_at=_dt(14, 0),
        )

        result = self.use_case.execute(now)

        assert "f-1" in result.notified_festivalier_ids
        assert self.notif.hydration_reminders[0]["tips"] is not None

    def test_drinks_outside_one_hour_window_are_not_counted(self):
        """
        Given a user who consumed 4 drinks more than 1 hour ago
        When the scheduler runs at the half-hour mark
        Then those drinks are NOT counted and the user is not notified
        """
        now = _dt(15, 30)
        _make_acknowledged_order(
            self.order_repo, "f-1",
            [{"name": "Bière", "quantity": 4}],
            acknowledged_at=_dt(14, 0),  # 1h30m ago — outside the 1h window
        )

        result = self.use_case.execute(now)

        assert result.notified_festivalier_ids == []

    def test_mixed_alcoholic_and_non_alcoholic_counts_only_alcoholic(self):
        """
        Given a user with 2 alcoholic + 5 non-alcoholic drinks in last hour
        When the scheduler runs at the half-hour mark
        Then only the 2 alcoholic units are counted → not a heavy drinker
        """
        now = _dt(14, 30)
        _make_acknowledged_order(
            self.order_repo, "f-1",
            [
                {"name": "Bière", "quantity": 2},
                {"name": "Eau", "quantity": 5},
            ],
            acknowledged_at=_dt(14, 0),
        )

        result = self.use_case.execute(now)

        assert result.notified_festivalier_ids == []


# ── Festival window enforcement ────────────────────────────────────────────────


class TestFestivalWindow:
    """No notifications should be sent outside 11:00–19:00."""

    def setup_method(self):
        self.use_case, self.order_repo, self.notif = _build_use_case(
            festivalier_ids=["f-1"],
        )

    def test_no_notification_before_11(self):
        result = self.use_case.execute(_dt(10, 0))
        assert result.notified_festivalier_ids == []
        assert self.notif.hydration_reminders == []

    def test_no_notification_after_19(self):
        result = self.use_case.execute(_dt(19, 30))
        assert result.notified_festivalier_ids == []

    def test_notification_at_exactly_11(self):
        result = self.use_case.execute(_dt(11, 0))
        assert "f-1" in result.notified_festivalier_ids

    def test_notification_at_exactly_19(self):
        result = self.use_case.execute(_dt(19, 0))
        assert "f-1" in result.notified_festivalier_ids

    def test_no_notification_at_19_30(self):
        result = self.use_case.execute(_dt(19, 30))
        assert result.notified_festivalier_ids == []


# ── Frequency rules ────────────────────────────────────────────────────────────


class TestFrequencyRules:
    """Scheduler correctly differentiates full-hour vs. half-hour runs."""

    def setup_method(self):
        self.use_case, self.order_repo, self.notif = _build_use_case(
            festivalier_ids=["f-1"],
            catalog_items=[
                ItemCost("Bière", drink_tokens_per_unit=1, item_type=ITEM_TYPE_NORMAL_ALCOHOLIC_DRINK),
            ],
        )

    def test_regular_drinker_notified_on_full_hour_run(self):
        """
        Given current time within 11:00–19:00 and user consumed <=3 drinks in last hour
        When scheduler runs at minute=0 (full-hour run)
        Then user receives a hydration reminder
        """
        result = self.use_case.execute(_dt(14, 0))
        assert "f-1" in result.notified_festivalier_ids

    def test_regular_drinker_not_notified_on_half_hour_run(self):
        """
        Given user consumed <=3 drinks in last hour
        When scheduler runs at minute=30 (half-hour run)
        Then user is NOT notified
        """
        result = self.use_case.execute(_dt(14, 30))
        assert result.notified_festivalier_ids == []

    def test_heavy_drinker_notified_on_half_hour_run(self):
        """
        Given user consumed 4 alcoholic drinks in last hour
        When scheduler runs at minute=30 (half-hour run)
        Then user receives a hydration reminder
        """
        _make_acknowledged_order(
            self.order_repo, "f-1",
            [{"name": "Bière", "quantity": 4}],
            acknowledged_at=_dt(14, 0),
        )

        result = self.use_case.execute(_dt(14, 30))

        assert "f-1" in result.notified_festivalier_ids

    def test_heavy_drinker_also_notified_on_full_hour_run(self):
        """Heavy drinkers are notified on both full-hour and half-hour runs."""
        _make_acknowledged_order(
            self.order_repo, "f-1",
            [{"name": "Bière", "quantity": 4}],
            acknowledged_at=_dt(14, 0),
        )

        result = self.use_case.execute(_dt(15, 0))

        assert "f-1" in result.notified_festivalier_ids


# ── Integration: scheduler decisioning ────────────────────────────────────────


class TestSchedulerDecisioning:
    """Integration test for mixed-user scenarios matching the issue Gherkin."""

    def setup_method(self):
        self.use_case, self.order_repo, self.notif = _build_use_case(
            festivalier_ids=["regular", "heavy"],
            catalog_items=[
                ItemCost("Bière", drink_tokens_per_unit=1, item_type=ITEM_TYPE_NORMAL_ALCOHOLIC_DRINK),
            ],
        )
        # heavy drinker has 4 drinks in the last hour
        _make_acknowledged_order(
            self.order_repo, "heavy",
            [{"name": "Bière", "quantity": 4}],
            acknowledged_at=_dt(14, 10),
        )

    def test_full_hour_run_notifies_all_users(self):
        """
        Scenario: Both regular and heavy drinkers are notified on the full-hour run.
        """
        result = self.use_case.execute(_dt(15, 0))

        assert set(result.notified_festivalier_ids) == {"regular", "heavy"}
        assert len(self.notif.hydration_reminders) == 2

    def test_half_hour_run_notifies_only_heavy_drinker(self):
        """
        Scenario: Heavy-drinker gets 30-minute reminders.
        Given user consumed 4 alcoholic drinks in last hour
        When scheduler runs (at half-hour mark)
        Then user receives a hydration reminder every 30 minutes
        """
        result = self.use_case.execute(_dt(14, 30))

        assert result.notified_festivalier_ids == ["heavy"]
        assert self.notif.hydration_reminders[0]["festivalier_id"] == "heavy"
        assert self.notif.hydration_reminders[0]["tips"] is not None

    def test_no_notifications_outside_window(self):
        """
        Regardless of drinking history, no notifications outside the window.
        """
        result = self.use_case.execute(_dt(10, 0))

        assert result.notified_festivalier_ids == []
        assert self.notif.hydration_reminders == []

    def test_empty_festivalier_list_produces_no_reminders(self):
        """
        When there are no festival goers registered, the scheduler is a no-op.
        """
        use_case, _, notif = _build_use_case(festivalier_ids=[])
        result = use_case.execute(_dt(14, 0))
        assert result.notified_festivalier_ids == []
        assert notif.hydration_reminders == []
