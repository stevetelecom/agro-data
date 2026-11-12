"""Agrégation des mesures pour le tableau de bord.

Rôle : transformer les mesures persistées en indicateurs du contrat §4.4
(`GET /api/v1/kpis`) et en courbe de prix §4.5 (`GET /api/v1/prices/forecast`).

Les formules métier restent dans `infestation.py` (RM2, RM1) et `pricing.py`
(RM3, RM5) : ce module ne fait que lire la base, regrouper par parcelle et
alimenter ces fonctions. Il est testable avec une session SQLAlchemy.

Rattachement des mesures : une mesure est reliée à une parcelle par son
`device_id` via la table `devices`. Un appareil inconnu ou non rattaché forme
son propre groupe (`plot_id = 0`, `plot_name = device_id`), pour que le
simulateur soit utilisable sans créer d'appareil au préalable.

Auteur : MEKONTSO Olivier Steve (MOD-A4, issue #13).
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Device, Measurement, Plot
from app.services.infestation import (
    ALERT_DURATION_HOURS,
    HUMIDITY_THRESHOLD_PCT,
    aggregate_index,
    compute_infestation_index,
    estimated_healthy_volume_pct,
    is_alert,
    level_for,
)
from app.services.pricing import (
    REFERENCE_PRICE_FCFA_PER_KG,
    build_forecast,
    forecast_payload,
)

# Une mesure est horaire : on tolère un trou d'une heure avant de casser une
# série d'humidité consécutive.
MAX_GAP_SECONDS = 2 * 3600
SECONDS_PER_DAY = 24 * 3600
# Fenêtre glissante d'évaluation de l'alerte RM1 (48 h).
ALERT_WINDOW_SECONDS = int(ALERT_DURATION_HOURS * 3600)


@dataclass
class PlotMetrics:
    """Indicateurs d'une parcelle sur la fenêtre d'analyse."""

    plot_id: int
    plot_name: str
    hours_above_85: float
    ia_detection_rate: float
    index: int
    under_alert: bool
    rows: list[Measurement] = field(default_factory=list)


def longest_run_hours(
    timestamps: list[int],
    humidities: list[float],
    threshold: float = HUMIDITY_THRESHOLD_PCT,
) -> float:
    """Durée de la plus longue série consécutive au-dessus du seuil, en heures.

    Chaque mesure couvre l'heure qui la suit : une série de 48 mesures
    horaires consécutives vaut 48 h. Un trou de plus de deux heures casse la
    série (mesures manquantes ou appareil hors ligne).
    """
    couples = sorted(zip(timestamps, humidities))
    meilleure = 0.0
    debut: int | None = None
    precedent: int | None = None

    for horodatage, humidite in couples:
        if humidite <= threshold:
            debut = None
            precedent = horodatage
            continue

        if debut is None or (precedent is not None and horodatage - precedent > MAX_GAP_SECONDS):
            debut = horodatage
        precedent = horodatage
        duree = (horodatage - debut) / 3600 + 1
        meilleure = max(meilleure, duree)

    return meilleure


def detection_rate(flags: list[int]) -> float:
    """Proportion de mesures où le diagnostic IA signale la pourriture brune."""
    if not flags:
        return 0.0
    return sum(1 for flag in flags if int(flag) == 1) / len(flags)


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def compute_plot_metrics(plot_id: int, plot_name: str, rows: list[Measurement]) -> PlotMetrics:
    """Calcule les indicateurs d'un groupe de mesures (RM2, RM1)."""
    heures = longest_run_hours(
        [row.timestamp for row in rows],
        [row.air_humidity_pct for row in rows],
    )
    taux = detection_rate([row.phytophthora_detected for row in rows])
    return PlotMetrics(
        plot_id=plot_id,
        plot_name=plot_name,
        hours_above_85=heures,
        ia_detection_rate=taux,
        index=compute_infestation_index(heures, taux),
        under_alert=is_alert(heures),
        rows=rows,
    )


def _group_rows(db: Session, rows: list[Measurement]) -> list[PlotMetrics]:
    """Regroupe les mesures par parcelle (ou par appareil non rattaché)."""
    appareils = {device.device_id: device for device in db.query(Device).all()}
    parcelles = {plot.id: plot for plot in db.query(Plot).all()}

    groupes: dict[tuple[int, str], list[Measurement]] = defaultdict(list)
    for row in rows:
        appareil = appareils.get(row.device_id)
        if appareil is not None and appareil.plot_id in parcelles:
            parcelle = parcelles[appareil.plot_id]
            cle = (parcelle.id, parcelle.name)
        else:
            cle = (0, row.device_id)
        groupes[cle].append(row)

    return [
        compute_plot_metrics(plot_id, plot_name, groupe)
        for (plot_id, plot_name), groupe in sorted(groupes.items())
    ]


def _query_rows(
    db: Session,
    start: int,
    end: int,
    plot_id: int | None = None,
) -> list[Measurement]:
    """Mesures de la fenêtre, éventuellement restreintes à une parcelle."""
    query = db.query(Measurement).filter(
        Measurement.timestamp >= start,
        Measurement.timestamp < end,
    )
    if plot_id is not None:
        appareils = [d.device_id for d in db.query(Device).filter(Device.plot_id == plot_id).all()]
        if not appareils:
            return []
        query = query.filter(Measurement.device_id.in_(appareils))
    return query.order_by(Measurement.timestamp).all()


def _daily_series(rows: list[Measurement]) -> list[dict[str, object]]:
    """Moyenne d'humidité par jour UTC. Un jour sans mesure est absent."""
    cumuls: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        jour = datetime.fromtimestamp(row.timestamp, tz=timezone.utc).date().isoformat()
        cumuls[jour].append(row.air_humidity_pct)
    return [
        {"date": jour, "air_humidity_pct": round(_mean(valeurs), 1)}
        for jour, valeurs in sorted(cumuls.items())
    ]


def plot_indicators(
    db: Session,
    plot_id: int,
    days: int = 7,
    now: int | None = None,
) -> dict[str, object]:
    """Champs calculés de `GET /api/v1/plots/{id}` (contrat §4.6).

    Les quatre valeurs sont en lecture seule : elles sont recalculées à chaque
    lecture depuis les mesures de la fenêtre, et jamais acceptées en écriture.
    """
    fin = now if now is not None else int(time.time())
    debut = fin - days * SECONDS_PER_DAY
    rows = _query_rows(db, debut, fin, plot_id=plot_id)
    metriques = compute_plot_metrics(plot_id, "", rows)
    return {
        "hours_above_85": int(round(metriques.hours_above_85)),
        "ia_detection_rate": round(metriques.ia_detection_rate, 3),
        "infestation_index": metriques.index,
        "level": level_for(metriques.index),
    }


def build_kpis(
    db: Session,
    days: int = 7,
    plot_id: int | None = None,
    now: int | None = None,
) -> dict[str, object]:
    """Construit la réponse de `GET /api/v1/kpis` (contrat §4.4)."""
    fin = now if now is not None else int(time.time())
    debut = fin - days * SECONDS_PER_DAY

    rows = _query_rows(db, debut, fin, plot_id)
    groupes = _group_rows(db, rows)

    index_global = aggregate_index([groupe.index for groupe in groupes])
    humidite_moyenne = _mean([row.air_humidity_pct for row in rows])
    # Volume encore commercialisable : volume de référence de chaque parcelle
    # diminué de son indice d'infestation. Une parcelle sans mesure dans la
    # fenêtre garde un indice nul : elle contribue à 100 % de son volume, comme
    # le prévoit le contrat §4.4. Les boîtiers non rattachés à une parcelle
    # (plot_id = 0) n'ont pas de volume de référence connu.
    indices = {groupe.plot_id: groupe.index for groupe in groupes}
    volumes = {plot.id: plot.reference_volume_kg for plot in db.query(Plot).all()}
    if plot_id is not None:
        volumes = {identifiant: volume for identifiant, volume in volumes.items() if identifiant == plot_id}
    volume_sain_kg = sum(
        volume * (1 - indices.get(identifiant, 0) / 100)
        for identifiant, volume in volumes.items()
    )

    # `humidity_delta_7d` compare toujours la fenêtre courante aux 7 jours qui
    # la précèdent, indépendamment de `days` : c'est ce que promet son nom et
    # le contrat §4.4.
    rows_precedents = _query_rows(db, debut - 7 * SECONDS_PER_DAY, debut, plot_id)
    if rows_precedents:
        humidite_precedente = _mean([row.air_humidity_pct for row in rows_precedents])
        delta_humidite = humidite_moyenne - humidite_precedente
    else:
        # Sans historique, l'écart n'est pas mesurable : on affiche 0 plutôt
        # qu'une hausse artificielle de toute la moyenne courante.
        delta_humidite = 0.0

    return {
        "global_infestation_index": index_global,
        "level": level_for(index_global),
        "active_alerts": sum(1 for groupe in groupes if groupe.under_alert),
        "avg_air_humidity_pct": round(humidite_moyenne, 1),
        "humidity_delta_7d": round(delta_humidite, 1),
        "estimated_healthy_volume_pct": estimated_healthy_volume_pct(index_global),
        "estimated_healthy_volume_kg": round(volume_sain_kg, 1),
        "plots_monitored": len(groupes),
        "generated_at": datetime.fromtimestamp(fin, tz=timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
        "humidity_series": [
            {
                "plot_id": groupe.plot_id,
                "plot_name": groupe.plot_name,
                "under_alert": groupe.under_alert,
                "points": _daily_series(groupe.rows),
            }
            for groupe in groupes
        ],
    }


def daily_global_indices(
    db: Session,
    days: int = 7,
    now: int | None = None,
) -> list[tuple[str, int]]:
    """Indice global par jour, du plus ancien au plus récent.

    Utilisé par la courbe de prix : chaque jour reçoit l'indice calculé sur une
    fenêtre glissante de 48 h se terminant à la fin de ce jour (RM2). Sans ce
    recouvrement, une journée seule ne pourrait jamais atteindre le seuil de
    48 h au-dessus de 85 %.
    """
    fin = now if now is not None else int(time.time())
    debut = fin - days * SECONDS_PER_DAY
    # On charge 48 h supplémentaires pour alimenter la fenêtre du premier jour.
    rows = _query_rows(db, debut - ALERT_WINDOW_SECONDS, fin)

    jours = sorted(
        {
            datetime.fromtimestamp(row.timestamp, tz=timezone.utc).date().isoformat()
            for row in rows
            if row.timestamp >= debut
        }
    )

    resultat: list[tuple[str, int]] = []
    for jour in jours:
        debut_jour = int(
            datetime.fromisoformat(jour).replace(tzinfo=timezone.utc).timestamp()
        )
        fin_jour = min(debut_jour + SECONDS_PER_DAY, fin)
        fenetre = [row for row in rows if fin_jour - ALERT_WINDOW_SECONDS <= row.timestamp < fin_jour]
        groupes = _group_rows(db, fenetre)
        resultat.append((jour, aggregate_index([groupe.index for groupe in groupes])))
    return resultat


def build_price_forecast(
    db: Session,
    days: int = 7,
    now: int | None = None,
) -> dict[str, object]:
    """Construit la réponse de `GET /api/v1/prices/forecast` (contrat §4.5)."""
    indices = daily_global_indices(db, days=days, now=now)
    if not indices:
        return forecast_payload([])

    dates = [jour for jour, _ in indices]
    valeurs = [index for _, index in indices]
    references = [REFERENCE_PRICE_FCFA_PER_KG] * len(dates)
    return forecast_payload(build_forecast(dates, references, valeurs))
