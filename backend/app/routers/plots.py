"""
Rôle : CRUD des parcelles.
Auteur : NKWANE Mourad (MOD-A6).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Device, Plot, User
from app.schemas.crud import PlotCreate, PlotRead, PlotUpdate
from app.security.auth import require_roles
from app.security.rate_limit import rate_limit_dependency
from app.services.indicators import plot_indicators

router = APIRouter(
    prefix="/api/v1/plots",
    tags=["plots"],
    dependencies=[Depends(rate_limit_dependency)],
)


def _read(db: Session, plot: Plot) -> dict[str, object]:
    """Réponse d'une parcelle : champs stockés + indicateurs calculés (§4.6)."""
    payload = PlotRead.model_validate(plot).model_dump()
    payload.update(plot_indicators(db, plot.id))
    return payload


@router.get("", response_model=list[PlotRead])
def list_plots(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "acheteur")),
) -> list[dict[str, object]]:
    return [_read(db, plot) for plot in db.query(Plot).order_by(Plot.id).all()]


@router.post("", response_model=PlotRead, status_code=status.HTTP_201_CREATED)
def create_plot(
    body: PlotCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
) -> dict[str, object]:
    if db.query(Plot).filter(Plot.code == body.code).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Code parcelle déjà utilisé")
    row = Plot(
        code=body.code,
        name=body.name,
        location_label=body.location_label,
        village=body.village,
        surface_ha=body.surface_ha,
        reference_volume_kg=body.reference_volume_kg,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _read(db, row)


@router.get("/{plot_id}", response_model=PlotRead)
def get_plot(
    plot_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "acheteur")),
) -> dict[str, object]:
    row = db.query(Plot).filter(Plot.id == plot_id).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcelle introuvable")
    return _read(db, row)


@router.put("/{plot_id}", response_model=PlotRead)
def update_plot(
    plot_id: int,
    body: PlotUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
) -> dict[str, object]:
    row = db.query(Plot).filter(Plot.id == plot_id).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcelle introuvable")
    data = body.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return _read(db, row)


@router.delete("/{plot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plot(
    plot_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
) -> None:
    row = db.query(Plot).filter(Plot.id == plot_id).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcelle introuvable")
    # Contrat §4.6 : on refuse de supprimer une parcelle encore supervisée par
    # un boîtier, pour ne pas détacher silencieusement l'appareil.
    attached = db.query(Device).filter(Device.plot_id == plot_id).count()
    if attached:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{attached} appareil(s) encore rattaché(s) à cette parcelle",
        )
    db.delete(row)
    db.commit()
