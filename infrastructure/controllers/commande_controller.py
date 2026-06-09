from typing import Any, Dict

from infrastructure.dto.commande import CreerCommandeRequest, CreerCommandeResponse


class CommandesController:
    """Controller handling commandes; delegates to an injected use-case.

    The controller accepts a `use_case` object with `execute(payload)` and
    `get_commande(commande_id)` methods. If none is provided, minimal
    behavior is returned to keep the interface usable.
    """

    def __init__(self, use_case: Any = None) -> None:
        self.use_case = use_case

    def creer_commande(self, req: CreerCommandeRequest) -> CreerCommandeResponse:
        # Authentication check
        if not req.festivalierId:
            return CreerCommandeResponse(401, {})

        # Basic payload validation
        if not req.articles or not isinstance(req.articles, list):
            return CreerCommandeResponse(400, {})

        payload: Dict[str, Any] = {"festivalierId": req.festivalierId, "articles": req.articles}

        if self.use_case:
            result = self.use_case.execute(payload)
            return CreerCommandeResponse(201, {"commandeId": result.get("id")})

        # Minimal default response when no use-case is wired
        return CreerCommandeResponse(201, {"commandeId": "order-todo"})

    def get_commande(self, commande_id: str) -> CreerCommandeResponse:
        if self.use_case:
            order = self.use_case.get_commande(commande_id)
            if not order:
                return CreerCommandeResponse(404, {})
            return CreerCommandeResponse(200, order)
        return CreerCommandeResponse(404, {})
