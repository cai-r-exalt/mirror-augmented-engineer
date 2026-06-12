"""Domain unit tests for PlaceGroupOrderUseCase.

Covers:
- Cost aggregation (drink vs food tokens separately)
- Contributor balance validation
- Stock validation (out-of-stock → 409, entire request fails)
- Successful group order creation
- Insufficient pooled funds rejection
"""

import pytest

from app.domain.exceptions import (
    ArticleInconnuException,
    ContributorBalanceExceededException,
    FestivalierInconnuException,
    InsufficientPooledFundsException,
    StockInsuffisantException,
)
from app.domain.use_cases.place_group_order import (
    ContributorInput,
    PlaceGroupOrderCommand,
    PlaceGroupOrderUseCase,
)


class TestPlaceGroupOrderUseCase:
    def setup_method(self):
        from app.infrastructure.adapters.in_memory_festivalier_repository import InMemoryFestivalierRepository
        from app.infrastructure.adapters.in_memory_item_catalog_repository import InMemoryItemCatalogRepository
        from app.infrastructure.adapters.in_memory_order_repository import InMemoryOrderRepository
        from app.infrastructure.adapters.in_memory_stock_repository import InMemoryStockRepository

        self.order_repo = InMemoryOrderRepository()
        self.stock_repo = InMemoryStockRepository({"Mojito": 10, "Burger": 5})
        self.festivalier_repo = InMemoryFestivalierRepository(
            {
                "f-1": {"drink_tokens": 10, "food_tokens": 0},
                "f-2": {"drink_tokens": 5, "food_tokens": 8},
                "f-3": {"drink_tokens": 3, "food_tokens": 0},
            }
        )
        self.catalog_repo = InMemoryItemCatalogRepository(
            {
                "Mojito": {"drink_tokens_per_unit": 3, "food_tokens_per_unit": 0},
                "Burger": {"drink_tokens_per_unit": 0, "food_tokens_per_unit": 4},
            }
        )

        self.use_case = PlaceGroupOrderUseCase(
            order_repository=self.order_repo,
            stock_repository=self.stock_repo,
            festivalier_repository=self.festivalier_repo,
            item_catalog_repository=self.catalog_repo,
        )

    # ── Successful group order ───────────────────────────────────────────────

    def test_successful_group_order_created_with_pending_status(self):
        """
        Given three users contribute drink tokens summing to required total and items are in stock
        When they submit a group order
        Then order is created with status EN_ATTENTE
        """
        cmd = PlaceGroupOrderCommand(
            items=[{"name": "Mojito", "quantity": 3}],  # cost: 9 drink tokens
            contributors=[
                ContributorInput(festivalier_id="f-1", drink_tokens=5, food_tokens=0),
                ContributorInput(festivalier_id="f-2", drink_tokens=4, food_tokens=0),
            ],
        )
        result = self.use_case.execute(cmd)

        assert result is not None
        assert result.id is not None
        assert result.status == "EN_ATTENTE"

    def test_successful_group_order_stores_contributors_metadata(self):
        cmd = PlaceGroupOrderCommand(
            items=[{"name": "Mojito", "quantity": 2}],  # cost: 6 drink tokens
            contributors=[
                ContributorInput(festivalier_id="f-1", drink_tokens=4, food_tokens=0),
                ContributorInput(festivalier_id="f-2", drink_tokens=2, food_tokens=0),
            ],
        )
        result = self.use_case.execute(cmd)

        assert result.contributors is not None
        assert len(result.contributors) == 2
        fids = [c.festivalier_id for c in result.contributors]
        assert "f-1" in fids
        assert "f-2" in fids

    def test_successful_group_order_decrements_stock(self):
        cmd = PlaceGroupOrderCommand(
            items=[{"name": "Mojito", "quantity": 4}],  # cost: 12 drink tokens
            contributors=[
                ContributorInput(festivalier_id="f-1", drink_tokens=10, food_tokens=0),
                ContributorInput(festivalier_id="f-2", drink_tokens=5, food_tokens=0),
            ],
        )
        self.use_case.execute(cmd)

        assert self.stock_repo.stock["Mojito"] == 6

    def test_successful_group_order_mixed_drink_and_food(self):
        cmd = PlaceGroupOrderCommand(
            items=[
                {"name": "Mojito", "quantity": 1},   # costs 3 drink tokens
                {"name": "Burger", "quantity": 1},   # costs 4 food tokens
            ],
            contributors=[
                ContributorInput(festivalier_id="f-1", drink_tokens=3, food_tokens=0),
                ContributorInput(festivalier_id="f-2", drink_tokens=0, food_tokens=4),
            ],
        )
        result = self.use_case.execute(cmd)

        assert result.status == "EN_ATTENTE"

    # ── Cost aggregation ────────────────────────────────────────────────────

    def test_cost_aggregation_drink_and_food_evaluated_separately(self):
        """Pooled drink tokens must cover drink costs; food tokens must cover food costs."""
        cmd = PlaceGroupOrderCommand(
            items=[
                {"name": "Mojito", "quantity": 2},   # costs 6 drink tokens
                {"name": "Burger", "quantity": 2},   # costs 8 food tokens
            ],
            contributors=[
                ContributorInput(festivalier_id="f-1", drink_tokens=6, food_tokens=0),
                ContributorInput(festivalier_id="f-2", drink_tokens=0, food_tokens=8),
            ],
        )
        result = self.use_case.execute(cmd)
        assert result.status == "EN_ATTENTE"

    # ── Contributor balance validation ──────────────────────────────────────

    def test_raises_when_contributor_exceeds_drink_balance(self):
        """f-3 only has 3 drink tokens but offers 5."""
        cmd = PlaceGroupOrderCommand(
            items=[{"name": "Mojito", "quantity": 1}],
            contributors=[
                ContributorInput(festivalier_id="f-3", drink_tokens=5, food_tokens=0),
            ],
        )
        with pytest.raises(ContributorBalanceExceededException) as exc_info:
            self.use_case.execute(cmd)
        assert exc_info.value.festivalier_id == "f-3"
        assert exc_info.value.token_type == "drink"

    def test_raises_when_contributor_exceeds_food_balance(self):
        """f-1 has 0 food tokens but offers 1."""
        cmd = PlaceGroupOrderCommand(
            items=[{"name": "Burger", "quantity": 1}],
            contributors=[
                ContributorInput(festivalier_id="f-1", drink_tokens=0, food_tokens=1),
            ],
        )
        with pytest.raises(ContributorBalanceExceededException) as exc_info:
            self.use_case.execute(cmd)
        assert exc_info.value.token_type == "food"

    def test_raises_when_festivalier_unknown(self):
        cmd = PlaceGroupOrderCommand(
            items=[{"name": "Mojito", "quantity": 1}],
            contributors=[
                ContributorInput(festivalier_id="unknown-99", drink_tokens=5, food_tokens=0),
            ],
        )
        with pytest.raises(FestivalierInconnuException):
            self.use_case.execute(cmd)

    # ── Insufficient pooled funds ────────────────────────────────────────────

    def test_raises_when_pooled_drink_tokens_insufficient(self):
        """
        Given pooled contributions are below required drink cost
        When group order is attempted
        Then raises InsufficientPooledFundsException and no balances change
        """
        cmd = PlaceGroupOrderCommand(
            items=[{"name": "Mojito", "quantity": 3}],  # costs 9 drink tokens
            contributors=[
                ContributorInput(festivalier_id="f-1", drink_tokens=4, food_tokens=0),
                ContributorInput(festivalier_id="f-2", drink_tokens=3, food_tokens=0),
                # pooled = 7, need 9
            ],
        )
        with pytest.raises(InsufficientPooledFundsException) as exc_info:
            self.use_case.execute(cmd)
        assert exc_info.value.token_type == "drink"
        assert exc_info.value.required == 9
        assert exc_info.value.pooled == 7

    def test_raises_when_pooled_food_tokens_insufficient(self):
        cmd = PlaceGroupOrderCommand(
            items=[{"name": "Burger", "quantity": 3}],  # costs 12 food tokens
            contributors=[
                ContributorInput(festivalier_id="f-2", drink_tokens=0, food_tokens=8),
                # pooled food = 8, need 12
            ],
        )
        with pytest.raises(InsufficientPooledFundsException) as exc_info:
            self.use_case.execute(cmd)
        assert exc_info.value.token_type == "food"

    def test_no_stock_decremented_when_pooled_funds_insufficient(self):
        """Stock must not change when the request fails."""
        cmd = PlaceGroupOrderCommand(
            items=[{"name": "Mojito", "quantity": 3}],  # costs 9
            contributors=[
                ContributorInput(festivalier_id="f-1", drink_tokens=4, food_tokens=0),
                ContributorInput(festivalier_id="f-2", drink_tokens=3, food_tokens=0),
            ],
        )
        stock_before = self.stock_repo.stock["Mojito"]
        with pytest.raises(InsufficientPooledFundsException):
            self.use_case.execute(cmd)
        assert self.stock_repo.stock["Mojito"] == stock_before

    # ── Stock validation ─────────────────────────────────────────────────────

    def test_raises_when_item_out_of_stock(self):
        """If any item is out of stock the entire request fails with no balance changes."""
        cmd = PlaceGroupOrderCommand(
            items=[{"name": "Mojito", "quantity": 99}],  # only 10 available
            contributors=[
                ContributorInput(festivalier_id="f-1", drink_tokens=10, food_tokens=0),
            ],
        )
        with pytest.raises(StockInsuffisantException):
            self.use_case.execute(cmd)

    def test_raises_when_item_unknown(self):
        cmd = PlaceGroupOrderCommand(
            items=[{"name": "Champagne", "quantity": 1}],
            contributors=[
                ContributorInput(festivalier_id="f-1", drink_tokens=5, food_tokens=0),
            ],
        )
        with pytest.raises(ArticleInconnuException):
            self.use_case.execute(cmd)
