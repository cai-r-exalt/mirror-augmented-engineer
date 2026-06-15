"""UpdateStockUseCase — admin operation to set an item's stock quantity.

Business rules:
- The item must exist in the stock repository.
- The requested quantity must be >= 0.
- On success the stock level is persisted and an audit log entry is emitted.
"""

from dataclasses import dataclass

from app.domain.exceptions import InvalidStockQuantityException, ItemNotFoundException
from app.domain.ports.audit_log_port import AuditLogPort
from app.domain.ports.stock_repository import StockRepository


@dataclass
class UpdateStockCommand:
    """Command for an admin to set the stock quantity of a given item."""

    item_id: str
    quantity: int


class UpdateStockUseCase:
    """Domain use case for an admin to update the stock quantity of an item.

    Actions performed:
    1. Validate quantity >= 0.
    2. Validate the item exists in stock.
    3. Record the old quantity, persist the new quantity.
    4. Emit an audit log entry with old and new values.
    """

    def __init__(
        self,
        stock_repository: StockRepository,
        audit_log_port: AuditLogPort,
    ) -> None:
        self.stock_repository = stock_repository
        self.audit_log_port = audit_log_port

    def execute(self, command: UpdateStockCommand) -> None:
        if command.quantity < 0:
            raise InvalidStockQuantityException(command.quantity)

        if not self.stock_repository.item_exists(command.item_id):
            raise ItemNotFoundException(command.item_id)

        old_quantity = self.stock_repository.get_quantity(command.item_id)
        self.stock_repository.set_quantity(command.item_id, command.quantity)
        self.audit_log_port.log_stock_update(
            item_name=command.item_id,
            old_quantity=old_quantity,
            new_quantity=command.quantity,
        )
