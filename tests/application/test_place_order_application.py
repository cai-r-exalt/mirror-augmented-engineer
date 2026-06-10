import pytest

from app.application.controllers.commande_controller import CommandesController
from app.application.dto.commande import CreerCommandeRequest
from app.domain.use_cases.place_order import PasserCommandeUseCase


class TestPlaceOrderApplicationController:
    def setup_method(self):
        # Use production in-memory stock repository for application tests
        from app.infrastructure.adapters.in_memory_stock_repository import InMemoryStockRepository
        from app.infrastructure.adapters.in_memory_order_repository import InMemoryOrderRepository

        # Provide some initial stock for the scenario
        self.fake_inventory = InMemoryStockRepository({"Mojito": 10})
        self.fake_order_repo = InMemoryOrderRepository()

        # Wire the real domain use-case into the controller
        self.use_case = PasserCommandeUseCase(
            order_repository=self.fake_order_repo, stock_repository=self.fake_inventory
        )

        self.client = CommandesController(use_case=self.use_case)
        self.CreerCommandeRequest = CreerCommandeRequest

    def test_given_mojito_in_stock_when_post_commandes_then_returns_201_and_order_pending(self):
        # Given
        req = self.CreerCommandeRequest("festivalier-1", [{"id": "Mojito", "quantite": 1}])

        # When
        response = self.client.creer_commande(req)

        # Then: should return 201 and provide a commandeId (this test is expected to fail)
        assert response.status_code == 201
        assert "commandeId" in response.json()
        assert response.json()["commandeId"]
