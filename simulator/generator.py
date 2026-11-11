"""Génération de mesures JSON conformes au contrat d'échange.

Rôle : simuler le boîtier d'acquisition (température, humidité de l'air et du
sol, diagnostic IA, horodatage) et remplacer le matériel quand il est
indisponible (plan de codage §8). Chaque message produit ici est accepté tel
quel par ``POST /api/v1/measurements`` (``docs/CONTRAT_JSON.md`` §3).

Auteur : NTEINTIE Mounpain (MOD-C1) — implémentation reprise par
MEKONTSO Olivier Steve (SM) après l'absence de livraison du bloc C.
"""

from __future__ import annotations

import json
import random
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Callable, Iterable

DEFAULT_DEVICE_ID = "AMB-P001"
DEFAULT_GEO_ENC = "lat:2.383,lon:11.283"
DEFAULT_API_BASE = "http://127.0.0.1:8000"
DEFAULT_API_KEY = "agro-device-demo-key"

# Bornes physiques du contrat (§3.3) : au-delà, le backend rejette en 422.
MIN_TEMPERATURE_C = -10.0
MAX_TEMPERATURE_C = 55.0


class SendError(Exception):
    """Échec d'envoi vers l'API."""


class TransientSendError(SendError):
    """Échec temporaire (réseau coupé, 5xx, 429) : la mesure doit rester en file."""


class PermanentSendError(SendError):
    """Échec définitif (422, 401) : renvoyer le même message ne servira à rien."""


def to_unix(when: datetime) -> int:
    """Convertit une date en secondes Unix UTC, comme l'exige le contrat.

    Une date sans fuseau est interprétée comme UTC : le boîtier n'a pas d'heure
    locale fiable en forêt.
    """
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return int(when.astimezone(timezone.utc).timestamp())


def build_measurement(
    device_id: str,
    when: datetime,
    *,
    temperature_c: float,
    air_humidity_pct: float,
    soil_humidity_pct: float,
    phytophthora_detected: int = 0,
    confidence: float = 0.93,
    geo_enc: str = DEFAULT_GEO_ENC,
) -> dict:
    """Assemble un message d'ingestion et vérifie les bornes du contrat.

    Lève ``ValueError`` plutôt que d'envoyer au backend un message qui serait
    rejeté : le simulateur sert aussi à prouver que le contrat est respecté.

    Args:
        device_id: identifiant de l'appareil (``^[A-Za-z0-9._-]{1,64}$``).
        when: instant de la mesure.
        temperature_c: température de l'air, en °C.
        air_humidity_pct: humidité de l'air, en %.
        soil_humidity_pct: humidité du sol, en %.
        phytophthora_detected: ``1`` si la pourriture brune est détectée.
        confidence: probabilité du diagnostic, entre 0 et 1.
        geo_enc: métriques géospatiales, chiffrées côté serveur.

    Returns:
        Le message prêt à être sérialisé en JSON.
    """
    if not device_id or len(device_id) > 64:
        raise ValueError(f"device_id invalide : {device_id!r}")
    if not MIN_TEMPERATURE_C <= temperature_c <= MAX_TEMPERATURE_C:
        raise ValueError(
            f"temperature_c hors plage [{MIN_TEMPERATURE_C}, {MAX_TEMPERATURE_C}] : {temperature_c}"
        )
    for nom, valeur in (("air_humidity_pct", air_humidity_pct), ("soil_humidity_pct", soil_humidity_pct)):
        if not 0 <= valeur <= 100:
            raise ValueError(f"{nom} hors plage [0, 100] : {valeur}")
    if phytophthora_detected not in (0, 1):
        raise ValueError(f"phytophthora_detected doit valoir 0 ou 1 : {phytophthora_detected}")
    if not 0 <= confidence <= 1:
        raise ValueError(f"confidence hors plage [0, 1] : {confidence}")
    if len(geo_enc) > 1024:
        raise ValueError("geo_enc dépasse 1024 caractères")

    return {
        "device_id": device_id,
        "timestamp": to_unix(when),
        "climate": {
            "temperature_c": round(float(temperature_c), 1),
            "air_humidity_pct": round(float(air_humidity_pct), 1),
            "soil_humidity_pct": round(float(soil_humidity_pct), 1),
        },
        "diagnostic_ia": {
            "phytophthora_detected": int(phytophthora_detected),
            "confidence": round(float(confidence), 2),
        },
        "geo_enc": geo_enc,
    }


def hourly_series(
    start: datetime,
    hours: int,
    *,
    device_id: str = DEFAULT_DEVICE_ID,
    humidity: Callable[[int], float] | float = 76.0,
    temperature: Callable[[int], float] | float = 27.0,
    soil_humidity: Callable[[int], float] | float = 61.0,
    detection: Callable[[int], tuple[int, float]] | None = None,
    step_minutes: int = 60,
    seed: int | None = None,
) -> list[dict]:
    """Produit une série de mesures régulièrement espacées.

    Args:
        start: première mesure.
        hours: nombre de mesures à produire.
        device_id: identifiant de l'appareil émetteur.
        humidity: humidité de l'air, valeur fixe ou fonction de l'index.
        temperature: température, valeur fixe ou fonction de l'index.
        soil_humidity: humidité du sol, valeur fixe ou fonction de l'index.
        detection: fonction ``index -> (detecte, confiance)`` du diagnostic IA.
        step_minutes: intervalle entre deux mesures (60 = horaire).
        seed: graine du bruit de mesure ; ``None`` pour un bruit non reproductible.

    Returns:
        La liste des messages, dans l'ordre chronologique.
    """
    if hours < 1:
        raise ValueError("hours doit être >= 1")
    if step_minutes < 1:
        raise ValueError("step_minutes doit être >= 1")

    rng = random.Random(seed)
    valeurs = {
        "humidity": humidity if callable(humidity) else lambda _index: humidity,
        "temperature": temperature if callable(temperature) else lambda _index: temperature,
        "soil_humidity": soil_humidity if callable(soil_humidity) else lambda _index: soil_humidity,
    }

    series: list[dict] = []
    for index in range(hours):
        detecte, confiance = detection(index) if detection else (0, 0.93)
        series.append(
            build_measurement(
                device_id,
                start + timedelta(minutes=step_minutes * index),
                temperature_c=valeurs["temperature"](index) + rng.uniform(-0.4, 0.4),
                air_humidity_pct=valeurs["humidity"](index) + rng.uniform(-0.6, 0.6),
                soil_humidity_pct=valeurs["soil_humidity"](index) + rng.uniform(-0.8, 0.8),
                phytophthora_detected=detecte,
                confidence=min(1.0, max(0.0, confiance + rng.uniform(-0.02, 0.02))),
            )
        )
    return series


def send_measurement(
    payload: dict,
    *,
    api_base: str = DEFAULT_API_BASE,
    api_key: str = DEFAULT_API_KEY,
    timeout: float = 10.0,
) -> int:
    """Envoie une mesure au backend et renvoie le code HTTP.

    Raises:
        PermanentSendError: le backend refuse le message (4xx autre que 429) ;
            le renvoyer à l'identique ne changera rien.
        TransientSendError: réseau coupé, 5xx ou 429 ; la mesure doit rester
            dans le tampon local (Store-and-Forward).
    """
    url = f"{api_base.rstrip('/')}/api/v1/measurements"
    requete = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-API-Key": api_key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(requete, timeout=timeout) as reponse:
            return reponse.status
    except urllib.error.HTTPError as erreur:
        detail = erreur.read().decode("utf-8", "replace")[:300]
        if erreur.code == 429 or erreur.code >= 500:
            raise TransientSendError(f"HTTP {erreur.code} : {detail}") from erreur
        raise PermanentSendError(f"HTTP {erreur.code} : {detail}") from erreur
    except (urllib.error.URLError, TimeoutError, OSError) as erreur:
        raise TransientSendError(f"backend injoignable : {erreur}") from erreur


def send_many(
    payloads: Iterable[dict],
    *,
    api_base: str = DEFAULT_API_BASE,
    api_key: str = DEFAULT_API_KEY,
    timeout: float = 10.0,
) -> int:
    """Envoie une série de mesures et renvoie le nombre accepté.

    S'arrête au premier échec temporaire : l'ordre chronologique compte pour
    les indicateurs, on ne saute pas une heure pour en envoyer une plus récente.
    """
    envoyees = 0
    for payload in payloads:
        send_measurement(payload, api_base=api_base, api_key=api_key, timeout=timeout)
        envoyees += 1
    return envoyees
