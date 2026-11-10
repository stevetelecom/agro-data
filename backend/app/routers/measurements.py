"""
Rôle : ingestion et consultation des mesures.
Auteur : NKWANE Mourad (MOD-A1 / A2 / A6).
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Measurement, User
from app.schemas.measurement import MeasurementCreate, MeasurementRead
from app.security.auth import get_current_user, require_device_api_key
from app.security.rate_limit import rate_limit_dependency
from app.services.crypto import prepare_geo_enc
from app.services.pipeline import run_pipeline

router = APIRouter(prefix="/api/v1/measurements", tags=["measurements"])


@router.post(
    "",
    response_model=MeasurementRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_dependency), Depends(require_device_api_key)],
)
def create_measurement(
    payload: MeasurementCreate,
    db: Session = Depends(get_db),
) -> Measurement:
    """Ingère une mesure JSON après validation Pydantic et pipeline."""
    run_pipeline(db, payload)
    geo_enc = prepare_geo_enc(payload.geo_enc)
    row = Measurement(
        device_id=payload.device_id,
        timestamp=payload.timestamp,
        temperature_c=payload.climate.temperature_c,
        air_humidity_pct=payload.climate.air_humidity_pct,
        soil_humidity_pct=payload.climate.soil_humidity_pct,
        phytophthora_detected=payload.diagnostic_ia.phytophthora_detected,
        confidence=payload.diagnostic_ia.confidence,
        geo_enc=geo_enc,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get(
    "",
    response_model=list[MeasurementRead],
    dependencies=[Depends(rate_limit_dependency)],
)
def list_measurements(
    device_id: str | None = Query(default=None),
    ts_from: int | None = Query(default=None, ge=0),
    ts_to: int | None = Query(default=None, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[Measurement]:
    """Liste filtrable des mesures (JWT requis)."""
    query = db.query(Measurement)
    if device_id:
        query = query.filter(Measurement.device_id == device_id)
    if ts_from is not None:
        query = query.filter(Measurement.timestamp >= ts_from)
    if ts_to is not None:
        query = query.filter(Measurement.timestamp <= ts_to)
    return query.order_by(Measurement.timestamp.desc()).limit(500).all()
