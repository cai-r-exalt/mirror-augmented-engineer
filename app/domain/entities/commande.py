from dataclasses import dataclass, field
from typing import List, Optional

from app.domain.value_objects.token_contribution import TokenContribution


@dataclass
class Article:
    name: str


@dataclass
class LigneCommande:
    article: Article
    quantite: int


@dataclass
class ContributorContribution:
    """Records a single contributor's token commitment to a group order."""

    festivalier_id: str
    contribution: TokenContribution


@dataclass
class Commande:
    id: str
    festivalier_id: str
    lignes: List[LigneCommande]
    status: str
    contributors: Optional[List[ContributorContribution]] = field(default=None)
    eta_minutes: Optional[int] = field(default=None)
    acknowledged_at: Optional[str] = field(default=None)
