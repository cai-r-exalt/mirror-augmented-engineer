"""ETA calculation domain service.

Provides a standalone ``calculate_eta`` function that computes the estimated
preparation time (in minutes) for a list of order items, based on item types
retrieved from the catalog.

ETA rules (from FEATURES.md):
- Non-alcoholic drinks : 1 minute × number of distinct drink types
- Normal alcoholic drinks : 2 minutes × total quantity ordered
- Premium alcoholic drinks : 3 minutes × total quantity ordered
- Snacks : 2 minutes × number of distinct snack types
- Meals : 10 minutes × number of distinct meal types
          + longest per-unit preparation time among all drinks in the order
            (1 min if only non-alc, 2 if normal alc present, 3 if premium alc present)
- Mixed orders : sum the above components
"""

from typing import Any, Dict, List

from app.domain.exceptions import ArticleInconnuException
from app.domain.ports.item_catalog_repository import (
    ITEM_TYPE_MEAL,
    ITEM_TYPE_NON_ALCOHOLIC_DRINK,
    ITEM_TYPE_NORMAL_ALCOHOLIC_DRINK,
    ITEM_TYPE_PREMIUM_ALCOHOLIC_DRINK,
    ITEM_TYPE_SNACK,
    ItemCatalogRepository,
)

# Per-unit preparation times (minutes)
_NON_ALC_UNIT_TIME = 1
_NORMAL_ALC_UNIT_TIME = 2
_PREMIUM_ALC_UNIT_TIME = 3
_SNACK_UNIT_TIME = 2
_MEAL_BASE_TIME = 10


def calculate_eta(items: List[Dict[str, Any]], item_catalog_repository: ItemCatalogRepository) -> int:
    """Return preparation ETA in minutes for the given list of items.

    Args:
        items: List of dicts with ``name`` and ``quantity`` keys.
        item_catalog_repository: Repository used to look up item types.

    Raises:
        ArticleInconnuException: If any item name is not found in the catalog.
    """
    non_alc_types: set = set()
    normal_alc_qty = 0
    premium_alc_qty = 0
    snack_types: set = set()
    meal_types: set = set()

    for item in items:
        name = item["name"]
        qty = item["quantity"]
        item_cost = item_catalog_repository.get_item_cost(name)
        if item_cost is None:
            raise ArticleInconnuException(name)

        item_type = item_cost.item_type
        if item_type == ITEM_TYPE_NON_ALCOHOLIC_DRINK:
            non_alc_types.add(name)
        elif item_type == ITEM_TYPE_NORMAL_ALCOHOLIC_DRINK:
            normal_alc_qty += qty
        elif item_type == ITEM_TYPE_PREMIUM_ALCOHOLIC_DRINK:
            premium_alc_qty += qty
        elif item_type == ITEM_TYPE_SNACK:
            snack_types.add(name)
        elif item_type == ITEM_TYPE_MEAL:
            meal_types.add(name)

    non_alc_time = _NON_ALC_UNIT_TIME * len(non_alc_types)
    normal_alc_time = _NORMAL_ALC_UNIT_TIME * normal_alc_qty
    premium_alc_time = _PREMIUM_ALC_UNIT_TIME * premium_alc_qty
    snack_time = _SNACK_UNIT_TIME * len(snack_types)

    longest_drink_unit_time = 0
    if non_alc_types:
        longest_drink_unit_time = max(longest_drink_unit_time, _NON_ALC_UNIT_TIME)
    if normal_alc_qty > 0:
        longest_drink_unit_time = max(longest_drink_unit_time, _NORMAL_ALC_UNIT_TIME)
    if premium_alc_qty > 0:
        longest_drink_unit_time = max(longest_drink_unit_time, _PREMIUM_ALC_UNIT_TIME)

    meal_time = (_MEAL_BASE_TIME * len(meal_types) + longest_drink_unit_time) if meal_types else 0

    return non_alc_time + normal_alc_time + premium_alc_time + snack_time + meal_time
