"""
Rôle : point d'entrée FastAPI (Bloc A - Mourad).
Auteur : NKWANE Mourad.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.database import SessionLocal, init_db
from app.routers import auth, devices, measurements, plots, subscribers
from app.seed import ensure_demo_user


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Initialise le schéma SQLite et l'utilisateur démo au démarrage."""
    init_db()
    db = SessionLocal()
    try:
        ensure_demo_user(db)
    finally:
        db.close()
    yield


def create_app() -> FastAPI:
    """Factory de l'application FastAPI."""
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description=(
            "API AGRO-DATA — ingestion, pipeline, sécurité AES/JWT et CRUD "
            "(modules MOD-A1, A2, A3, A6 — NKWANE Mourad)."
        ),
        lifespan=lifespan,
    )
    application.include_router(auth.router)
    application.include_router(measurements.router)
    application.include_router(plots.router)
    application.include_router(devices.router)
    application.include_router(subscribers.router)

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
