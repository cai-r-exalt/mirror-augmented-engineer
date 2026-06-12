from typing import Any, Dict, List, Optional


class ContributionRequest:
    def __init__(self, drink_tokens: int = 0, food_tokens: int = 0) -> None:
        self.drink_tokens = drink_tokens
        self.food_tokens = food_tokens


class ContributorRequest:
    def __init__(self, festivalier_id: str, contribution: ContributionRequest) -> None:
        self.festivalier_id = festivalier_id
        self.contribution = contribution


class GroupOrderRequest:
    def __init__(
        self,
        items: Optional[List[Dict[str, Any]]],
        contributors: Optional[List[ContributorRequest]],
    ) -> None:
        self.items = items
        self.contributors = contributors


class GroupOrderResponse:
    def __init__(self, status_code: int, body: Dict[str, Any]) -> None:
        self.status_code = status_code
        self._body = body

    def json(self) -> Dict[str, Any]:
        return self._body
