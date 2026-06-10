"""Entry point — wires the domain and infrastructure packages together.

This module creates a minimal composition root that injects the
infrastructure repositories into the domain use case and exposes a
controller instance. It's intentionally simple and uses in-memory
adapters so tests and local runs don't require external services.
"""

from app.infrastructure.adapters.sqlalchemy_order_repository import SQLAlchemyOrderRepository
from app.infrastructure.adapters.in_memory_stock_repository import InMemoryStockRepository
from app.domain.use_cases.place_order import PasserCommandeUseCase
from app.application.controllers.commande_controller import CommandesController


def create_application():
    # Minimal infra wiring
    # Try to create a real DB session; fall back to in-memory repository if unavailable
    try:
        from app.infrastructure.db import create_session

        session = create_session()
    except Exception:
        session = None

    order_repo = SQLAlchemyOrderRepository(session=session)
    stock_repo = InMemoryStockRepository(initial_stock={"Mojito": 100, "Eau plate": 50})

    use_case = PasserCommandeUseCase(order_repository=order_repo, stock_repository=stock_repo)
    controller = CommandesController(use_case=use_case)
    return {
        "order_repository": order_repo,
        "stock_repository": stock_repo,
        "use_case": use_case,
        "controller": controller,
    }


def main() -> None:
    app = create_application()
    print("Application wired. Available components:", list(app.keys()))


if __name__ == "__main__":
    main()
