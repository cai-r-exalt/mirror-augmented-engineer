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
        self.ready_notifications: List[dict] = []
        self.transfer_created_notifications: List[dict] = []
        self.transfer_finalized_notifications: List[dict] = []
        self.hydration_reminders: List[dict] = []

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
        new_eta_minutes: Optional[int] = None,
    ) -> None:
        self.festivalier_notifications.append(
            {
                "festivalier_id": festivalier_id,
                "order_id": order_id,
                "accepted": accepted,
                "rejection_reason": rejection_reason,
                "new_eta_minutes": new_eta_minutes,
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

    def notify_festivalier_order_ready(
        self,
        festivalier_id: str,
        order_id: str,
        pickup_details: str,
    ) -> None:
        self.ready_notifications.append(
            {
                "festivalier_id": festivalier_id,
                "order_id": order_id,
                "pickup_details": pickup_details,
            }
        )

    def notify_transfer_created(
        self,
        recipient_id: str,
        transfer_id: str,
        sender_id: str,
        drink_tokens: int,
        food_tokens: int,
    ) -> None:
        self.transfer_created_notifications.append(
            {
                "recipient_id": recipient_id,
                "transfer_id": transfer_id,
                "sender_id": sender_id,
                "drink_tokens": drink_tokens,
                "food_tokens": food_tokens,
            }
        )

    def notify_transfer_finalized(
        self,
        sender_id: str,
        recipient_id: str,
        transfer_id: str,
        confirmed: bool,
    ) -> None:
        self.transfer_finalized_notifications.append(
            {
                "sender_id": sender_id,
                "recipient_id": recipient_id,
                "transfer_id": transfer_id,
                "confirmed": confirmed,
            }
        )

    def notify_festivalier_hydration_reminder(
        self,
        festivalier_id: str,
        tips: Optional[str] = None,
    ) -> None:
        self.hydration_reminders.append(
            {
                "festivalier_id": festivalier_id,
                "tips": tips,
            }
        )
