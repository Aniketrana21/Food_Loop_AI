"""
FoodLoop AI - Food Processing Units API Router
Manages secondary processing, dehydration, canning, and surplus upcycling units.
"""
from typing import Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.models.models import ProcessingUnit
from app.schemas.enterprise_schemas import ProcessingUnitCreate, ProcessingUnitOut
from app.repositories.base import BaseRepository
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/processing", tags=["4. Processing & Upcycling Units"])


@router.get("", response_model=dict)
def list_processing_units(
    organization_id: Optional[str] = Query(None),
    params: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Lists processing units with pagination."""
    repo = BaseRepository(ProcessingUnit, db)
    filters = {"organization_id": organization_id} if organization_id else {}
    return repo.list(params, filters=filters, search_columns=["name", "unit_type", "contact_person"])


@router.post("", response_model=ProcessingUnitOut, status_code=status.HTTP_201_CREATED)
def create_processing_unit(
    unit_in: ProcessingUnitCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "PROCESSOR"]))
):
    """Registers a food processing and upcycling facility."""
    repo = BaseRepository(ProcessingUnit, db)
    return repo.create(**unit_in.model_dump())


@router.get("/{unit_id}", response_model=ProcessingUnitOut)
def get_processing_unit(
    unit_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Retrieves processing unit details."""
    repo = BaseRepository(ProcessingUnit, db)
    return repo.get_or_404(unit_id, "ProcessingUnit")
