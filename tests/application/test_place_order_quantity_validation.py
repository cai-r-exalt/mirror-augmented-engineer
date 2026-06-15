
from app.application.controllers.commande_controller import CommandesController
from app.application.dto.commande import CreerCommandeRequest
from app.domain.use_cases.place_order import PasserCommandeUseCase


class TestPlaceOrderInvalidQuantity:
    def setup_method(self):
        from app.infrastructure.adapters.in_memory_order_repository import InMemoryOrderRepository
        from app.infrastructure.adapters.in_memory_stock_repository import InMemoryStockRepository

        self.fake_inventory = InMemoryStockRepository({"Mojito": 5})
        self.fake_order_repo = InMemoryOrderRepository()

        self.use_case = PasserCommandeUseCase(
            order_repository=self.fake_order_repo, stock_repository=self.fake_inventory
        )

        self.client = CommandesController(use_case=self.use_case)

    def test_when_quantity_zero_then_returns_400_and_validation_error(self):
        # Given: an authenticated festival goer and an item with quantity 0
        req = CreerCommandeRequest("festivalier-1", [{"id": "Mojito", "quantite": 0}])

        # When
        response = self.client.creer_commande(req)

        # Then: API should return 400 Bad Request with a validation error about quantity
        assert response.status_code == 400
        body = response.json()
        assert "errors" in body, f"expected validation errors in response, got: {body}"
        assert any(err.get("field") == "quantity" for err in body.get("errors", []))
