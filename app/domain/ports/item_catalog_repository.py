from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

# Valid item type constants
ITEM_TYPE_NON_ALCOHOLIC_DRINK = "non_alcoholic_drink"
ITEM_TYPE_NORMAL_ALCOHOLIC_DRINK = "normal_alcoholic_drink"
ITEM_TYPE_PREMIUM_ALCOHOLIC_DRINK = "premium_alcoholic_drink"
ITEM_TYPE_SNACK = "snack"
ITEM_TYPE_MEAL = "meal"


@dataclass(frozen=True)
class ItemCost:
    """Token cost per unit and preparation metadata for a catalog item."""

    name: str
    drink_tokens_per_unit: int = 0
    food_tokens_per_unit: int = 0
    item_type: Optional[str] = None


class ItemCatalogRepository(ABC):
    """Port for retrieving item pricing information."""

    @abstractmethod
    def get_item_cost(self, item_name: str) -> Optional[ItemCost]:
        """Return the token cost for the given item, or None if not found."""
        raise NotImplementedError
