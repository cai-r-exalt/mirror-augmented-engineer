from abc import ABC, abstractmethod


class AuditLogPort(ABC):
    """Secondary port for emitting audit log entries."""

    @abstractmethod
    def log_stock_update(self, item_name: str, old_quantity: int, new_quantity: int) -> None:
        """Record an audit log entry for a stock quantity update.

        Args:
            item_name: The identifier of the item whose stock was updated.
            old_quantity: The stock level before the update.
            new_quantity: The stock level after the update.
        """
        raise NotImplementedError
