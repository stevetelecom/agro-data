"""
Rôle : fixtures pytest (DB isolée, client HTTP, utilisateur démo).
Auteur : NKWANE Mourad.
"""

import os
import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Forcer une config de test avant l'import de l'app.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["AGRO_AES_KEY"] = "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY="
os.environ["JWT_SECRET"] = "test-jwt-secret-32bytes-minimum!!"
os.environ["DEVICE_API_KEY"] = "test-device-key"
os.environ["DEMO_ADMIN_EMAIL"] = "acheteur@ebolowa.cm"
os.environ["DEMO_ADMIN_PASSWORD"] = "demo1234"
os.environ["DEMO_BUYER_EMAIL"] = "lecteur@ebolowa.cm"
os.environ["DEMO_BUYER_PASSWORD"] = "demo1234"
os.environ["RATE_LIMIT_PER_MINUTE"] = "1000"

from app.config import get_settings
from app.database import Base, get_db
from app.main import create_app
from app.security.rate_limit import reset_rate_limits
from app.seed import ensure_demo_user

get_settings.cache_clear()


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Client TestClient avec SQLite mémoire partagée et Data Lake temporaire."""
    monkeypatch.setenv("DATA_LAKE_DIR", str(tmp_path / "data_lake"))
    get_settings.cache_clear()
    reset_rate_limits()

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    ensure_demo_user(db)
    db.close()

    def _override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    application = create_app()
    application.dependency_overrides[get_db] = _override_get_db

    with TestClient(application) as test_client:
        yield test_client

    application.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    get_settings.cache_clear()
    reset_rate_limits()


@pytest.fixture()
def db_session():
    """Session SQLAlchemy isolée (SQLite mémoire) pour tester les services."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def api_headers() -> dict[str, str]:
    return {"X-API-Key": "test-device-key"}


@pytest.fixture()
def valid_measurement() -> dict:
    return {
        "device_id": "AMB-P001",
        "timestamp": int(time.time()) - 60,
        "climate": {
            "temperature_c": 27.4,
            "air_humidity_pct": 88.2,
            "soil_humidity_pct": 61.0,
        },
        "diagnostic_ia": {
            "phytophthora_detected": 0,
            "confidence": 0.93,
        },
        "geo_enc": "lat:2.383,lon:11.283",
    }


@pytest.fixture()
def auth_headers(client: TestClient) -> dict[str, str]:
    """JWT admin (compte démo historique)."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "acheteur@ebolowa.cm", "password": "demo1234"},
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def buyer_headers(client: TestClient) -> dict[str, str]:
    """JWT acheteur (lecture seule CRUD)."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "lecteur@ebolowa.cm", "password": "demo1234"},
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
