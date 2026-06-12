"""Application integration tests for the POST /group-orders endpoint.

Tests the full flow through the GroupOrderController → PlaceGroupOrderUseCase.
"""


from app.application.controllers.group_order_controller import GroupOrderController
from app.application.dto.group_order import ContributionRequest, ContributorRequest, GroupOrderRequest
from app.domain.use_cases.place_group_order import PlaceGroupOrderUseCase
from app.infrastructure.adapters.in_memory_festivalier_repository import InMemoryFestivalierRepository
from app.infrastructure.adapters.in_memory_item_catalog_repository import InMemoryItemCatalogRepository
from app.infrastructure.adapters.in_memory_order_repository import InMemoryOrderRepository
from app.infrastructure.adapters.in_memory_stock_repository import InMemoryStockRepository


def _build_controller(
    stock: dict | None = None,
    balances: dict | None = None,
    catalog: dict | None = None,
) -> GroupOrderController:
    order_repo = InMemoryOrderRepository()
    stock_repo = InMemoryStockRepository(stock or {"Mojito": 10, "Burger": 5})
    festivalier_repo = InMemoryFestivalierRepository(
        balances
        or {
            "user-1": {"drink_tokens": 10, "food_tokens": 0},
            "user-2": {"drink_tokens": 5, "food_tokens": 10},
        }
    )
    catalog_repo = InMemoryItemCatalogRepository(
        catalog
        or {
            "Mojito": {"drink_tokens_per_unit": 3, "food_tokens_per_unit": 0},
            "Burger": {"drink_tokens_per_unit": 0, "food_tokens_per_unit": 4},
        }
    )
    use_case = PlaceGroupOrderUseCase(
        order_repository=order_repo,
        stock_repository=stock_repo,
        festivalier_repository=festivalier_repo,
        item_catalog_repository=catalog_repo,
    )
    return GroupOrderController(use_case=use_case)


class TestGroupOrderApplicationIntegration:
    """Integration tests covering successful group order and error paths."""

    # ── Scenario: Successful group order ─────────────────────────────────────

    def test_successful_group_order_returns_201_with_order_id(self):
        """
        Given users with sufficient token balances and items in stock
        When a group order is submitted
        Then 201 is returned with an orderId
        """
        controller = _build_controller()
        req = GroupOrderRequest(
            items=[{"id": "Mojito", "quantity": 3}],  # costs 9 drink tokens
            contributors=[
                ContributorRequest("user-1", ContributionRequest(drink_tokens=5, food_tokens=0)),
                ContributorRequest("user-2", ContributionRequest(drink_tokens=4, food_tokens=0)),
            ],
        )
        response = controller.create_group_order(req)

        assert response.status_code == 201
        assert "orderId" in response.json()
        assert response.json()["orderId"] is not None

    def test_successful_group_order_with_id_field_in_items(self):
        """Items can be referenced by the 'id' field as well as 'name'."""
        controller = _build_controller()
        req = GroupOrderRequest(
            items=[{"id": "Mojito", "quantity": 2}],  # costs 6 drink tokens
            contributors=[
                ContributorRequest("user-1", ContributionRequest(drink_tokens=6, food_tokens=0)),
            ],
        )
        response = controller.create_group_order(req)
        assert response.status_code == 201

    # ── Scenario: Malformed request ───────────────────────────────────────────

    def test_returns_400_when_items_missing(self):
        controller = _build_controller()
        req = GroupOrderRequest(
            items=None,
            contributors=[
                ContributorRequest("user-1", ContributionRequest(drink_tokens=5, food_tokens=0)),
            ],
        )
        response = controller.create_group_order(req)
        assert response.status_code == 400

    def test_returns_400_when_contributors_missing(self):
        controller = _build_controller()
        req = GroupOrderRequest(
            items=[{"id": "Mojito", "quantity": 1}],
            contributors=None,
        )
        response = controller.create_group_order(req)
        assert response.status_code == 400

    def test_returns_400_when_item_missing_quantity(self):
        controller = _build_controller()
        req = GroupOrderRequest(
            items=[{"id": "Mojito"}],
            contributors=[
                ContributorRequest("user-1", ContributionRequest(drink_tokens=5, food_tokens=0)),
            ],
        )
        response = controller.create_group_order(req)
        assert response.status_code == 400

    # ── Scenario: Insufficient pooled funds ──────────────────────────────────

    def test_returns_402_when_pooled_drink_tokens_insufficient(self):
        """
        Given pooled contributions are below required cost
        When group order is attempted
        Then the API returns 402 and no balances are changed
        """
        controller = _build_controller()
        req = GroupOrderRequest(
            items=[{"id": "Mojito", "quantity": 4}],  # costs 12 drink tokens
            contributors=[
                ContributorRequest("user-1", ContributionRequest(drink_tokens=5, food_tokens=0)),
                ContributorRequest("user-2", ContributionRequest(drink_tokens=5, food_tokens=0)),
                # pooled = 10, need 12
            ],
        )
        response = controller.create_group_order(req)
        assert response.status_code == 402
        assert "error" in response.json()

    # ── Scenario: Stock issues ────────────────────────────────────────────────

    def test_returns_409_when_item_out_of_stock(self):
        controller = _build_controller(stock={"Mojito": 2})
        req = GroupOrderRequest(
            items=[{"id": "Mojito", "quantity": 5}],  # only 2 available
            contributors=[
                ContributorRequest("user-1", ContributionRequest(drink_tokens=10, food_tokens=0)),
            ],
        )
        response = controller.create_group_order(req)
        assert response.status_code == 409

    def test_returns_409_when_contributor_balance_exceeded(self):
        """A contributor cannot offer more than their available balance."""
        controller = _build_controller()
        req = GroupOrderRequest(
            items=[{"id": "Mojito", "quantity": 1}],  # costs 3 drink tokens
            contributors=[
                ContributorRequest("user-1", ContributionRequest(drink_tokens=99, food_tokens=0)),  # user-1 only has 10
            ],
        )
        response = controller.create_group_order(req)
        assert response.status_code == 409
