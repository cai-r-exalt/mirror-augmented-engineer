"""Domain unit tests for UpdateStockUseCase.

Covers:
- Successful stock update with audit log entry emitted
- Validation: quantity cannot be negative
- Validation: item must exist in stock repository
"""

import pytest

from app.domain.exceptions import InvalidStockQuantityException, ItemNotFoundException
from app.domain.use_cases.update_stock import UpdateStockCommand, UpdateStockUseCase
from app.infrastructure.adapters.in_memory_audit_log_adapter import InMemoryAuditLogAdapter
from app.infrastructure.adapters.in_memory_stock_repository import InMemoryStockRepository


def _make_use_case(
    initial_stock: dict | None = None,
) -> tuple[UpdateStockUseCase, InMemoryStockRepository, InMemoryAuditLogAdapter]:
    stock_repo = InMemoryStockRepository(initial_stock or {"Bière": 5})
    audit_log = InMemoryAuditLogAdapter()
    use_case = UpdateStockUseCase(stock_repository=stock_repo, audit_log_port=audit_log)
    return use_case, stock_repo, audit_log


class TestUpdateStockSuccess:
    """Happy-path tests for UpdateStockUseCase."""

    def test_sets_quantity_to_requested_value(self):
        """
        Given an existing item with stock 5
        When admin sets quantity to 10
        Then stock is persisted as 10
        """
        use_case, stock_repo, _ = _make_use_case({"Bière": 5})
        use_case.execute(UpdateStockCommand(item_id="Bière", quantity=10))
        assert stock_repo.get_quantity("Bière") == 10

    def test_sets_quantity_to_zero(self):
        """Quantity zero is valid — depletes the stock entirely."""
        use_case, stock_repo, _ = _make_use_case({"Bière": 3})
        use_case.execute(UpdateStockCommand(item_id="Bière", quantity=0))
        assert stock_repo.get_quantity("Bière") == 0

    def test_emits_audit_log_entry_with_old_and_new_quantity(self):
        """An audit entry is emitted recording old and new stock levels."""
        use_case, _, audit_log = _make_use_case({"Bière": 5})
        use_case.execute(UpdateStockCommand(item_id="Bière", quantity=10))

        assert len(audit_log.entries) == 1
        entry = audit_log.entries[0]
        assert entry["event"] == "stock_update"
        assert entry["item_name"] == "Bière"
        assert entry["old_quantity"] == 5
        assert entry["new_quantity"] == 10

    def test_audit_log_records_correct_old_quantity_before_update(self):
        """The audit entry captures the stock level at the time of the update."""
        use_case, _, audit_log = _make_use_case({"Chips": 7})
        use_case.execute(UpdateStockCommand(item_id="Chips", quantity=2))

        assert audit_log.entries[0]["old_quantity"] == 7
        assert audit_log.entries[0]["new_quantity"] == 2


class TestUpdateStockValidation:
    """Validation-error tests for UpdateStockUseCase."""

    def test_raises_invalid_quantity_for_negative_value(self):
        """Negative quantity is rejected before any repository call."""
        use_case, stock_repo, audit_log = _make_use_case({"Bière": 5})
        with pytest.raises(InvalidStockQuantityException):
            use_case.execute(UpdateStockCommand(item_id="Bière", quantity=-1))

        # Stock and audit log must be unchanged
        assert stock_repo.get_quantity("Bière") == 5
        assert len(audit_log.entries) == 0

    def test_raises_item_not_found_for_unknown_item(self):
        """Unknown item_id raises ItemNotFoundException."""
        use_case, _, audit_log = _make_use_case({"Bière": 5})
        with pytest.raises(ItemNotFoundException):
            use_case.execute(UpdateStockCommand(item_id="Inconnue", quantity=3))

        assert len(audit_log.entries) == 0
