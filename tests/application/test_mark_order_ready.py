from app.application.controllers.mark_order_ready_controller import MarkOrderReadyController
from app.application.dto.mark_order_ready import MarkOrderReadyRequest
from app.domain.entities.commande import Article, Commande, LigneCommande
from app.domain.use_cases.mark_order_ready import MarkOrderReadyUseCase
from app.infrastructure.adapters.in_memory_order_repository import InMemoryOrderRepository
from app.infrastructure.adapters.in_memory_stock_repository import InMemoryStockRepository
from app.infrastructure.adapters.mock_notification_adapter import MockNotificationAdapter


def _build_infrastructure(prepared_stock: dict | None = None):
    order_repo = InMemoryOrderRepository()
    stock_repo = InMemoryStockRepository(initial_prepared_stock=prepared_stock or {"Bière": 3})
    notifications = MockNotificationAdapter()
    use_case = MarkOrderReadyUseCase(order_repo, stock_repo, notifications)
    controller = MarkOrderReadyController(mark_order_ready_use_case=use_case)
    return controller, order_repo, notifications


def _acknowledged_order(order_id: str, festivalier_id: str, items: list) -> Commande:
    lignes = [LigneCommande(article=Article(name=item["name"]), quantite=item["quantity"]) for item in items]
    return Commande(id=order_id, festivalier_id=festivalier_id, lignes=lignes, status="ACKNOWLEDGED")


class TestMarkOrderReadyEndpoint:
    def test_returns_200_and_sets_ready_status(self):
        controller, order_repo, notifications = _build_infrastructure(prepared_stock={"Bière": 2})
        order_repo.save(_acknowledged_order("order-1", "f-1", [{"name": "Bière", "quantity": 2}]))

        response = controller.mark_order_ready(MarkOrderReadyRequest(order_id="order-1"))

        assert response.status_code == 200
        body = response.json()
        assert body["orderId"] == "order-1"
        assert body["status"] == "READY"
        assert body["readyAt"] is not None
        assert len(notifications.ready_notifications) == 1
        assert notifications.ready_notifications[0]["order_id"] == "order-1"

    def test_returns_409_when_prepared_counts_insufficient(self):
        controller, order_repo, notifications = _build_infrastructure(prepared_stock={"Bière": 1})
        order_repo.save(_acknowledged_order("order-1", "f-1", [{"name": "Bière", "quantity": 2}]))

        response = controller.mark_order_ready(MarkOrderReadyRequest(order_id="order-1"))

        assert response.status_code == 409
        assert "prepared" in response.json()["error"].lower()
        assert notifications.ready_notifications == []
