"""
Rôle : CRUD des appareils.
Auteur : NKWANE Mourad (MOD-A6).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Device, Plot, User
from app.schemas.crud import DeviceCreate, DeviceRead, DeviceUpdate
from app.security.auth import get_current_user
from app.security.rate_limit import rate_limit_dependency

router = APIRouter(
    prefix="/api/v1/devices",
    tags=["devices"],
    dependencies=[Depends(rate_limit_dependency), Depends(get_current_user)],
)


@router.get("", response_model=list[DeviceRead])
def list_devices(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> list[Device]:
    return db.query(Device).order_by(Device.id).all()


@router.post("", response_model=DeviceRead, status_code=status.HTTP_201_CREATED)
def create_device(
    body: DeviceCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Device:
    if db.query(Device).filter(Device.device_id == body.device_id).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="device_id déjà utilisé")
    if body.plot_id is not None and db.query(Plot).filter(Plot.id == body.plot_id).first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcelle introuvable")
    row = Device(
        device_id=body.device_id,
        label=body.label,
        plot_id=body.plot_id,
        is_active=body.is_active,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/{device_pk}", response_model=DeviceRead)
def get_device(
    device_pk: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Device:
    row = db.query(Device).filter(Device.id == device_pk).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appareil introuvable")
    return row


@router.put("/{device_pk}", response_model=DeviceRead)
def update_device(
    device_pk: int,
    body: DeviceUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Device:
    row = db.query(Device).filter(Device.id == device_pk).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appareil introuvable")
    data = body.model_dump(exclude_unset=True)
    if "plot_id" in data and data["plot_id"] is not None:
        if db.query(Plot).filter(Plot.id == data["plot_id"]).first() is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcelle introuvable")
    for key, value in data.items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{device_pk}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(
    device_pk: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> None:
    row = db.query(Device).filter(Device.id == device_pk).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appareil introuvable")
    db.delete(row)
    db.commit()
