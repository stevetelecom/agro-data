"""Routes des indicateurs du tableau de bord.

Rôle : GET /api/v1/kpis et GET /api/v1/prices/forecast (contrat §4.4 / §4.5).
Auteur : MEKONTSO Olivier Steve (MOD-A4, issue #13).
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas.indicators import KpisRead, PriceForecastRead
from app.security.auth import require_roles
from app.security.rate_limit import rate_limit_dependency
from app.services.indicators import build_kpis, build_price_forecast

router = APIRouter(
    prefix="/api/v1",
    tags=["indicators"],
    dependencies=[Depends(rate_limit_dependency)],
)


@router.get("/kpis", response_model=KpisRead)
def get_kpis(
    days: int = Query(default=7, ge=1, le=30, description="Fenêtre d'analyse en jours."),
    plot_id: int | None = Query(default=None, ge=1, description="Restreindre à une parcelle."),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "acheteur")),
) -> dict[str, object]:
    """Indicateurs du tableau de bord : indice global, alertes, humidité."""
    return build_kpis(db, days=days, plot_id=plot_id)


@router.get("/prices/forecast", response_model=PriceForecastRead)
def get_price_forecast(
    days: int = Query(default=7, ge=1, le=30, description="Horizon de la courbe en jours."),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "acheteur")),
) -> dict[str, object]:
    """Courbe de prix prédictive ajustée par l'indice d'infestation (RM3)."""
    return build_price_forecast(db, days=days)
