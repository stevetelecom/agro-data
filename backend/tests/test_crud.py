"""
Rôle : tests MOD-A6 — CRUD, RBAC, GET measurements, 429.
Auteur : NKWANE Mourad.
"""

import time

from app.config import get_settings
from app.security.rate_limit import reset_rate_limits


def _measurement_payload(device_id: str, timestamp: int, humidity: float) -> dict:
    return {
        "device_id": device_id,
        "timestamp": timestamp,
        "climate": {
            "temperature_c": 27.0,
            "air_humidity_pct": humidity,
            "soil_humidity_pct": 60.0,
        },
        "diagnostic_ia": {"phytophthora_detected": 0, "confidence": 0.9},
        "geo_enc": "",
    }


def test_plots_crud_requires_auth(client):
    response = client.get("/api/v1/plots")
    assert response.status_code == 401


def test_plots_crud_happy_path(client, auth_headers):
    created = client.post(
        "/api/v1/plots",
        json={
            "code": "P-001",
            "name": "Parcelle Ambam Nord",
            "location_label": "Ambam",
            "village": "Ambam centre",
            "surface_ha": 1.5,
            "reference_volume_kg": 1200,
        },
        headers=auth_headers,
    )
    assert created.status_code == 201, created.text
    plot_id = created.json()["id"]

    listed = client.get("/api/v1/plots", headers=auth_headers)
    assert listed.status_code == 200
    assert any(p["id"] == plot_id for p in listed.json())

    updated = client.put(
        f"/api/v1/plots/{plot_id}",
        json={"name": "Parcelle Ambam Sud"},
        headers=auth_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Parcelle Ambam Sud"

    deleted = client.delete(f"/api/v1/plots/{plot_id}", headers=auth_headers)
    assert deleted.status_code == 204


def test_delete_plot_refused_while_device_attached(client, auth_headers):
    """Contrat §4.6 : `409` tant qu'un appareil est rattaché à la parcelle."""
    plot = client.post(
        "/api/v1/plots",
        json={
            "code": "P-DEL",
            "name": "Parcelle rattachée",
            "village": "Ambam",
            "surface_ha": 1.0,
        },
        headers=auth_headers,
    ).json()
    device = client.post(
        "/api/v1/devices",
        json={"device_id": "AMB-DEL", "label": "Boîtier", "plot_id": plot["id"]},
        headers=auth_headers,
    )
    assert device.status_code == 201, device.text

    refused = client.delete(f"/api/v1/plots/{plot['id']}", headers=auth_headers)
    assert refused.status_code == 409, refused.text
    # La parcelle et son rattachement sont intacts.
    kept = client.get(f"/api/v1/plots/{plot['id']}", headers=auth_headers)
    assert kept.status_code == 200
    assert kept.json()["id"] == plot["id"]

    # Une fois l'appareil détaché, la suppression redevient possible.
    detached = client.put(
        f"/api/v1/devices/{device.json()['id']}",
        json={"plot_id": None},
        headers=auth_headers,
    )
    assert detached.status_code == 200, detached.text
    assert detached.json()["plot_id"] is None
    assert client.delete(f"/api/v1/plots/{plot['id']}", headers=auth_headers).status_code == 204


def test_plot_read_exposes_computed_contract_fields(client, auth_headers, api_headers):
    """Contrat §4.6 : `hours_above_85`, `ia_detection_rate`, indice et niveau."""
    plot = client.post(
        "/api/v1/plots",
        json={
            "code": "P-KPI",
            "name": "Parcelle indicateurs",
            "village": "Ambam",
            "surface_ha": 2.0,
            "reference_volume_kg": 1200,
        },
        headers=auth_headers,
    ).json()
    # Une parcelle sans mesure expose des valeurs nulles, pas des champs absents.
    assert plot["hours_above_85"] == 0
    assert plot["ia_detection_rate"] == 0.0
    assert plot["infestation_index"] == 0
    assert plot["level"] == "faible"

    device = client.post(
        "/api/v1/devices",
        json={"device_id": "AMB-KPI", "plot_id": plot["id"]},
        headers=auth_headers,
    )
    assert device.status_code == 201, device.text

    maintenant = int(time.time())
    for offset in range(48):
        response = client.post(
            "/api/v1/measurements",
            json=_measurement_payload("AMB-KPI", maintenant - (48 - offset) * 3600, 90.0),
            headers=api_headers,
        )
        assert response.status_code == 201, response.text

    body = client.get(f"/api/v1/plots/{plot['id']}", headers=auth_headers).json()
    assert body["hours_above_85"] == 48
    assert body["ia_detection_rate"] == 0.0
    assert body["infestation_index"] == 60
    assert body["level"] == "modere"

    # La liste renvoie les mêmes champs que la lecture unitaire.
    listed = client.get("/api/v1/plots", headers=auth_headers).json()
    assert next(item for item in listed if item["id"] == plot["id"]) == body


def test_plot_without_village_or_surface_is_rejected(client, auth_headers):
    missing = client.post(
        "/api/v1/plots",
        json={"code": "P-002", "name": "Sans village"},
        headers=auth_headers,
    )
    assert missing.status_code == 422

    negative = client.post(
        "/api/v1/plots",
        json={"code": "P-003", "name": "Surface nulle", "village": "Ambam", "surface_ha": 0},
        headers=auth_headers,
    )
    assert negative.status_code == 422


def test_buyer_can_read_but_not_write(client, buyer_headers):
    listed = client.get("/api/v1/plots", headers=buyer_headers)
    assert listed.status_code == 200
    created = client.post(
        "/api/v1/plots",
        json={
            "code": "P-FORBIDDEN",
            "name": "Nope",
            "location_label": "Ambam",
            "village": "Ambam",
            "surface_ha": 1.0,
        },
        headers=buyer_headers,
    )
    assert created.status_code == 403


def test_devices_and_subscribers_crud(client, auth_headers):
    plot = client.post(
        "/api/v1/plots",
        json={
            "code": "P-010",
            "name": "Plot",
            "location_label": "Ambam",
            "village": "Ambam",
            "surface_ha": 2.0,
        },
        headers=auth_headers,
    ).json()

    device = client.post(
        "/api/v1/devices",
        json={"device_id": "AMB-P010", "label": "Boîtier 10", "plot_id": plot["id"]},
        headers=auth_headers,
    )
    assert device.status_code == 201, device.text

    sub = client.post(
        "/api/v1/subscribers",
        json={"email": "export@yaounde.cm", "organization": "Export SA", "plan": "pro"},
        headers=auth_headers,
    )
    assert sub.status_code == 201, sub.text
    assert sub.json()["email"] == "export@yaounde.cm"


def test_get_measurements_filtered(client, api_headers, auth_headers, valid_measurement):
    post = client.post("/api/v1/measurements", json=valid_measurement, headers=api_headers)
    assert post.status_code == 201

    listed = client.get(
        "/api/v1/measurements",
        params={"device_id": "AMB-P001"},
        headers=auth_headers,
    )
    assert listed.status_code == 200
    assert len(listed.json()) >= 1
    assert listed.json()[0]["device_id"] == "AMB-P001"
    assert listed.json()[0]["geo_enc"] == "lat:2.383,lon:11.283"


def test_rate_limit_returns_429(client, monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "2")
    get_settings.cache_clear()
    reset_rate_limits()
    codes = [
        client.post(
            "/api/v1/auth/login",
            json={"email": "acheteur@ebolowa.cm", "password": "demo1234"},
        ).status_code
        for _ in range(4)
    ]
    get_settings.cache_clear()
    reset_rate_limits()
    assert 429 in codes, codes


def test_openapi_docs_available(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/measurements" in paths
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/plots" in paths
    schemas = response.json()["components"]["schemas"]
    assert "PlotCreate" in schemas
    plot_schema = schemas["PlotCreate"]
    assert plot_schema.get("example") is not None or plot_schema.get("examples") is not None
