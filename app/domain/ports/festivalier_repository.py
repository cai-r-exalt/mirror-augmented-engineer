from abc import ABC, abstractmethod
from typing import Optional

from app.domain.value_objects.token_contribution import TokenContribution


class FestivalierRepository(ABC):
    """Port for retrieving and updating festival-goer token balances."""

    @abstractmethod
    def get_balance(self, festivalier_id: str) -> Optional[TokenContribution]:
        """Return the token balance for the given festivalier, or None if not found."""
        raise NotImplementedError

    @abstractmethod
    def deduct_tokens(self, festivalier_id: str, drink_tokens: int, food_tokens: int) -> None:
        """Deduct the given amounts from the festivalier's token balance."""
        raise NotImplementedError

    @abstractmethod
    def add_tokens(self, festivalier_id: str, drink_tokens: int, food_tokens: int) -> None:
        """Add the given amounts to the festivalier's token balance."""
        raise NotImplementedError
