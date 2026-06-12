from abc import ABC, abstractmethod
from typing import Optional


class NotificationPort(ABC):
    """Secondary port for sending notifications to bartenders and festivaliers."""

    @abstractmethod
    def notify_bartender_change_requested(self, order_id: str, change_request_id: str) -> None:
        """Notify bartender(s) that a change request has been submitted for the given order."""
        raise NotImplementedError

    @abstractmethod
    def notify_festivalier_change_resolved(
        self,
        festivalier_id: str,
        order_id: str,
        accepted: bool,
        rejection_reason: Optional[str] = None,
        new_eta_minutes: Optional[int] = None,
    ) -> None:
        """Notify the festivalier of the bartender's resolution of a change request.

        When *accepted* is ``True`` and ``new_eta_minutes`` is provided, the
        notification should include the updated estimated preparation time.
        """
        raise NotImplementedError

    @abstractmethod
    def notify_festivalier_order_acknowledged(
        self,
        festivalier_id: str,
        order_id: str,
        eta_minutes: int,
    ) -> None:
        """Notify the festivalier that their order has been acknowledged with an ETA."""
        raise NotImplementedError

    @abstractmethod
    def notify_festivalier_order_ready(
        self,
        festivalier_id: str,
        order_id: str,
        pickup_details: str,
    ) -> None:
        """Notify the festivalier that their order is ready for pickup."""
        raise NotImplementedError
