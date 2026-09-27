"""
FoodLoop AI - Consumption Records API Router
Tracks meal service headcounts, portions consumed, and post-service leftovers.
"""
from typing import Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.models.models import ConsumptionRecord
from app.schemas.enterprise_schemas import ConsumptionRecordCreate, ConsumptionRecordOut
from app.repositories.base import BaseRepository
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/consumption", tags=["8. Meal Consumption & Headcount"])


@router.get("", response_model=dict)
def list_consumption_records(
    kitchen_id: Optional[str] = Query(None),
    meal_service: Optional[str] = Query(None),
    params: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Lists consumption records with pagination."""
    repo = BaseRepository(ConsumptionRecord, db)
    filters = {}
    if kitchen_id:
        filters["kitchen_id"] = kitchen_id
    if meal_service:
        filters["meal_service"] = meal_service

    return repo.list(params, filters=filters)


@router.post("", response_model=ConsumptionRecordOut, status_code=status.HTTP_201_CREATED)
def record_consumption(
    record_in: ConsumptionRecordCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "KITCHEN_MANAGER"]))
):
    """Logs headcounts served and surplus remaining post-meal service."""
    repo = BaseRepository(ConsumptionRecord, db)
    data = record_in.model_dump()
    data["recorded_by_user_id"] = user["id"]
    return repo.create(**data)


@router.get("/{record_id}", response_model=ConsumptionRecordOut)
def get_consumption_record(
    record_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Retrieves consumption record details."""
    repo = BaseRepository(ConsumptionRecord, db)
    return repo.get_or_404(record_id, "ConsumptionRecord")


@router.post("/{record_id}/route-leftover", response_model=dict, status_code=status.HTTP_201_CREATED)
def route_leftover(
    record_id: str,
    route_in: dict,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "KITCHEN_MANAGER"]))
):
    """
    Routes post-service meal leftovers into either:
    1. DIVERT_TO_SURPLUS: automatically creates a verified surplus lot for donation matching.
    2. LOG_AS_WASTE: records institutional waste with category and root cause.
    """
    from datetime import datetime, timezone, timedelta
    from app.models.models import ConsumptionRecord, SurplusItem, WasteRecord
    
    repo = BaseRepository(ConsumptionRecord, db)
    record = repo.get_or_404(record_id, "ConsumptionRecord")
    
    action = route_in.get("action", "DIVERT_TO_SURPLUS")
    qty_kg = float(route_in.get("quantity_kg") or record.unconsumed_kg or 15.0)
    portions = int(route_in.get("portions") or (qty_kg * 2.2))
    notes = route_in.get("notes", "Post-service culinary leftover")
    storage_temp = route_in.get("storage_temp_condition", "REFRIGERATED_4C")
    now = datetime.now(timezone.utc)
    
    batch = record.batch
    kitchen = batch.kitchen if batch else None
    org_id = kitchen.organization_id if kitchen else user.get("organization_id", "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
    kitchen_id = kitchen.id if kitchen else None
    
    dish_name = "Prepared Meal"
    if batch and getattr(batch, "menu_item", None):
        dish_name = getattr(batch.menu_item, "dish_name", None) or getattr(batch.menu_item, "name", None) or "Prepared Meal"

    if action == "DIVERT_TO_SURPLUS":
        # Create surplus item lot
        surplus = SurplusItem(
            organization_id=org_id,
            kitchen_id=kitchen_id,
            production_batch_id=batch.id if batch else None,
            item_name=f"Surplus {batch.batch_number if batch else 'Meal'} ({dish_name})",
            category="COOKED_MEALS",
            quantity_kg=qty_kg,
            estimated_portions=portions,
            storage_temp_condition=storage_temp,
            consumption_safe_until=now + timedelta(hours=4),
            pickup_window_start=now,
            pickup_window_end=now + timedelta(hours=3),
            pickup_address=kitchen.address if kitchen else "Main Kitchen Loading Dock",
            pickup_lat=kitchen.latitude if kitchen else 37.7749,
            pickup_lng=kitchen.longitude if kitchen else -122.4194,
            status="AVAILABLE"
        )
        db.add(surplus)
        record.diverted_to_surplus_kg = round(record.diverted_to_surplus_kg + qty_kg, 2)
        db.commit()
        db.refresh(surplus)
        return {
            "action": "DIVERT_TO_SURPLUS",
            "message": f"Successfully diverted {qty_kg} kg ({portions} portions) to surplus marketplace lot.",
            "surplus_id": surplus.id,
            "status": "AVAILABLE"
        }
    else:
        # Log as waste
        category = route_in.get("category", "OVERPRODUCTION")
        waste = WasteRecord(
            organization_id=org_id,
            kitchen_id=kitchen_id or "00000000-0000-0000-0000-000000000000",
            batch_id=batch.id if batch else None,
            food_item=dish_name,
            waste_category=category,
            weight_kg=qty_kg,
            cost_loss_usd=round(qty_kg * 4.25, 2),
            root_cause=notes,
            epa_hierarchy_tier="COMPOST",
            department="Culinary Operations",
            logged_by_user_id=user["id"]
        )
        db.add(waste)
        db.commit()
        db.refresh(waste)
        return {
            "action": "LOG_AS_WASTE",
            "message": f"Logged {qty_kg} kg as {category} food waste.",
            "waste_id": waste.id,
            "cost_loss_usd": waste.cost_loss_usd
        }
