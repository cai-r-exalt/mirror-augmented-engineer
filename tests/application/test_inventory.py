"""Application integration tests for PATCH /inventory/{item_id}.

These tests exercise the full wiring through controller → use case → in-memory
adapters and verify correct HTTP status codes, response shapes, audit log
emission, and validation behaviour.
"""

from app.application.controllers.inventory_controller import InventoryController
from app.application.dto.inventory import UpdateStockRequest
from app.domain.use_cases.update_stock import UpdateStockUseCase
from app.infrastructure.adapters.in_memory_audit_log_adapter import InMemoryAuditLogAdapter
from app.infrastructure.adapters.in_memory_stock_repository import InMemoryStockRepository


def _build_controller(
    initial_stock: dict | None = None,
) -> tuple[InventoryController, InMemoryStockRepository, InMemoryAuditLogAdapter]:
    stock_repo = InMemoryStockRepository(initial_stock or {"Bière": 5, "Chips": 10})
    audit_log = InMemoryAuditLogAdapter()
    use_case = UpdateStockUseCase(stock_repository=stock_repo, audit_log_port=audit_log)
    controller = InventoryController(update_stock_use_case=use_case)
    return controller, stock_repo, audit_log


class TestUpdateStockEndpoint:
    """Integration tests for PATCH /inventory/{item_id}."""

    def setup_method(self):
        self.controller, self.stock_repo, self.audit_log = _build_controller()

    # ── Success cases ────────────────────────────────────────────────────────

    def test_returns_200_with_item_id_and_quantity(self):
        """
        Given a bartender updates an item stock to 10
        When the PATCH request is accepted
        Then the response is 200 with itemId and quantity
        """
        response = self.controller.update_stock(UpdateStockRequest("Bière", 10))

        assert response.status_code == 200
        body = response.json()
        assert body["itemId"] == "Bière"
        assert body["quantity"] == 10

    def test_stock_is_persisted_after_update(self):
        """Stock repository reflects the new quantity after a successful update."""
        self.controller.update_stock(UpdateStockRequest("Bière", 10))
        assert self.stock_repo.get_quantity("Bière") == 10

    def test_audit_log_entry_is_emitted_on_success(self):
        """An audit log entry is emitted recording old and new stock levels."""
        self.controller.update_stock(UpdateStockRequest("Bière", 10))

        assert len(self.audit_log.entries) == 1
        entry = self.audit_log.entries[0]
        assert entry["item_name"] == "Bière"
        assert entry["old_quantity"] == 5
        assert entry["new_quantity"] == 10

    def test_accepts_zero_quantity(self):
        """Zero is a valid quantity — fully depletes stock."""
        response = self.controller.update_stock(UpdateStockRequest("Chips", 0))

        assert response.status_code == 200
        assert response.json()["quantity"] == 0
        assert self.stock_repo.get_quantity("Chips") == 0

    # ── Validation / error cases ─────────────────────────────────────────────

    def test_returns_422_for_negative_quantity(self):
        """
        Scenario: Update stock quantity
        Given a bartender updates an item stock to -1
        Then the system rejects it with 422 and stock is unchanged
        """
        response = self.controller.update_stock(UpdateStockRequest("Bière", -1))

        assert response.status_code == 422
        assert "negative" in response.json()["error"].lower()
        # Stock must be unchanged
        assert self.stock_repo.get_quantity("Bière") == 5

    def test_returns_404_for_unknown_item(self):
        """Unknown item identifier returns 404."""
        response = self.controller.update_stock(UpdateStockRequest("Inconnue", 5))

        assert response.status_code == 404
        assert "not found" in response.json()["error"].lower()

    def test_returns_400_when_quantity_is_missing(self):
        """Missing quantity field in the request returns 400."""
        response = self.controller.update_stock(UpdateStockRequest("Bière", None))

        assert response.status_code == 400
        assert "quantity" in response.json()["error"].lower()

    def test_no_audit_log_on_failure(self):
        """Audit log must not be written when the update is rejected."""
        self.controller.update_stock(UpdateStockRequest("Bière", -1))
        assert len(self.audit_log.entries) == 0
