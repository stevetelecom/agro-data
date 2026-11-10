"""
Rôle : CRUD des abonnés DaaS.
Auteur : NKWANE Mourad (MOD-A6).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Subscriber, User
from app.schemas.crud import SubscriberCreate, SubscriberRead, SubscriberUpdate
from app.security.auth import require_roles
from app.security.rate_limit import rate_limit_dependency

router = APIRouter(
    prefix="/api/v1/subscribers",
    tags=["subscribers"],
    dependencies=[Depends(rate_limit_dependency)],
)


@router.get("", response_model=list[SubscriberRead])
def list_subscribers(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "acheteur")),
) -> list[Subscriber]:
    return db.query(Subscriber).order_by(Subscriber.id).all()


@router.post("", response_model=SubscriberRead, status_code=status.HTTP_201_CREATED)
def create_subscriber(
    body: SubscriberCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
) -> Subscriber:
    if db.query(Subscriber).filter(Subscriber.email == body.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email déjà abonné")
    row = Subscriber(
        email=body.email,
        organization=body.organization,
        plan=body.plan,
        is_active=body.is_active,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/{subscriber_id}", response_model=SubscriberRead)
def get_subscriber(
    subscriber_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "acheteur")),
) -> Subscriber:
    row = db.query(Subscriber).filter(Subscriber.id == subscriber_id).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Abonné introuvable")
    return row


@router.put("/{subscriber_id}", response_model=SubscriberRead)
def update_subscriber(
    subscriber_id: int,
    body: SubscriberUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
) -> Subscriber:
    row = db.query(Subscriber).filter(Subscriber.id == subscriber_id).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Abonné introuvable")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{subscriber_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subscriber(
    subscriber_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
) -> None:
    row = db.query(Subscriber).filter(Subscriber.id == subscriber_id).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Abonné introuvable")
    db.delete(row)
    db.commit()
