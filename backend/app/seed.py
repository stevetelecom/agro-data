"""
Rôle : initialisation utilisateurs démo (admin + acheteur) si absents.
Auteur : NKWANE Mourad (MOD-A3 / A6).
"""

import time

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Device, Measurement, Plot, User
from app.security.auth import hash_password


def _ensure_user(db: Session, email: str, password: str, role: str) -> None:
    existing = db.query(User).filter(User.email == email).first()
    if existing is not None:
        return
    db.add(
        User(
            email=email,
            password_hash=hash_password(password),
            role=role,
            is_active=True,
        )
    )
    db.commit()


def ensure_demo_user(db: Session) -> None:
    """Crée l'admin et l'acheteur de démonstration si nécessaire."""
    settings = get_settings()
    # Compte historique (email acheteur@...) conservé en rôle admin pour la démo CRUD.
    _ensure_user(db, settings.demo_admin_email, settings.demo_admin_password, "admin")
    _ensure_user(db, settings.demo_buyer_email, settings.demo_buyer_password, "acheteur")


def ensure_trial_dataset(db: Session) -> None:
    """Ajoute une parcelle, un boîtier et des mesures horaires si la base est vide."""
    if db.query(Measurement).first() is not None:
        return
    plot = db.query(Plot).filter(Plot.code == "P-NORD").first()
    if plot is None:
        plot = Plot(code="P-NORD", name="Parcelle Nord", location_label="Ambam Nord")
        db.add(plot)
        db.flush()
    if db.query(Device).filter(Device.device_id == "AMB-P001").first() is None:
        db.add(Device(device_id="AMB-P001", label="Boîtier Nord", plot_id=plot.id, is_active=True))
    hour = int(time.time())
    hour -= hour % 3600
    for index in range(8):
        db.add(
            Measurement(
                device_id="AMB-P001",
                timestamp=hour - (7 - index) * 3600,
                temperature_c=26.5,
                air_humidity_pct=round(78 + index * 1.4, 1),
                soil_humidity_pct=60.0,
                phytophthora_detected=0,
                confidence=0.91,
                geo_enc="",
            )
        )
    db.commit()
