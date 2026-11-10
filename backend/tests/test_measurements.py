"""
Rôle : tests MOD-A1 / A2 — ingestion, pipeline et Data Lake.
Auteur : NKWANE Mourad.
"""

import time
from pathlib import Path

from app.config import get_settings


def test_post_measurement_accepts_valid_json(client, api_headers, valid_measurement):
    response = client.post("/api/v1/measurements", json=valid_measurement, headers=api_headers)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["device_id"] == "AMB-P001"
    assert body["air_humidity_pct"] == 88.2
    assert body["geo_enc"] != "lat:2.383,lon:11.283"
    assert body["geo_enc"] != ""


def test_post_measurement_stores_raw_in_data_lake(client, api_headers, valid_measurement):
    response = client.post("/api/v1/measurements", json=valid_measurement, headers=api_headers)
    assert response.status_code == 201
    raw_dir = Path(get_settings().data_lake_dir) / "raw"
    files = list(raw_dir.glob("*.json"))
    assert len(files) >= 1


def test_post_measurement_rejects_invalid_json(client, api_headers):
    payload = {
        "device_id": "AMB-P001",
        "timestamp": int(time.time()),
        "climate": {
            "temperature_c": 27.4,
            "air_humidity_pct": 150.0,  # hors plage Pydantic
            "soil_humidity_pct": 61.0,
        },
        "diagnostic_ia": {"phytophthora_detected": 0, "confidence": 0.9},
        "geo_enc": "",
    }
    response = client.post("/api/v1/measurements", json=payload, headers=api_headers)
    assert response.status_code == 422


def test_post_measurement_rejects_missing_api_key(client, valid_measurement):
    response = client.post("/api/v1/measurements", json=valid_measurement)
    assert response.status_code == 401


def test_pipeline_rejects_out_of_range_temperature(client, api_headers, valid_measurement):
    valid_measurement["climate"]["temperature_c"] = 99.0
    response = client.post("/api/v1/measurements", json=valid_measurement, headers=api_headers)
    assert response.status_code == 422
    assert "temperature_c" in response.json()["detail"]
    rejects = Path(get_settings().data_lake_dir) / "rejects.log"
    assert rejects.exists()
    assert "temperature_c" in rejects.read_text(encoding="utf-8")


def test_pipeline_rejects_duplicate(client, api_headers, valid_measurement):
    first = client.post("/api/v1/measurements", json=valid_measurement, headers=api_headers)
    assert first.status_code == 201
    second = client.post("/api/v1/measurements", json=valid_measurement, headers=api_headers)
    assert second.status_code == 422
    assert "doublon" in second.json()["detail"].lower()


def test_pipeline_rejects_future_timestamp(client, api_headers, valid_measurement):
    valid_measurement["timestamp"] = int(time.time()) + 3600
    response = client.post("/api/v1/measurements", json=valid_measurement, headers=api_headers)
    assert response.status_code == 422


def test_openapi_measurement_example_present(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schemas = response.json()["components"]["schemas"]
    assert "MeasurementCreate" in schemas
    example = schemas["MeasurementCreate"].get("example") or schemas["MeasurementCreate"].get(
        "examples"
    )
    assert example is not None
