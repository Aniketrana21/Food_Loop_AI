"""
FoodLoop AI - Standardized API Response Envelopes
Ensures every endpoint returns consistent structure with request_id tracking.
"""
from typing import Generic, TypeVar, Optional, Any, Dict, List
from pydantic import BaseModel

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None
    request_id: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


def success_response(
    data: Any = None,
    request_id: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Generates standard success response dictionary."""
    res = {
        "success": True,
        "data": data,
        "request_id": request_id
    }
    if meta is not None:
        res["meta"] = meta
    return res


def error_response(
    code: str,
    message: str,
    request_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Generates standard error response dictionary."""
    err: Dict[str, Any] = {
        "code": code,
        "message": message
    }
    if details:
        err["details"] = details
        
    return {
        "success": False,
        "error": err,
        "request_id": request_id
    }
