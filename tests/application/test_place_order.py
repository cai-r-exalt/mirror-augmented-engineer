import pytest

"""Application-layer test: Passer une commande (simple, article en stock).

Scenario:
    Given un festivalier identifié
    And un article "Mojito" disponible en stock
    When le festivalier passe une commande pour 1 "Mojito"
    Then la commande est créée avec le statut "EN_ATTENTE"
    And le festivalier reçoit un identifiant de commande

This test is expected to fail until the application use case is implemented.
"""

from app.application.use_cases.place_order import PasserCommandeUseCase, PasserCommandeCommand


class TestPlaceOrder:
    def setup_method(self):
        # Use production in-memory stock repository for application tests
        from app.infrastructure.adapters.in_memory_stock_repository import InMemoryStockRepository
        from app.infrastructure.adapters.in_memory_order_repository import InMemoryOrderRepository

        self.fake_inventory = InMemoryStockRepository({"Mojito": 10})
        self.fake_order_repo = InMemoryOrderRepository()

        # Use production use-case and command classes
        self.use_case = PasserCommandeUseCase(
            order_repository=self.fake_order_repo,
            stock_repository=self.fake_inventory,
        )

    def test_commande_simple_mojito_en_stock_cree_commande_en_attente_avec_id(self):
        # Given
        cmd = PasserCommandeCommand(festivalier_id="festivalier-1", items=[{"name": "Mojito", "quantity": 1}])

        # When
        result = self.use_case.execute(cmd)

        # Then
        assert result is not None
        assert result.status == "EN_ATTENTE"
        assert getattr(result, "id", None) is not None
