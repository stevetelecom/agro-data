"""
Rôle : tests MOD-A6 — CRUD, RBAC, GET measurements, 429.
Auteur : NKWANE Mourad.
"""

from app.config import get_settings
from app.security.rate_limit import reset_rate_limits


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


def test_plot_without_village_or_surface_is_rejected(client, auth_headers):
    """Contrat §4.6 : village obligatoire et surface_ha strictement positive."""
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
