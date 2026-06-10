from typing import Dict, List, Optional
from app.domain.entities.commande import Commande, Article, LigneCommande


class InMemoryOrderRepository:
    def __init__(self):
        self._store: Dict[str, Commande] = {}
        self._next = 1

    def create_order(self, festivalier_id: str, items: List[Dict]) -> Commande:
        cid = f"order-{self._next}"
        self._next += 1

        lignes = []
        for it in items:
            name = it.get("name") or it.get("id")
            qty = it.get("quantity") or it.get("quantite") or 0
            lignes.append(LigneCommande(article=Article(name=name), quantite=qty))

        commande = Commande(id=cid, festivalier_id=festivalier_id, lignes=lignes, status="EN_ATTENTE")
        self._store[cid] = commande
        return commande

    def get_commande(self, cid: str) -> Optional[Commande]:
        return self._store.get(cid)
