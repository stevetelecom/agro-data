"""
Rôle : connexion SQLAlchemy et sessions.
Auteur : NKWANE Mourad (MOD-A1).
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings


class Base(DeclarativeBase):
    """Base déclarative SQLAlchemy."""


def _build_engine():
    settings = get_settings()
    url = settings.database_url
    if url == "sqlite://" or url.startswith("sqlite:///:memory:"):
        # Une seule base mémoire partagée entre connexions (tests / démo).
        return create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args)


engine = _build_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Fournit une session DB pour les dépendances FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Crée les tables si elles n'existent pas."""
    from app import models  # noqa: F401 — enregistre les modèles

    Base.metadata.create_all(bind=engine)
