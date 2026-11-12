"""
Rôle : schémas CRUD parcelles, appareils, abonnés.
Auteur : NKWANE Mourad (MOD-A6).
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

_EMAIL = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

# Niveaux d'infestation du contrat §4.4 / §4.6.
Level = Literal["faible", "modere", "eleve"]


class PlotCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "P-001",
                "name": "Parcelle Ambam Nord",
                "location_label": "Ambam",
                "village": "Ambam centre",
                "surface_ha": 1.5,
                "reference_volume_kg": 1200,
            }
        }
    )

    code: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=255)
    location_label: str = Field(default="", max_length=255)
    # Contrat §4.6 : village obligatoire (1 à 40 caractères), surface > 0.
    village: str = Field(..., min_length=1, max_length=40)
    surface_ha: float = Field(..., gt=0, le=1000)
    reference_volume_kg: float = Field(default=0.0, ge=0, le=1_000_000)


class PlotUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    location_label: str | None = Field(default=None, max_length=255)
    village: str | None = Field(default=None, min_length=1, max_length=40)
    surface_ha: float | None = Field(default=None, gt=0, le=1000)
    reference_volume_kg: float | None = Field(default=None, ge=0, le=1_000_000)


class PlotRead(BaseModel):
    id: int
    code: str
    name: str
    location_label: str
    village: str
    surface_ha: float
    reference_volume_kg: float
    # Champs calculés, en lecture seule (contrat §4.6). Ils sont renseignés par
    # le routeur depuis les mesures ; les valeurs par défaut couvrent une
    # parcelle sans mesure.
    hours_above_85: int = Field(default=0, ge=0, le=168)
    ia_detection_rate: float = Field(default=0.0, ge=0, le=1)
    infestation_index: int = Field(default=0, ge=0, le=100)
    level: Level = "faible"

    model_config = ConfigDict(from_attributes=True)


class DeviceCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "device_id": "AMB-P001",
                "label": "Boîtier Ambam 1",
                "plot_id": 1,
                "is_active": True,
            }
        }
    )

    device_id: str = Field(..., min_length=1, max_length=64, pattern=r"^[A-Za-z0-9._-]+$")
    label: str = Field(default="", max_length=255)
    plot_id: int | None = None
    is_active: bool = True


class DeviceUpdate(BaseModel):
    label: str | None = Field(default=None, max_length=255)
    plot_id: int | None = None
    is_active: bool | None = None


class DeviceRead(BaseModel):
    id: int
    device_id: str
    label: str
    plot_id: int | None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class SubscriberCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "export@yaounde.cm",
                "organization": "Export SA",
                "plan": "pro",
                "is_active": True,
            }
        }
    )

    email: str = Field(..., min_length=3, max_length=255, pattern=_EMAIL)
    organization: str = Field(default="", max_length=255)
    plan: str = Field(default="basic", max_length=64)
    is_active: bool = True


class SubscriberUpdate(BaseModel):
    organization: str | None = Field(default=None, max_length=255)
    plan: str | None = Field(default=None, max_length=64)
    is_active: bool | None = None


class SubscriberRead(BaseModel):
    id: int
    email: str
    organization: str
    plan: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
