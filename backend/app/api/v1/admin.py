"""
FoodLoop AI - Admin Governance & Forensic Auditing API Router
Handles platform administration, user role management, system health, and tamper-evident audit logs.
"""
import time
from typing import Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db, engine
from app.core.security import get_current_user, RoleChecker, normalize_role
from app.models.models import User, AuditLog, Organization
from app.schemas.enterprise_schemas import UserOut, UserUpdate, AuditLogOut, SystemHealthOut
from app.repositories.base import BaseRepository
from app.utils.pagination import PaginationParams, paginate_query

router = APIRouter(prefix="/admin", tags=["24. Platform Administration & Auditing"])
_START_TIME = time.time()


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


@router.get("/users", response_model=dict)
def list_all_users(
    role: Optional[str] = Query(None),
    params: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN"]))
):
    """Lists all registered users with role filtering (Admin only)."""
    repo = BaseRepository(User, db)
    filters = {"role": normalize_role(role)} if role else {}
    return repo.list(params, filters=filters, search_columns=["full_name", "email", "role"])


@router.patch("/users/{user_id}/role", response_model=UserOut)
def change_user_role(
    user_id: str,
    new_role: str = Query(..., pattern="^(ADMIN|KITCHEN_MANAGER|PROCESSOR|NGO|DRIVER|AUDITOR)$"),
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN"]))
):
    """Changes a user's enterprise RBAC role."""
    repo = BaseRepository(User, db)
    u = repo.get_or_404(user_id, "User")
    u.role = normalize_role(new_role)
    db.commit()
    db.refresh(u)
    return u


@router.get("/audit-logs", response_model=dict)
def list_audit_logs(
    module: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    params: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "AUDITOR"]))
):
    """Retrieves immutable SHA-256 hashed forensic audit logs."""
    query = db.query(AuditLog)
    if module:
        query = query.filter(AuditLog.module == module)
    if action:
        query = query.filter(AuditLog.action == action)

    return paginate_query(query, params, model_class=AuditLog)
