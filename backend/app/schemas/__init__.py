"""Schémas Pydantic AGRO-DATA."""

from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.crud import (
    DeviceCreate,
    DeviceRead,
    DeviceUpdate,
    PlotCreate,
    PlotRead,
    PlotUpdate,
    SubscriberCreate,
    SubscriberRead,
    SubscriberUpdate,
)
from app.schemas.measurement import (
    ClimateData,
    DiagnosticIA,
    MeasurementCreate,
    MeasurementRead,
)

__all__ = [
    "ClimateData",
    "DiagnosticIA",
    "MeasurementCreate",
    "MeasurementRead",
    "LoginRequest",
    "TokenResponse",
    "PlotCreate",
    "PlotRead",
    "PlotUpdate",
    "DeviceCreate",
    "DeviceRead",
    "DeviceUpdate",
    "SubscriberCreate",
    "SubscriberRead",
    "SubscriberUpdate",
]
