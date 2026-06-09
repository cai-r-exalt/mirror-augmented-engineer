class TestCreateOrderInfrastructureEndToEnd:
    def setup_method(self):
        # Given: un festivalier
        self.festivalier_id = "festivalier-42"

        # Small test-local mock use-case to back the controller
        class MockUseCase:
            def __init__(self):
                self._store = {}
                self._next = 1

            def execute(self, payload):
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

            def get_commande(self, cid):
                return self._store.get(cid)

        # Wire controller to the mock use-case
        from infrastructure.controllers.commande_controller import CommandesController
        from infrastructure.dto.commande import CreerCommandeRequest

        self.client = CommandesController(use_case=MockUseCase())
        self.CreerCommandeRequest = CreerCommandeRequest

    def test_given_inventory_when_post_commandes_then_returns_201_and_order_pending(self):
        # When: le festivalier envoie une requête POST /commandes
        req = self.CreerCommandeRequest(self.festivalier_id, [{"id": "mojito", "quantite": 2}])

        response = self.client.creer_commande(req)

        # Then: la réponse a le statut HTTP 201
        assert response.status_code == 201

        # And: la réponse contient un champ "commandeId" non vide
        assert "commandeId" in response.json()
        assert response.json()["commandeId"]

        # And: la commande est créée avec le statut "EN_ATTENTE"
        # (vérifié en récupérant la ressource créée)
        commande_id = response.json()["commandeId"]
        get_resp = self.client.get_commande(commande_id)
        assert get_resp.status_code == 200
        assert get_resp.json().get("status") == "EN_ATTENTE"

    def test_unauthenticated_post_commandes_returns_401(self):
        # Given: aucun festivalier authentifié
        req = self.CreerCommandeRequest(None, [{"id": "mojito", "quantite": 1}])

        # When: une requête POST /commandes est envoyée sans authentification
        response = self.client.creer_commande(req)

        # Then: la réponse a le statut HTTP 401 (test should fail with current adapter)
        assert response.status_code == 401

    def test_post_commandes_without_articles_returns_400(self):
        # Given: un festivalier identifié
        req = self.CreerCommandeRequest(self.festivalier_id, None)

        # When: le festivalier envoie une requête POST /commandes sans articles
        response = self.client.creer_commande(req)

        # Then: la réponse a le statut HTTP 400 (test should fail with current adapter)
        assert response.status_code == 400
