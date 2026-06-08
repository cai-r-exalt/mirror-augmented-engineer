import pytest
from dataclasses import dataclass
from typing import List, Dict, Any

"""Application-layer test: Passer une commande (simple, article en stock).

Scenario:
  Given un festivalier identifié
  And un article "Mojito" disponible en stock
  When le festivalier passe une commande pour 1 "Mojito"
  Then la commande est créée avec le statut "EN_ATTENTE"
  And le festivalier reçoit un identifiant de commande

This test is expected to fail until the application use case is implemented.
"""


@dataclass
class PlaceOrderCommand:
    festivalier_id: str
    items: List[Dict[str, Any]]


class PlaceOrderUseCase:
    def __init__(self, order_repository, inventory_repository):
        self.order_repository = order_repository
        self.inventory_repository = inventory_repository

    def execute(self, command: PlaceOrderCommand):
        for item in command.items:
            if not self.inventory_repository.is_in_stock(item["name"], item["quantity"]):
                raise ValueError("Item out of stock")
        return self.order_repository.create_order(command.festivalier_id, command.items)


class TestPlaceOrder:
    def setup_method(self):
        # Simple fakes to fulfil the use-case constructor shape in the future.
        class FakeInventoryRepository:
            def is_in_stock(self, item_name: str, quantity: int) -> bool:
                return True

        class FakeOrderRepository:
            def create_order(self, festivalier_id: str, items: list):
                class Order:
                    def __init__(self, order_id, status):
                        self.id = order_id
                        self.status = status

                # Intentionally return a placeholder order
                return Order(order_id=None, status="PENDING")

        self.fake_inventory = FakeInventoryRepository()
        self.fake_order_repo = FakeOrderRepository()

        # Use test-local use-case and command classes (no production imports)
        self.use_case = PlaceOrderUseCase(
            order_repository=self.fake_order_repo,
            inventory_repository=self.fake_inventory,
        )

    def test_commande_simple_mojito_en_stock_cree_commande_en_attente_avec_id(self):
        # Given
        cmd = PlaceOrderCommand(festivalier_id="festivalier-1", items=[{"name": "Mojito", "quantity": 1}])

        # When
        result = self.use_case.execute(cmd)

        # Then
        assert result is not None
        assert result.status == "EN_ATTENTE"
        assert getattr(result, "id", None) is not None
