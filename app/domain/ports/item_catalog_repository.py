from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ItemCost:
    """Token cost per unit for a catalog item."""

    name: str
    drink_tokens_per_unit: int = 0
    food_tokens_per_unit: int = 0


class ItemCatalogRepository(ABC):
    """Port for retrieving item pricing information."""

    @abstractmethod
    def get_item_cost(self, item_name: str) -> Optional[ItemCost]:
        """Return the token cost for the given item, or None if not found."""
        raise NotImplementedError
