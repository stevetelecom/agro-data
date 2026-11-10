"""
Rôle : authentification acheteur (login JWT).
Auteur : NKWANE Mourad (MOD-A3).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.security.auth import create_access_token, verify_password
from app.security.rate_limit import rate_limit_dependency

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(rate_limit_dependency)])
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Authentifie un utilisateur et retourne un jeton JWT."""
    user = db.query(User).filter(User.email == body.email).first()
    if user is None or not user.is_active or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants invalides")
    token = create_access_token(subject=user.email, role=user.role)
    return TokenResponse(access_token=token)
