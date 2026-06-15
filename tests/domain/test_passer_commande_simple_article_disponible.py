
from app.domain.use_cases.place_order import PasserCommandeCommand, PasserCommandeUseCase

"""Scenario: Passer une commande simple avec un article disponible

Given un article "Bière Pale Ale" disponible en stock (10 unités)
When un client commande 2 unités
Then la commande est créée avec succès
And le stock est décrémenté de 2
"""


class TestPasserCommandeSimpleArticleDisponible:
    def setup_method(self):
        from app.infrastructure.adapters.in_memory_order_repository import InMemoryOrderRepository
        from app.infrastructure.adapters.in_memory_stock_repository import InMemoryStockRepository

        # Use production in-memory repositories
        self.inventory = InMemoryStockRepository({"Bière Pale Ale": 10})
        self.order_repo = InMemoryOrderRepository()

        self.use_case = PasserCommandeUseCase(order_repository=self.order_repo, stock_repository=self.inventory)

    def test_passer_une_commande_simple_avec_article_disponible(self):
        # Given
        cmd = PasserCommandeCommand(festivalier_id="client-1", items=[{"name": "Bière Pale Ale", "quantity": 2}])

        # When
        result = self.use_case.execute(cmd)

        # Then: la commande est créée
        assert result is not None
        assert getattr(result, "id", None) is not None
        assert result.status == "EN_ATTENTE"

        # And: le stock est décrémenté de 2
        assert self.inventory.stock["Bière Pale Ale"] == 8

        # And: the order repository contains the created commande with correct ligne
        stored = self.order_repo.get_by_id(result.id)
        assert stored is not None
        assert stored.lignes[0].article.name == "Bière Pale Ale"
        assert stored.lignes[0].quantite == 2
