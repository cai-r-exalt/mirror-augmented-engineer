from dataclasses import dataclass
from typing import List


@dataclass
class Article:
    name: str


@dataclass
class LigneCommande:
    article: Article
    quantite: int


@dataclass
class Commande:
    id: str
    festivalier_id: str
    lignes: List[LigneCommande]
    status: str
