from typing import Dict, Optional

from app.domain.entities.token_transfer import TokenTransfer
from app.domain.ports.transfer_repository import TransferRepository


class InMemoryTransferRepository(TransferRepository):
    """In-memory implementation of the TransferRepository port.

    Stores token transfer requests by id.
    """

    def __init__(self) -> None:
        self._transfers: Dict[str, TokenTransfer] = {}

    def save(self, transfer: TokenTransfer) -> None:
        self._transfers[transfer.id] = transfer

    def get_by_id(self, transfer_id: str) -> Optional[TokenTransfer]:
        return self._transfers.get(transfer_id)
