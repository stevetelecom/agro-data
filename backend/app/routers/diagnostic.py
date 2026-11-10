"""Route de diagnostic IA.

Rôle : POST /api/v1/diagnostic (image -> drapeau + confiance, contrat §4.7).
Auteur : MEKONTSO Olivier Steve (MOD-A5, issue #14).
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.models import User
from app.schemas.diagnostic import DiagnosticRead
from app.security.auth import require_roles
from app.security.rate_limit import rate_limit_dependency
from app.services.diagnostic import MAX_IMAGE_BYTES, InvalidImageError, predict

router = APIRouter(
    prefix="/api/v1/diagnostic",
    tags=["diagnostic"],
    dependencies=[Depends(rate_limit_dependency)],
)


@router.post("", response_model=DiagnosticRead)
async def diagnose(
    image: UploadFile = File(..., description="Image JPEG ou PNG (5 Mo maximum)."),
    _: User = Depends(require_roles("admin", "acheteur")),
) -> dict[str, object]:
    """Diagnostique une image de cabosse et retourne drapeau, confiance et conseil."""
    data = await image.read(MAX_IMAGE_BYTES + 1)
    try:
        resultat = predict(data)
    except InvalidImageError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    return resultat.as_dict()
