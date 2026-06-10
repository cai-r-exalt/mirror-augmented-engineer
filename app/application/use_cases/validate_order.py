from typing import Any, Dict, List


def validate_order_request(req: Any) -> List[Dict[str, str]]:
    """Validate an incoming CreerCommandeRequest-like object.

    Returns a list of error dicts with keys `field` and `message`.
    """
    errors: List[Dict[str, str]] = []

    if not req.festivalierId:
        errors.append({"field": "festivalierId", "message": "missing festivalierId"})

    if not req.articles or not isinstance(req.articles, list):
        errors.append({"field": "articles", "message": "articles must be a list"})
        return errors

    for a in req.articles:
        if not (a.get("id") or a.get("name")):
            errors.append({"field": "item_id", "message": "missing item_id"})

        # Validate quantity exists and is a positive integer
        qty = None
        if "quantite" in a:
            qty = a.get("quantite")
        elif "quantity" in a:
            qty = a.get("quantity")

        if qty is None or not isinstance(qty, int) or qty <= 0:
            errors.append({"field": "quantity", "message": "invalid quantity"})

    return errors


def map_request_to_domain_command(req: Any):
    """Map a `CreerCommandeRequest`-like object to a `PasserCommandeCommand`.

    This helper centralises the mapping logic so controllers can stay thin.
    """
    from app.domain.use_cases.place_order import PasserCommandeCommand

    items = []
    for a in req.articles:
        name = a.get("id") or a.get("name")
        qty = a.get("quantite") or a.get("quantity")
        items.append({"name": name, "quantity": qty})

    return PasserCommandeCommand(festivalier_id=req.festivalierId, items=items)

