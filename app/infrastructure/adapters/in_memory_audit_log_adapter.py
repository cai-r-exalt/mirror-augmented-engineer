from typing import Any, Dict, List

from app.domain.ports.audit_log_port import AuditLogPort


class InMemoryAuditLogAdapter(AuditLogPort):
    """In-memory implementation of AuditLogPort for tests and local runs.

    Records all emitted audit entries so they can be inspected in tests.
    """

    def __init__(self) -> None:
        self.entries: List[Dict[str, Any]] = []

    def log_stock_update(self, item_name: str, old_quantity: int, new_quantity: int) -> None:
        self.entries.append(
            {
                "event": "stock_update",
                "item_name": item_name,
                "old_quantity": old_quantity,
                "new_quantity": new_quantity,
            }
        )
