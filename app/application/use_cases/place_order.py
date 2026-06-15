from dataclasses import dataclass
from typing import Any, Dict, List

from app.domain.use_cases.place_order import PasserCommandeCommand as DomainPasserCommandeCommand
from app.domain.use_cases.place_order import PasserCommandeUseCase as DomainPasserCommandeUseCase


@dataclass
class PasserCommandeCommand:
    festivalier_id: str
    items: List[Dict[str, Any]]


class PasserCommandeUseCase:
    """Application-layer wrapper for the domain `PasserCommandeUseCase`.

    Keeps the same constructor and `execute` API so application tests can
    depend on the application layer implementation while delegating the
    business behaviour to the domain use case.
    """

    def __init__(self, order_repository, stock_repository):
        self._domain_uc = DomainPasserCommandeUseCase(
            order_repository=order_repository, stock_repository=stock_repository
        )

    def execute(self, command: PasserCommandeCommand):
        # Convert to domain command if needed (same structure here)
        domain_cmd = DomainPasserCommandeCommand(
            festivalier_id=command.festivalier_id, items=command.items
        )
        return self._domain_uc.execute(domain_cmd)
