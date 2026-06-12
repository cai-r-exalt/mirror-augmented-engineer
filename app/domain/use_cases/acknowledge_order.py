"""AcknowledgeOrderUseCase — bartender acknowledges an order and calculates ETA.

ETA calculation rules (from FEATURES.md):
- Non-alcoholic drinks : 1 minute × number of distinct drink types
- Normal alcoholic drinks : 2 minutes × total quantity ordered
- Premium alcoholic drinks : 3 minutes × total quantity ordered
- Snacks : 2 minutes × number of distinct snack types
- Meals : 10 minutes × number of distinct meal types
          + longest per-unit preparation time among all drinks in the order
            (1 min if only non-alc, 2 if normal alc present, 3 if premium alc present)
- Mixed orders : sum the above components

Token deduction:
- Solo order : deduct computed item costs from the single festivalier's balance
- Group order : deduct each contributor's pledged amounts from their balance
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List

from app.domain.entities.commande import Commande
from app.domain.exceptions import (
    ArticleInconnuException,
    FestivalierInconnuException,
    OrderAlreadyAcknowledgedException,
    OrderNotAcknowledgeableException,
    OrderNotFoundException,
)
from app.domain.ports.festivalier_repository import FestivalierRepository
from app.domain.ports.item_catalog_repository import (
    ITEM_TYPE_MEAL,
    ITEM_TYPE_NON_ALCOHOLIC_DRINK,
    ITEM_TYPE_NORMAL_ALCOHOLIC_DRINK,
    ITEM_TYPE_PREMIUM_ALCOHOLIC_DRINK,
    ITEM_TYPE_SNACK,
    ItemCatalogRepository,
)
from app.domain.ports.notification_port import NotificationPort
from app.domain.ports.order_repository import OrderRepository
from app.domain.ports.stock_repository import StockRepository


@dataclass
class AcknowledgeOrderCommand:
    """Command for a bartender to acknowledge a pending order."""

    order_id: str


class AcknowledgeOrderUseCase:
    """Domain use case for a bartender to acknowledge an order.

    Actions performed:
    1. Validate the order exists and is in EN_ATTENTE status.
    2. Validate stock is still sufficient for all items.
    3. Calculate the estimated time (ETA) in minutes.
    4. Deduct tokens from the festivalier(s) balance.
    5. Persist the ETA, acknowledged_at timestamp, and ACKNOWLEDGED status.
    6. Notify the festivalier with the ETA.
    """

    def __init__(
        self,
        order_repository: OrderRepository,
        stock_repository: StockRepository,
        item_catalog_repository: ItemCatalogRepository,
        festivalier_repository: FestivalierRepository,
        notification_port: NotificationPort,
    ) -> None:
        self.order_repository = order_repository
        self.stock_repository = stock_repository
        self.item_catalog_repository = item_catalog_repository
        self.festivalier_repository = festivalier_repository
        self.notification_port = notification_port

    def execute(self, command: AcknowledgeOrderCommand) -> Commande:
        order = self.order_repository.get_by_id(command.order_id)
        if order is None:
            raise OrderNotFoundException(command.order_id)

        if order.status == "ACKNOWLEDGED":
            raise OrderAlreadyAcknowledgedException(command.order_id)

        if order.status != "EN_ATTENTE":
            raise OrderNotAcknowledgeableException(
                command.order_id,
                f"order is in status {order.status}",
            )

        items = self._extract_items(order)

        self._validate_stock(items)
        eta_minutes = self._calculate_eta(items)
        self._deduct_tokens(order, items)

        order.status = "ACKNOWLEDGED"
        order.eta_minutes = eta_minutes
        order.acknowledged_at = datetime.now(timezone.utc).isoformat()
        self.order_repository.save(order)

        festivalier_id = self._resolve_festivalier_id(order)
        self.notification_port.notify_festivalier_order_acknowledged(
            festivalier_id=festivalier_id,
            order_id=command.order_id,
            eta_minutes=eta_minutes,
        )

        return order

    # ── Private helpers ──────────────────────────────────────────────────────

    def _extract_items(self, order: Commande) -> List[Dict[str, Any]]:
        """Convert order lines into a list of {name, quantity} dicts."""
        return [
            {"name": ligne.article.name, "quantity": ligne.quantite}
            for ligne in order.lignes
        ]

    def _validate_stock(self, items: List[Dict[str, Any]]) -> None:
        """Re-validate that stock is still sufficient at acknowledgement time."""
        for item in items:
            name = item["name"]
            qty = item["quantity"]
            if not self.stock_repository.is_in_stock(name, qty):
                raise OrderNotAcknowledgeableException(
                    "order",
                    f"insufficient stock for {name}",
                )

    def _calculate_eta(self, items: List[Dict[str, Any]]) -> int:
        """Calculate ETA in minutes following the rules in FEATURES.md."""
        non_alc_types: set = set()
        normal_alc_qty = 0
        premium_alc_qty = 0
        snack_types: set = set()
        meal_types: set = set()

        for item in items:
            name = item["name"]
            qty = item["quantity"]
            item_cost = self.item_catalog_repository.get_item_cost(name)
            if item_cost is None:
                raise ArticleInconnuException(name)

            item_type = item_cost.item_type
            if item_type == ITEM_TYPE_NON_ALCOHOLIC_DRINK:
                non_alc_types.add(name)
            elif item_type == ITEM_TYPE_NORMAL_ALCOHOLIC_DRINK:
                normal_alc_qty += qty
            elif item_type == ITEM_TYPE_PREMIUM_ALCOHOLIC_DRINK:
                premium_alc_qty += qty
            elif item_type == ITEM_TYPE_SNACK:
                snack_types.add(name)
            elif item_type == ITEM_TYPE_MEAL:
                meal_types.add(name)

        non_alc_time = 1 * len(non_alc_types)
        normal_alc_time = 2 * normal_alc_qty
        premium_alc_time = 3 * premium_alc_qty
        snack_time = 2 * len(snack_types)

        # Longest per-unit preparation time among all drink categories in the order
        longest_drink_unit_time = 0
        if non_alc_types:
            longest_drink_unit_time = max(longest_drink_unit_time, 1)
        if normal_alc_qty > 0:
            longest_drink_unit_time = max(longest_drink_unit_time, 2)
        if premium_alc_qty > 0:
            longest_drink_unit_time = max(longest_drink_unit_time, 3)

        meal_time = (10 * len(meal_types) + longest_drink_unit_time) if meal_types else 0

        return non_alc_time + normal_alc_time + premium_alc_time + snack_time + meal_time

    def _deduct_tokens(self, order: Commande, items: List[Dict[str, Any]]) -> None:
        """Deduct tokens from festivalier(s) at acknowledgement time."""
        if order.contributors:
            # Group order — deduct each contributor's pledged amount
            for contributor in order.contributors:
                fid = contributor.festivalier_id
                balance = self.festivalier_repository.get_balance(fid)
                if balance is None:
                    raise FestivalierInconnuException(fid)
                self.festivalier_repository.deduct_tokens(
                    fid,
                    drink_tokens=contributor.contribution.drink_tokens,
                    food_tokens=contributor.contribution.food_tokens,
                )
        else:
            # Solo order — compute cost from catalog and deduct
            total_drink = 0
            total_food = 0
            for item in items:
                name = item["name"]
                qty = item["quantity"]
                item_cost = self.item_catalog_repository.get_item_cost(name)
                if item_cost is None:
                    raise ArticleInconnuException(name)
                total_drink += item_cost.drink_tokens_per_unit * qty
                total_food += item_cost.food_tokens_per_unit * qty

            fid = order.festivalier_id
            balance = self.festivalier_repository.get_balance(fid)
            if balance is None:
                raise FestivalierInconnuException(fid)
            self.festivalier_repository.deduct_tokens(
                fid,
                drink_tokens=total_drink,
                food_tokens=total_food,
            )

    def _resolve_festivalier_id(self, order: Commande) -> str:
        """Return a representative festivalier id for notifications."""
        if order.contributors:
            return order.contributors[0].festivalier_id
        return order.festivalier_id
