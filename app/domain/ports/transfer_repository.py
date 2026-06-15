from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities.token_transfer import TokenTransfer


class TransferRepository(ABC):
    """Port for persisting and retrieving token transfer requests."""

    @abstractmethod
    def save(self, transfer: TokenTransfer) -> None:
        """Persist (insert or update) the given transfer."""
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, transfer_id: str) -> Optional[TokenTransfer]:
        """Return the transfer with the given id, or None if not found."""
        raise NotImplementedError
