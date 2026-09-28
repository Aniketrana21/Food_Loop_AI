"""
FoodLoop AI - Donations & Redistribution Manifests API Router
Manages formal redistribution manifests, custody handovers, and tracking numbers.
Phase 11: Integrated with QR Chain of Custody and immutable ID tracking.
"""
from typing import Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.models.models import Donation, DonationItem
from app.schemas.enterprise_schemas import DonationCreate, DonationOut
from app.repositories.donation_repo import DonationRepository
from app.services.custody_service import CustodyService
from app.utils.pagination import PaginationParams, paginate_query

router = APIRouter(prefix="/donations", tags=["15. Donations & Dispatches"])


@router.get("", response_model=dict)
def list_donations(
    status_filter: Optional[str] = Query(None, alias="status"),
    donor_org_id: Optional[str] = Query(None),
    params: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Lists donation manifests with pagination and status filters."""
    query = db.query(Donation)
    if status_filter:
        query = query.filter(Donation.status == status_filter)
    if donor_org_id:
        query = query.filter(Donation.donor_org_id == donor_org_id)

    if params.search:
        query = query.filter(
            (Donation.tracking_number.ilike(f"%{params.search}%")) |
            (Donation.immutable_donation_id.ilike(f"%{params.search}%"))
        )

    return paginate_query(query, params, model_class=Donation)


@router.post("", response_model=DonationOut, status_code=status.HTTP_201_CREATED)
def create_donation(
    donation_in: DonationCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "KITCHEN_MANAGER", "NGO"]))
):
    """Creates a formal donation manifest linking surplus items and assigning an immutable ID."""
    repo = DonationRepository(db)
    items_data = [item.model_dump() for item in donation_in.items]
    return repo.create_donation_manifest(
        donor_org_id=donation_in.donor_org_id,
        recipient_org_id=donation_in.recipient_org_id or "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        items_payload=items_data,
        haccp_verified=donation_in.haccp_verified,
        user_id=user.get("id"),
        role=user.get("role", "KITCHEN_MANAGER")
    )


@router.get("/{donation_id}", response_model=DonationOut)
def get_donation(
    donation_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Retrieves donation manifest by ID, immutable donation ID, or tracking number."""
    donation = db.query(Donation).filter(
        (Donation.id == donation_id) |
        (Donation.immutable_donation_id == donation_id) |
        (Donation.tracking_number == donation_id)
    ).first()
    if not donation:
        repo = DonationRepository(db)
        return repo.get_or_404(donation_id, "Donation")
    return donation


from app.core.security import get_current_user, RoleChecker, security_bearer, HTTPAuthorizationCredentials
from app.utils.exceptions import (
    UnauthorizedScannerError,
    InvalidStateTransitionError,
    ValidationError,
    NotFoundError
)
from fastapi import HTTPException


@router.patch("/{donation_id}/status", response_model=DonationOut)
def update_donation_status(
    donation_id: str,
    new_status: str = Query(..., pattern="^(DONATION_CREATED|ACCEPTED|PICKUP_ASSIGNED|PICKED_UP|IN_TRANSIT|DELIVERED|RECEIVED|DECLARED|MATCHED|COURIER_ASSIGNED|CANCELLED)$"),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "KITCHEN_MANAGER", "DRIVER", "NGO", "LOGISTICS_MANAGER"]))
):
    """Updates donation custody stage enforcing RBAC and state machine constraints."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required to update donation custody.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    service = CustodyService(db)
    try:
        updated = service.transition_status(donation_id, new_status, user=user)
        return updated
    except (UnauthorizedScannerError, PermissionError) as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except (InvalidStateTransitionError, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
