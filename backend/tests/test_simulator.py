"""Tests du simulateur et du Store-and-Forward (issues #6, #12, #19).

Rôle : vérifier que les messages produits sont acceptés par le contrat, que le
scénario « humidité critique » déclenche bien l'alerte RM1 et que les mesures
produites hors ligne sont renvoyées une seule fois au retour du réseau
(critère §17.2 du cahier des charges).

Auteur : MEKONTSO Olivier Steve (SM) — reprend le bloc C non livré.
"""

from __future__ import annotations

import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[2]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from app.schemas.measurement import MeasurementCreate  # noqa: E402
from app.config import get_settings  # noqa: E402
from simulator.generator import (  # noqa: E402
    PermanentSendError,
    TransientSendError,
    build_measurement,
    hourly_series,
    send_measurement,
)
from simulator.scenarios import (  # noqa: E402
    ALERT_HOURS,
    HUMIDITE_CRITIQUE,
    SAIN,
    build_scenario,
    consecutive_hours_above,
)
from simulator.store_forward import StoreAndForward  # noqa: E402

DEBUT = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0) - timedelta(hours=70)


def test_message_conforme_au_contrat() -> None:
    """Le générateur produit exactement les champs du contrat §3."""
    payload = build_measurement(
        "AMB-P001",
        DEBUT,
        temperature_c=27.4,
        air_humidity_pct=88.2,
        soil_humidity_pct=61.0,
    )

    assert payload["timestamp"] == int(DEBUT.timestamp())
    assert payload["climate"] == {
        "temperature_c": 27.4,
        "air_humidity_pct": 88.2,
        "soil_humidity_pct": 61.0,
    }
    assert payload["diagnostic_ia"] == {"phytophthora_detected": 0, "confidence": 0.93}
    # Le schéma Pydantic est la référence exécutable du contrat.
    MeasurementCreate.model_validate(payload)


def test_message_invalide_refuse_avant_envoi() -> None:
    """Une valeur hors plage physique est refusée côté boîtier, pas côté serveur."""
    with pytest.raises(ValueError, match="air_humidity_pct"):
        build_measurement(
            "AMB-P001",
            DEBUT,
            temperature_c=27.0,
            air_humidity_pct=140.0,
            soil_humidity_pct=60.0,
        )


def test_serie_horaire_espacee_dune_heure() -> None:
    """La série respecte la fréquence demandée et l'appareil configuré."""
    serie = hourly_series(DEBUT, 4, device_id="AMB-P042", step_minutes=60, seed=1)

    assert [point["timestamp"] for point in serie] == [int(DEBUT.timestamp()) + 3600 * i for i in range(4)]
    assert {point["device_id"] for point in serie} == {"AMB-P042"}


def test_scenario_sain_ne_declenche_aucune_alerte() -> None:
    """Humidité sous 85 % : aucune heure consécutive au-dessus du seuil."""
    run = build_scenario(SAIN, hours=72, start=DEBUT)

    assert len(run.measurements) == 72
    assert consecutive_hours_above(run.measurements) == 0
    assert all(m["climate"]["air_humidity_pct"] < 85 for m in run.measurements)


def test_scenario_humidite_critique_declenche_rm1() -> None:
    """Le scénario critique dépasse 48 h au-dessus de 85 % et détecte la maladie."""
    run = build_scenario(HUMIDITE_CRITIQUE, hours=60, start=DEBUT)

    assert len(run.measurements) == 60
    assert consecutive_hours_above(run.measurements) > ALERT_HOURS
    assert any(m["diagnostic_ia"]["phytophthora_detected"] == 1 for m in run.measurements)
    for mesure in run.measurements:
        MeasurementCreate.model_validate(mesure)


def test_scenario_inconnu_refuse() -> None:
    """Un nom de scénario inconnu échoue explicitement."""
    with pytest.raises(ValueError, match="scénario inconnu"):
        build_scenario("ouragan", hours=10)


def test_tampon_persiste_et_dedoublonne(tmp_path: Path) -> None:
    """Le tampon survit à la réouverture et n'accepte pas deux fois la même mesure."""
    chemin = tmp_path / "buffer.jsonl"
    mesure = build_measurement(
        "AMB-P001",
        DEBUT,
        temperature_c=27.0,
        air_humidity_pct=80.0,
        soil_humidity_pct=60.0,
    )

    tampon = StoreAndForward(chemin)
    assert tampon.enqueue(mesure) is True
    assert tampon.enqueue(mesure) is False
    assert len(StoreAndForward(chemin)) == 1


def test_reprise_apres_coupure_envoie_tout_une_seule_fois(tmp_path: Path) -> None:
    """Scénario §17.2 : 24 h hors ligne, puis reprise complète et sans doublon."""
    run = build_scenario("coupure_reseau", hours=48, start=DEBUT)
    assert run.offline_count == 24

    envoyees: list[dict] = []

    def reseau_coupe(_payload: dict) -> None:
        raise TransientSendError("WiFi indisponible")

    tampon = StoreAndForward(tmp_path / "buffer.jsonl", sender=reseau_coupe)
    assert tampon.enqueue_many(run.offline_measurements()) == 24
    assert len(tampon) == 24

    premier = tampon.flush()
    assert premier.sent == 0
    assert premier.remaining == 24
    assert "WiFi" in premier.error

    rapport = tampon.flush(sender=envoyees.append)
    assert rapport.sent == 24
    assert rapport.remaining == 0
    assert rapport.complete is True
    assert [m["timestamp"] for m in envoyees] == sorted(m["timestamp"] for m in envoyees)
    assert len(tampon) == 0

    # Deuxième passage : plus rien à envoyer, donc aucun risque de doublon.
    assert tampon.flush(sender=envoyees.append).sent == 0
    assert len(envoyees) == 24


def test_echec_temporaire_conserve_lordre(tmp_path: Path) -> None:
    """Un échec au milieu du tampon arrête l'envoi et laisse la suite en attente."""
    tampon = StoreAndForward(tmp_path / "buffer.jsonl")
    serie = hourly_series(DEBUT, 5, humidity=80.0, seed=3)
    tampon.enqueue_many(serie)

    appels: list[int] = []

    def parfois_coupe(payload: dict) -> None:
        if len(appels) == 2:
            raise TransientSendError("coupure brève")
        appels.append(payload["timestamp"])

    rapport = tampon.flush(sender=parfois_coupe)
    assert rapport.sent == 2
    assert rapport.remaining == 3
    assert [m["timestamp"] for m in tampon.pending()] == [m["timestamp"] for m in serie[2:]]


def test_refus_definitif_retire_la_mesure(tmp_path: Path) -> None:
    """Un 422 (doublon ou mesure invalide) ne doit pas bloquer la file pour toujours."""
    tampon = StoreAndForward(tmp_path / "buffer.jsonl")
    tampon.enqueue_many(hourly_series(DEBUT, 2, humidity=80.0, seed=4))

    def refuse(payload: dict) -> None:
        if payload["timestamp"] == int(DEBUT.timestamp()):
            raise PermanentSendError("HTTP 422 : doublon")

    rapport = tampon.flush(sender=refuse)
    assert rapport.sent == 1
    assert rapport.rejected == 1
    assert rapport.remaining == 0
    assert "doublon" in rapport.details[0]


def test_api_refuse_un_doublon_mais_accepte_la_reprise(client, api_headers, auth_headers, tmp_path) -> None:
    """Le backend protège la reprise : rejouer une mesure répond 422, sans doublon."""
    run = build_scenario("coupure_reseau", hours=8, start=DEBUT)

    def envoyer(payload: dict) -> None:
        reponse = client.post("/api/v1/measurements", json=payload, headers=api_headers)
        if reponse.status_code in (401, 403, 422):
            raise PermanentSendError(reponse.text[:200])
        if reponse.status_code >= 500 or reponse.status_code == 429:
            raise TransientSendError(reponse.text[:200])

    tampon = StoreAndForward(tmp_path / "buffer.jsonl", sender=envoyer)

    for payload in run.measurements:
        assert tampon.enqueue(payload) is True
    premier = tampon.flush()
    assert premier.sent == len(run.measurements)

    # Toutes les mesures sont dans l'API, une seule fois chacune.
    reponse = client.get("/api/v1/measurements", params={"device_id": run.measurements[0]["device_id"]}, headers=auth_headers)
    assert reponse.status_code == 200
    assert len(reponse.json()) == len(run.measurements)

    # Rejeu volontaire de la même heure : refusée proprement, rien n'est ajouté.
    rejeu = StoreAndForward(tmp_path / "rejeu.jsonl", sender=envoyer)
    rejeu.enqueue(run.measurements[-1])
    rapport = rejeu.flush()
    assert rapport.rejected == 1
    assert rapport.remaining == 0
    apres = client.get("/api/v1/measurements", params={"device_id": run.measurements[0]["device_id"]}, headers=auth_headers)
    assert len(apres.json()) == len(run.measurements)


def test_envoi_http_vers_backend_injoignable_est_temporaire() -> None:
    """Un port fermé est un échec temporaire : la mesure doit rester en file."""
    payload = build_measurement(
        "AMB-P001",
        datetime.now(timezone.utc),
        temperature_c=27.0,
        air_humidity_pct=80.0,
        soil_humidity_pct=60.0,
    )
    with pytest.raises(TransientSendError):
        send_measurement(payload, api_base="http://127.0.0.1:9", api_key=get_settings().device_api_key, timeout=1.0)


def test_horodatage_en_secondes_unix() -> None:
    """Le contrat exige des secondes entières, pas des millisecondes."""
    payload = build_measurement(
        "AMB-P001",
        datetime(2026, 11, 10, 11, 0, tzinfo=timezone.utc),
        temperature_c=27.0,
        air_humidity_pct=80.0,
        soil_humidity_pct=60.0,
    )
    assert payload["timestamp"] == 1794308400
    assert payload["timestamp"] < int(time.time() * 10)
