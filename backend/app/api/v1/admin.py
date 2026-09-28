"""
FoodLoop AI - Super Admin Governance & Forensic Auditing API Router (Phase 16)
Provides secure, audited administrative endpoints:
- 11 Platform KPIs overview
- Multi-facility Geographic Map
- 6-Category Platform Alerts
- Governed Organization Management
- Recipient Verification & Approval
- User Account Suspension / Activation
- System Business Rule Configuration
- ML Model Performance Telemetry
- Tamper-Evident SHA-256 Audit Log Ledger
"""
import time
from typing import Optional, List
from fastapi import APIRouter, Depends, status, Query, Request, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text, desc

from app.core.database import get_db, engine
from app.core.security import get_current_user, RoleChecker, normalize_role
from app.models.models import User, Organization, Recipient, Kitchen, ProcessingUnit
from app.schemas.enterprise_schemas import UserOut, SystemHealthOut
from app.schemas.admin_schemas import (
    AdminOverviewKpiOut,
    AdminGeoMapResponse,
    AdminAlertsSummaryOut,
    BusinessRuleCreate,
    BusinessRuleOut,
    AdminOrgActionRequest,
    AdminRecipientApprovalRequest,
    AdminUserSuspensionRequest,
    AdminModelPerformanceOut,
    AdminAuditLogsResponse
)
from app.services.admin_service import AdminService
from app.repositories.base import BaseRepository
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/admin", tags=["24. Platform Administration & Auditing"])
_START_TIME = time.time()


# -----------------------------------------------------------------------------
# 1. SYSTEM HEALTH DIAGNOSTICS (Existing backward-compatible)
# -----------------------------------------------------------------------------
@router.get("/health-diagnostics", response_model=SystemHealthOut)
def get_system_diagnostics(
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "AUDITOR"]))
):
    """Deep system health, database latency, and dialect diagnostics."""
    db_connected = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_connected = False

    return SystemHealthOut(
        service="FoodLoop AI Enterprise Backend",
        status="operational" if db_connected else "degraded",
        version="1.0.0",
        database_connected=db_connected,
        database_dialect=engine.dialect.name,
        uptime_seconds=round(time.time() - _START_TIME, 1)
    )


# -----------------------------------------------------------------------------
# 2. PLATFORM OVERVIEW (11 MANDATORY KPIS)
# -----------------------------------------------------------------------------
@router.get("/overview", response_model=AdminOverviewKpiOut)
def get_admin_overview_kpis(
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "AUDITOR"]))
):
    """
    Returns the 11 platform-wide KPIs:
    Total organizations, Active kitchens, Processing units, Registered recipients,
    Food rescued, Waste generated, Waste reduction, Successful donations,
    Active deliveries, People served, Estimated value preserved.
    """
    return AdminService.get_super_admin_kpis(db)


# -----------------------------------------------------------------------------
# 3. GEOGRAPHIC MAP NODES
# -----------------------------------------------------------------------------
@router.get("/geo-map", response_model=AdminGeoMapResponse)
def get_admin_geographic_map(
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "AUDITOR"]))
):
    """
    Retrieves geographic coordinates and operational statuses for all platform
    kitchens, food processing units, recipients, and live couriers.
    """
    return AdminService.get_geographic_map_nodes(db)


# -----------------------------------------------------------------------------
# 4. SYSTEM ALERTS (6 MANDATED CATEGORIES)
# -----------------------------------------------------------------------------
@router.get("/alerts", response_model=AdminAlertsSummaryOut)
def get_admin_alerts(
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "AUDITOR"]))
):
    """
    Aggregates active system alerts conforming to the 6 mandated categories:
    - expired surplus
    - failed delivery
    - abnormal waste increase
    - model failure
    - low prediction confidence
    - system errors
    """
    return AdminService.get_system_alerts(db)


# -----------------------------------------------------------------------------
# 5. GOVERNED ORGANIZATION MANAGEMENT
# -----------------------------------------------------------------------------
@router.get("/organizations", response_model=List[dict])
def list_admin_organizations(
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "AUDITOR"]))
):
    """Lists all registered tenant organizations with sub-facility counts."""
    orgs = db.query(Organization).filter(Organization.deleted_at.is_(None)).all()
    results = []
    for o in orgs:
        k_count = db.query(Kitchen).filter(Kitchen.organization_id == o.id, Kitchen.deleted_at.is_(None)).count()
        f_count = db.query(ProcessingUnit).filter(ProcessingUnit.organization_id == o.id, ProcessingUnit.deleted_at.is_(None)).count()
        u_count = len(o.members) if o.members else 0
        results.append({
            "id": o.id,
            "name": o.name,
            "org_type": o.org_type,
            "registration_number": o.registration_number,
            "is_active": getattr(o, "is_active", True),
            "is_verified": o.is_verified,
            "contact_email": o.contact_email,
            "contact_phone": o.contact_phone,
            "kitchens_count": k_count,
            "fpus_count": f_count,
            "members_count": u_count,
            "created_at": o.created_at
        })
    return results


@router.patch("/organizations/{org_id}/action", response_model=dict)
def manage_organization_status(
    org_id: str,
    payload: AdminOrgActionRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN"]))
):
    """
    Governed organization management (ACTIVATE, SUSPEND, VERIFY).
    Strictly recorded in tamper-evident forensic audit log.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    org = AdminService.manage_organization(
        db=db,
        actor=user,
        org_id=org_id,
        action=payload.action,
        reason=payload.reason,
        client_ip=client_ip
    )
    return {
        "status": "success",
        "organization_id": org.id,
        "name": org.name,
        "is_active": getattr(org, "is_active", True),
        "is_verified": org.is_verified,
        "action": payload.action
    }


# -----------------------------------------------------------------------------
# 6. RECIPIENT APPROVAL WORKFLOW
# -----------------------------------------------------------------------------
@router.get("/recipients", response_model=List[dict])
def list_admin_recipients(
    verification_status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "AUDITOR"]))
):
    """Lists registered charity recipients with verification statuses."""
    query = db.query(Recipient).filter(Recipient.deleted_at.is_(None))
    if verification_status:
        query = query.filter(Recipient.verification_status == verification_status)
    recipients = query.order_by(desc(Recipient.created_at)).all()

    return [
        {
            "id": r.id,
            "name": r.name,
            "facility_type": r.facility_type,
            "address": r.address,
            "verified_charity_id": r.verified_charity_id,
            "contact_person": r.contact_person,
            "contact_phone": r.contact_phone,
            "max_daily_intake_kg": r.max_daily_intake_kg,
            "cold_storage_available": r.cold_storage_available,
            "verification_status": r.verification_status,
            "is_active": r.is_active,
            "reliability_score": r.reliability_score,
            "created_at": r.created_at
        }
        for r in recipients
    ]


@router.patch("/recipients/{recipient_id}/approval", response_model=dict)
def approve_or_reject_recipient(
    recipient_id: str,
    payload: AdminRecipientApprovalRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN"]))
):
    """
    Approves or rejects a recipient charity with mandatory audit entry.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    rec = AdminService.approve_or_reject_recipient(
        db=db,
        actor=user,
        recipient_id=recipient_id,
        new_status=payload.status,
        notes=payload.notes,
        client_ip=client_ip
    )
    return {
        "status": "success",
        "recipient_id": rec.id,
        "name": rec.name,
        "verification_status": rec.verification_status,
        "is_active": rec.is_active
    }


# -----------------------------------------------------------------------------
# 7. USER ACCOUNT GOVERNANCE & SUSPENSION
# -----------------------------------------------------------------------------
@router.get("/users", response_model=dict)
def list_all_users(
    role: Optional[str] = Query(None),
    params: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "AUDITOR"]))
):
    """Lists registered platform users with role filtering."""
    repo = BaseRepository(User, db)
    filters = {"role": normalize_role(role)} if role else {}
    return repo.list(params, filters=filters, search_columns=["full_name", "email", "role"])


@router.patch("/users/{user_id}/status", response_model=dict)
def set_user_suspension_status(
    user_id: str,
    payload: AdminUserSuspensionRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN"]))
):
    """
    Governed user suspension/reactivation with required audit justification.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    updated_user = AdminService.suspend_or_activate_user(
        db=db,
        actor=user,
        target_user_id=user_id,
        is_active=payload.is_active,
        reason=payload.reason,
        client_ip=client_ip
    )
    return {
        "status": "success",
        "user_id": updated_user.id,
        "email": updated_user.email,
        "is_active": updated_user.is_active,
        "reason": payload.reason
    }


@router.patch("/users/{user_id}/role", response_model=UserOut)
def change_user_role(
    user_id: str,
    new_role: str = Query(..., pattern="^(ADMIN|KITCHEN_MANAGER|PROCESSOR|NGO|DRIVER|AUDITOR)$"),
    request: Request = None,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN"]))
):
    """Changes a user's enterprise RBAC role with audit trail."""
    repo = BaseRepository(User, db)
    u = repo.get_or_404(user_id, "User")
    old_role = u.role
    u.role = normalize_role(new_role)
    db.commit()
    db.refresh(u)

    client_ip = request.client.host if (request and request.client) else "127.0.0.1"
    AdminService.record_audit_event(
        db=db,
        actor=user,
        module="USER_GOVERNANCE",
        action="CHANGE_ROLE",
        entity_name="User",
        entity_id=u.id,
        old_values={"role": old_role},
        new_values={"role": u.role},
        client_ip=client_ip
    )
    db.commit()
    return u


# -----------------------------------------------------------------------------
# 8. BUSINESS RULES CONFIGURATION
# -----------------------------------------------------------------------------
@router.get("/business-rules", response_model=List[BusinessRuleOut])
def get_business_rules(
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "AUDITOR"]))
):
    """Lists configurable platform and food-safety business rules."""
    return AdminService.list_business_rules(db)


@router.post("/business-rules", response_model=BusinessRuleOut)
def configure_business_rule(
    payload: BusinessRuleCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN"]))
):
    """
    Creates or updates a system business rule with strict auditing.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    return AdminService.set_business_rule(
        db=db,
        actor=user,
        rule_in=payload,
        client_ip=client_ip
    )


# -----------------------------------------------------------------------------
# 9. ML & CV MODEL PERFORMANCE TELEMETRY
# -----------------------------------------------------------------------------
@router.get("/model-performance", response_model=AdminModelPerformanceOut)
def get_model_performance(
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "AUDITOR"]))
):
    """
    Retrieves real-time accuracy, latency, and drift status across
    Demand Forecasting, Waste Prediction, and Edge Computer Vision models.
    """
    return AdminService.get_model_performance(db)


# -----------------------------------------------------------------------------
# 10. FORENSIC AUDIT LOG VIEWER
# -----------------------------------------------------------------------------
@router.get("/audit-logs", response_model=AdminAuditLogsResponse)
def list_forensic_audit_logs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    module: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "AUDITOR"]))
):
    """
    Retrieves immutable SHA-256 hashed forensic audit logs with cryptographic
    integrity check and user attribution.
    """
    return AdminService.get_audit_logs(
        db=db,
        page=page,
        size=size,
        module=module,
        action=action,
        search=search
    )
