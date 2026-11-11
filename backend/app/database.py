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


# Colonnes ajoutées après la première livraison (issue #18).
# create_all() ne modifie pas une table existante : on complète la base SQLite
# existante pour que la démonstration reparte sans la supprimer.
_ADDED_COLUMNS = {
    "plots": {
        "village": "VARCHAR(40) NOT NULL DEFAULT ''",
        "surface_ha": "FLOAT NOT NULL DEFAULT 0",
        "reference_volume_kg": "FLOAT NOT NULL DEFAULT 0",
    },
}


def upgrade_existing_tables() -> None:
    """Ajoute les colonnes manquantes aux tables déjà créées (SQLite uniquement)."""
    if not engine.url.get_backend_name().startswith("sqlite"):
        return
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    with engine.begin() as connection:
        for table, columns in _ADDED_COLUMNS.items():
            if table not in tables:
                continue
            existing = {column["name"] for column in inspector.get_columns(table)}
            for name, ddl in columns.items():
                if name not in existing:
                    connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))


def init_db() -> None:
    """Crée les tables si elles n'existent pas, puis complète les colonnes ajoutées."""
    from app import models  # noqa: F401 — enregistre les modèles

    Base.metadata.create_all(bind=engine)
    upgrade_existing_tables()
