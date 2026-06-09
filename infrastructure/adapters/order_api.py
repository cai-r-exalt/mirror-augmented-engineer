from typing import Any, Dict, Optional

from infrastructure.controllers.commande_controller import CommandesController
from infrastructure.dto.commande import CreerCommandeRequest, CreerCommandeResponse


class InfrastructureOrderAPI:
    """Adapter providing a simple HTTP-like client interface backed by
    the local `CommandesController`.

    This keeps the old `post_commandes`/`get_commande` shape while delegating
    to the controller and using the DTOs.
    """

    def __init__(self, base_url: str = "http://localhost:8000", controller: Optional[CommandesController] = None) -> None:
        self.base_url = base_url
        self.controller = controller or CommandesController()

    def post_commandes(self, payload: Dict[str, Any]) -> CreerCommandeResponse:
        req = CreerCommandeRequest(payload.get("festivalierId"), payload.get("articles"))
        return self.controller.creer_commande(req)

    def get_commande(self, commande_id: str) -> CreerCommandeResponse:
        return self.controller.get_commande(commande_id)

