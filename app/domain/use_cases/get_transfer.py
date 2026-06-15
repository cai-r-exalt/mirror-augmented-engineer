from dataclasses import dataclass

from app.domain.entities.token_transfer import TokenTransfer
from app.domain.exceptions import TransferNotFoundException
from app.domain.ports.transfer_repository import TransferRepository


@dataclass
class GetTransferCommand:
    """Command to retrieve the current status of a token transfer."""

    transfer_id: str


class GetTransferUseCase:
    """Domain use case to retrieve a token transfer by its id."""

    def __init__(self, transfer_repository: TransferRepository) -> None:
        self.transfer_repository = transfer_repository

    def execute(self, command: GetTransferCommand) -> TokenTransfer:
        transfer = self.transfer_repository.get_by_id(command.transfer_id)
        if transfer is None:
            raise TransferNotFoundException(command.transfer_id)
        return transfer
