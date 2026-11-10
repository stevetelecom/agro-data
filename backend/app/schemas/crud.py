"""
Rôle : schémas CRUD parcelles, appareils, abonnés.
Auteur : NKWANE Mourad (MOD-A6).
"""

from pydantic import BaseModel, ConfigDict, Field

_EMAIL = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class PlotCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "P-001",
                "name": "Parcelle Ambam Nord",
                "location_label": "Ambam",
            }
        }
    )

    code: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=255)
    location_label: str = Field(default="", max_length=255)


class PlotUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    location_label: str | None = Field(default=None, max_length=255)


class PlotRead(BaseModel):
    id: int
    code: str
    name: str
    location_label: str

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

    device_id: str = Field(..., min_length=1, max_length=64)
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
