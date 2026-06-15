"""HydrationSchedulerUseCase — scheduled hydration reminders for festival goers.

Business rules:
- Reminders are sent only between 11:00 and 19:00 (local festival time).
- Default frequency: every 60 minutes (sent on full-hour scheduler runs).
- Heavy-drinker frequency: every 30 minutes, for users who consumed >3
  alcoholic drink units (normal or premium) in the last hour.
- The scheduler runs every 30 minutes; each run decides per-user whether
  to send based on the above rules.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List

from app.domain.ports.festivalier_repository import FestivalierRepository
from app.domain.ports.item_catalog_repository import (
    ITEM_TYPE_NORMAL_ALCOHOLIC_DRINK,
    ITEM_TYPE_PREMIUM_ALCOHOLIC_DRINK,
    ItemCatalogRepository,
)
from app.domain.ports.notification_port import NotificationPort
from app.domain.ports.order_repository import OrderRepository

# A festivalier is considered a heavy drinker when they exceed this threshold.
HEAVY_DRINKER_THRESHOLD = 3

# Festival notification window (hours, inclusive).
FESTIVAL_START_HOUR = 11
FESTIVAL_END_HOUR = 19

_ALCOHOLIC_ITEM_TYPES = frozenset(
    {ITEM_TYPE_NORMAL_ALCOHOLIC_DRINK, ITEM_TYPE_PREMIUM_ALCOHOLIC_DRINK}
)

_HEAVY_DRINKER_TIPS = (
    "Stay safe: drink water between alcoholic drinks and eat regularly."
)


@dataclass
class HydrationSchedulerResult:
    """Summary of a scheduler run."""

    notified_festivalier_ids: List[str] = field(default_factory=list)


class HydrationSchedulerUseCase:
    """Send hydration reminders to festival goers based on their alcohol consumption.

    The use case is designed to be invoked every 30 minutes by an external
    scheduler (e.g. APScheduler, Celery Beat).  It receives ``current_time``
    explicitly so that behaviour is fully deterministic and testable.

    Frequency rules:
    - Heavy drinker (>3 alcoholic units in last hour): notify on every run.
    - Regular drinker: notify only on full-hour runs (when ``minute == 0``).
    """

    def __init__(
        self,
        order_repository: OrderRepository,
        item_catalog_repository: ItemCatalogRepository,
        festivalier_repository: FestivalierRepository,
        notification_port: NotificationPort,
    ) -> None:
        self.order_repository = order_repository
        self.item_catalog_repository = item_catalog_repository
        self.festivalier_repository = festivalier_repository
        self.notification_port = notification_port

    def execute(self, current_time: datetime) -> HydrationSchedulerResult:
        """Run the hydration scheduler for the given moment in time.

        Args:
            current_time: The current local festival time used to evaluate
                the notification window and hourly vs. half-hourly logic.

        Returns:
            A result object listing the IDs of notified festival goers.
        """
        if not self._is_in_festival_window(current_time):
            return HydrationSchedulerResult()

        is_full_hour_run = current_time.minute == 0
        one_hour_ago = current_time - timedelta(hours=1)

        notified: List[str] = []
        for festivalier_id in self.festivalier_repository.list_all_ids():
            alcoholic_units = self._count_alcoholic_units_since(
                festivalier_id, one_hour_ago
            )
            is_heavy_drinker = alcoholic_units > HEAVY_DRINKER_THRESHOLD

            if is_heavy_drinker or is_full_hour_run:
                self.notification_port.notify_festivalier_hydration_reminder(
                    festivalier_id=festivalier_id,
                    tips=_HEAVY_DRINKER_TIPS if is_heavy_drinker else None,
                )
                notified.append(festivalier_id)

        return HydrationSchedulerResult(notified_festivalier_ids=notified)

    # ── Private helpers ──────────────────────────────────────────────────────

    def _is_in_festival_window(self, current_time: datetime) -> bool:
        """Return True if current_time falls within 11:00–19:00 (inclusive)."""
        total_minutes = current_time.hour * 60 + current_time.minute
        return FESTIVAL_START_HOUR * 60 <= total_minutes <= FESTIVAL_END_HOUR * 60

    def _count_alcoholic_units_since(
        self, festivalier_id: str, since: datetime
    ) -> int:
        """Return total alcoholic drink units ordered by the festivalier since *since*."""
        orders = self.order_repository.find_by_festivalier_acknowledged_since(
            festivalier_id, since
        )
        total = 0
        for order in orders:
            for ligne in order.lignes:
                item_cost = self.item_catalog_repository.get_item_cost(
                    ligne.article.name
                )
                if item_cost is not None and item_cost.item_type in _ALCOHOLIC_ITEM_TYPES:
                    total += ligne.quantite
        return total
