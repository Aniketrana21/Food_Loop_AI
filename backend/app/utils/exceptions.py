"""
FoodLoop AI - Custom Application Exceptions
Standardized exception hierarchy with error codes and HTTP status mappings.
"""
from typing import Optional, Any, Dict


class AppException(Exception):
    """Base application exception with standardized code and status."""
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class NotFoundError(AppException):
    """Entity or resource not found (404)."""
    def __init__(self, message: str = "Resource not found", code: str = "RESOURCE_NOT_FOUND", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code=code, status_code=404, details=details)


class ValidationError(AppException):
    """Request validation or business data invalid (422)."""
    def __init__(self, message: str = "Validation failed", code: str = "VALIDATION_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code=code, status_code=422, details=details)


class ConflictError(AppException):
    """Resource already exists or state conflict (409)."""
    def __init__(self, message: str = "Resource conflict occurred", code: str = "CONFLICT_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code=code, status_code=409, details=details)


class PermissionDeniedError(AppException):
    """User lacks required permissions or role (403)."""
    def __init__(self, message: str = "Operation not permitted", code: str = "PERMISSION_DENIED", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code=code, status_code=403, details=details)


class AuthenticationError(AppException):
    """Missing or invalid authentication credentials (401)."""
    def __init__(self, message: str = "Authentication required", code: str = "UNAUTHORIZED", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code=code, status_code=401, details=details)


class RateLimitExceededError(AppException):
    """Too many requests (429)."""
    def __init__(self, message: str = "Rate limit exceeded. Please try again later.", code: str = "RATE_LIMIT_EXCEEDED", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code=code, status_code=429, details=details)


class BusinessLogicError(AppException):
    """Business rule constraint violated (400)."""
    def __init__(self, message: str, code: str = "BUSINESS_RULE_VIOLATION", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code=code, status_code=400, details=details)


# Domain-specific convenience exceptions
class SurplusNotFoundError(NotFoundError):
    def __init__(self, message: str = "Surplus item was not found"):
        super().__init__(message=message, code="SURPLUS_NOT_FOUND")


class QRVerificationError(BusinessLogicError):
    def __init__(self, message: str = "QR verification code is invalid, expired, or already burned"):
        super().__init__(message=message, code="QR_TOKEN_INVALID_OR_BURNED")


class InventoryInsufficientError(BusinessLogicError):
    def __init__(self, message: str = "Insufficient inventory stock for this transaction"):
        super().__init__(message=message, code="INSUFFICIENT_INVENTORY")


class DuplicateScanError(ConflictError):
    def __init__(self, message: str = "QR token has already been scanned and burned. Duplicate scans are rejected."):
        super().__init__(message=message, code="DUPLICATE_SCAN_DETECTED")


class UnauthorizedScannerError(PermissionDeniedError):
    def __init__(self, message: str = "Unauthorized scanner role for this custody stage."):
        super().__init__(message=message, code="UNAUTHORIZED_SCANNER_ROLE")


class InvalidStateTransitionError(ValidationError):
    def __init__(self, message: str = "Invalid custody state transition."):
        super().__init__(message=message, code="INVALID_STATE_TRANSITION")


class TamperedTokenError(BusinessLogicError):
    def __init__(self, message: str = "Cryptographic signature mismatch. Token has been tampered with or corrupted."):
        super().__init__(message=message, code="TAMPERED_DONATION_ID")


class TokenExpiredError(BusinessLogicError):
    def __init__(self, message: str = "QR verification token has expired. Request a refreshed token."):
        super().__init__(message=message, code="TOKEN_EXPIRED")

