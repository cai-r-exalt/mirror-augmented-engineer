from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.domain.entities.commande import Article, Commande, ContributorContribution, LigneCommande


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

    def create_group_order(
        self,
        contributors: List[ContributorContribution],
        items: List[dict],
    ) -> Commande:
        cid = f"order-{self._next}"
        self._next += 1

        lignes: List[LigneCommande] = []
        for it in items:
            name = it.get("name") or it.get("id")
            qty = it.get("quantity") or it.get("quantite") or 0
            lignes.append(LigneCommande(article=Article(name=name), quantite=qty))

        commande = Commande(
            id=cid,
            festivalier_id="GROUP",
            lignes=lignes,
            status="EN_ATTENTE",
            contributors=contributors,
        )
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

    def find_by_festivalier_acknowledged_since(
        self, festivalier_id: str, since: datetime
    ) -> List[Commande]:
        results = []
        for c in self._store.values():
            if c.festivalier_id != festivalier_id:
                continue
            if not c.acknowledged_at:
                continue
            ack_dt = datetime.fromisoformat(c.acknowledged_at)
            if ack_dt.tzinfo is None:
                ack_dt = ack_dt.replace(tzinfo=timezone.utc)
            since_aware = since if since.tzinfo is not None else since.replace(tzinfo=timezone.utc)
            if ack_dt >= since_aware:
                results.append(c)
        return results

    # Backwards-compatibility adapter used by some application-layer tests
    def get_commande(self, cid: str) -> Optional[Commande]:
        return self.get_by_id(cid)
