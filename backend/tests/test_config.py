"""Tests du garde-fou de configuration (constat d'audit A8).

Rôle : vérifier qu'un démarrage en production refuse les secrets de
démonstration, sans bloquer le mode développement.
"""

import pytest

from app.config import (
    DEFAULT_AGRO_AES_KEY,
    DEFAULT_DEVICE_API_KEY,
    DEFAULT_JWT_SECRET,
    Settings,
)


def test_production_refuse_les_secrets_de_demonstration():
    settings = Settings(
        app_env="production",
        jwt_secret=DEFAULT_JWT_SECRET,
        agro_aes_key=DEFAULT_AGRO_AES_KEY,
        device_api_key=DEFAULT_DEVICE_API_KEY,
    )
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        settings.validate_production_settings()


def test_production_accepte_des_secrets_surcharges():
    settings = Settings(
        app_env="production",
        jwt_secret="un-secret-de-production-de-40-caracteres!!",
        agro_aes_key="dW5lLWNsZS1kZS1wcm9kdWN0aW9uLWRlLTMyLW9jdGV0cyE=",
        device_api_key="cle-appareil-production",
    )
    settings.validate_production_settings()


def test_developpement_tolere_les_valeurs_par_defaut():
    settings = Settings(
        app_env="development",
        jwt_secret=DEFAULT_JWT_SECRET,
        agro_aes_key=DEFAULT_AGRO_AES_KEY,
        device_api_key=DEFAULT_DEVICE_API_KEY,
    )
    settings.validate_production_settings()
