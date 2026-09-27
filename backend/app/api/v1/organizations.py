"""
FoodLoop AI - Organizations API Router
Handles organization profiles, facility registrations, and member roster management.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.models.models import Organization, OrganizationMember, User
from app.schemas.enterprise_schemas import OrganizationCreate, OrganizationUpdate, OrganizationOut, OrgMemberCreate, OrgMemberOut
from app.repositories.base import BaseRepository
from app.utils.pagination import PaginationParams
from app.utils.exceptions import NotFoundError, ConflictError

router = APIRouter(prefix="/organizations", tags=["2. Organizations & Tenants"])


@router.get("", response_model=dict)
def list_organizations(
    org_type: Optional[str] = Query(None, description="Filter by org type"),
    params: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Lists organizations with pagination, filtering, and sorting."""
    repo = BaseRepository(Organization, db)
    filters = {"org_type": org_type} if org_type else {}
    return repo.list(params, filters=filters, search_columns=["name", "city", "email"])


@router.post("", response_model=OrganizationOut, status_code=status.HTTP_201_CREATED)
def create_organization(
    org_in: OrganizationCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN"]))
):
    """Registers a new organization (Admin only)."""
    repo = BaseRepository(Organization, db)
    if org_in.registration_number:
        exists = db.query(Organization).filter(Organization.registration_number == org_in.registration_number).first()
        if exists:
            raise ConflictError(f"Registration number '{org_in.registration_number}' is already registered.", code="DUPLICATE_REGISTRATION_NUMBER")

    import uuid
    reg_no = org_in.registration_number or f"REG-{uuid.uuid4().hex[:8].upper()}"
    contact_email = org_in.contact_email or org_in.email or f"org_{uuid.uuid4().hex[:6]}@foodloop.ai"
    contact_phone = org_in.contact_phone or org_in.phone or "+1-555-0100"

    org = Organization(
        name=org_in.name,
        org_type=org_in.org_type,
        registration_number=reg_no,
        tax_id=org_in.tax_id,
        address=org_in.address,
        latitude=org_in.latitude or 37.7749,
        longitude=org_in.longitude or -122.4194,
        contact_email=contact_email,
        contact_phone=contact_phone,
        is_verified=True
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


@router.get("/{org_id}", response_model=OrganizationOut)
def get_organization(
    org_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Retrieves organization profile by ID."""
    repo = BaseRepository(Organization, db)
    return repo.get_or_404(org_id, "Organization")


@router.put("/{org_id}", response_model=OrganizationOut)
def update_organization(
    org_id: str,
    org_in: OrganizationUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "KITCHEN_MANAGER"]))
):
    """Updates organization profile."""
    repo = BaseRepository(Organization, db)
    return repo.update(org_id, **org_in.model_dump(exclude_unset=True))


@router.get("/{org_id}/members", response_model=List[OrgMemberOut])
def list_org_members(
    org_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Lists members belonging to an organization."""
    return db.query(OrganizationMember).filter(OrganizationMember.organization_id == org_id).all()


@router.post("/{org_id}/members", response_model=OrgMemberOut, status_code=status.HTTP_201_CREATED)
def add_org_member(
    org_id: str,
    member_in: OrgMemberCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "KITCHEN_MANAGER"]))
):
    """Adds a user to the organization membership roster."""
    existing = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == org_id,
        OrganizationMember.user_id == member_in.user_id
    ).first()
    if existing:
        raise ConflictError("User is already a member of this organization", code="MEMBER_ALREADY_EXISTS")

    member = OrganizationMember(
        organization_id=org_id,
        user_id=member_in.user_id,
        role_in_org=member_in.role_in_org,
        title=member_in.title,
        can_dispatch_donations=member_in.can_dispatch_donations,
        can_accept_deliveries=member_in.can_accept_deliveries
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member
