"""
Rôle : initialisation utilisateurs démo (admin + acheteur) si absents.
Auteur : NKWANE Mourad (MOD-A3 / A6).
"""

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import User
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
