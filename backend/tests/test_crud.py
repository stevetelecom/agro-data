"""
Rôle : tests MOD-A6 — CRUD + GET measurements + 401.
Auteur : NKWANE Mourad.
"""


def test_plots_crud_requires_auth(client):
    response = client.get("/api/v1/plots")
    assert response.status_code == 401


def test_plots_crud_happy_path(client, auth_headers):
    created = client.post(
        "/api/v1/plots",
        json={"code": "P-001", "name": "Parcelle Ambam Nord", "location_label": "Ambam"},
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


def test_devices_and_subscribers_crud(client, auth_headers):
    plot = client.post(
        "/api/v1/plots",
        json={"code": "P-010", "name": "Plot", "location_label": "Ambam"},
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


def test_openapi_docs_available(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/measurements" in paths
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/plots" in paths
