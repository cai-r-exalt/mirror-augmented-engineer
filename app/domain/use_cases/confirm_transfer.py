from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from app.domain.entities.token_transfer import TokenTransfer
from app.domain.exceptions import (
    FestivalierInconnuException,
    TransferNotFoundException,
    TransferNotPendingException,
    TransferUnauthorizedException,
)
from app.domain.ports.festivalier_repository import FestivalierRepository
from app.domain.ports.notification_port import NotificationPort
from app.domain.ports.transfer_repository import TransferRepository


@dataclass
class ConfirmTransferCommand:
    """Command for the recipient to accept or reject a pending token transfer."""

    transfer_id: str
    confirming_user_id: str
    accept: bool
    rejection_reason: Optional[str] = None


class ConfirmTransferUseCase:
    """Domain use case for the recipient to finalize a pending token transfer.

    On acceptance:
    - Tokens are added to the recipient's balance (they were already deducted
      from the sender's balance at creation time).
    - The transfer status is set to CONFIRMED.

    On rejection:
    - The reserved tokens are returned to the sender's balance.
    - The transfer status is set to REJECTED.

    In both cases both parties are notified.
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

    def execute(self, command: ConfirmTransferCommand) -> TokenTransfer:
        transfer = self.transfer_repository.get_by_id(command.transfer_id)
        if transfer is None:
            raise TransferNotFoundException(command.transfer_id)

        if transfer.status != "PENDING":
            raise TransferNotPendingException(command.transfer_id, transfer.status)

        if transfer.recipient_id != command.confirming_user_id:
            raise TransferUnauthorizedException(command.transfer_id, command.confirming_user_id)

        transfer.resolved_at = datetime.now(timezone.utc).isoformat()

        if command.accept:
            self._finalize_accepted(transfer)
        else:
            self._finalize_rejected(transfer)

        self.transfer_repository.save(transfer)

        self.notification_port.notify_transfer_finalized(
            sender_id=transfer.sender_id,
            recipient_id=transfer.recipient_id,
            transfer_id=transfer.id,
            confirmed=command.accept,
        )

        return transfer

    # ── Private helpers ──────────────────────────────────────────────────────

    def _finalize_accepted(self, transfer: TokenTransfer) -> None:
        """Credit recipient and mark transfer CONFIRMED."""
        recipient_balance = self.festivalier_repository.get_balance(transfer.recipient_id)
        if recipient_balance is None:
            raise FestivalierInconnuException(transfer.recipient_id)

        self.festivalier_repository.add_tokens(
            transfer.recipient_id,
            drink_tokens=transfer.drink_tokens,
            food_tokens=transfer.food_tokens,
        )
        transfer.status = "CONFIRMED"

    def _finalize_rejected(self, transfer: TokenTransfer) -> None:
        """Return reserved tokens to sender and mark transfer REJECTED."""
        self.festivalier_repository.add_tokens(
            transfer.sender_id,
            drink_tokens=transfer.drink_tokens,
            food_tokens=transfer.food_tokens,
        )
        transfer.status = "REJECTED"
