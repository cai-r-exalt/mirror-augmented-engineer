"""Lightweight SQLAlchemy setup helper.

This module attempts to create an in-memory SQLite engine and a sessionmaker
if SQLAlchemy is installed. If SQLAlchemy is unavailable, functions return
None and callers should fall back to in-memory implementations.
"""
from typing import Optional

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker, Session

    def create_session() -> Optional[Session]:
        engine = create_engine("sqlite:///:memory:")
        SessionLocal = sessionmaker(bind=engine)
        return SessionLocal()

except Exception:
    def create_session() -> Optional[object]:
        return None
