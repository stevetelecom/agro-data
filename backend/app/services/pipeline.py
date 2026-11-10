"""
Rôle : pipeline de nettoyage des flux JSON entrants (anomalies, plages, doublons).
Auteur : NKWANE Mourad (MOD-A2).
"""

import time

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Measurement
from app.schemas.measurement import MeasurementCreate
from app.services.data_lake import log_rejection

# Plages physiques raisonnables pour Ambam (air ambient).
TEMP_MIN_C = -10.0
TEMP_MAX_C = 55.0
# Tolérance horodatage : pas plus de 5 minutes dans le futur.
FUTURE_SKEW_SECONDS = 300
# Mesures trop anciennes (> 30 jours) rejetées comme anomalies réseau.
MAX_AGE_SECONDS = 30 * 24 * 3600


class PipelineError(Exception):
    """Erreur métier explicite du pipeline (message exposé au client)."""


def validate_physical_ranges(payload: MeasurementCreate) -> None:
    """Rejette les valeurs hors plages physiques (RM4)."""
    climate = payload.climate
    if not (TEMP_MIN_C <= climate.temperature_c <= TEMP_MAX_C):
        raise PipelineError(
            f"temperature_c hors plage [{TEMP_MIN_C}, {TEMP_MAX_C}]: {climate.temperature_c}"
        )
    if not (0.0 <= climate.air_humidity_pct <= 100.0):
        raise PipelineError(f"air_humidity_pct hors plage [0, 100]: {climate.air_humidity_pct}")
    if not (0.0 <= climate.soil_humidity_pct <= 100.0):
        raise PipelineError(f"soil_humidity_pct hors plage [0, 100]: {climate.soil_humidity_pct}")


def validate_timestamp(payload: MeasurementCreate, now: int | None = None) -> None:
    """Rejette un horodatage incohérent ou trop futur / trop ancien."""
    now_ts = now if now is not None else int(time.time())
    ts = payload.timestamp
    if ts <= 0:
        raise PipelineError("timestamp invalide (doit être > 0)")
    if ts > now_ts + FUTURE_SKEW_SECONDS:
        raise PipelineError("timestamp trop dans le futur (anomalie réseau)")
    if ts < now_ts - MAX_AGE_SECONDS:
        raise PipelineError("timestamp trop ancien (anomalie réseau)")


def ensure_not_duplicate(db: Session, payload: MeasurementCreate) -> None:
    """Rejette les doublons (device_id, timestamp)."""
    exists = (
        db.query(Measurement)
        .filter(
            Measurement.device_id == payload.device_id,
            Measurement.timestamp == payload.timestamp,
        )
        .first()
    )
    if exists is not None:
        raise PipelineError(
            f"doublon détecté pour device_id={payload.device_id} timestamp={payload.timestamp}"
        )


def run_pipeline(db: Session, payload: MeasurementCreate, now: int | None = None) -> MeasurementCreate:
    """
    Exécute le pipeline complet avant persistance.
    Lève HTTPException 422 en cas d'anomalie explicite et journalise le motif.
    """
    try:
        validate_physical_ranges(payload)
        validate_timestamp(payload, now=now)
        ensure_not_duplicate(db, payload)
    except PipelineError as exc:
        log_rejection(payload.device_id, payload.timestamp, str(exc))
        code = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", status.HTTP_422_UNPROCESSABLE_ENTITY)
        raise HTTPException(status_code=code, detail=str(exc)) from exc
    return payload
