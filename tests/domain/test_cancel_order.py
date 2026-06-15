from app.domain.entities.commande import Article, Commande, LigneCommande
from app.domain.ports.order_repository import OrderRepository


class FakeOrderRepository(OrderRepository):
    def __init__(self):
        self._store = {}

    def create_order(self, festivalier_id: str, items):
        raise NotImplementedError

    def save(self, commande: Commande) -> None:
        self._store[commande.id] = commande

    def get_by_id(self, order_id: str):
        return self._store.get(order_id)

    def update_status(self, order_id: str, status: str) -> None:
        if order_id in self._store:
            self._store[order_id].status = status

    def create_group_order(self, contributors, items):
        raise NotImplementedError

    def find_by_festivalier_and_status(self, festivalier_id: str, status: str):
        return [c for c in self._store.values() if c.festivalier_id == festivalier_id and c.status == status]

    def find_by_festivalier_acknowledged_since(self, festivalier_id: str, since):
        raise NotImplementedError


def test_given_pending_order_when_cancel_then_status_becomes_annule():
    # Given: a saved order with status EN_ATTENTE
    repo = FakeOrderRepository()
    order = Commande(
        id="o-123",
        festivalier_id="f-1",
        lignes=[
            LigneCommande(article=Article(name="Mojito"), quantite=1),
        ],
        status="EN_ATTENTE",
    )
    repo.save(order)

    # When: cancelling the order via the domain use case
    from app.domain.use_cases.cancel_order import CancelOrderUseCase

    use_case = CancelOrderUseCase(order_repository=repo)
    use_case.execute(order_id="o-123")

    # Then: the order status is updated to ANNULEE
    updated = repo.get_by_id("o-123")
    assert updated is not None
    assert updated.status == "ANNULEE"
