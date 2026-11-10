"""
Rôle : schémas Pydantic du contrat JSON §12 (ingestion / lecture).
Auteur : NKWANE Mourad (MOD-A1).
"""

from pydantic import BaseModel, ConfigDict, Field

# Exemple officiel aligné sur le cahier des charges section 12.1.
JSON_CONTRACT_EXAMPLE = {
    "device_id": "AMB-P001",
    "timestamp": 1731225600,
    "climate": {
        "temperature_c": 27.4,
        "air_humidity_pct": 88.2,
        "soil_humidity_pct": 61.0,
    },
    "diagnostic_ia": {
        "phytophthora_detected": 0,
        "confidence": 0.93,
    },
    "geo_enc": "lat:2.383,lon:11.283",
}


class ClimateData(BaseModel):
    """Mesures climatiques horaires."""

    temperature_c: float
    air_humidity_pct: float = Field(..., ge=0, le=100)
    soil_humidity_pct: float = Field(..., ge=0, le=100)


class DiagnosticIA(BaseModel):
    """Résultat diagnostic pourriture brune."""

    phytophthora_detected: int = Field(..., ge=0, le=1)
    confidence: float = Field(..., ge=0, le=1)


class MeasurementCreate(BaseModel):
    """Payload d'ingestion conforme au cahier des charges §12.1."""

    model_config = ConfigDict(json_schema_extra={"example": JSON_CONTRACT_EXAMPLE})

    device_id: str = Field(..., min_length=1, max_length=64)
    timestamp: int = Field(..., gt=0)
    climate: ClimateData
    diagnostic_ia: DiagnosticIA
    geo_enc: str = Field(default="", max_length=1024)


class MeasurementRead(BaseModel):
    """Mesure persistée exposée à l'API de consultation."""

    id: int
    device_id: str
    timestamp: int
    temperature_c: float
    air_humidity_pct: float
    soil_humidity_pct: float
    phytophthora_detected: int
    confidence: float
    geo_enc: str

    model_config = ConfigDict(from_attributes=True)
