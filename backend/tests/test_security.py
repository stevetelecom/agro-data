"""
Rôle : tests MOD-A3 — login JWT, clé API, chiffrement geo_enc.
Auteur : NKWANE Mourad.
"""

from app.services.crypto import decrypt_geo


def test_login_success(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "acheteur@agro-data.local", "password": "ChangeMe123!"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_failure(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "acheteur@agro-data.local", "password": "WrongPass999"},
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
