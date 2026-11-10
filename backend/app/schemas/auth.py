"""
Rôle : schémas d'authentification JWT.
Auteur : NKWANE Mourad (MOD-A3).
"""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Identifiants de connexion acheteur / admin."""

    email: str = Field(..., min_length=3, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(..., min_length=8, max_length=128)


class TokenResponse(BaseModel):
    """Jeton JWT retourné après login."""

    access_token: str
    token_type: str = "bearer"
