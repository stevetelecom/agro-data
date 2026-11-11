"""
Rôle : tables SQLAlchemy (mesures, parcelles, appareils, abonnés, utilisateurs).
Auteur : NKWANE Mourad (MOD-A1 / A6).
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    """Compte acheteur / administrateur authentifié par JWT."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="acheteur")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Plot(Base):
    """Parcelle cacaoyère suivie."""

    __tablename__ = "plots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location_label: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    # Champs du contrat §4.6 (issue #18) : village et surface cultivée.
    village: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    surface_ha: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    # Volume de référence de la parcelle, base du KPI « volume sain » (kg).
    reference_volume_kg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    devices: Mapped[list["Device"]] = relationship(back_populates="plot")


class Device(Base):
    """Boîtier / appareil d'acquisition rattaché à une parcelle."""

    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    plot_id: Mapped[int | None] = mapped_column(ForeignKey("plots.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    plot: Mapped[Plot | None] = relationship(back_populates="devices")


class Subscriber(Base):
    """Abonné au service DaaS (acheteur)."""

    __tablename__ = "subscribers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    organization: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    plan: Mapped[str] = mapped_column(String(64), nullable=False, default="basic")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Measurement(Base):
    """Mesure microclimatique + diagnostic IA (contrat JSON §12)."""

    __tablename__ = "measurements"
    __table_args__ = (UniqueConstraint("device_id", "timestamp", name="uq_device_timestamp"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    timestamp: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    temperature_c: Mapped[float] = mapped_column(Float, nullable=False)
    air_humidity_pct: Mapped[float] = mapped_column(Float, nullable=False)
    soil_humidity_pct: Mapped[float] = mapped_column(Float, nullable=False)
    phytophthora_detected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    geo_enc: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
