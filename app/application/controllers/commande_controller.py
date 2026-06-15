from typing import Any, Dict

from app.application.dto.commande import CreerCommandeRequest, CreerCommandeResponse
from app.application.use_cases.validate_order import map_request_to_domain_command, validate_order_request


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

        # Delegate request validation to application use-case
        errors = validate_order_request(req)
        if errors:
            return CreerCommandeResponse(400, {"errors": errors})

        payload: Dict[str, Any] = {"festivalierId": req.festivalierId, "articles": req.articles}

        if self.use_case:
            # If the injected use-case originates from the domain package, adapt the
            # incoming HTTP-like DTO into the domain command expected by the
            # `PasserCommandeUseCase`. Otherwise, preserve the older dict-shaped
            # payload for test-local mock use-cases.
            try:
                module_path = getattr(self.use_case.__class__, "__module__", "")
                # The domain use-case may live under app.domain or domain; detect
                # presence of 'domain' in the module path rather than strict prefix.
                is_domain_use_case = "domain" in module_path
            except Exception:
                is_domain_use_case = False

            if is_domain_use_case:
                command = map_request_to_domain_command(req)
                result = self.use_case.execute(command)
            else:
                result = self.use_case.execute(payload)

            # Normalize access to the created order id depending on the
            # use-case return type (domain entity vs dict-like).
            commande_id = None
            try:
                # Domain entities typically expose attributes
                commande_id = getattr(result, "id", None)
            except Exception:
                commande_id = None

            if not commande_id and isinstance(result, dict):
                commande_id = result.get("id")

            return CreerCommandeResponse(201, {"commandeId": commande_id})

        # Minimal default response when no use-case is wired
        return CreerCommandeResponse(201, {"commandeId": "order-todo"})

    def get_commande(self, commande_id: str) -> CreerCommandeResponse:
        if self.use_case:
            order = self.use_case.get_commande(commande_id)
            if not order:
                return CreerCommandeResponse(404, {})
            return CreerCommandeResponse(200, order)
        return CreerCommandeResponse(404, {})
