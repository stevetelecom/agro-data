"""Scénarios de simulation.

Rôle : fournir les trois situations demandées par l'issue #6 — parcelle saine,
humidité critique (> 85 % pendant plus de 48 h, RM1) et coupure réseau — pour
que la démonstration et les tests n'inventent pas de données à la main.

Auteur : NTEINTIE Mounpain (MOD-C1) — implémentation reprise par
MEKONTSO Olivier Steve (SM) après l'absence de livraison du bloc C.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from simulator.generator import (
    DEFAULT_DEVICE_ID,
    hourly_series,
)

# Seuils du cahier des charges (RM1) : 85 % pendant 48 h consécutives.
HUMIDITY_ALERT = 85.0
ALERT_HOURS = 48

SAIN = "sain"
HUMIDITE_CRITIQUE = "humidite_critique"
COUPURE_RESEAU = "coupure_reseau"
SCENARIOS = (SAIN, HUMIDITE_CRITIQUE, COUPURE_RESEAU)


@dataclass(frozen=True)
class ScenarioRun:
    """Résultat d'un scénario.

    Attributes:
        name: nom du scénario (voir ``SCENARIOS``).
        description: ce que la série doit démontrer.
        measurements: messages conformes au contrat, du plus ancien au plus récent.
        offline_count: nombre de mesures produites **hors ligne** ; elles doivent
            passer par le tampon local avant d'atteindre l'API (scénario coupure).
    """

    name: str
    description: str
    measurements: list[dict]
    offline_count: int = 0

    def online_measurements(self) -> list[dict]:
        """Mesures produites une fois le réseau revenu."""
        return self.measurements[self.offline_count :]

    def offline_measurements(self) -> list[dict]:
        """Mesures à conserver dans le tampon local."""
        return self.measurements[: self.offline_count]


def _start(when: datetime | None, count: int) -> datetime:
    """Retourne la première heure de la série, arrondie à l'heure pleine UTC.

    Sans instant explicite, la série **se termine à l'heure courante** : une
    démonstration en direct doit produire des mesures acceptées par l'API, qui
    refuse tout horodatage situé à plus de 300 s dans le futur.
    """
    if when is not None:
        base = when if when.tzinfo else when.replace(tzinfo=timezone.utc)
        return base.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)
    fin = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    return fin - timedelta(hours=max(0, count - 1))


def _sain(start: datetime | None, device_id: str, hours: int) -> ScenarioRun:
    """Parcelle saine : humidité sous le seuil, aucune détection."""
    debut = _start(start, hours)
    measurements = hourly_series(
        debut,
        hours,
        device_id=device_id,
        humidity=lambda index: 74.0 + 1.5 * ((index % 12) / 11),
        temperature=lambda index: 26.5 + 1.0 * ((index % 24) / 23),
        soil_humidity=lambda index: 58.0 + 2.0 * ((index % 8) / 7),
        seed=11,
    )
    return ScenarioRun(
        SAIN,
        "Humidité entre 74 et 76 %, pas de détection : aucune alerte attendue.",
        measurements,
    )


def _humidite_critique(start: datetime | None, device_id: str, hours: int) -> ScenarioRun:
    """Humidité critique : plus de 48 h au-dessus de 85 %, puis détections."""
    seuil = max(ALERT_HOURS + 12, hours)
    debut = _start(start, seuil)

    def humidite(index: int) -> float:
        # 88 % dès le début, pour dépasser le seuil de 48 h avant la fin.
        return 88.0 + 2.0 * ((index % 6) / 5)

    def detection(index: int) -> tuple[int, float]:
        # Les premières heures sont humides sans symptôme visible, puis la
        # pourriture brune apparaît : c'est ce que montre la démonstration.
        return (1, 0.88) if index >= 6 else (0, 0.9)

    measurements = hourly_series(
        debut,
        seuil,
        device_id=device_id,
        humidity=humidite,
        temperature=lambda index: 27.5 + 0.5 * ((index % 5) / 4),
        soil_humidity=lambda index: 68.0 + 2.0 * ((index % 6) / 5),
        detection=detection,
        seed=23,
    )
    return ScenarioRun(
        HUMIDITE_CRITIQUE,
        f"Humidité au-dessus de 85 % pendant {seuil} h : alerte RM1 attendue.",
        measurements,
    )


def _coupure_reseau(start: datetime | None, device_id: str, hours: int) -> ScenarioRun:
    """Coupure réseau : 24 h hors ligne, puis retour du réseau.

    Les mesures hors ligne sont produites normalement mais restent dans le
    tampon local ; le Store-and-Forward les renvoie à la reconnexion, dans
    l'ordre, sans doublon.
    """
    total = max(48, hours)
    hors_ligne = min(24, total // 2)
    debut = _start(start, total)

    def humidite(index: int) -> float:
        return 86.0 if index >= hors_ligne else 80.0

    measurements = hourly_series(
        debut,
        total,
        device_id=device_id,
        humidity=humidite,
        temperature=lambda index: 27.0,
        soil_humidity=lambda index: 62.0,
        seed=37,
    )
    return ScenarioRun(
        COUPURE_RESEAU,
        f"{hors_ligne} h enregistrées hors ligne puis renvoyées au retour du réseau.",
        measurements,
        offline_count=hors_ligne,
    )


def build_scenario(
    name: str,
    *,
    device_id: str = DEFAULT_DEVICE_ID,
    hours: int = 72,
    start: datetime | None = None,
) -> ScenarioRun:
    """Construit un scénario prêt à être envoyé.

    Args:
        name: ``sain``, ``humidite_critique`` ou ``coupure_reseau``.
        device_id: identifiant de l'appareil simulé.
        hours: durée visée ; le scénario critique impose au moins 60 h pour
            franchir le seuil RM1, la coupure au moins 48 h.
        start: première mesure de la série ; par défaut la série se termine à
            l'heure courante (horodatages acceptés par l'API).

    Raises:
        ValueError: nom de scénario inconnu ou durée invalide.
    """
    if name not in SCENARIOS:
        raise ValueError(f"scénario inconnu : {name!r} (attendu : {', '.join(SCENARIOS)})")
    if hours < 1:
        raise ValueError("hours doit être >= 1")

    builders = {
        SAIN: _sain,
        HUMIDITE_CRITIQUE: _humidite_critique,
        COUPURE_RESEAU: _coupure_reseau,
    }
    return builders[name](start, device_id, hours)


def consecutive_hours_above(measurements: list[dict], seuil: float = HUMIDITY_ALERT) -> int:
    """Compte les heures consécutives au-dessus du seuil, depuis la fin.

    Reproduit la règle RM1 telle que l'appliquent le backend et le dashboard :
    dès qu'une heure redescend sous le seuil, le décompte s'arrête.
    """
    heures = 0
    for mesure in reversed(measurements):
        if mesure["climate"]["air_humidity_pct"] > seuil:
            heures += 1
        else:
            break
    return heures


def is_alerting(name: str, **kwargs) -> bool:
    """Indique si le scénario franchit le seuil RM1 (utile aux tests et à la démo)."""
    run = build_scenario(name, **kwargs)
    return consecutive_hours_above(run.measurements) > ALERT_HOURS


def next_hour(when: datetime | None = None) -> datetime:
    """Retourne l'heure pleine suivante, pour espacer deux exécutions de démo."""
    return _start(when, 1) + timedelta(hours=1)
