"""
FoodLoop AI - Pagination, Filtering, and Sorting Utilities
Provides standardized pagination metadata and query helpers for SQLAlchemy queries.
"""
import math
from typing import Generic, TypeVar, List, Optional, Any, Dict
from pydantic import BaseModel, Field
from fastapi import Query
from sqlalchemy.orm import Query as SAQuery

T = TypeVar("T")


class PaginationParams:
    """Standardized dependency for query pagination and sorting."""
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number (1-indexed)"),
        limit: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
        sort_by: Optional[str] = Query("created_at", description="Field to sort by"),
        sort_order: Optional[str] = Query("desc", pattern="^(asc|desc)$", description="Sort direction ('asc' or 'desc')"),
        search: Optional[str] = Query(None, description="Free-text search filter")
    ):
        self.page = page
        self.limit = limit
        self.sort_by = sort_by
        self.sort_order = sort_order
        self.search = search

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class PaginationMeta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    data: List[T]
    pagination: PaginationMeta
    request_id: Optional[str] = None


class RowDict(dict):
    """Dictionary that allows attribute-style access and transparent serialization."""
    def __getattr__(self, key: str) -> Any:
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key: str, value: Any) -> None:
        self[key] = value


def row_to_dict(obj: Any) -> Any:
    """Converts a SQLAlchemy ORM model to a serializable RowDict."""
    if hasattr(obj, "__table__"):
        d = RowDict()
        for c in obj.__table__.columns:
            d[c.name] = getattr(obj, c.name)
        # Dynamic compatibility properties
        for prop in [
            "quantity", "item_name", "category", "resulting_balance",
            "quantity_change", "recipient_type", "contact_name",
            "contact_phone", "has_cold_storage", "has_hot_holding",
            "facility_type", "estimated_remaining_safe_hours", "is_quarantined"
        ]:
            if hasattr(obj, prop):
                try:
                    d[prop] = getattr(obj, prop)
                except Exception:
                    pass
        return d
    return obj


def paginate_query(
    query: SAQuery,
    params: PaginationParams,
    model_class: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Applies sorting, counts total records, and slices query by offset & limit.
    Returns dictionary with items list and pagination metadata.
    """
    total = query.count()

    # Dynamic sorting if model class is provided and has the attribute
    if model_class and params.sort_by and hasattr(model_class, params.sort_by):
        col = getattr(model_class, params.sort_by)
        if params.sort_order == "desc":
            query = query.order_by(col.desc())
        else:
            query = query.order_by(col.asc())

    raw_items = query.offset(params.offset).limit(params.limit).all()
    items = [row_to_dict(it) for it in raw_items]
    total_pages = math.ceil(total / params.limit) if total > 0 else 1

    meta = {
        "page": params.page,
        "limit": params.limit,
        "total": total,
        "total_pages": total_pages,
        "has_next": params.page < total_pages,
        "has_prev": params.page > 1
    }

    return {
        "items": items,
        "pagination": meta
    }
