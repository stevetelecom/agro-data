"""
Rôle : point d'entrée FastAPI (Bloc A - Mourad).
Auteur : NKWANE Mourad.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import SessionLocal, init_db
from app.routers import auth, devices, diagnostic, kpis, measurements, plots, subscribers
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
    origins = [
        origine.strip() for origine in settings.cors_origins.split(",") if origine.strip()
    ]
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(auth.router)
    application.include_router(measurements.router)
    application.include_router(plots.router)
    application.include_router(devices.router)
    application.include_router(subscribers.router)
    application.include_router(kpis.router)
    application.include_router(diagnostic.router)

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
