from dataclasses import dataclass


@dataclass(frozen=True)
class TokenContribution:
    """Represents a pool of drink and food token amounts."""

    drink_tokens: int = 0
    food_tokens: int = 0

    def __add__(self, other: "TokenContribution") -> "TokenContribution":
        return TokenContribution(
            drink_tokens=self.drink_tokens + other.drink_tokens,
            food_tokens=self.food_tokens + other.food_tokens,
        )

    def covers(self, cost: "TokenContribution") -> bool:
        """Return True if this contribution can cover the given cost."""
        return self.drink_tokens >= cost.drink_tokens and self.food_tokens >= cost.food_tokens
