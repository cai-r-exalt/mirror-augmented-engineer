from dataclasses import dataclass
from typing import Any, Dict, List

from app.domain.entities.commande import Commande, ContributorContribution
from app.domain.exceptions import (
    ArticleInconnuException,
    ContributorBalanceExceededException,
    FestivalierInconnuException,
    InsufficientPooledFundsException,
    StockInsuffisantException,
)
from app.domain.ports.festivalier_repository import FestivalierRepository
from app.domain.ports.item_catalog_repository import ItemCatalogRepository
from app.domain.ports.order_repository import OrderRepository
from app.domain.ports.stock_repository import StockRepository
from app.domain.value_objects.token_contribution import TokenContribution


@dataclass
class ContributorInput:
    """A single contributor's offered token amounts."""

    festivalier_id: str
    drink_tokens: int
    food_tokens: int


@dataclass
class PlaceGroupOrderCommand:
    """Command object for placing a group order."""

    items: List[Dict[str, Any]]
    contributors: List[ContributorInput]


class PlaceGroupOrderUseCase:
    """Domain use case for placing a group order pooling multiple contributors' tokens.

    Validates contributor balances, checks that the pooled contribution covers the
    aggregated item cost, verifies stock availability, and creates the order.
    Tokens are only deducted on acknowledgement (existing rule); this use case
    only validates and persists the pending order.
    """

    def __init__(
        self,
        order_repository: OrderRepository,
        stock_repository: StockRepository,
        festivalier_repository: FestivalierRepository,
        item_catalog_repository: ItemCatalogRepository,
    ) -> None:
        self.order_repository = order_repository
        self.stock_repository = stock_repository
        self.festivalier_repository = festivalier_repository
        self.item_catalog_repository = item_catalog_repository

    def execute(self, command: PlaceGroupOrderCommand) -> Commande:
        self._validate_stock(command.items)
        self._validate_contributor_balances(command.contributors)
        total_cost = self._compute_total_cost(command.items)
        self._validate_pooled_funds(command.contributors, total_cost)

        contributors_data = [
            ContributorContribution(
                festivalier_id=c.festivalier_id,
                contribution=TokenContribution(
                    drink_tokens=c.drink_tokens,
                    food_tokens=c.food_tokens,
                ),
            )
            for c in command.contributors
        ]

        commande = self.order_repository.create_group_order(contributors_data, command.items)

        for item in command.items:
            self.stock_repository.decrement(item["name"], item["quantity"])

        return commande

    # ── Private helpers ─────────────────────────────────────────────────────

    def _validate_stock(self, items: List[Dict[str, Any]]) -> None:
        for item in items:
            name = item["name"]
            qty = item["quantity"]

            if not self.stock_repository.item_exists(name):
                raise ArticleInconnuException(name)

            if not self.stock_repository.is_in_stock(name, qty):
                raise StockInsuffisantException(name)

    def _validate_contributor_balances(self, contributors: List[ContributorInput]) -> None:
        for contributor in contributors:
            balance = self.festivalier_repository.get_balance(contributor.festivalier_id)
            if balance is None:
                raise FestivalierInconnuException(contributor.festivalier_id)
            if contributor.drink_tokens > balance.drink_tokens:
                raise ContributorBalanceExceededException(contributor.festivalier_id, "drink")
            if contributor.food_tokens > balance.food_tokens:
                raise ContributorBalanceExceededException(contributor.festivalier_id, "food")

    def _compute_total_cost(self, items: List[Dict[str, Any]]) -> TokenContribution:
        total_drink = 0
        total_food = 0
        for item in items:
            name = item["name"]
            qty = item["quantity"]
            cost = self.item_catalog_repository.get_item_cost(name)
            if cost is None:
                raise ArticleInconnuException(name)
            total_drink += cost.drink_tokens_per_unit * qty
            total_food += cost.food_tokens_per_unit * qty
        return TokenContribution(drink_tokens=total_drink, food_tokens=total_food)

    def _validate_pooled_funds(
        self,
        contributors: List[ContributorInput],
        total_cost: TokenContribution,
    ) -> None:
        pooled_drink = sum(c.drink_tokens for c in contributors)
        pooled_food = sum(c.food_tokens for c in contributors)

        if pooled_drink < total_cost.drink_tokens:
            raise InsufficientPooledFundsException("drink", total_cost.drink_tokens, pooled_drink)
        if pooled_food < total_cost.food_tokens:
            raise InsufficientPooledFundsException("food", total_cost.food_tokens, pooled_food)
