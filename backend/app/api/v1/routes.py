"""
FoodLoop AI - Routes & Multi-Stop Dispatch API Router
Manages execution routes, sequence of stops, and courier route assignments.
"""
from typing import Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.models.models import Route
from app.schemas.enterprise_schemas import RouteCreate, RouteOut
from app.repositories.base import BaseRepository
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/routes", tags=["17. Delivery Routes"])


@router.get("", response_model=dict)
def list_routes(
    driver_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    params: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Lists dispatch routes with pagination."""
    repo = BaseRepository(Route, db)
    filters = {}
    if driver_id:
        filters["driver_id"] = driver_id
    if status_filter:
        filters["status"] = status_filter

    return repo.list(params, filters=filters)


@router.post("", response_model=RouteOut, status_code=status.HTTP_201_CREATED)
def create_route(
    route_in: RouteCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "LOGISTICS"]))
):
    """Creates a new multi-stop courier route."""
    repo = BaseRepository(Route, db)
    return repo.create(**route_in.model_dump())


@router.get("/{route_id}", response_model=RouteOut)
def get_route(
    route_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Retrieves route details with sequence of stops."""
    repo = BaseRepository(Route, db)
    return repo.get_or_404(route_id, "Route")
