"""
Rôle : configuration centralisée (variables d'environnement).
Auteur : NKWANE Mourad (MOD-A1 / A3).
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Paramètres runtime du backend AGRO-DATA."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AGRO-DATA API"
    database_url: str = "sqlite:///./agro_data.db"
    # Clé AES-256 (32 octets) encodée en base64 — à surcharger via AGRO_AES_KEY.
    agro_aes_key: str = "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY="
    jwt_secret: str = "change-me-agro-data-jwt-secret"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    # Clé d'API appareil de démonstration (header X-API-Key).
    device_api_key: str = "agro-device-demo-key"
    rate_limit_per_minute: int = 120
    data_lake_dir: str = "data_lake"
    # Origines autorisées pour le tableau de bord statique (dev local).
    # `null` couvre l'ouverture directe des fichiers en `file://`.
    cors_origins: str = (
        "http://localhost:8000,http://127.0.0.1:8000,"
        "http://localhost:5500,http://127.0.0.1:5500,"
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:8080,http://127.0.0.1:8080,null"
    )
    # Comptes de démonstration, alignés sur la maquette (docs/DESIGN_SYSTEM.md).
    # À supprimer ou à changer avant toute mise en ligne.
    demo_admin_email: str = "acheteur@ebolowa.cm"
    demo_admin_password: str = "demo1234"
    demo_buyer_email: str = "lecteur@ebolowa.cm"
    demo_buyer_password: str = "demo1234"


@lru_cache
def get_settings() -> Settings:
    """Retourne l'instance mise en cache des paramètres."""
    return Settings()
