from typing import Dict, Optional

from app.domain.ports.festivalier_repository import FestivalierRepository
from app.domain.value_objects.token_contribution import TokenContribution


class InMemoryFestivalierRepository(FestivalierRepository):
    """In-memory implementation of the FestivalierRepository port.

    Stores festivalier token balances by id.
    """

    def __init__(self, balances: Dict[str, Dict[str, int]] | None = None) -> None:
        self._balances: Dict[str, TokenContribution] = {}
        if balances:
            for fid, amounts in balances.items():
                self._balances[fid] = TokenContribution(
                    drink_tokens=amounts.get("drink_tokens", 0),
                    food_tokens=amounts.get("food_tokens", 0),
                )

    def get_balance(self, festivalier_id: str) -> Optional[TokenContribution]:
        return self._balances.get(festivalier_id)

    def set_balance(self, festivalier_id: str, contribution: TokenContribution) -> None:
        self._balances[festivalier_id] = contribution

    def deduct_tokens(self, festivalier_id: str, drink_tokens: int, food_tokens: int) -> None:
        """Deduct the given amounts from the festivalier's token balance."""
        balance = self._balances.get(festivalier_id)
        if balance is None:
            from app.domain.exceptions import FestivalierInconnuException
            raise FestivalierInconnuException(festivalier_id)
        self._balances[festivalier_id] = TokenContribution(
            drink_tokens=balance.drink_tokens - drink_tokens,
            food_tokens=balance.food_tokens - food_tokens,
        )
