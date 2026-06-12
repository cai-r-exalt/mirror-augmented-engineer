"""Domain unit tests for ModifyOrderUseCase.

Covers:
- Happy path: modifying a pending (EN_ATTENTE) order with valid items
- Stock is correctly restored and re-committed on modification
- Failure when order not found
- Failure when order is not in EN_ATTENTE status
- Failure when new items are out of stock or unknown
"""

import pytest

from app.domain.entities.commande import Article, Commande, LigneCommande
from app.domain.exceptions import (
    ArticleInconnuException,
    OrderNotFoundException,
    OrderNotModifiableException,
    StockInsuffisantException,
)
from app.domain.use_cases.modify_order import ModifyOrderCommand, ModifyOrderUseCase
from app.infrastructure.adapters.in_memory_order_repository import InMemoryOrderRepository
from app.infrastructure.adapters.in_memory_stock_repository import InMemoryStockRepository


class TestModifyOrderUseCase:
    def setup_method(self):
        self.order_repo = InMemoryOrderRepository()
        self.stock_repo = InMemoryStockRepository({"Mojito": 10, "Bière": 8, "Eau plate": 20})

        # Pre-place an order (Mojito x2, stock decremented to 8)
        self.stock_repo.decrement("Mojito", 2)
        self.order = Commande(
            id="order-1",
            festivalier_id="f-1",
            lignes=[LigneCommande(article=Article(name="Mojito"), quantite=2)],
            status="EN_ATTENTE",
        )
        self.order_repo.save(self.order)

        self.use_case = ModifyOrderUseCase(
            order_repository=self.order_repo,
            stock_repository=self.stock_repo,
        )

    # ── Happy path ───────────────────────────────────────────────────────────

    def test_modify_pending_order_returns_updated_order(self):
        """
        Given an unacknowledged order and sufficient stock
        When festivalier requests modifications via PATCH
        Then modifications are accepted and updated order is returned
        """
        cmd = ModifyOrderCommand(order_id="order-1", items=[{"name": "Bière", "quantity": 3}])
        result = self.use_case.execute(cmd)

        assert result.id == "order-1"
        assert len(result.lignes) == 1
        assert result.lignes[0].article.name == "Bière"
        assert result.lignes[0].quantite == 3

    def test_modify_pending_order_persists_changes(self):
        """Updated order is retrievable from the repository after modification."""
        cmd = ModifyOrderCommand(order_id="order-1", items=[{"name": "Eau plate", "quantity": 5}])
        self.use_case.execute(cmd)

        saved = self.order_repo.get_by_id("order-1")
        assert saved is not None
        assert saved.lignes[0].article.name == "Eau plate"
        assert saved.lignes[0].quantite == 5

    def test_modify_pending_order_restores_original_stock(self):
        """The stock originally committed by the order is released before re-committing."""
        # Mojito stock was decremented from 10 to 8 when order was placed.
        # After modification to Bière x1, Mojito should be back to 10.
        cmd = ModifyOrderCommand(order_id="order-1", items=[{"name": "Bière", "quantity": 1}])
        self.use_case.execute(cmd)

        assert self.stock_repo.stock["Mojito"] == 10
        assert self.stock_repo.stock["Bière"] == 7

    def test_modify_pending_order_with_same_item_different_quantity(self):
        """Modifying quantity of the same item correctly adjusts stock."""
        # Current: Mojito x2 (stock = 8). Change to Mojito x4 → stock should become 6.
        cmd = ModifyOrderCommand(order_id="order-1", items=[{"name": "Mojito", "quantity": 4}])
        self.use_case.execute(cmd)

        assert self.stock_repo.stock["Mojito"] == 6

    def test_modify_pending_order_preserves_status(self):
        """Order status remains EN_ATTENTE after a successful modification."""
        cmd = ModifyOrderCommand(order_id="order-1", items=[{"name": "Bière", "quantity": 1}])
        result = self.use_case.execute(cmd)

        assert result.status == "EN_ATTENTE"

    def test_modify_pending_order_with_multiple_new_items(self):
        """Modification can replace the order with multiple new items."""
        cmd = ModifyOrderCommand(
            order_id="order-1",
            items=[
                {"name": "Bière", "quantity": 2},
                {"name": "Eau plate", "quantity": 3},
            ],
        )
        result = self.use_case.execute(cmd)

        assert len(result.lignes) == 2
        names = {l.article.name for l in result.lignes}
        assert names == {"Bière", "Eau plate"}

    # ── Failure: order not found ─────────────────────────────────────────────

    def test_raises_order_not_found_when_order_does_not_exist(self):
        """
        Given a non-existent order id
        When festivalier requests modifications
        Then OrderNotFoundException is raised
        """
        cmd = ModifyOrderCommand(order_id="ghost-99", items=[{"name": "Mojito", "quantity": 1}])
        with pytest.raises(OrderNotFoundException) as exc_info:
            self.use_case.execute(cmd)
        assert exc_info.value.order_id == "ghost-99"

    # ── Failure: wrong status ────────────────────────────────────────────────

    def test_raises_not_modifiable_when_order_is_acknowledged(self):
        """
        Given an order with status ACQUITTEE
        When festivalier attempts direct modification via PATCH
        Then OrderNotModifiableException is raised
        """
        self.order.status = "ACQUITTEE"
        self.order_repo.save(self.order)

        cmd = ModifyOrderCommand(order_id="order-1", items=[{"name": "Bière", "quantity": 1}])
        with pytest.raises(OrderNotModifiableException) as exc_info:
            self.use_case.execute(cmd)
        assert exc_info.value.order_id == "order-1"
        assert exc_info.value.current_status == "ACQUITTEE"

    def test_raises_not_modifiable_when_order_is_cancelled(self):
        """Cancelled orders cannot be modified."""
        self.order.status = "ANNULEE"
        self.order_repo.save(self.order)

        cmd = ModifyOrderCommand(order_id="order-1", items=[{"name": "Bière", "quantity": 1}])
        with pytest.raises(OrderNotModifiableException):
            self.use_case.execute(cmd)

    # ── Failure: stock validation ────────────────────────────────────────────

    def test_raises_when_new_item_is_unknown(self):
        """
        Given an item not in the catalog
        When modification is requested
        Then ArticleInconnuException is raised and stock is unchanged
        """
        cmd = ModifyOrderCommand(order_id="order-1", items=[{"name": "Champagne", "quantity": 1}])
        with pytest.raises(ArticleInconnuException):
            self.use_case.execute(cmd)

    def test_stock_not_changed_when_new_item_is_unknown(self):
        """No stock changes occur when the modification fails due to unknown item."""
        stock_before = dict(self.stock_repo.stock)

        cmd = ModifyOrderCommand(order_id="order-1", items=[{"name": "Champagne", "quantity": 1}])
        with pytest.raises(ArticleInconnuException):
            self.use_case.execute(cmd)

        assert self.stock_repo.stock == stock_before

    def test_raises_when_new_item_is_out_of_stock(self):
        """
        Given insufficient stock for the new item
        When modification is requested
        Then StockInsuffisantException is raised
        """
        cmd = ModifyOrderCommand(order_id="order-1", items=[{"name": "Bière", "quantity": 99}])
        with pytest.raises(StockInsuffisantException):
            self.use_case.execute(cmd)

    def test_stock_not_changed_when_new_item_is_out_of_stock(self):
        """No stock changes occur when the modification fails due to insufficient stock."""
        stock_before = dict(self.stock_repo.stock)

        cmd = ModifyOrderCommand(order_id="order-1", items=[{"name": "Bière", "quantity": 99}])
        with pytest.raises(StockInsuffisantException):
            self.use_case.execute(cmd)

        assert self.stock_repo.stock == stock_before
