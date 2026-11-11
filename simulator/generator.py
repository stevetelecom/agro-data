"""Génération de mesures JSON conformes au contrat d'échange.

Rôle : simuler le boîtier d'acquisition (température, humidité, diagnostic IA,
horodatage) et produire des mesures horaires au format de
`docs/CONTRAT_JSON.md` §3, prêtes pour `POST /api/v1/measurements`.

Deux niveaux sont fournis :

- `build_measurement()` assemble et valide un message à partir de valeurs
  explicites : contrôle total, utilisé par les scénarios (`scenarios.py`).
- `SensorSimulator` simule un boîtier réel : cycle diurne plausible
  (température culminant l'après-midi, air plus humide la nuit), humidité du
  sol lissée par inertie, bruit de capteur et diagnostic IA corrélé à
  l'humidité prolongée au-dessus de 85 % (règle RM1).

Bibliothèque standard uniquement : le simulateur doit tourner sur le PC de
démonstration sans installation supplémentaire.

Auteur : NTEINTIE Mounpain (MOD-C1).
"""

from __future__ import annotations

import json
import math
import random
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

# Bornes du contrat (docs/CONTRAT_JSON.md §3.2 et §3.3).
DEVICE_ID_MAX_LENGTH = 64
GEO_ENC_MAX_LENGTH = 1024
TEMPERATURE_MIN_C = -10.0
TEMPERATURE_MAX_C = 55.0
HUMIDITY_MIN_PCT = 0.0
HUMIDITY_MAX_PCT = 100.0
CONFIDENCE_MIN = 0.0
CONFIDENCE_MAX = 1.0

# Seuil d'alerte humidité (RM1), identique à `infestation.HUMIDITY_THRESHOLD_PCT`.
HUMIDITY_ALERT_THRESHOLD_PCT = 85.0

# Valeurs par défaut alignées sur l'exemple canonique du contrat (§3.1) :
# boîtier AMB-P001, parcelle d'Ambam (Cameroun).
DEFAULT_DEVICE_ID = "AMB-P001"
DEFAULT_GEO_ENC = "lat:2.383,lon:11.283"


def _as_utc(at: datetime) -> datetime:
    """Renvoie `at` en UTC ; un `datetime` naïf est supposé déjà en UTC."""
    if at.tzinfo is None:
        return at.replace(tzinfo=timezone.utc)
    return at.astimezone(timezone.utc)


def _to_unix_seconds(at: datetime) -> int:
    """Convertit un `datetime` en secondes Unix UTC, entier sans milliseconde."""
    return int(_as_utc(at).timestamp())


def _hour_of_day(at: datetime) -> float:
    """Heure de la journée en fraction (ex. 14,5 pour 14 h 30), en UTC."""
    utc = _as_utc(at)
    return utc.hour + utc.minute / 60.0 + utc.second / 3600.0


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _check_range(field: str, value: float, low: float, high: float) -> None:
    if not low <= value <= high:
        raise ValueError(f"{field} hors plage [{low}, {high}] : {value}")


def _check_device_id(device_id: str) -> None:
    if not isinstance(device_id, str) or not 1 <= len(device_id) <= DEVICE_ID_MAX_LENGTH:
        raise ValueError(
            f"device_id doit être une chaîne de 1 à {DEVICE_ID_MAX_LENGTH} caractères"
        )


def _check_geo_enc(geo_enc: str) -> None:
    if not isinstance(geo_enc, str) or len(geo_enc) > GEO_ENC_MAX_LENGTH:
        raise ValueError(f"geo_enc doit être une chaîne de {GEO_ENC_MAX_LENGTH} caractères maximum")


@dataclass(frozen=True)
class ClimateProfile:
    """Paramètres du modèle climatique du simulateur.

    Le cycle diurne est une sinusoïde sur 24 h : la température culmine à
    `temperature_peak_hour`, l'humidité de l'air à `air_humidity_peak_hour`
    (≈ 5 h du matin, l'air est plus lourd la nuit). Le sol suit l'air avec
    inertie. Les valeurs par défaut décrivent un climat équatorial d'Ambam.
    """

    temperature_mean_c: float = 26.5
    temperature_amplitude_c: float = 4.0
    temperature_peak_hour: float = 15.0
    air_humidity_mean_pct: float = 80.0
    air_humidity_amplitude_pct: float = 10.0
    air_humidity_peak_hour: float = 5.0
    soil_humidity_mean_pct: float = 65.0
    soil_air_coupling: float = 0.4
    soil_smoothing: float = 0.3
    temperature_noise_c: float = 0.3
    air_humidity_noise_pct: float = 1.5
    soil_humidity_noise_pct: float = 0.8

    def __post_init__(self) -> None:
        _check_range("temperature_mean_c", self.temperature_mean_c, TEMPERATURE_MIN_C, TEMPERATURE_MAX_C)
        _check_range("air_humidity_mean_pct", self.air_humidity_mean_pct, HUMIDITY_MIN_PCT, HUMIDITY_MAX_PCT)
        _check_range("soil_humidity_mean_pct", self.soil_humidity_mean_pct, HUMIDITY_MIN_PCT, HUMIDITY_MAX_PCT)
        if self.temperature_amplitude_c < 0 or self.air_humidity_amplitude_pct < 0:
            raise ValueError("les amplitudes du cycle diurne ne peuvent pas être négatives")
        if self.soil_air_coupling < 0:
            raise ValueError("soil_air_coupling ne peut pas être négatif")
        if not 0.0 <= self.soil_smoothing <= 1.0:
            raise ValueError("soil_smoothing doit être compris entre 0 et 1")
        if min(self.temperature_noise_c, self.air_humidity_noise_pct, self.soil_humidity_noise_pct) < 0:
            raise ValueError("les bruits de capteur ne peuvent pas être négatifs")


@dataclass(frozen=True)
class DiagnosticProfile:
    """Paramètres du diagnostic IA simulé (sous-objet `diagnostic_ia`).

    La pourriture brune est favorisée par l'humidité : une fois
    `detection_delay_hours` heures consécutives au-dessus de 85 % (seuil RM1)
    atteintes, la probabilité de détection vaut `detection_rate` ; sinon elle
    retombe à `false_positive_rate`.
    """

    detection_delay_hours: float = 24.0
    detection_rate: float = 0.8
    false_positive_rate: float = 0.02

    def __post_init__(self) -> None:
        if self.detection_delay_hours < 0:
            raise ValueError("detection_delay_hours ne peut pas être négatif")
        if not 0.0 <= self.detection_rate <= 1.0 or not 0.0 <= self.false_positive_rate <= 1.0:
            raise ValueError("les taux de détection doivent être compris entre 0 et 1")


def build_measurement(
    *,
    at: datetime,
    temperature_c: float,
    air_humidity_pct: float,
    soil_humidity_pct: float,
    phytophthora_detected: int,
    confidence: float,
    device_id: str = DEFAULT_DEVICE_ID,
    geo_enc: str = DEFAULT_GEO_ENC,
) -> dict:
    """Assemble et valide un message d'ingestion conforme au contrat §3.

    Toute valeur hors des bornes du contrat déclenche un `ValueError` : le
    simulateur ne doit jamais émettre un message que le backend rejetterait
    (règle RM4). Les réels sont arrondis comme l'exemple canonique : une
    décimale pour le climat, deux pour la confiance.

    :param at: instant de la mesure (`datetime`, naïf = UTC).
    :param phytophthora_detected: `0` sain, `1` détecté (entier, pas booléen).
    """
    _check_device_id(device_id)
    _check_geo_enc(geo_enc)

    temperature_c = round(float(temperature_c), 1)
    air_humidity_pct = round(float(air_humidity_pct), 1)
    soil_humidity_pct = round(float(soil_humidity_pct), 1)
    confidence = round(float(confidence), 2)

    _check_range("climate.temperature_c", temperature_c, TEMPERATURE_MIN_C, TEMPERATURE_MAX_C)
    _check_range("climate.air_humidity_pct", air_humidity_pct, HUMIDITY_MIN_PCT, HUMIDITY_MAX_PCT)
    _check_range("climate.soil_humidity_pct", soil_humidity_pct, HUMIDITY_MIN_PCT, HUMIDITY_MAX_PCT)
    _check_range("diagnostic_ia.confidence", confidence, CONFIDENCE_MIN, CONFIDENCE_MAX)
    if not isinstance(phytophthora_detected, int) or isinstance(phytophthora_detected, bool) or phytophthora_detected not in (0, 1):
        raise ValueError("diagnostic_ia.phytophthora_detected doit être l'entier 0 ou 1")

    return {
        "device_id": device_id,
        "timestamp": _to_unix_seconds(at),
        "climate": {
            "temperature_c": temperature_c,
            "air_humidity_pct": air_humidity_pct,
            "soil_humidity_pct": soil_humidity_pct,
        },
        "diagnostic_ia": {
            "phytophthora_detected": phytophthora_detected,
            "confidence": confidence,
        },
        "geo_enc": geo_enc,
    }


def to_json(measurement: dict) -> str:
    """Sérialise une mesure en JSON UTF-8, corps prêt pour `POST /api/v1/measurements`."""
    return json.dumps(measurement)


class SensorSimulator:
    """Simule un boîtier d'acquisition pour une parcelle.

    Produit des messages conformes au contrat §3 : mesures horaires avec
    cycle diurne plausible, humidité du sol lissée par inertie, bruit de
    capteur et diagnostic IA corrélé à l'humidité prolongée (RM1).

    :param device_id: identifiant du boîtier (contrat §3.2).
    :param geo_enc: métriques en clair, chiffrées côté serveur (1024 car. max).
    :param climate: profil climatique (défaut : cycle diurne d'Ambam).
    :param diagnostic: profil du diagnostic IA simulé.
    :param seed: graine aléatoire pour des séries reproductibles.
    """

    def __init__(
        self,
        device_id: str = DEFAULT_DEVICE_ID,
        geo_enc: str = DEFAULT_GEO_ENC,
        climate: ClimateProfile | None = None,
        diagnostic: DiagnosticProfile | None = None,
        seed: int | None = None,
    ) -> None:
        _check_device_id(device_id)
        _check_geo_enc(geo_enc)
        self._device_id = device_id
        self._geo_enc = geo_enc
        self._climate = climate if climate is not None else ClimateProfile()
        self._diagnostic = diagnostic if diagnostic is not None else DiagnosticProfile()
        self._rng = random.Random(seed)
        self._soil_humidity_pct = self._climate.soil_humidity_mean_pct
        self._hours_above_85 = 0

    def measure(self, at: datetime) -> dict:
        """Retourne la mesure émise par le boîtier à l'instant `at`.

        Les appels doivent se faire par ordre chronologique : l'humidité du
        sol et le compteur d'heures consécutives au-dessus de 85 % sont des
        états internes mis à jour à chaque mesure.
        """
        profile = self._climate
        hour = _hour_of_day(at)

        temperature_c = round(
            _clamp(
                profile.temperature_mean_c
                + profile.temperature_amplitude_c
                * math.cos(2.0 * math.pi * (hour - profile.temperature_peak_hour) / 24.0)
                + self._rng.gauss(0.0, profile.temperature_noise_c),
                TEMPERATURE_MIN_C,
                TEMPERATURE_MAX_C,
            ),
            1,
        )
        air_humidity_pct = round(
            _clamp(
                profile.air_humidity_mean_pct
                + profile.air_humidity_amplitude_pct
                * math.cos(2.0 * math.pi * (hour - profile.air_humidity_peak_hour) / 24.0)
                + self._rng.gauss(0.0, profile.air_humidity_noise_pct),
                HUMIDITY_MIN_PCT,
                HUMIDITY_MAX_PCT,
            ),
            1,
        )
        soil_humidity_pct = round(self._next_soil_humidity(air_humidity_pct), 1)
        detected, confidence = self._next_diagnostic(air_humidity_pct)

        return build_measurement(
            at=at,
            temperature_c=temperature_c,
            air_humidity_pct=air_humidity_pct,
            soil_humidity_pct=soil_humidity_pct,
            phytophthora_detected=detected,
            confidence=confidence,
            device_id=self._device_id,
            geo_enc=self._geo_enc,
        )

    def hourly(self, start: datetime, count: int) -> Iterator[dict]:
        """Produit `count` mesures horaires à partir de `start`.

        Les instants sont alignés sur l'heure pile UTC (minute = seconde = 0)
        : une acquisition par heure, `start` est arrondi à l'heure inférieure.
        Le générateur est paresseux : les mesures sont produites au fil de la
        consommation, ce qui permet de les envoyer ou de les tamponner au fur
        et à mesure (Store-and-Forward, issue #12).
        """
        if count < 1:
            raise ValueError("count doit être supérieur ou égal à 1")
        at = _as_utc(start).replace(minute=0, second=0, microsecond=0)
        for _ in range(count):
            yield self.measure(at)
            at += timedelta(hours=1)

    def _next_soil_humidity(self, air_humidity_pct: float) -> float:
        """Humidité du sol : suit l'air avec inertie (lissage exponentiel)."""
        profile = self._climate
        target = _clamp(
            profile.soil_humidity_mean_pct
            + profile.soil_air_coupling * (air_humidity_pct - profile.air_humidity_mean_pct),
            HUMIDITY_MIN_PCT,
            HUMIDITY_MAX_PCT,
        )
        self._soil_humidity_pct += profile.soil_smoothing * (target - self._soil_humidity_pct)
        return _clamp(
            self._soil_humidity_pct + self._rng.gauss(0.0, profile.soil_humidity_noise_pct),
            HUMIDITY_MIN_PCT,
            HUMIDITY_MAX_PCT,
        )

    def _next_diagnostic(self, air_humidity_pct: float) -> tuple[int, float]:
        """Diagnostic IA simulé, corrélé à l'humidité prolongée (RM1)."""
        if air_humidity_pct > HUMIDITY_ALERT_THRESHOLD_PCT:
            self._hours_above_85 += 1
        else:
            self._hours_above_85 = 0

        profile = self._diagnostic
        p_detect = (
            profile.detection_rate
            if self._hours_above_85 >= profile.detection_delay_hours
            else profile.false_positive_rate
        )
        if self._rng.random() < p_detect:
            return 1, round(self._rng.uniform(0.75, 0.99), 2)
        return 0, round(self._rng.uniform(0.55, 0.97), 2)


def generate_hourly(
    start: datetime,
    count: int,
    *,
    device_id: str = DEFAULT_DEVICE_ID,
    geo_enc: str = DEFAULT_GEO_ENC,
    climate: ClimateProfile | None = None,
    diagnostic: DiagnosticProfile | None = None,
    seed: int | None = None,
) -> Iterator[dict]:
    """Produit `count` mesures horaires conformes au contrat à partir de `start`.

    Raccourci qui instancie un `SensorSimulator` ; voir `SensorSimulator.hourly`
    pour le détail de l'alignement des instants.
    """
    simulator = SensorSimulator(
        device_id=device_id,
        geo_enc=geo_enc,
        climate=climate,
        diagnostic=diagnostic,
        seed=seed,
    )
    return simulator.hourly(start, count)


def _post_measurement(api_url: str, api_key: str, payload: str) -> None:
    """Envoie une mesure à `POST {api_url}/api/v1/measurements`.

    Lève une exception en cas d'erreur HTTP ou réseau : l'appelant
    (tampon Store-and-Forward) décide alors de conserver le message.
    """
    import urllib.request

    request = urllib.request.Request(
        api_url.rstrip("/") + "/api/v1/measurements",
        data=payload.encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-API-Key": api_key,
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        response.read()


def main(argv: list[str] | None = None) -> int:
    """Point d'entrée du simulateur : génère et envoie des mesures au backend.

    Usage::

        python -m simulator.generator --scenario healthy --hours 24 \\
            --api http://localhost:8000 --api-key SECRET

    Scénarios : `healthy`, `critical` (humidité > 85 % prolongée),
    `network` (coupure puis rejeu via le tampon Store-and-Forward).
    `--dry-run` affiche les mesures sur stdout au lieu de les envoyer.
    """
    import argparse
    from datetime import datetime, timezone

    from simulator import scenarios
    from simulator.store_forward import StoreForward

    parser = argparse.ArgumentParser(
        prog="simulator.generator",
        description="Simule le boîtier d'acquisition et envoie les mesures à l'API.",
    )
    parser.add_argument(
        "--scenario",
        choices=["healthy", "critical", "network"],
        default="healthy",
        help="scénario de démonstration (défaut : healthy)",
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="nombre de mesures horaires (défaut : 24)",
    )
    parser.add_argument(
        "--api",
        default="http://localhost:8000",
        help="URL de base de l'API (défaut : http://localhost:8000)",
    )
    parser.add_argument(
        "--api-key",
        default="",
        help="clé d'API appareil (en-tête X-API-Key)",
    )
    parser.add_argument(
        "--spool",
        default="simulator/spool.jsonl",
        help="fichier tampon Store-and-Forward (défaut : simulator/spool.jsonl)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="graine aléatoire pour des mesures reproductibles",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="affiche les mesures JSON au lieu de les envoyer",
    )
    args = parser.parse_args(argv)

    if args.hours < 1:
        parser.error("--hours doit être supérieur ou égal à 1")

    start = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)

    def emit(payload: str, status: str = "") -> None:
        """Affiche ou envoie une mesure sérialisée."""
        if args.dry_run:
            print(f"[{status}] {payload}" if status else payload)
        else:
            _post_measurement(args.api, args.api_key, payload)
            print(f"envoyé ({status})" if status else "envoyé")

    if args.scenario == "network":
        spool = StoreForward(args.spool)
        offline = max(1, args.hours // 3)
        online = args.hours - offline
        events = scenarios.network_outage(
            start,
            offline_hours=offline,
            online_hours=online,
            spool=spool,
            send_fn=None if args.dry_run else lambda p: _post_measurement(args.api, args.api_key, p),
            seed=args.seed,
        )
        for status, measurement in events:
            if status == "live":
                # Seules les mesures « live » ne sont pas déjà prises en
                # charge : buffered/replayed/pending_retry passent par le
                # tampon (send_fn de flush) ou restent en attente.
                emit(to_json(measurement), status)
            elif status == "buffered" and args.dry_run:
                # En dry-run, seul le premier passage affiche le payload :
                # replayed/pending_retry renverraient les mêmes messages.
                print(f"[buffered] {to_json(measurement)}")
            elif args.dry_run:
                print(f"[{status}]")
            else:
                print(status)
    else:
        scenario = scenarios.healthy if args.scenario == "healthy" else scenarios.critical_humidity
        for measurement in scenario(start, args.hours, seed=args.seed):
            emit(to_json(measurement))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
