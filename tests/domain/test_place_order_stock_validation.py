import pytest

from app.domain.use_cases.place_order import PasserCommandeUseCase, PasserCommandeCommand
from app.domain.exceptions import StockInsuffisantException, ArticleInconnuException


class TestPlaceOrderStockValidation:
    def setup_method(self):
        # Use production in-memory stock repository for domain tests
        from app.infrastructure.adapters.in_memory_stock_repository import InMemoryStockRepository

        class FakeOrderRepository:
            def create_order(self, festivalier_id: str, items: list):
                class Order:
                    def __init__(self, order_id, status):
                        self.id = order_id
                        self.status = status

                return Order(order_id="order-42", status="EN_ATTENTE")

        self.FakeInventoryRepository = InMemoryStockRepository
        self.fake_order_repo = FakeOrderRepository()

    def test_commande_created_and_stock_decremented_when_stock_sufficient(self):
        # Given
        inventory = self.FakeInventoryRepository({"Mojito": 10})
        use_case = PasserCommandeUseCase(order_repository=self.fake_order_repo, stock_repository=inventory)

        # When
        cmd = PasserCommandeCommand(festivalier_id="f-1", items=[{"name": "Mojito", "quantity": 2}])
        result = use_case.execute(cmd)

        # Then: order created and stock decremented by 2
        assert result is not None
        assert result.status == "EN_ATTENTE"
        # The following assertion is expected to fail because stock decrement is
        # not implemented in the current use case.
        assert inventory.stock["Mojito"] == 8

    def test_commande_refused_when_stock_insufficient(self):
        # Given
        inventory = self.FakeInventoryRepository({"Mojito": 1})
        use_case = PasserCommandeUseCase(order_repository=self.fake_order_repo, stock_repository=inventory)

        # When / Then: expect a domain-specific STOCK_INSUFFISANT error
        cmd = PasserCommandeCommand(festivalier_id="f-1", items=[{"name": "Mojito", "quantity": 2}])
        with pytest.raises(StockInsuffisantException):
            use_case.execute(cmd)

    def test_commande_refused_if_article_unknown(self):
        # Given: empty catalogue
        inventory = self.FakeInventoryRepository({})
        use_case = PasserCommandeUseCase(order_repository=self.fake_order_repo, stock_repository=inventory)

        # When / Then: expect ARTICLE_INCONNU error
        cmd = PasserCommandeCommand(festivalier_id="f-1", items=[{"name": "Champagne", "quantity": 1}])
        with pytest.raises(ArticleInconnuException):
            use_case.execute(cmd)
