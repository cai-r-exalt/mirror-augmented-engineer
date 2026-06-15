# Infrastructure tests — adapters, persistence, and integrations.
# These tests describe the expected persistence behaviour for orders.

from app.domain.entities.commande import Article, Commande, LigneCommande
from app.infrastructure.adapters.sqlalchemy_order_repository import SQLAlchemyOrderRepository


def test_save_and_retrieve_commande_via_repository():
    # Given: a commande with status EN_ATTENTE and two lines
    lignes = [
        LigneCommande(article=Article(name="Mojito"), quantite=2),
        LigneCommande(article=Article(name="Eau plate"), quantite=1),
    ]
    commande = Commande(id="order-1", festivalier_id="festivalier-1", lignes=lignes, status="EN_ATTENTE")

    # When: we persist the commande and then retrieve it by id
    repo = SQLAlchemyOrderRepository()
    repo.save(commande)
    fetched = repo.get_by_id("order-1")

    # Then: the commande can be found, has the expected status and two lines
    assert fetched is not None
    assert fetched.status == "EN_ATTENTE"
    assert len(fetched.lignes) == 2


def test_update_commande_status_via_repository():
    # Given: a saved commande with status EN_ATTENTE
    repo = SQLAlchemyOrderRepository()
    lignes = [LigneCommande(article=Article(name="Mojito"), quantite=1)]
    commande = Commande(id="order-2", festivalier_id="festivalier-2", lignes=lignes, status="EN_ATTENTE")
    repo.save(commande)

    # When: we update its status to PRÊTE
    repo.update_status("order-2", "PRÊTE")

    # Then: retrieving the commande shows the new status
    fetched = repo.get_by_id("order-2")
    assert fetched is not None
    assert fetched.status == "PRÊTE"


def test_find_commandes_by_festivalier_and_status():
    # Given: three commandes for festivalier-42 with varying statuses
    repo = SQLAlchemyOrderRepository()

    repo.save(Commande(id="o-1", festivalier_id="festivalier-42", lignes=[], status="EN_ATTENTE"))
    repo.save(Commande(id="o-2", festivalier_id="festivalier-42", lignes=[], status="EN_ATTENTE"))
    repo.save(Commande(id="o-3", festivalier_id="festivalier-42", lignes=[], status="PRÊTE"))

    # When: we query commandes for festivalier-42 with status EN_ATTENTE
    results = repo.find_by_festivalier_and_status("festivalier-42", "EN_ATTENTE")

    # Then: we obtain exactly 2 commandes
    assert isinstance(results, list)
    assert len(results) == 2

