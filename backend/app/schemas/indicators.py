"""Schémas des indicateurs du tableau de bord.

Rôle : décrire les réponses du contrat d'échange §4.4 (`GET /api/v1/kpis`) et
§4.5 (`GET /api/v1/prices/forecast`).
Auteur : MEKONTSO Olivier Steve (MOD-A4, issue #13).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Level = Literal["faible", "modere", "eleve"]


class HumidityPoint(BaseModel):
    """Humidité moyenne de l'air pour une journée (UTC)."""

    date: str = Field(..., description="Jour au format ISO 8601 (AAAA-MM-JJ).")
    air_humidity_pct: float = Field(..., ge=0, le=100)


class HumiditySeries(BaseModel):
    """Série d'humidité d'une parcelle suivie."""

    plot_id: int
    plot_name: str
    under_alert: bool = Field(..., description="Vrai si la parcelle reste 48 h ou plus au-dessus de 85 %.")
    points: list[HumidityPoint]


class KpisRead(BaseModel):
    """Réponse de `GET /api/v1/kpis` (contrat §4.4)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "global_infestation_index": 62,
                "level": "eleve",
                "active_alerts": 2,
                "avg_air_humidity_pct": 83.0,
                "humidity_delta_7d": 4.0,
                "estimated_healthy_volume_pct": 57,
                "estimated_healthy_volume_kg": 2415.0,
                "plots_monitored": 4,
                "generated_at": "2026-11-10T11:00:00Z",
                "humidity_series": [
                    {
                        "plot_id": 1,
                        "plot_name": "Parcelle Nkoulou",
                        "under_alert": True,
                        "points": [
                            {"date": "2026-11-09", "air_humidity_pct": 87.0},
                            {"date": "2026-11-10", "air_humidity_pct": 89.0},
                        ],
                    }
                ],
            }
        }
    )

    global_infestation_index: int = Field(..., ge=0, le=100)
    level: Level
    active_alerts: int = Field(..., ge=0)
    avg_air_humidity_pct: float = Field(..., ge=0, le=100)
    humidity_delta_7d: float
    estimated_healthy_volume_pct: int = Field(..., ge=0, le=100)
    estimated_healthy_volume_kg: float = Field(
        ..., ge=0, description="Volume de référence des parcelles encore commercialisable."
    )
    plots_monitored: int = Field(..., ge=0)
    generated_at: str
    humidity_series: list[HumiditySeries]


class PricePointRead(BaseModel):
    """Un point de la courbe de prix (contrat §4.5)."""

    date: str
    reference_price: float = Field(..., gt=0)
    adjusted_price: float = Field(..., gt=0)


class PriceForecastRead(BaseModel):
    """Réponse de `GET /api/v1/prices/forecast` (contrat §4.5)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "unit": "FCFA/kg",
                "horizon_days": 2,
                "is_demo": True,
                "formula_version": "v1",
                "points": [
                    {"date": "2026-11-09", "reference_price": 1050.0, "adjusted_price": 1050.0},
                    {"date": "2026-11-10", "reference_price": 1050.0, "adjusted_price": 1147.65},
                ],
            }
        }
    )

    unit: str
    horizon_days: int = Field(..., ge=0)
    is_demo: bool
    formula_version: str
    points: list[PricePointRead]
