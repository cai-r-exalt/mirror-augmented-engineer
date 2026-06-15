"""Domain unit tests for token transfer use cases.

Covers:
- CreateTransferUseCase: limit enforcement, balance validation, reservation, notification
- GetTransferUseCase: retrieval by id
- ConfirmTransferUseCase: acceptance flow, rejection flow, authorization, state guard
"""

import pytest

from app.domain.exceptions import (
    FestivalierInconnuException,
    TransferInsufficientTokensException,
    TransferLimitExceededException,
    TransferNotFoundException,
    TransferNotPendingException,
    TransferUnauthorizedException,
)
from app.domain.use_cases.confirm_transfer import ConfirmTransferCommand, ConfirmTransferUseCase
from app.domain.use_cases.create_transfer import CreateTransferCommand, CreateTransferUseCase
from app.domain.use_cases.get_transfer import GetTransferCommand, GetTransferUseCase


class TestCreateTransferUseCase:
    def setup_method(self):
        from app.infrastructure.adapters.in_memory_festivalier_repository import InMemoryFestivalierRepository
        from app.infrastructure.adapters.in_memory_transfer_repository import InMemoryTransferRepository
        from app.infrastructure.adapters.mock_notification_adapter import MockNotificationAdapter

        self.transfer_repo = InMemoryTransferRepository()
        self.festivalier_repo = InMemoryFestivalierRepository(
            {
                "sender-1": {"drink_tokens": 5, "food_tokens": 4},
                "recipient-1": {"drink_tokens": 0, "food_tokens": 0},
            }
        )
        self.notif = MockNotificationAdapter()
        self.use_case = CreateTransferUseCase(
            transfer_repository=self.transfer_repo,
            festivalier_repository=self.festivalier_repo,
            notification_port=self.notif,
        )

    # ── Successful transfer ──────────────────────────────────────────────────

    def test_successful_transfer_returns_pending_entity(self):
        """
        Given sender has 5 drink tokens
        When they transfer 3 drink tokens
        Then a PENDING transfer entity is returned
        """
        cmd = CreateTransferCommand(
            sender_id="sender-1",
            recipient_id="recipient-1",
            drink_tokens=3,
            food_tokens=0,
        )
        result = self.use_case.execute(cmd)

        assert result.id is not None
        assert result.status == "PENDING"
        assert result.drink_tokens == 3
        assert result.food_tokens == 0

    def test_transfer_persisted_in_repository(self):
        cmd = CreateTransferCommand(
            sender_id="sender-1",
            recipient_id="recipient-1",
            drink_tokens=2,
            food_tokens=1,
        )
        result = self.use_case.execute(cmd)

        stored = self.transfer_repo.get_by_id(result.id)
        assert stored is not None
        assert stored.id == result.id

    def test_sender_tokens_are_reserved_on_creation(self):
        """Sender's balance decreases immediately when transfer is created (reservation)."""
        cmd = CreateTransferCommand(
            sender_id="sender-1",
            recipient_id="recipient-1",
            drink_tokens=3,
            food_tokens=2,
        )
        self.use_case.execute(cmd)

        balance = self.festivalier_repo.get_balance("sender-1")
        assert balance.drink_tokens == 2  # 5 - 3
        assert balance.food_tokens == 2   # 4 - 2

    def test_recipient_notified_on_transfer_creation(self):
        cmd = CreateTransferCommand(
            sender_id="sender-1",
            recipient_id="recipient-1",
            drink_tokens=1,
            food_tokens=0,
        )
        result = self.use_case.execute(cmd)

        assert len(self.notif.transfer_created_notifications) == 1
        notif = self.notif.transfer_created_notifications[0]
        assert notif["recipient_id"] == "recipient-1"
        assert notif["sender_id"] == "sender-1"
        assert notif["transfer_id"] == result.id
        assert notif["drink_tokens"] == 1
        assert notif["food_tokens"] == 0

    # ── Limit enforcement ────────────────────────────────────────────────────

    def test_raises_when_drink_tokens_exceed_limit(self):
        """
        Given A has only 1 snack token and attempts to transfer 4
        When transfer is requested
        Then the system rejects the transfer (limit exceeded)
        """
        cmd = CreateTransferCommand(
            sender_id="sender-1",
            recipient_id="recipient-1",
            drink_tokens=4,
            food_tokens=0,
        )
        with pytest.raises(TransferLimitExceededException) as exc_info:
            self.use_case.execute(cmd)
        assert exc_info.value.token_type == "drink"
        assert exc_info.value.requested == 4

    def test_raises_when_food_tokens_exceed_limit(self):
        cmd = CreateTransferCommand(
            sender_id="sender-1",
            recipient_id="recipient-1",
            drink_tokens=0,
            food_tokens=4,
        )
        with pytest.raises(TransferLimitExceededException) as exc_info:
            self.use_case.execute(cmd)
        assert exc_info.value.token_type == "food"

    def test_exactly_three_tokens_is_allowed(self):
        """Transfer of exactly 3 tokens (the maximum) is valid."""
        cmd = CreateTransferCommand(
            sender_id="sender-1",
            recipient_id="recipient-1",
            drink_tokens=3,
            food_tokens=3,
        )
        result = self.use_case.execute(cmd)
        assert result.status == "PENDING"

    # ── Insufficient tokens ──────────────────────────────────────────────────

    def test_raises_when_sender_has_insufficient_drink_tokens(self):
        """
        Given A has only 1 drink token and attempts to transfer 3
        When transfer is requested
        Then the system rejects the transfer
        """
        from app.infrastructure.adapters.in_memory_festivalier_repository import InMemoryFestivalierRepository

        festivalier_repo = InMemoryFestivalierRepository(
            {"sender-poor": {"drink_tokens": 1, "food_tokens": 5}}
        )
        use_case = CreateTransferUseCase(
            transfer_repository=self.transfer_repo,
            festivalier_repository=festivalier_repo,
            notification_port=self.notif,
        )
        cmd = CreateTransferCommand(
            sender_id="sender-poor",
            recipient_id="recipient-1",
            drink_tokens=3,
            food_tokens=0,
        )
        with pytest.raises(TransferInsufficientTokensException) as exc_info:
            use_case.execute(cmd)
        assert exc_info.value.token_type == "drink"

    def test_raises_when_sender_has_insufficient_food_tokens(self):
        cmd = CreateTransferCommand(
            sender_id="sender-1",
            recipient_id="recipient-1",
            drink_tokens=0,
            food_tokens=3,
        )
        # sender-1 has 4 food tokens – this should succeed
        result = self.use_case.execute(cmd)
        assert result.status == "PENDING"

        # Now sender-1 has 1 food token; trying to transfer 3 more should fail
        cmd2 = CreateTransferCommand(
            sender_id="sender-1",
            recipient_id="recipient-1",
            drink_tokens=0,
            food_tokens=3,
        )
        with pytest.raises(TransferInsufficientTokensException) as exc_info:
            self.use_case.execute(cmd2)
        assert exc_info.value.token_type == "food"

    def test_no_reservation_when_validation_fails(self):
        """Balance must remain unchanged when transfer is rejected."""
        balance_before = self.festivalier_repo.get_balance("sender-1")
        cmd = CreateTransferCommand(
            sender_id="sender-1",
            recipient_id="recipient-1",
            drink_tokens=4,  # exceeds limit
            food_tokens=0,
        )
        with pytest.raises(TransferLimitExceededException):
            self.use_case.execute(cmd)

        balance_after = self.festivalier_repo.get_balance("sender-1")
        assert balance_after.drink_tokens == balance_before.drink_tokens

    def test_raises_when_sender_unknown(self):
        cmd = CreateTransferCommand(
            sender_id="nobody",
            recipient_id="recipient-1",
            drink_tokens=1,
            food_tokens=0,
        )
        with pytest.raises(FestivalierInconnuException):
            self.use_case.execute(cmd)


class TestGetTransferUseCase:
    def setup_method(self):
        from app.infrastructure.adapters.in_memory_transfer_repository import InMemoryTransferRepository

        self.transfer_repo = InMemoryTransferRepository()
        self.use_case = GetTransferUseCase(transfer_repository=self.transfer_repo)

    def test_returns_transfer_when_found(self):
        from app.domain.entities.token_transfer import TokenTransfer

        transfer = TokenTransfer(
            id="t-1",
            sender_id="s-1",
            recipient_id="r-1",
            drink_tokens=2,
            food_tokens=0,
        )
        self.transfer_repo.save(transfer)

        result = self.use_case.execute(GetTransferCommand(transfer_id="t-1"))
        assert result.id == "t-1"
        assert result.status == "PENDING"

    def test_raises_when_transfer_not_found(self):
        with pytest.raises(TransferNotFoundException) as exc_info:
            self.use_case.execute(GetTransferCommand(transfer_id="nonexistent"))
        assert exc_info.value.transfer_id == "nonexistent"


class TestConfirmTransferUseCase:
    def setup_method(self):
        from app.infrastructure.adapters.in_memory_festivalier_repository import InMemoryFestivalierRepository
        from app.infrastructure.adapters.in_memory_transfer_repository import InMemoryTransferRepository
        from app.infrastructure.adapters.mock_notification_adapter import MockNotificationAdapter

        self.transfer_repo = InMemoryTransferRepository()
        self.festivalier_repo = InMemoryFestivalierRepository(
            {
                "sender-1": {"drink_tokens": 2, "food_tokens": 1},  # already reduced by reservation
                "recipient-1": {"drink_tokens": 0, "food_tokens": 0},
            }
        )
        self.notif = MockNotificationAdapter()
        self.use_case = ConfirmTransferUseCase(
            transfer_repository=self.transfer_repo,
            festivalier_repository=self.festivalier_repo,
            notification_port=self.notif,
        )
        # Seed a PENDING transfer (tokens already reserved from sender)
        from app.domain.entities.token_transfer import TokenTransfer

        self.pending_transfer = TokenTransfer(
            id="transfer-99",
            sender_id="sender-1",
            recipient_id="recipient-1",
            drink_tokens=3,
            food_tokens=1,
            status="PENDING",
        )
        self.transfer_repo.save(self.pending_transfer)

    # ── Acceptance flow ──────────────────────────────────────────────────────

    def test_accepted_transfer_status_becomes_confirmed(self):
        """
        Given user A has at least 3 drink tokens and user B accepts transfer
        When A transfers 3 drink tokens to B
        Then the transfer status is CONFIRMED
        """
        result = self.use_case.execute(
            ConfirmTransferCommand(
                transfer_id="transfer-99",
                confirming_user_id="recipient-1",
                accept=True,
            )
        )
        assert result.status == "CONFIRMED"

    def test_accepted_transfer_credits_recipient(self):
        self.use_case.execute(
            ConfirmTransferCommand(
                transfer_id="transfer-99",
                confirming_user_id="recipient-1",
                accept=True,
            )
        )
        balance = self.festivalier_repo.get_balance("recipient-1")
        assert balance.drink_tokens == 3  # 0 + 3
        assert balance.food_tokens == 1   # 0 + 1

    def test_accepted_transfer_does_not_restore_sender_tokens(self):
        """Sender's reserved tokens are not returned on acceptance."""
        sender_before = self.festivalier_repo.get_balance("sender-1")
        self.use_case.execute(
            ConfirmTransferCommand(
                transfer_id="transfer-99",
                confirming_user_id="recipient-1",
                accept=True,
            )
        )
        sender_after = self.festivalier_repo.get_balance("sender-1")
        assert sender_after.drink_tokens == sender_before.drink_tokens

    def test_both_parties_notified_on_acceptance(self):
        self.use_case.execute(
            ConfirmTransferCommand(
                transfer_id="transfer-99",
                confirming_user_id="recipient-1",
                accept=True,
            )
        )
        assert len(self.notif.transfer_finalized_notifications) == 1
        notif = self.notif.transfer_finalized_notifications[0]
        assert notif["sender_id"] == "sender-1"
        assert notif["recipient_id"] == "recipient-1"
        assert notif["transfer_id"] == "transfer-99"
        assert notif["confirmed"] is True

    # ── Rejection flow ───────────────────────────────────────────────────────

    def test_rejected_transfer_status_becomes_rejected(self):
        result = self.use_case.execute(
            ConfirmTransferCommand(
                transfer_id="transfer-99",
                confirming_user_id="recipient-1",
                accept=False,
            )
        )
        assert result.status == "REJECTED"

    def test_rejected_transfer_restores_sender_tokens(self):
        """Reservation is released when recipient rejects the transfer."""
        sender_before = self.festivalier_repo.get_balance("sender-1")
        self.use_case.execute(
            ConfirmTransferCommand(
                transfer_id="transfer-99",
                confirming_user_id="recipient-1",
                accept=False,
            )
        )
        sender_after = self.festivalier_repo.get_balance("sender-1")
        assert sender_after.drink_tokens == sender_before.drink_tokens + 3
        assert sender_after.food_tokens == sender_before.food_tokens + 1

    def test_rejected_transfer_does_not_credit_recipient(self):
        self.use_case.execute(
            ConfirmTransferCommand(
                transfer_id="transfer-99",
                confirming_user_id="recipient-1",
                accept=False,
            )
        )
        balance = self.festivalier_repo.get_balance("recipient-1")
        assert balance.drink_tokens == 0
        assert balance.food_tokens == 0

    def test_both_parties_notified_on_rejection(self):
        self.use_case.execute(
            ConfirmTransferCommand(
                transfer_id="transfer-99",
                confirming_user_id="recipient-1",
                accept=False,
            )
        )
        notif = self.notif.transfer_finalized_notifications[0]
        assert notif["confirmed"] is False

    # ── Guard: authorization ──────────────────────────────────────────────────

    def test_raises_when_non_recipient_tries_to_confirm(self):
        with pytest.raises(TransferUnauthorizedException) as exc_info:
            self.use_case.execute(
                ConfirmTransferCommand(
                    transfer_id="transfer-99",
                    confirming_user_id="intruder-99",
                    accept=True,
                )
            )
        assert exc_info.value.festivalier_id == "intruder-99"

    # ── Guard: state ─────────────────────────────────────────────────────────

    def test_raises_when_transfer_already_confirmed(self):
        """Attempting to confirm an already-confirmed transfer raises TransferNotPendingException."""
        self.use_case.execute(
            ConfirmTransferCommand(
                transfer_id="transfer-99",
                confirming_user_id="recipient-1",
                accept=True,
            )
        )
        with pytest.raises(TransferNotPendingException) as exc_info:
            self.use_case.execute(
                ConfirmTransferCommand(
                    transfer_id="transfer-99",
                    confirming_user_id="recipient-1",
                    accept=True,
                )
            )
        assert exc_info.value.current_status == "CONFIRMED"

    def test_raises_when_transfer_not_found(self):
        with pytest.raises(TransferNotFoundException):
            self.use_case.execute(
                ConfirmTransferCommand(
                    transfer_id="no-such-id",
                    confirming_user_id="recipient-1",
                    accept=True,
                )
            )
