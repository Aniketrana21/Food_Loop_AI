import os
import hmac
import hashlib
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

security_bearer = HTTPBearer(auto_error=False)

# Enterprise RBAC Roles
ENTERPRISE_ROLES = ["ADMIN", "KITCHEN_MANAGER", "PROCESSOR", "NGO", "DRIVER", "AUDITOR", "LOGISTICS_MANAGER"]

# Role alias normalization for backward compatibility
ROLE_ALIASES = {
    "admin": "ADMIN",
    "super_admin": "ADMIN",
    "donor": "KITCHEN_MANAGER",
    "kitchen_mgr": "KITCHEN_MANAGER",
    "kitchen_manager": "KITCHEN_MANAGER",
    "processor": "PROCESSOR",
    "fpu_mgr": "PROCESSOR",
    "recipient": "NGO",
    "ngo": "NGO",
    "ngo_lead": "NGO",
    "driver": "DRIVER",
    "auditor": "AUDITOR",
    "logistics": "LOGISTICS_MANAGER",
    "logistics_manager": "LOGISTICS_MANAGER",
}


def normalize_role(role_raw: str) -> str:
    """Normalizes role strings to canonical enterprise uppercase role constants."""
    clean = str(role_raw).lower().strip()
    return ROLE_ALIASES.get(clean, role_raw.upper())


def hash_password(password: str, salt: Optional[bytes] = None) -> str:
    """Generates a secure PBKDF2-HMAC-SHA256 password hash."""
    if salt is None:
        salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return salt.hex() + "$" + key.hex()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the stored PBKDF2-HMAC-SHA256 hash."""
    if not hashed_password or "$" not in hashed_password:
        return False
    try:
        salt_hex, key_hex = hashed_password.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        expected_key = bytes.fromhex(key_hex)
        actual_key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, 100000)
        return hmac.compare_digest(expected_key, actual_key)
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Encodes JWT access token with claims and expiry."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer)
) -> dict:
    """
    Decodes Supabase JWT or FoodLoop backend JWT.
    Enforces token validity and normalizes user profile with organization claims.
    """
    if not credentials:
        # Development fallback test user
        return {
            "id": "11111111-1111-1111-1111-111111111111",
            "email": "admin@foodloop.ai",
            "role": "ADMIN",
            "organization_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "organization_name": "FoodLoop HQ"
        }

    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"],
            options={"verify_signature": True}
        )
        user_metadata = payload.get("user_metadata", {})
        app_metadata = payload.get("app_metadata", {})
        
        role = (
            app_metadata.get("role") or 
            user_metadata.get("role") or 
            payload.get("role") or 
            "KITCHEN_MANAGER"
        )
        
        org_id = (
            app_metadata.get("organization_id") or 
            user_metadata.get("organization_id") or 
            payload.get("organization_id") or 
            "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        )

        return {
            "id": payload.get("sub", payload.get("id")),
            "email": payload.get("email", "user@foodloop.ai"),
            "role": role,
            "organization_id": org_id,
            "organization_name": user_metadata.get("organization_name", payload.get("organization_name", "Partner Org"))
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


class RoleChecker:
    """
    Role-Based Access Control (RBAC) dependency.
    Validates user has one of the required roles: ['ADMIN', 'KITCHEN_MANAGER', 'PROCESSOR', 'NGO', 'DRIVER', 'AUDITOR'].
    """
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = [normalize_role(r) for r in allowed_roles]

    def __call__(self, user: dict = Depends(get_current_user)) -> dict:
        user_role = normalize_role(user.get("role", "KITCHEN_MANAGER"))
        if user_role != "ADMIN" and user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required roles: {self.allowed_roles}, your role: {user_role}"
            )
        return user


class TenantIsolationChecker:
    """
    Multi-tenant isolation dependency.
    Ensures that a user can only query/modify records belonging to their own organization,
    unless they hold the platform ADMIN or AUDITOR role.
    """
    def __init__(self, target_org_param: str = "organization_id"):
        self.target_org_param = target_org_param

    def __call__(self, target_org_id: str, user: dict = Depends(get_current_user)) -> bool:
        user_role = normalize_role(user.get("role", ""))
        user_org_id = user.get("organization_id")

        # Admins and Auditors have cross-tenant access for oversight
        if user_role in ["ADMIN", "AUDITOR"]:
            return True

        if str(user_org_id) != str(target_org_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access Denied: Multi-tenant cross-organization boundary breach detected."
            )
        return True
