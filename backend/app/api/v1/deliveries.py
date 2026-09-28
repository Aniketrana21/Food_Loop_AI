"""
FoodLoop AI - Deliveries & Chain of Custody API Router
Tracks individual delivery legs, transit holding temperatures, and recipient delivery confirmations.
"""
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.models.models import Delivery, SurplusItem
from app.schemas.enterprise_schemas import DeliveryCreate, DeliveryUpdate, DeliveryOut
from app.schemas.logistics_schemas import (
    DeliveryStatusTransitionPayload,
    ProofOfDeliveryPayload,
    DeliveryRecordOut,
    LOGISTICS_STATUSES
)
from app.repositories.base import BaseRepository
from app.utils.pagination import PaginationParams
from app.utils.exceptions import NotFoundError, ValidationError

router = APIRouter(prefix="/deliveries", tags=["18. Deliveries & Chain of Custody"])


@router.get("", response_model=dict)
def list_deliveries(
    driver_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    params: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Lists delivery legs with pagination."""
    repo = BaseRepository(Delivery, db)
    filters = {}
    if driver_id:
        filters["driver_id"] = driver_id
    if status_filter:
        filters["status"] = status_filter

    return repo.list(params, filters=filters)


@router.post("", response_model=DeliveryOut, status_code=status.HTTP_201_CREATED)
def create_delivery(
    deliv_in: DeliveryCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "LOGISTICS", "LOGISTICS_MANAGER"]))
):
    """Dispatches a delivery leg for a donation."""
    repo = BaseRepository(Delivery, db)
    return repo.create(**deliv_in.model_dump())


@router.get("/{delivery_id}", response_model=DeliveryOut)
def get_delivery(
    delivery_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Retrieves delivery leg details."""
    repo = BaseRepository(Delivery, db)
    return repo.get_or_404(delivery_id, "Delivery")


@router.patch("/{delivery_id}", response_model=DeliveryOut)
def update_delivery(
    delivery_id: str,
    deliv_in: DeliveryUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "DRIVER", "LOGISTICS", "LOGISTICS_MANAGER", "NGO"]))
):
    """Updates delivery transit telemetry, temperatures, and proof of delivery."""
    repo = BaseRepository(Delivery, db)
    deliv = repo.get_or_404(delivery_id, "Delivery")

    # Terminal delivery state immutability
    if deliv.status.upper() in ["DELIVERED", "CANCELLED", "RECEIVED"]:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Terminal delivery state immutable: Delivery '{delivery_id}' is already {deliv.status} and cannot be modified."
        )

    # Driver ownership authorization check (Prevent IDOR)
    from app.core.security import normalize_role
    user_role = normalize_role(user.get("role", ""))
    if user_role == "DRIVER":
        from fastapi import HTTPException
        from app.models.models import Driver
        drv_rec = db.query(Driver).filter(Driver.user_id == user.get("id")).first()
        valid_ids = [user.get("id")]
        if drv_rec:
            valid_ids.append(drv_rec.id)
        if deliv.driver_id and deliv.driver_id not in valid_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access Denied: You cannot modify a delivery assigned to another driver."
            )

    return repo.update(delivery_id, **deliv_in.model_dump(exclude_unset=True))


@router.patch("/{delivery_id}/status")
def transition_delivery_status(
    delivery_id: str,
    transition: DeliveryStatusTransitionPayload,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "LOGISTICS_MANAGER", "DRIVER", "LOGISTICS", "NGO"]))
):
    """Transitions delivery status across 8 statuses."""
    from app.api.v1.logistics import transition_delivery_status as log_transition
    return log_transition(delivery_id=delivery_id, transition=transition, db=db, user=user)


@router.post("/{delivery_id}/proof-of-delivery")
def submit_delivery_proof(
    delivery_id: str,
    pod: ProofOfDeliveryPayload,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "LOGISTICS_MANAGER", "DRIVER", "LOGISTICS", "NGO"]))
):
    """Submits proof of delivery and marks delivery DELIVERED."""
    from app.api.v1.logistics import submit_proof_of_delivery as log_pod
    return log_pod(delivery_id=delivery_id, pod=pod, db=db, user=user)

