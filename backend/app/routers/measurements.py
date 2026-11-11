"""
Rôle : ingestion et consultation des mesures.
Auteur : NKWANE Mourad (MOD-A1 / A2 / A6).
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Measurement, User
from app.schemas.measurement import MeasurementCreate, MeasurementRead
from app.security.auth import require_device_api_key, require_roles
from app.security.rate_limit import rate_limit_dependency
from app.services.crypto import decrypt_geo, prepare_geo_enc
from app.services.data_lake import store_raw_measurement
from app.services.pipeline import run_pipeline

router = APIRouter(prefix="/api/v1/measurements", tags=["measurements"])


def _to_read(row: Measurement, *, decrypt: bool = False) -> MeasurementRead:
    """Construit le schéma de lecture ; déchiffre geo_enc si lecture autorisée."""
    geo = row.geo_enc
    if decrypt and geo:
        try:
            geo = decrypt_geo(geo)
        except Exception:
            geo = row.geo_enc
    return MeasurementRead(
        id=row.id,
        device_id=row.device_id,
        timestamp=row.timestamp,
        temperature_c=row.temperature_c,
        air_humidity_pct=row.air_humidity_pct,
        soil_humidity_pct=row.soil_humidity_pct,
        phytophthora_detected=row.phytophthora_detected,
        confidence=row.confidence,
        geo_enc=geo,
    )


@router.post(
    "",
    response_model=MeasurementRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_dependency), Depends(require_device_api_key)],
    summary="Ingérer une mesure (contrat JSON §12.1)",
)
def create_measurement(
    payload: MeasurementCreate,
    db: Session = Depends(get_db),
) -> MeasurementRead:
    """Ingère une mesure JSON après validation Pydantic et pipeline."""
    # Zone brute : dump JSON tel que reçu (après validation schéma).
    store_raw_measurement(payload)
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
    # Réponse création : geo_enc reste chiffré (preuve BNF3 en base / réponse appareil).
    return _to_read(row, decrypt=False)


@router.get(
    "",
    response_model=list[MeasurementRead],
    dependencies=[Depends(rate_limit_dependency)],
    summary="Lister les mesures (JWT, geo_enc déchiffré)",
)
def list_measurements(
    device_id: str | None = Query(default=None),
    ts_from: int | None = Query(default=None, ge=0),
    ts_to: int | None = Query(default=None, ge=0),
    limit: int = Query(default=500, ge=1, le=5000, description="Nombre maximum de mesures renvoyées."),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "acheteur")),
) -> list[MeasurementRead]:
    """Liste filtrable des mesures ; geo_enc déchiffré pour lecture autorisée."""
    query = db.query(Measurement)
    if device_id:
        query = query.filter(Measurement.device_id == device_id)
    if ts_from is not None:
        query = query.filter(Measurement.timestamp >= ts_from)
    if ts_to is not None:
        query = query.filter(Measurement.timestamp <= ts_to)
    rows = query.order_by(Measurement.timestamp.desc()).limit(limit).all()
    return [_to_read(row, decrypt=True) for row in rows]
