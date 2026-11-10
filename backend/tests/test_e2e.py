"""Test de bout en bout de la chaîne AGRO-DATA (issue #20).

Rôle : vérifier le scénario de démonstration reproductible, sans dépendance
externe, du boîtier simulé jusqu'au tableau de bord :

    ingestion JSON -> Data Lake -> diagnostic IA -> KPIs -> courbe de prix

Chaque étape passe par les routes HTTP réelles, avec les mêmes en-têtes que le
boîtier et le tableau de bord. Le test couvre les critères 1, 3, 4, 5 et 6 du
cahier des charges §17.
Auteur : MEKONTSO Olivier Steve (MOD-G1, issue #20).
"""

from __future__ import annotations

import time
from pathlib import Path

from app.config import get_settings

# Image PNG minimale (en-tête magique + contenu) : suffisant pour le prototype.
PNG = b"\x89PNG\r\n\x1a\n" + b"cabosse-e2e"
HORLOGE = int(time.time())


def _mesure(device_id: str, timestamp: int, humidite: float, detecte: int = 0) -> dict:
    return {
        "device_id": device_id,
        "timestamp": timestamp,
        "climate": {
            "temperature_c": 27.0,
            "air_humidity_pct": humidite,
            "soil_humidity_pct": 61.0,
        },
        "diagnostic_ia": {"phytophthora_detected": detecte, "confidence": 0.9},
        "geo_enc": "lat:2.383,lon:11.283",
    }


def _ingerer_48h(client, api_headers, device_id: str = "E2E-AMB-01") -> None:
    """Ingère 48 mesures horaires à 90 % d'humidité, terminant il y a une heure."""
    for offset in range(48):
        timestamp = HORLOGE - (offset + 1) * 3600
        response = client.post(
            "/api/v1/measurements",
            json=_mesure(device_id, timestamp, 90.0),
            headers=api_headers,
        )
        assert response.status_code == 201, response.text


def test_scenario_complet_de_demonstration(client, api_headers, auth_headers):
    # 1. Ingestion : les 48 mesures sont acceptées et horodatées dans le passé.
    _ingerer_48h(client, api_headers)

    # 2. Data Lake : la zone brute contient un fichier par mesure, sans geo_enc en clair.
    brut = Path(get_settings().data_lake_dir) / "raw"
    fichiers = sorted(brut.glob("E2E-AMB-01_*.json"))
    assert len(fichiers) == 48, f"{len(fichiers)} fichiers bruts au lieu de 48"
    contenu = fichiers[-1].read_text(encoding="utf-8")
    assert "lat:2.383" not in contenu
    assert "air_humidity_pct" in contenu

    # 3. Diagnostic IA : image valide -> drapeau binaire + confiance, mode démo assumé.
    diagnostic = client.post(
        "/api/v1/diagnostic",
        files={"image": ("cabosse.png", PNG, "image/png")},
        headers=auth_headers,
    )
    assert diagnostic.status_code == 200, diagnostic.text
    resultat = diagnostic.json()
    assert resultat["phytophthora_detected"] in (0, 1)
    assert 0.0 <= resultat["confidence"] <= 1.0
    assert resultat["is_demo"] is True

    # 4. KPIs : l'alerte RM1 se déclenche et l'indice reflète les 48 h > 85 %.
    kpis = client.get("/api/v1/kpis", headers=auth_headers)
    assert kpis.status_code == 200, kpis.text
    indicateurs = kpis.json()
    assert indicateurs["active_alerts"] == 1
    assert indicateurs["humidity_series"][0]["under_alert"] is True
    assert indicateurs["global_infestation_index"] >= 60
    assert indicateurs["level"] in ("modere", "eleve")
    assert indicateurs["plots_monitored"] == 1

    # 5. Courbe de prix : ajustée à la hausse, explicitement de démonstration.
    prix = client.get("/api/v1/prices/forecast", headers=auth_headers)
    assert prix.status_code == 200, prix.text
    courbe = prix.json()
    assert courbe["is_demo"] is True
    assert courbe["formula_version"] == "v1"
    assert courbe["points"], "la courbe doit contenir au moins un point"
    dernier = courbe["points"][-1]
    assert dernier["adjusted_price"] > dernier["reference_price"]


def test_rejet_d_une_mesure_malveillante_puis_ingestion_normale(
    client, api_headers, auth_headers
):
    """Critère 6 : une entrée invalide est rejetée sans casser la chaîne."""
    invalide = _mesure("../etc/passwd", HORLOGE - 60, 90.0)
    response = client.post("/api/v1/measurements", json=invalide, headers=api_headers)
    assert response.status_code == 422

    # La chaîne reste utilisable après le rejet.
    _ingerer_48h(client, api_headers, device_id="E2E-AMB-02")
    kpis = client.get("/api/v1/kpis", headers=auth_headers)
    assert kpis.status_code == 200, kpis.text
    assert kpis.json()["plots_monitored"] == 1

    # Une lecture sans jeton est refusée (critère 6).
    assert client.get("/api/v1/kpis").status_code == 401
