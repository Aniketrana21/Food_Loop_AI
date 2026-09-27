"""
Security module interface for FoodLoop AI.
Provides authentication dependencies, password hashing, JWT operations, and RBAC role checking.
"""
from app.core.security import (
    get_current_user,
    RoleChecker,
    hash_password,
    verify_password,
    create_access_token,
    normalize_role,
    ENTERPRISE_ROLES,
    ROLE_ALIASES,
    security_bearer,
)

__all__ = [
    "get_current_user",
    "RoleChecker",
    "hash_password",
    "verify_password",
    "create_access_token",
    "normalize_role",
    "ENTERPRISE_ROLES",
    "ROLE_ALIASES",
    "security_bearer",
]
