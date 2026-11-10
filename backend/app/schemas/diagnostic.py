"""Schéma de la réponse du diagnostic IA.

Rôle : décrire `POST /api/v1/diagnostic` (contrat §4.7).
Auteur : MEKONTSO Olivier Steve (MOD-A5, issue #14).
"""

from pydantic import BaseModel, ConfigDict, Field


class DiagnosticRead(BaseModel):
    """Résultat du diagnostic d'une image de cabosse."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "phytophthora_detected": 1,
                "confidence": 0.87,
                "label": "pourriture brune",
                "recommendation": "Pulvérisation ciblée sur la parcelle concernée.",
                "model": "mobilenetv2-v1",
                "is_demo": True,
            }
        }
    )

    phytophthora_detected: int = Field(..., ge=0, le=1)
    confidence: float = Field(..., ge=0, le=1)
    label: str
    recommendation: str
    model: str
    is_demo: bool
