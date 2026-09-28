"""
FoodLoop AI - Authentication & Identity API Router
Supports enterprise RBAC, email/password JWT tokens, Supabase session validation, and demo fast-login.
"""
from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import (
    get_current_user,
    create_access_token,
    verify_password,
    hash_password,
    normalize_role
)
from app.models.models import User, Profile, Organization, OrganizationMember
from app.schemas.schemas import ProfileCreate, ProfileOut
from app.schemas.enterprise_schemas import LoginRequest, TokenResponse, RegisterRequest, UserOut
from app.middleware.rate_limit import RateLimiter
from app.utils.exceptions import AuthenticationError, ConflictError

router = APIRouter(prefix="/auth", tags=["1. Authentication & RBAC"])


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(RateLimiter(times=30, seconds=60))])
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Authenticates user with email and password, returning JWT access token."""
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        raise AuthenticationError("Invalid email or password", code="INVALID_CREDENTIALS")

    if not user.is_active:
        raise AuthenticationError("User account has been deactivated", code="ACCOUNT_DEACTIVATED")

    # Find primary organization
    membership = db.query(OrganizationMember).filter(OrganizationMember.user_id == user.id).first()
    org_id = membership.organization_id if membership else "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

    token = create_access_token({
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "organization_id": org_id,
        "full_name": user.full_name
    }, expires_delta=timedelta(days=7))

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in_minutes": 10080,
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "organization_id": org_id
        }
    }


@router.post("/register", response_model=ProfileOut)
def register_profile(profile_in: ProfileCreate, db: Session = Depends(get_db)):
    """Registers a profile with email validation."""
    existing = db.query(User).filter(User.email == profile_in.email).first()
    if existing:
        raise ConflictError("A user with this email address already exists.", code="USER_ALREADY_EXISTS")

    requested_role = normalize_role(profile_in.role)
    # Privilege Escalation Defense: Public registration cannot grant administrative roles
    if requested_role in ["ADMIN", "AUDITOR"]:
        requested_role = "KITCHEN_MANAGER"

    pwd_hash = hash_password("DemoSafePass2026!")
    user = User(
        email=profile_in.email,
        password_hash=pwd_hash,
        full_name=profile_in.full_name,
        role=requested_role,
        phone=profile_in.phone,
        avatar_url=profile_in.avatar_url,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Also sync organization if provided
    if profile_in.organization_name:
        org = Organization(
            name=profile_in.organization_name,
            org_type="HOTEL_BANQUET" if profile_in.role in ["donor", "KITCHEN_MANAGER"] else "NGO_CHARITY",
            address=profile_in.address or "Default Street",
            city="Metropolis",
            state="State",
            postal_code="10001",
            phone=profile_in.phone or "+1-555-0100",
            email=profile_in.email
        )
        db.add(org)
        db.flush()
        member = OrganizationMember(
            organization_id=org.id,
            user_id=user.id,
            role_in_org="ADMIN"
        )
        db.add(member)
        db.commit()

    return user


@router.post("/demo-login")
def demo_login(role: str = "donor", db: Session = Depends(get_db)):
    """Convenient role-switching login for demonstrations."""
    user = db.query(User).filter(User.role == role).first()
    if not user:
        user = db.query(User).filter(User.email == f"{role.lower()}@foodloop.ai").first()
    if not user:
        user = User(
            email=f"{role.lower()}@foodloop.ai",
            password_hash=hash_password("DemoSafePass2026!"),
            full_name=f"FoodLoop {role.capitalize()} Lead",
            role=role,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.role = role
        db.commit()

    token = create_access_token({
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "organization_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        "organization_name": f"City {role.capitalize()} Station"
    }, expires_delta=timedelta(days=7))

    return {
        "access_token": token,
        "token_type": "bearer",
        "profile": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": role,  # preserve original casing for backward compat test
            "is_verified": True,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }
    }


@router.get("/me")
def get_my_profile(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Returns the authenticated user's profile and active organization context."""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        user = db.query(User).filter(User.email == current_user.get("email")).first()

    if not user:
        return {
            "id": current_user["id"],
            "email": current_user.get("email", "user@foodloop.ai"),
            "full_name": current_user.get("organization_name", "FoodLoop Partner"),
            "role": current_user.get("role", "KITCHEN_MANAGER"),
            "organization_id": current_user.get("organization_id", "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
            "is_verified": True
        }

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "phone": user.phone,
        "avatar_url": user.avatar_url,
        "organization_id": current_user.get("organization_id", "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
        "is_verified": True,
        "created_at": user.created_at
    }
