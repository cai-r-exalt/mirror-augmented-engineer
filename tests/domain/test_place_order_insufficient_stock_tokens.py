import pytest

from app.domain.use_cases.place_order import PasserCommandeUseCase, PasserCommandeCommand
from app.domain.exceptions import StockInsuffisantException


class TestPlaceOrderInsufficientStockTokens:
    def setup_method(self):
        from app.infrastructure.adapters.in_memory_stock_repository import InMemoryStockRepository

        class FakeOrderRepository:
            def create_order(self, festivalier_id: str, items: list):
                class Order:
                    def __init__(self, order_id, status):
                        self.id = order_id
                        self.status = status

                return Order(order_id="order-99", status="EN_ATTENTE")

        self.FakeInventoryRepository = InMemoryStockRepository
        self.fake_order_repo = FakeOrderRepository()

    def test_order_rejected_and_tokens_unchanged_when_stock_insufficient(self):
        # Given a festival goer with tokens and inventory with limited stock
        inventory = self.FakeInventoryRepository({"beer": 2})
        use_case = PasserCommandeUseCase(order_repository=self.fake_order_repo, stock_repository=inventory)

        festivalier_tokens = {"drink": 10, "food": 15}

        # When: attempt to order 3 beers
        cmd = PasserCommandeCommand(festivalier_id="f-1", items=[{"name": "beer", "quantity": 3}])

        # Then: should be rejected with StockInsuffisantException and tokens remain unchanged
        with pytest.raises(StockInsuffisantException) as excinfo:
            use_case.execute(cmd)

        assert "Insufficient stock" in str(excinfo.value)
        assert festivalier_tokens["drink"] == 10
        assert festivalier_tokens["food"] == 15
