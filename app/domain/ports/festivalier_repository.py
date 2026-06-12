from abc import ABC, abstractmethod
from typing import Optional

from app.domain.value_objects.token_contribution import TokenContribution


class FestivalierRepository(ABC):
    """Port for retrieving festival-goer token balances."""

    @abstractmethod
    def get_balance(self, festivalier_id: str) -> Optional[TokenContribution]:
        """Return the token balance for the given festivalier, or None if not found."""
        raise NotImplementedError
