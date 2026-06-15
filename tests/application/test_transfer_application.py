"""Application-layer tests for the TransferController.

Covers HTTP status codes and response shapes for:
- POST /transfers (create_transfer)
- GET /transfers/{id} (get_transfer)
- POST /transfers/{id}/confirm (confirm_transfer)
"""

from app.application.controllers.transfer_controller import TransferController
from app.application.dto.transfer import ConfirmTransferRequest, CreateTransferRequest
from app.domain.use_cases.confirm_transfer import ConfirmTransferUseCase
from app.domain.use_cases.create_transfer import CreateTransferUseCase
from app.domain.use_cases.get_transfer import GetTransferUseCase


def _make_controller():
    """Wire the controller with in-memory adapters."""
    from app.infrastructure.adapters.in_memory_festivalier_repository import InMemoryFestivalierRepository
    from app.infrastructure.adapters.in_memory_transfer_repository import InMemoryTransferRepository
    from app.infrastructure.adapters.mock_notification_adapter import MockNotificationAdapter

    transfer_repo = InMemoryTransferRepository()
    festivalier_repo = InMemoryFestivalierRepository(
        {
            "user-a": {"drink_tokens": 5, "food_tokens": 4},
            "user-b": {"drink_tokens": 1, "food_tokens": 1},
        }
    )
    notif = MockNotificationAdapter()

    create_uc = CreateTransferUseCase(
        transfer_repository=transfer_repo,
        festivalier_repository=festivalier_repo,
        notification_port=notif,
    )
    get_uc = GetTransferUseCase(transfer_repository=transfer_repo)
    confirm_uc = ConfirmTransferUseCase(
        transfer_repository=transfer_repo,
        festivalier_repository=festivalier_repo,
        notification_port=notif,
    )

    controller = TransferController(
        create_transfer_use_case=create_uc,
        get_transfer_use_case=get_uc,
        confirm_transfer_use_case=confirm_uc,
    )
    return controller, transfer_repo, festivalier_repo, notif


class TestCreateTransferController:
    def setup_method(self):
        self.controller, self.transfer_repo, self.festivalier_repo, self.notif = _make_controller()

    def test_returns_201_on_valid_request(self):
        req = CreateTransferRequest(from_id="user-a", to_id="user-b", drink_tokens=3, food_tokens=0)
        response = self.controller.create_transfer(req)
        assert response.status_code == 201
        body = response.json()
        assert body["status"] == "PENDING"
        assert body["transferId"] is not None

    def test_response_body_contains_transfer_details(self):
        req = CreateTransferRequest(from_id="user-a", to_id="user-b", drink_tokens=2, food_tokens=1)
        body = self.controller.create_transfer(req).json()
        assert body["senderId"] == "user-a"
        assert body["recipientId"] == "user-b"
        assert body["drinkTokens"] == 2
        assert body["foodTokens"] == 1

    def test_returns_409_when_limit_exceeded(self):
        req = CreateTransferRequest(from_id="user-a", to_id="user-b", drink_tokens=4, food_tokens=0)
        response = self.controller.create_transfer(req)
        assert response.status_code == 409

    def test_returns_409_when_insufficient_tokens(self):
        """
        Given A has only 1 snack token and attempts to transfer 3
        When transfer is requested
        Then the system rejects the transfer with 409
        """
        from app.infrastructure.adapters.in_memory_festivalier_repository import InMemoryFestivalierRepository
        from app.infrastructure.adapters.in_memory_transfer_repository import InMemoryTransferRepository
        from app.infrastructure.adapters.mock_notification_adapter import MockNotificationAdapter

        poor_repo = InMemoryFestivalierRepository(
            {"poor-user": {"drink_tokens": 0, "food_tokens": 1}, "user-b": {"drink_tokens": 0, "food_tokens": 0}}
        )
        create_uc = CreateTransferUseCase(
            transfer_repository=InMemoryTransferRepository(),
            festivalier_repository=poor_repo,
            notification_port=MockNotificationAdapter(),
        )
        controller = TransferController(
            create_transfer_use_case=create_uc,
            get_transfer_use_case=GetTransferUseCase(InMemoryTransferRepository()),
            confirm_transfer_use_case=ConfirmTransferUseCase(
                InMemoryTransferRepository(), poor_repo, MockNotificationAdapter()
            ),
        )
        req = CreateTransferRequest(from_id="poor-user", to_id="user-b", drink_tokens=3, food_tokens=0)
        response = controller.create_transfer(req)
        assert response.status_code == 409

    def test_returns_400_when_missing_from_id(self):
        req = CreateTransferRequest(from_id="", to_id="user-b", drink_tokens=1, food_tokens=0)
        response = self.controller.create_transfer(req)
        assert response.status_code == 400

    def test_returns_400_when_all_tokens_zero(self):
        req = CreateTransferRequest(from_id="user-a", to_id="user-b", drink_tokens=0, food_tokens=0)
        response = self.controller.create_transfer(req)
        assert response.status_code == 400

    def test_returns_404_when_sender_unknown(self):
        req = CreateTransferRequest(from_id="ghost", to_id="user-b", drink_tokens=1, food_tokens=0)
        response = self.controller.create_transfer(req)
        assert response.status_code == 404


class TestGetTransferController:
    def setup_method(self):
        self.controller, self.transfer_repo, self.festivalier_repo, self.notif = _make_controller()

    def _create_transfer(self):
        req = CreateTransferRequest(from_id="user-a", to_id="user-b", drink_tokens=1, food_tokens=0)
        return self.controller.create_transfer(req).json()["transferId"]

    def test_returns_200_with_transfer_details(self):
        transfer_id = self._create_transfer()
        response = self.controller.get_transfer(transfer_id)
        assert response.status_code == 200
        body = response.json()
        assert body["transferId"] == transfer_id
        assert body["status"] == "PENDING"

    def test_returns_404_when_transfer_not_found(self):
        response = self.controller.get_transfer("no-such-id")
        assert response.status_code == 404


class TestConfirmTransferController:
    def setup_method(self):
        self.controller, self.transfer_repo, self.festivalier_repo, self.notif = _make_controller()

    def _create_transfer(self, drink_tokens: int = 3, food_tokens: int = 0) -> str:
        req = CreateTransferRequest(
            from_id="user-a", to_id="user-b", drink_tokens=drink_tokens, food_tokens=food_tokens
        )
        return self.controller.create_transfer(req).json()["transferId"]

    def test_returns_200_on_acceptance(self):
        transfer_id = self._create_transfer()
        req = ConfirmTransferRequest(
            transfer_id=transfer_id, confirming_user_id="user-b", accept=True
        )
        response = self.controller.confirm_transfer(req)
        assert response.status_code == 200
        assert response.json()["status"] == "CONFIRMED"

    def test_balances_updated_on_acceptance(self):
        """
        Given user A has at least 3 drink tokens and user B accepts transfer
        When A transfers 3 drink tokens to B
        Then A's balance decreases and B's increases accordingly
        """
        transfer_id = self._create_transfer(drink_tokens=3)
        req = ConfirmTransferRequest(
            transfer_id=transfer_id, confirming_user_id="user-b", accept=True
        )
        self.controller.confirm_transfer(req)

        sender_balance = self.festivalier_repo.get_balance("user-a")
        recipient_balance = self.festivalier_repo.get_balance("user-b")
        assert sender_balance.drink_tokens == 2   # 5 - 3
        assert recipient_balance.drink_tokens == 4  # 1 + 3

    def test_returns_200_on_rejection(self):
        transfer_id = self._create_transfer()
        req = ConfirmTransferRequest(
            transfer_id=transfer_id, confirming_user_id="user-b", accept=False
        )
        response = self.controller.confirm_transfer(req)
        assert response.status_code == 200
        assert response.json()["status"] == "REJECTED"

    def test_sender_tokens_restored_on_rejection(self):
        transfer_id = self._create_transfer(drink_tokens=3)
        sender_before = self.festivalier_repo.get_balance("user-a").drink_tokens
        req = ConfirmTransferRequest(
            transfer_id=transfer_id, confirming_user_id="user-b", accept=False
        )
        self.controller.confirm_transfer(req)

        sender_after = self.festivalier_repo.get_balance("user-a").drink_tokens
        assert sender_after == sender_before + 3

    def test_returns_403_when_non_recipient_confirms(self):
        transfer_id = self._create_transfer()
        req = ConfirmTransferRequest(
            transfer_id=transfer_id, confirming_user_id="intruder", accept=True
        )
        response = self.controller.confirm_transfer(req)
        assert response.status_code == 403

    def test_returns_422_when_transfer_not_pending(self):
        transfer_id = self._create_transfer()
        # Confirm once (accept)
        self.controller.confirm_transfer(
            ConfirmTransferRequest(transfer_id=transfer_id, confirming_user_id="user-b", accept=True)
        )
        # Try to confirm again
        response = self.controller.confirm_transfer(
            ConfirmTransferRequest(transfer_id=transfer_id, confirming_user_id="user-b", accept=True)
        )
        assert response.status_code == 422

    def test_returns_404_when_transfer_not_found(self):
        req = ConfirmTransferRequest(
            transfer_id="ghost-id", confirming_user_id="user-b", accept=True
        )
        response = self.controller.confirm_transfer(req)
        assert response.status_code == 404

    def test_returns_400_when_accept_is_none(self):
        transfer_id = self._create_transfer()
        req = ConfirmTransferRequest(
            transfer_id=transfer_id, confirming_user_id="user-b", accept=None
        )
        response = self.controller.confirm_transfer(req)
        assert response.status_code == 400
