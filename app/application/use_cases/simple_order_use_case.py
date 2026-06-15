from typing import Any, Dict


class SimpleOrderUseCase:
    """Small application-layer use-case used for simple end-to-end wiring in tests.

    Implements the lightweight interface expected by the controller: `execute(payload)`
    returning a dict-like order, and `get_commande(cid)`.
    """

    def __init__(self):
        self._store = {}
        self._next = 1

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        cid = f"order-{self._next}"
        self._next += 1
        order = {
            "id": cid,
            "festivalierId": payload.get("festivalierId"),
            "articles": payload.get("articles", []),
            "status": "EN_ATTENTE",
        }
        self._store[cid] = order
        return order

    def get_commande(self, cid: str) -> Dict[str, Any]:
        return self._store.get(cid)
