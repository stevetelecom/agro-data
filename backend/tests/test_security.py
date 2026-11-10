"""
Rôle : tests MOD-A3 — login JWT, clé API, chiffrement geo_enc.
Auteur : NKWANE Mourad.
"""

from pathlib import Path

from app.config import get_settings
from app.services.crypto import decrypt_geo


def test_login_success(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "acheteur@ebolowa.cm", "password": "demo1234"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_failure(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "acheteur@ebolowa.cm", "password": "WrongPass999"},
    )
    assert response.status_code == 401


def test_geo_enc_not_stored_plaintext(client, api_headers, valid_measurement):
    plaintext = "lat:2.383,lon:11.283"
    valid_measurement["geo_enc"] = plaintext
    response = client.post("/api/v1/measurements", json=valid_measurement, headers=api_headers)
    assert response.status_code == 201
    stored = response.json()["geo_enc"]
    assert plaintext not in stored
    assert decrypt_geo(stored) == plaintext


def test_geo_enc_decrypted_on_authorized_read(client, api_headers, auth_headers, valid_measurement):
    plaintext = "lat:2.383,lon:11.283"
    valid_measurement["geo_enc"] = plaintext
    assert client.post("/api/v1/measurements", json=valid_measurement, headers=api_headers).status_code == 201
    listed = client.get("/api/v1/measurements", headers=auth_headers)
    assert listed.status_code == 200
    assert listed.json()[0]["geo_enc"] == plaintext


def test_invalid_token_rejected(client):
    response = client.get(
        "/api/v1/measurements",
        headers={"Authorization": "Bearer not-a-valid-token"},
    )
    assert response.status_code == 401


def test_missing_token_rejected(client):
    response = client.get("/api/v1/measurements")
    assert response.status_code == 401


def test_data_lake_raw_zone_chiffre_geo_enc(client, api_headers, valid_measurement):
    """La zone brute ne doit contenir aucune coordonnée en clair (BNF3)."""
    plaintext = "lat:2.383,lon:11.283"
    valid_measurement["geo_enc"] = plaintext
    assert client.post("/api/v1/measurements", json=valid_measurement, headers=api_headers).status_code == 201

    raw_dir = Path(get_settings().data_lake_dir) / "raw"
    fichiers = list(raw_dir.glob("*.json"))
    assert fichiers, "la zone brute doit contenir le message ingéré"
    contenu = fichiers[0].read_text(encoding="utf-8")
    assert plaintext not in contenu
    assert "lat:2.383" not in contenu


def test_device_id_refuse_les_caracteres_dangereux(client, api_headers, valid_measurement):
    for device_id in ["../etc/passwd", "AMB P001", "amb/p001", "a" * 65]:
        valid_measurement["device_id"] = device_id
        response = client.post(
            "/api/v1/measurements", json=valid_measurement, headers=api_headers
        )
        assert response.status_code == 422, device_id


def test_cors_autorise_le_dashboard_local(client):
    response = client.options(
        "/api/v1/kpis",
        headers={
            "Origin": "http://127.0.0.1:5500",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5500"
