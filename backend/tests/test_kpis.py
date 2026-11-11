"""Tests MOD-A4 : indicateurs du tableau de bord (contrat §4.4) et courbe de prix (§4.5).

Rôle : vérifier l'agrégation des mesures persistées (RM1, RM2), le
rattachement des appareils aux parcelles et les routes exposées.
Auteur : MEKONTSO Olivier Steve (issue #13).
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

import pytest

from app.models import Device, Measurement, Plot
from app.services.indicators import (
    build_kpis,
    build_price_forecast,
    detection_rate,
    longest_run_hours,
)
from app.services.pricing import REFERENCE_PRICE_FCFA_PER_KG, adjust_price

NOW = int(datetime(2026, 11, 10, 12, 0, tzinfo=timezone.utc).timestamp())


def _add_measurement(
    db,
    device_id: str,
    timestamp: int,
    humidity: float,
    detected: int = 0,
) -> None:
    db.add(
        Measurement(
            device_id=device_id,
            timestamp=timestamp,
            temperature_c=27.0,
            air_humidity_pct=humidity,
            soil_humidity_pct=60.0,
            phytophthora_detected=detected,
            confidence=0.9,
            geo_enc="",
        )
    )


def _hourly_run(db, device_id: str, hours: int, humidity: float, end: int = NOW - 1) -> None:
    """Ajoute `hours` mesures horaires consécutives terminant à `end`."""
    for offset in range(hours):
        _add_measurement(db, device_id, end - (hours - 1 - offset) * 3600, humidity)
    db.commit()


# --- Fonctions pures -------------------------------------------------------


def test_plus_longue_serie_au_dessus_du_seuil():
    timestamps = [NOW + heure * 3600 for heure in range(5)]
    humidites = [90.0, 90.0, 70.0, 90.0, 90.0]
    assert longest_run_hours(timestamps, humidites) == 2


def test_serie_cassee_par_un_trou_de_plus_de_deux_heures():
    timestamps = [NOW, NOW + 3600, NOW + 6 * 3600]
    assert longest_run_hours(timestamps, [90.0, 90.0, 90.0]) == 2


def test_taux_de_detection_ia():
    assert detection_rate([]) == 0.0
    assert detection_rate([1, 0, 1, 0]) == pytest.approx(0.5)
    assert detection_rate([1, 1, 1]) == 1.0


# --- Agrégation sur la base ------------------------------------------------


def test_kpis_sans_mesure(db_session):
    kpis = build_kpis(db_session, now=NOW)
    assert kpis["global_infestation_index"] == 0
    assert kpis["level"] == "faible"
    assert kpis["active_alerts"] == 0
    assert kpis["avg_air_humidity_pct"] == 0.0
    assert kpis["humidity_delta_7d"] == 0.0
    assert kpis["estimated_healthy_volume_pct"] == 100
    assert kpis["plots_monitored"] == 0
    assert kpis["humidity_series"] == []
    assert kpis["generated_at"].endswith("Z")


def test_alerte_apres_48h_au_dessus_de_85(db_session):
    _hourly_run(db_session, "AMB-P001", 48, 90.0)
    kpis = build_kpis(db_session, now=NOW)
    assert kpis["active_alerts"] == 1
    assert kpis["plots_monitored"] == 1
    assert kpis["humidity_series"][0]["under_alert"] is True
    # 60 x min(1, 48/48) + 40 x 0 = 60
    assert kpis["global_infestation_index"] == 60
    assert kpis["level"] == "modere"
    # Aucune mesure sur les 7 jours précédents : l'écart n'est pas mesurable.
    assert kpis["humidity_delta_7d"] == 0.0


def test_pas_d_alerte_avant_48h(db_session):
    _hourly_run(db_session, "AMB-P001", 47, 90.0)
    kpis = build_kpis(db_session, now=NOW)
    assert kpis["active_alerts"] == 0
    assert kpis["humidity_series"][0]["under_alert"] is False


def test_mesures_regroupees_par_parcelle(db_session):
    parcelle = Plot(code="P-001", name="Parcelle Nkoulou")
    db_session.add(parcelle)
    db_session.flush()
    db_session.add(Device(device_id="AMB-P001", label="Boîtier 1", plot_id=parcelle.id))
    db_session.commit()

    for offset, humidity in enumerate([80.0, 82.0, 84.0]):
        _add_measurement(db_session, "AMB-P001", NOW - 3600 - offset * 86400, humidity)
    db_session.commit()

    kpis = build_kpis(db_session, now=NOW)
    serie = kpis["humidity_series"][0]
    assert serie["plot_id"] == parcelle.id
    assert serie["plot_name"] == "Parcelle Nkoulou"
    assert len(serie["points"]) == 3
    assert kpis["avg_air_humidity_pct"] == pytest.approx(82.0)


def test_volume_sain_utilise_le_volume_de_reference(db_session):
    """Le KPI « volume sain » vaut volume de référence x (1 - indice)."""
    parcelle = Plot(
        code="P-VOL",
        name="Parcelle Volume",
        village="Ambam",
        surface_ha=2.0,
        reference_volume_kg=1000.0,
    )
    db_session.add(parcelle)
    db_session.flush()
    db_session.add(Device(device_id="AMB-P001", plot_id=parcelle.id))
    db_session.commit()

    # 48 h au-dessus de 85 % : indice 60, donc 40 % du volume encore sain.
    _hourly_run(db_session, "AMB-P001", 48, 90.0)
    kpis = build_kpis(db_session, now=NOW)
    assert kpis["global_infestation_index"] == 60
    assert kpis["estimated_healthy_volume_kg"] == pytest.approx(400.0)


def test_volume_sain_nul_sans_volume_de_reference(db_session):
    _hourly_run(db_session, "SIM-001", 48, 90.0)
    assert build_kpis(db_session, now=NOW)["estimated_healthy_volume_kg"] == 0.0


def test_appareil_non_rattache_forme_sa_propre_serie(db_session):
    _add_measurement(db_session, "SIM-001", NOW - 3600, 78.0)
    db_session.commit()

    serie = build_kpis(db_session, now=NOW)["humidity_series"][0]
    assert serie["plot_id"] == 0
    assert serie["plot_name"] == "SIM-001"


def test_filtre_par_parcelle(db_session):
    nord = Plot(code="P-001", name="Nord")
    sud = Plot(code="P-002", name="Sud")
    db_session.add_all([nord, sud])
    db_session.flush()
    db_session.add_all(
        [
            Device(device_id="AMB-P001", plot_id=nord.id),
            Device(device_id="AMB-P002", plot_id=sud.id),
        ]
    )
    db_session.commit()

    _add_measurement(db_session, "AMB-P001", NOW - 3600, 80.0)
    _add_measurement(db_session, "AMB-P002", NOW - 3600, 95.0)
    db_session.commit()

    kpis = build_kpis(db_session, now=NOW, plot_id=nord.id)
    assert kpis["plots_monitored"] == 1
    assert kpis["humidity_series"][0]["plot_name"] == "Nord"
    assert kpis["avg_air_humidity_pct"] == pytest.approx(80.0)


def test_delta_humidite_sur_sept_jours(db_session):
    # Semaine courante à 80 %, semaine précédente à 75 %.
    _add_measurement(db_session, "AMB-P001", NOW - 2 * 86400, 80.0)
    _add_measurement(db_session, "AMB-P001", NOW - 9 * 86400, 75.0)
    db_session.commit()

    kpis = build_kpis(db_session, now=NOW)
    assert kpis["avg_air_humidity_pct"] == pytest.approx(80.0)
    assert kpis["humidity_delta_7d"] == pytest.approx(5.0)


def test_courbe_de_prix_utilise_un_prix_de_reference_constant(db_session):
    _hourly_run(db_session, "AMB-P001", 48, 90.0)
    payload = build_price_forecast(db_session, now=NOW)

    assert payload["unit"] == "FCFA/kg"
    assert payload["is_demo"] is True
    assert payload["formula_version"] == "v1"
    assert payload["horizon_days"] == len(payload["points"]) >= 1
    for point in payload["points"]:
        assert point["reference_price"] == pytest.approx(REFERENCE_PRICE_FCFA_PER_KG)
    # Dernier jour : 48 h au-dessus de 85 % dans la fenêtre glissante -> indice 60.
    assert payload["points"][-1]["adjusted_price"] == pytest.approx(adjust_price(1050.0, 60))


def test_courbe_de_prix_sans_mesure(db_session):
    payload = build_price_forecast(db_session, now=NOW)
    assert payload["points"] == []
    assert payload["horizon_days"] == 0


# --- Routes HTTP -----------------------------------------------------------


def _payload(device_id: str, timestamp: int, humidity: float) -> dict:
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


def test_route_kpis_exige_un_jeton(client):
    assert client.get("/api/v1/kpis").status_code == 401


def test_route_kpis_avec_jeton_acheteur(client, api_headers, buyer_headers):
    maintenant = int(time.time())
    for offset, humidity in [(7200, 80.0), (3600, 86.0)]:
        response = client.post(
            "/api/v1/measurements",
            json=_payload("AMB-P001", maintenant - offset, humidity),
            headers=api_headers,
        )
        assert response.status_code == 201, response.text

    response = client.get("/api/v1/kpis", headers=buyer_headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["plots_monitored"] == 1
    assert body["humidity_series"][0]["plot_name"] == "AMB-P001"
    assert body["avg_air_humidity_pct"] == pytest.approx(83.0)


def test_route_kpis_valide_la_fenetre(client, auth_headers):
    assert client.get("/api/v1/kpis?days=0", headers=auth_headers).status_code == 422
    assert client.get("/api/v1/kpis?days=31", headers=auth_headers).status_code == 422
    assert client.get("/api/v1/kpis?plot_id=0", headers=auth_headers).status_code == 422


def test_route_prix_avec_jeton(client, api_headers, auth_headers):
    response = client.post(
        "/api/v1/measurements",
        json=_payload("AMB-P001", int(time.time()) - 3600, 88.0),
        headers=api_headers,
    )
    assert response.status_code == 201, response.text

    response = client.get("/api/v1/prices/forecast", headers=auth_headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["unit"] == "FCFA/kg"
    assert body["is_demo"] is True
    assert len(body["points"]) == body["horizon_days"] == 1
    assert body["points"][0]["reference_price"] == pytest.approx(REFERENCE_PRICE_FCFA_PER_KG)
