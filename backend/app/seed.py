"""
Rôle : initialisation utilisateur démo (acheteur) si absent.
Auteur : NKWANE Mourad (MOD-A3).
"""

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import User
from app.security.auth import hash_password


def ensure_demo_user(db: Session) -> None:
    """Crée l'utilisateur acheteur de démonstration si nécessaire."""
    settings = get_settings()
    existing = db.query(User).filter(User.email == settings.demo_admin_email).first()
    if existing is not None:
        return
    user = User(
        email=settings.demo_admin_email,
        password_hash=hash_password(settings.demo_admin_password),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
