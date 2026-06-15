import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from app.domain.entities.token_transfer import TokenTransfer
from app.domain.exceptions import (
    FestivalierInconnuException,
    TransferInsufficientTokensException,
    TransferLimitExceededException,
)
from app.domain.ports.festivalier_repository import FestivalierRepository
from app.domain.ports.notification_port import NotificationPort
from app.domain.ports.transfer_repository import TransferRepository

MAX_TOKENS_PER_TRANSFER = 3


@dataclass
class CreateTransferCommand:
    """Command to create a token transfer request."""

    sender_id: str
    recipient_id: str
    drink_tokens: int
    food_tokens: int


class CreateTransferUseCase:
    """Domain use case to create a token transfer request between two festival goers.

    Business rules:
    - At most 3 tokens of each type may be transferred in a single request.
    - The sender must have sufficient available tokens; they are reserved
      (deducted) immediately to prevent over-spending while the request is pending.
    - The recipient is notified of the pending transfer.
    """

    def __init__(
        self,
        transfer_repository: TransferRepository,
        festivalier_repository: FestivalierRepository,
        notification_port: NotificationPort,
    ) -> None:
        self.transfer_repository = transfer_repository
        self.festivalier_repository = festivalier_repository
        self.notification_port = notification_port

    def execute(self, command: CreateTransferCommand) -> TokenTransfer:
        self._validate_limits(command)
        self._validate_sender_balance(command)

        transfer = TokenTransfer(
            id=str(uuid.uuid4()),
            sender_id=command.sender_id,
            recipient_id=command.recipient_id,
            drink_tokens=command.drink_tokens,
            food_tokens=command.food_tokens,
            status="PENDING",
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        # Reserve tokens from sender's balance upfront.
        self.festivalier_repository.deduct_tokens(
            command.sender_id,
            drink_tokens=command.drink_tokens,
            food_tokens=command.food_tokens,
        )

        self.transfer_repository.save(transfer)

        self.notification_port.notify_transfer_created(
            recipient_id=command.recipient_id,
            transfer_id=transfer.id,
            sender_id=command.sender_id,
            drink_tokens=command.drink_tokens,
            food_tokens=command.food_tokens,
        )

        return transfer

    # ── Private helpers ──────────────────────────────────────────────────────

    def _validate_limits(self, command: CreateTransferCommand) -> None:
        if command.drink_tokens > MAX_TOKENS_PER_TRANSFER:
            raise TransferLimitExceededException("drink", command.drink_tokens)
        if command.food_tokens > MAX_TOKENS_PER_TRANSFER:
            raise TransferLimitExceededException("food", command.food_tokens)

    def _validate_sender_balance(self, command: CreateTransferCommand) -> None:
        balance = self.festivalier_repository.get_balance(command.sender_id)
        if balance is None:
            raise FestivalierInconnuException(command.sender_id)

        if command.drink_tokens > balance.drink_tokens:
            raise TransferInsufficientTokensException(command.sender_id, "drink")
        if command.food_tokens > balance.food_tokens:
            raise TransferInsufficientTokensException(command.sender_id, "food")
