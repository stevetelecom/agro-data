"""
Rôle : CRUD des parcelles.
Auteur : NKWANE Mourad (MOD-A6).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Plot, User
from app.schemas.crud import PlotCreate, PlotRead, PlotUpdate
from app.security.auth import require_roles
from app.security.rate_limit import rate_limit_dependency

router = APIRouter(
    prefix="/api/v1/plots",
    tags=["plots"],
    dependencies=[Depends(rate_limit_dependency)],
)


@router.get("", response_model=list[PlotRead])
def list_plots(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "acheteur")),
) -> list[Plot]:
    return db.query(Plot).order_by(Plot.id).all()


@router.post("", response_model=PlotRead, status_code=status.HTTP_201_CREATED)
def create_plot(
    body: PlotCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
) -> Plot:
    if db.query(Plot).filter(Plot.code == body.code).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Code parcelle déjà utilisé")
    row = Plot(code=body.code, name=body.name, location_label=body.location_label)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/{plot_id}", response_model=PlotRead)
def get_plot(
    plot_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "acheteur")),
) -> Plot:
    row = db.query(Plot).filter(Plot.id == plot_id).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcelle introuvable")
    return row


@router.put("/{plot_id}", response_model=PlotRead)
def update_plot(
    plot_id: int,
    body: PlotUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
) -> Plot:
    row = db.query(Plot).filter(Plot.id == plot_id).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcelle introuvable")
    data = body.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{plot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plot(
    plot_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
) -> None:
    row = db.query(Plot).filter(Plot.id == plot_id).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcelle introuvable")
    db.delete(row)
    db.commit()
