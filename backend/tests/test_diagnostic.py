"""Tests MOD-A5 : diagnostic IA (contrat §4.7) et route POST /api/v1/diagnostic.

Auteur : MEKONTSO Olivier Steve (issue #14).
"""

from __future__ import annotations

import pytest

from app.services.diagnostic import (
    IS_DEMO,
    MAX_IMAGE_BYTES,
    MODEL_NAME,
    InvalidImageError,
    image_format,
    predict,
)

PNG = b"\x89PNG\r\n\x1a\n" + b"cabosse-demo"
JPEG = b"\xff\xd8\xff\xe0" + b"cabosse-demo"
CHAMPS = {
    "phytophthora_detected",
    "confidence",
    "label",
    "recommendation",
    "model",
    "is_demo",
}


# --- Module d'inférence ----------------------------------------------------


def test_formats_reconnus():
    assert image_format(PNG) == "png"
    assert image_format(JPEG) == "jpeg"


def test_image_invalide_rejetee():
    with pytest.raises(InvalidImageError):
        image_format(b"GIF89a")
    with pytest.raises(InvalidImageError):
        predict(b"")
    with pytest.raises(InvalidImageError):
        predict(b"pas une image")


def test_image_trop_volumineuse_rejetee():
    with pytest.raises(InvalidImageError):
        predict(PNG + b"\x00" * MAX_IMAGE_BYTES)


def test_inference_deterministe_et_conforme():
    premier = predict(PNG)
    second = predict(PNG)
    assert premier == second
    assert premier.model == MODEL_NAME
    assert premier.is_demo is IS_DEMO
    assert premier.phytophthora_detected in (0, 1)
    assert 0.0 <= premier.confidence <= 1.0
    assert set(premier.as_dict()) == CHAMPS


def test_seuil_configurable():
    assert predict(PNG, threshold=0.0).phytophthora_detected == 1
    assert predict(PNG, threshold=1.0).phytophthora_detected == 0


def test_seuil_lu_dans_l_environnement(monkeypatch):
    monkeypatch.setenv("IA_DETECTION_THRESHOLD", "0")
    assert predict(PNG).phytophthora_detected == 1
    monkeypatch.setenv("IA_DETECTION_THRESHOLD", "1")
    assert predict(PNG).phytophthora_detected == 0
    monkeypatch.setenv("IA_DETECTION_THRESHOLD", "valeur-invalide")
    assert predict(PNG).phytophthora_detected in (0, 1)


# --- Route HTTP ------------------------------------------------------------


def _post(client, headers, contenu: bytes = PNG, nom: str = "cabosse.png"):
    return client.post(
        "/api/v1/diagnostic",
        files={"image": (nom, contenu, "image/png")},
        headers=headers,
    )


def test_route_diagnostic_image_valide(client, auth_headers):
    response = _post(client, auth_headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) == CHAMPS
    assert body["phytophthora_detected"] in (0, 1)
    assert body["is_demo"] is True
    assert body["model"] == MODEL_NAME
    assert 0.0 <= body["confidence"] <= 1.0


def test_route_diagnostic_image_invalide(client, auth_headers):
    response = _post(client, auth_headers, contenu=b"pas une image", nom="notes.txt")
    assert response.status_code == 422
    assert "JPEG ou PNG" in response.json()["detail"]


def test_route_diagnostic_image_trop_volumineuse(client, auth_headers):
    response = _post(client, auth_headers, contenu=PNG + b"\x00" * MAX_IMAGE_BYTES)
    assert response.status_code == 422


def test_route_diagnostic_sans_image(client, auth_headers):
    response = client.post("/api/v1/diagnostic", headers=auth_headers)
    assert response.status_code == 422


def test_route_diagnostic_exige_un_jeton(client):
    assert _post(client, {}).status_code == 401
