from typing import Dict, List, Optional
from app.domain.entities.commande import Commande, Article, LigneCommande


class InMemoryOrderRepository:
    def __init__(self):
        self._store: Dict[str, Commande] = {}
        self._next = 1

    def create_order(self, festivalier_id: str, items: List[dict]) -> Commande:
        cid = f"order-{self._next}"
        self._next += 1

        lignes: List[LigneCommande] = []
        for it in items:
            name = it.get("name") or it.get("id")
            qty = it.get("quantity") or it.get("quantite") or 0
            lignes.append(LigneCommande(article=Article(name=name), quantite=qty))

        commande = Commande(id=cid, festivalier_id=festivalier_id, lignes=lignes, status="EN_ATTENTE")
        self._store[cid] = commande
        return commande

    # Persistence-like interface used by domain use-cases and infrastructure tests
    def save(self, commande: Commande) -> None:
        self._store[commande.id] = commande

    def get_by_id(self, order_id: str) -> Optional[Commande]:
        return self._store.get(order_id)

    def update_status(self, order_id: str, status: str) -> None:
        if order_id in self._store:
            self._store[order_id].status = status

    def find_by_festivalier_and_status(self, festivalier_id: str, status: str) -> List[Commande]:
        return [c for c in self._store.values() if c.festivalier_id == festivalier_id and c.status == status]

    # Backwards-compatibility adapter used by some application-layer tests
    def get_commande(self, cid: str) -> Optional[Commande]:
        return self.get_by_id(cid)
