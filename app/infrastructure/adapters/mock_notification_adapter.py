from typing import List, Optional

from app.domain.ports.notification_port import NotificationPort


class MockNotificationAdapter(NotificationPort):
    """Mock implementation of the NotificationPort for tests and local runs.

    Records all sent notifications so they can be inspected in tests.
    """

    def __init__(self) -> None:
        self.bartender_notifications: List[dict] = []
        self.festivalier_notifications: List[dict] = []
        self.acknowledgement_notifications: List[dict] = []

    def notify_bartender_change_requested(self, order_id: str, change_request_id: str) -> None:
        self.bartender_notifications.append(
            {"order_id": order_id, "change_request_id": change_request_id}
        )

    def notify_festivalier_change_resolved(
        self,
        festivalier_id: str,
        order_id: str,
        accepted: bool,
        rejection_reason: Optional[str] = None,
    ) -> None:
        self.festivalier_notifications.append(
            {
                "festivalier_id": festivalier_id,
                "order_id": order_id,
                "accepted": accepted,
                "rejection_reason": rejection_reason,
            }
        )

    def notify_festivalier_order_acknowledged(
        self,
        festivalier_id: str,
        order_id: str,
        eta_minutes: int,
    ) -> None:
        self.acknowledgement_notifications.append(
            {
                "festivalier_id": festivalier_id,
                "order_id": order_id,
                "eta_minutes": eta_minutes,
            }
        )
