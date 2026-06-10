"""Minimal OrderRepository adapter used by infrastructure tests.

This is a small in-memory implementation intended to replace test-local
fakes during the refactor step. It keeps behaviour identical to the
previous test-local class (dict-backed store) so tests remain green.
"""
from typing import Optional, List, Dict, Any

from app.domain.entities.commande import Commande, LigneCommande, Article


# Optional SQLAlchemy ORM models for persistence mapping. Import is guarded
# so tests or environments without SQLAlchemy still work using the in-memory
# fallback implementation.
try:
    from sqlalchemy import Column, Integer, String, ForeignKey
    from sqlalchemy.orm import declarative_base, relationship

    Base = declarative_base()


    class OrderItemORM(Base):
        __tablename__ = "order_items"
        id = Column(Integer, primary_key=True, autoincrement=True)
        order_id = Column(String, ForeignKey("orders.id"))
        article_name = Column(String, nullable=False)
        quantite = Column(Integer, nullable=False)


    class OrderORM(Base):
        __tablename__ = "orders"
        id = Column(String, primary_key=True)
        festivalier_id = Column(String, nullable=False)
        status = Column(String, nullable=False)
        items = relationship("OrderItemORM", cascade="all, delete-orphan")

except Exception:
    Base = None


class SQLAlchemyOrderRepository:
    """Minimal in-memory repository that implements the `OrderRepository` port.

    It also provides SQLAlchemy ORM models above for teams that wire a real DB.
    """

    def __init__(self, session=None):
        # `session` would be a SQLAlchemy session in a real implementation.
        self._session = session
        self._store: Dict[str, Commande] = {}

    def _model_to_domain(self, orm_order: Any) -> Commande:
        # Convert ORM to domain Commande (only used if SQLAlchemy models are used)
        lignes = [LigneCommande(article=Article(name=item.article_name), quantite=item.quantite) for item in getattr(orm_order, "items", [])]
        return Commande(id=orm_order.id, festivalier_id=orm_order.festivalier_id, lignes=lignes, status=orm_order.status)

    def _domain_to_model(self, commande: Commande) -> Any:
        # Convert domain Commande to ORM structure (if SQLAlchemy available)
        if Base is None:
            return None
        order = OrderORM(id=commande.id, festivalier_id=commande.festivalier_id, status=commande.status)
        order.items = [OrderItemORM(article_name=l.article.name, quantite=l.quantite) for l in commande.lignes]
        return order

    def create_order(self, festivalier_id: str, items: List[Dict[str, Any]]) -> Commande:
        # Minimal id generation for the example; real impl should use UUIDs or DB-generated ids
        if self._session is not None and Base is not None:
            # Use the DB to create a persistent order
            # Generate a simple id here; in real DB you'd use a UUID or DB-side id
            next_id = f"order-db-{len(self._store) + 1}"
            lignes = [LigneCommande(article=Article(name=i["name"]), quantite=i["quantity"]) for i in items]
            commande = Commande(id=next_id, festivalier_id=festivalier_id, lignes=lignes, status="EN_ATTENTE")
            orm = self._domain_to_model(commande)
            # persist via session
            self._session.add(orm)
            try:
                self._session.commit()
            except Exception:
                self._session.rollback()
                raise
            # reload to include relationships
            persisted = self._session.query(OrderORM).filter(OrderORM.id == orm.id).one()
            domain = self._model_to_domain(persisted)
            # keep a local copy for fallback/test visibility
            self._store[domain.id] = domain
            return domain

        next_id = f"order-{len(self._store) + 1}"
        lignes = [LigneCommande(article=Article(name=i["name"]), quantite=i["quantity"]) for i in items]
        commande = Commande(id=next_id, festivalier_id=festivalier_id, lignes=lignes, status="EN_ATTENTE")
        self.save(commande)
        return commande

    def save(self, commande: Commande) -> None:
        # If a SQLAlchemy session is provided, persist using ORM models.
        if self._session is not None and Base is not None:
            orm = self._domain_to_model(commande)
            # remove existing rows if present
            existing = self._session.query(OrderORM).filter(OrderORM.id == orm.id).one_or_none()
            if existing:
                self._session.delete(existing)
                self._session.flush()
            self._session.add(orm)
            try:
                self._session.commit()
            except Exception:
                self._session.rollback()
                raise
            # update local cache
            persisted = self._session.query(OrderORM).filter(OrderORM.id == orm.id).one()
            self._store[commande.id] = self._model_to_domain(persisted)
            return

        # In-memory persistence fallback
        self._store[commande.id] = commande

    def get_by_id(self, order_id: str) -> Optional[Commande]:
        if self._session is not None and Base is not None:
            orm = self._session.query(OrderORM).filter(OrderORM.id == order_id).one_or_none()
            if orm:
                return self._model_to_domain(orm)
        return self._store.get(order_id)

    def update_status(self, order_id: str, status: str) -> None:
        if self._session is not None and Base is not None:
            orm = self._session.query(OrderORM).filter(OrderORM.id == order_id).one_or_none()
            if orm:
                orm.status = status
                try:
                    self._session.commit()
                except Exception:
                    self._session.rollback()
                    raise
                # update local cache
                self._store[order_id] = self._model_to_domain(orm)
                return

        if order_id in self._store:
            self._store[order_id].status = status

    def find_by_festivalier_and_status(self, festivalier_id: str, status: str) -> List[Commande]:
        if self._session is not None and Base is not None:
            orms = self._session.query(OrderORM).filter(OrderORM.festivalier_id == festivalier_id, OrderORM.status == status).all()
            return [self._model_to_domain(o) for o in orms]

        return [c for c in self._store.values() if c.festivalier_id == festivalier_id and c.status == status]
