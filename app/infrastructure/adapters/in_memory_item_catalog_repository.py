from typing import Dict, Optional

from app.domain.ports.item_catalog_repository import ItemCatalogRepository, ItemCost


class InMemoryItemCatalogRepository(ItemCatalogRepository):
    """In-memory implementation of the ItemCatalogRepository port.

    Stores item pricing keyed by item name.
    """

    def __init__(self, catalog: Dict[str, Dict] | None = None) -> None:
        self._catalog: Dict[str, ItemCost] = {}
        if catalog:
            for name, costs in catalog.items():
                self._catalog[name] = ItemCost(
                    name=name,
                    drink_tokens_per_unit=costs.get("drink_tokens_per_unit", 0),
                    food_tokens_per_unit=costs.get("food_tokens_per_unit", 0),
                    item_type=costs.get("item_type"),
                )

    def get_item_cost(self, item_name: str) -> Optional[ItemCost]:
        return self._catalog.get(item_name)

    def register(self, item_cost: ItemCost) -> None:
        self._catalog[item_cost.name] = item_cost
