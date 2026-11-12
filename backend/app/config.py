"""
Rôle : configuration centralisée (variables d'environnement).
Auteur : NKWANE Mourad (MOD-A1 / A3).
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# Valeurs de démonstration : elles ne doivent jamais servir en production.
DEFAULT_AGRO_AES_KEY = "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY="
DEFAULT_JWT_SECRET = "change-me-agro-data-jwt-secret"
DEFAULT_DEVICE_API_KEY = "agro-device-demo-key"
PRODUCTION_ENVIRONMENTS = {"prod", "production"}


class Settings(BaseSettings):
    """Paramètres runtime du backend AGRO-DATA."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AGRO-DATA API"
    # Environnement d'exécution : `development` (défaut) ou `production`.
    # En production, les secrets de démonstration sont refusés au démarrage.
    app_env: str = "development"
    database_url: str = "sqlite:///./agro_data.db"
    # Clé AES-256 (32 octets) encodée en base64 — à surcharger via AGRO_AES_KEY.
    agro_aes_key: str = DEFAULT_AGRO_AES_KEY
    jwt_secret: str = DEFAULT_JWT_SECRET
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    # Clé d'API appareil de démonstration (header X-API-Key).
    device_api_key: str = DEFAULT_DEVICE_API_KEY
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

    def is_production(self) -> bool:
        """Vrai si l'application tourne en production."""
        return self.app_env.strip().lower() in PRODUCTION_ENVIRONMENTS

    def validate_production_settings(self) -> None:
        """Refuse les secrets de démonstration quand `APP_ENV=production`.

        Le démarrage en développement reste permissif (démonstration locale),
        mais un déploiement qui oublie `.env` ne peut plus signer des JWT avec
        un secret public : l'erreur est explicite au démarrage.
        """
        if not self.is_production():
            return
        defaults = {
            "JWT_SECRET": (self.jwt_secret, DEFAULT_JWT_SECRET),
            "AGRO_AES_KEY": (self.agro_aes_key, DEFAULT_AGRO_AES_KEY),
            "DEVICE_API_KEY": (self.device_api_key, DEFAULT_DEVICE_API_KEY),
        }
        restants = [nom for nom, (valeur, defaut) in defaults.items() if valeur == defaut]
        if restants:
            raise RuntimeError(
                "Configuration de production invalide : surchargez "
                + ", ".join(restants)
                + " par des variables d'environnement avant de démarrer."
            )


@lru_cache
def get_settings() -> Settings:
    """Retourne l'instance mise en cache des paramètres."""
    return Settings()
