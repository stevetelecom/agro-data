"""Scénarios de simulation.

Rôle : fournir les scénarios de démonstration du projet :

- `healthy` : climat nominal, aucune détection (PB-01, cas nominal).
- `critical_humidity` : humidité de l'air maintenue au-dessus de 85 %
  pendant plus de 48 h, ce qui déclenche la règle RM1 et les détections
  du diagnostic IA (PB-02).
- `network_outage` : coupure réseau pendant `offline_hours`, les mesures
  sont tamponnées dans un `StoreForward` puis rejouées au retour du
  réseau (PB-03, BNF1/BNF8).

Chaque fonction retourne un itérateur paresseux de messages. Pour les deux
premiers scénarios, chaque élément est une mesure conforme au contrat
§3 (`dict`, voir `generator.to_json` pour la sérialisation). Pour
`network_outage`, chaque élément est un couple `(statut, mesure)` où
`statut` vaut `"buffered"` (tamponné pendant la coupure), `"replayed"`
(renvoyé au retour du réseau) ou `"live"` (émis en direct) ; si `send_fn`
est fourni, les messages rejoués sont réellement passés à l'appelable et
ne sont pas renvoyés dans l'itérateur.

Bibliothèque standard uniquement.

Auteur : Sahoda (MOD-C1).
"""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Callable, Iterator
from datetime import datetime, timedelta

from simulator.generator import (
    DEFAULT_DEVICE_ID,
    DEFAULT_GEO_ENC,
    ClimateProfile,
    DiagnosticProfile,
    SensorSimulator,
)
from simulator.store_forward import StoreForward

# Durée du scénario d'humidité critique : 72 h suffisent à couvrir la
# fenêtre de 48 h de la règle RM1 avec de la marge.
CRITICAL_HUMIDITY_HOURS = 72

# Durée de coupure réseau par défaut pour le scénario `network_outage`.
DEFAULT_OFFLINE_HOURS = 12

# Durée de fonctionnement après rétablissement du réseau.
DEFAULT_ONLINE_HOURS = 24


def _critical_climate() -> ClimateProfile:
    """Profil climatique maintenant l'humidité de l'air au-dessus de 85 %.

    Moyenne 93 % et amplitude 2 % : la valeur reste dans [91, 95] avant
    bruit, ce qui laisse une marge suffisante face au bruit de capteur
    (0,8 %) pour que le compteur d'heures consécutives ne retombe pas sous
    le seuil RM1 pendant les 48 h requises.
    """
    return ClimateProfile(
        temperature_mean_c=27.0,
        temperature_amplitude_c=2.5,
        air_humidity_mean_pct=93.0,
        air_humidity_amplitude_pct=2.0,
        soil_humidity_mean_pct=82.0,
        soil_air_coupling=0.5,
        air_humidity_noise_pct=0.8,
        soil_humidity_noise_pct=0.5,
    )


def _critical_diagnostic() -> DiagnosticProfile:
    """Diagnostic sensible : détection dès 24 h au-dessus du seuil (RM1)."""
    return DiagnosticProfile(
        detection_delay_hours=24.0,
        detection_rate=0.85,
        false_positive_rate=0.01,
    )


def healthy(
    start: datetime,
    count: int,
    *,
    device_id: str = DEFAULT_DEVICE_ID,
    geo_enc: str = DEFAULT_GEO_ENC,
    seed: int | None = None,
) -> Iterator[dict]:
    """Scénario nominal : `count` mesures horaires en climat normal.

    Le profil par défaut d'Ambam maintient l'humidité de l'air autour de
    80 %, sous le seuil de 85 % : pas de détection attendue, hors rares
    faux positifs.

    :param start: instant de la première mesure (aligné sur l'heure UTC).
    :param count: nombre de mesures horaires à produire.
    :param seed: graine pour une série reproductible.
    """
    simulator = SensorSimulator(
        device_id=device_id,
        geo_enc=geo_enc,
        diagnostic=DiagnosticProfile(false_positive_rate=0.01),
        seed=seed,
    )
    return simulator.hourly(start, count)


def critical_humidity(
    start: datetime,
    hours: int = CRITICAL_HUMIDITY_HOURS,
    *,
    device_id: str = DEFAULT_DEVICE_ID,
    geo_enc: str = DEFAULT_GEO_ENC,
    seed: int | None = None,
) -> Iterator[dict]:
    """Scénario d'alerte : humidité > 85 % prolongée, détections RM1 attendues.

    L'humidité de l'air reste au-dessus de 85 % pendant toute la durée,
    donc au-delà des 48 h de la règle RM1. À partir de `detection_delay_hours`
    (24 h par défaut) le diagnostic IA se déclenche avec `detection_rate`.

    :param start: instant de la première mesure.
    :param hours: nombre de mesures horaires (72 h par défaut).
    :param seed: graine pour une série reproductible.
    """
    simulator = SensorSimulator(
        device_id=device_id,
        geo_enc=geo_enc,
        climate=_critical_climate(),
        diagnostic=_critical_diagnostic(),
        seed=seed,
    )
    return simulator.hourly(start, hours)


def network_outage(
    start: datetime,
    offline_hours: int = DEFAULT_OFFLINE_HOURS,
    spool: StoreForward | None = None,
    *,
    online_hours: int = DEFAULT_ONLINE_HOURS,
    send_fn: Callable[[str], None] | None = None,
    device_id: str = DEFAULT_DEVICE_ID,
    geo_enc: str = DEFAULT_GEO_ENC,
    seed: int | None = None,
) -> Iterator[tuple[str, dict]]:
    """Scénario de coupure réseau avec tampon Store-and-Forward.

    Déroulé :

    1. `offline_hours` mesures sont produites puis **tamponnées** dans
       `spool` (fichier JSONL, survivant au redémarrage) ; statut
       `"buffered"`.
    2. Au retour du réseau, `spool.flush(send_fn)` rejoue le tampon dans
       l'ordre d'arrivée ; chaque message accepté est marqué `"replayed"`.
       Sans `send_fn`, les messages sont seulement vidés du tampon et
       signalés `"replayed"` (mode démonstration sans serveur).
    3. Les `online_hours` mesures suivantes sont émises en direct ;
       statut `"live"`.

    :param start: instant de la première mesure.
    :param offline_hours: durée de la coupure en heures de mesures.
    :param spool: tampon à utiliser ; un spool temporaire est créé si `None`.
    :param online_hours: durée après rétablissement du réseau.
    :param send_fn: appelable d'envoi `payload JSON -> None` (ex.
        `requests.post(...).raise_for_status`) ; `None` = pas de réseau.
    :param seed: graine pour une série reproductible.
    """
    owns_spool = spool is None
    if owns_spool:
        fd, tmp_path = tempfile.mkstemp(prefix="agro_spool_", suffix=".jsonl")
        os.close(fd)
        spool = StoreForward(tmp_path)

    simulator = SensorSimulator(
        device_id=device_id,
        geo_enc=geo_enc,
        diagnostic=DiagnosticProfile(false_positive_rate=0.01),
        seed=seed,
    )

    try:
        # Phase 1 : coupure réseau, tout est tamponné.
        for measurement in simulator.hourly(start, offline_hours):
            spool.buffer(json.dumps(measurement))
            yield "buffered", measurement

        # Phase 2 : retour du réseau, rejeu du tampon puis flux direct.
        flushed = spool.flush(send_fn)
        for payload in flushed.sent:
            yield "replayed", json.loads(payload)
        for payload in flushed.pending:
            # Messages non renvoyés (send_fn en échec) : on les re-tamponne
            # déjà fait par flush ; on les signale sans les perdre.
            yield "pending_retry", json.loads(payload)

        # Reprendre après la coupure : `hourly` aligne sur l'heure, on
        # décale explicitement pour enchaîner sans trou ni chevauchement.
        online_start = start + timedelta(hours=offline_hours)
        for measurement in simulator.hourly(online_start, online_hours):
            yield "live", measurement
    finally:
        if owns_spool:
            try:
                spool.path.unlink(missing_ok=True)
            except OSError:
                pass
