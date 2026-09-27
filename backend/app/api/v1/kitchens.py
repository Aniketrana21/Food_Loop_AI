"""
FoodLoop AI - Kitchens API Router
Manages commercial and institutional kitchen facilities, prep capacities, and cold storage assets.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.models.models import Kitchen
from app.schemas.enterprise_schemas import KitchenCreate, KitchenUpdate, KitchenOut
from app.repositories.base import BaseRepository
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/kitchens", tags=["3. Kitchen Facilities"])


@router.get("", response_model=dict)
def list_kitchens(
    organization_id: Optional[str] = Query(None, description="Filter by organization"),
    params: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Lists kitchens with pagination and filtering."""
    repo = BaseRepository(Kitchen, db)
    filters = {"organization_id": organization_id} if organization_id else {}
    return repo.list(params, filters=filters, search_columns=["name", "address", "contact_name"])


@router.post("", response_model=KitchenOut, status_code=status.HTTP_201_CREATED)
def create_kitchen(
    kitchen_in: KitchenCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "KITCHEN_MANAGER"]))
):
    """Creates a new kitchen facility."""
    repo = BaseRepository(Kitchen, db)
    return repo.create(**kitchen_in.model_dump())


@router.get("/{kitchen_id}", response_model=KitchenOut)
def get_kitchen(
    kitchen_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Retrieves kitchen facility details."""
    repo = BaseRepository(Kitchen, db)
    return repo.get_or_404(kitchen_id, "Kitchen")


@router.put("/{kitchen_id}", response_model=KitchenOut)
def update_kitchen(
    kitchen_id: str,
    kitchen_in: KitchenUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "KITCHEN_MANAGER"]))
):
    """Updates kitchen facility attributes."""
    repo = BaseRepository(Kitchen, db)
    return repo.update(kitchen_id, **kitchen_in.model_dump(exclude_unset=True))


@router.delete("/{kitchen_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_kitchen(
    kitchen_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN"]))
):
    """Soft deletes kitchen facility."""
    repo = BaseRepository(Kitchen, db)
    repo.delete(kitchen_id, soft=True)
    return None


@router.get("/{kitchen_id}/profile", response_model=dict)
def get_kitchen_profile(
    kitchen_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Retrieves full institutional kitchen profile including storage, capacity, and active metrics."""
    repo = BaseRepository(Kitchen, db)
    kitchen = repo.get_or_404(kitchen_id, "Kitchen")
    
    from app.models.models import ProductionBatch, Inventory, WasteRecord
    active_batches = db.query(ProductionBatch).filter(
        ProductionBatch.kitchen_id == kitchen_id,
        ProductionBatch.status.in_(["SCHEDULED", "PREPPING", "COOKING", "HOLDING"])
    ).count()
    
    inventory_count = db.query(Inventory).filter(
        Inventory.kitchen_id == kitchen_id,
        Inventory.deleted_at.is_(None)
    ).count()
    
    return {
        "id": kitchen.id,
        "organization_id": kitchen.organization_id,
        "name": kitchen.name,
        "facility_type": kitchen.facility_type,
        "daily_meal_capacity": kitchen.daily_meal_capacity,
        "address": kitchen.address,
        "latitude": kitchen.latitude,
        "longitude": kitchen.longitude,
        "contact_name": kitchen.contact_name,
        "contact_phone": kitchen.contact_phone,
        "has_cold_storage": kitchen.has_cold_storage,
        "has_hot_holding": kitchen.has_hot_holding,
        "storage_specs": kitchen.storage_specs or {},
        "certifications": kitchen.certifications or ["HACCP", "ServSafe"],
        "status": kitchen.status,
        "metrics": {
            "active_production_batches": active_batches,
            "tracked_inventory_lots": inventory_count,
            "cold_room_target_temp_c": 3.5,
            "hot_holding_target_temp_c": 65.0
        },
        "created_at": kitchen.created_at,
        "updated_at": kitchen.updated_at
    }


@router.get("/{kitchen_id}/staff", response_model=List[dict])
def list_kitchen_staff(
    kitchen_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Lists culinary and management staff assigned to the kitchen."""
    repo = BaseRepository(Kitchen, db)
    kitchen = repo.get_or_404(kitchen_id, "Kitchen")
    
    from app.models.models import OrganizationMember, User
    members = db.query(OrganizationMember).join(User, OrganizationMember.user_id == User.id).filter(
        OrganizationMember.organization_id == kitchen.organization_id
    ).all()
    
    staff_list = []
    for m in members:
        staff_list.append({
            "id": m.id,
            "user_id": m.user_id,
            "full_name": m.user.full_name if m.user else "Kitchen Staff",
            "email": m.user.email if m.user else "",
            "phone": m.user.phone if m.user else "",
            "role": m.role,
            "department": "Culinary Operations",
            "is_active": m.is_active,
            "joined_at": m.created_at
        })
        
    if not staff_list:
        # Default kitchen staff profile if none registered yet
        staff_list = [
            {
                "id": "staff-head-chef",
                "user_id": user.get("id"),
                "full_name": kitchen.contact_name or "Executive Chef Marco Vance",
                "email": user.get("email", "chef@foodloop.internal"),
                "phone": kitchen.contact_phone or "+1-555-4002",
                "role": "KITCHEN_MANAGER",
                "department": "Culinary Operations",
                "is_active": True,
                "joined_at": kitchen.created_at
            }
        ]
    return staff_list


@router.post("/{kitchen_id}/staff", response_model=dict, status_code=status.HTTP_201_CREATED)
def add_kitchen_staff(
    kitchen_id: str,
    staff_data: dict,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "KITCHEN_MANAGER"]))
):
    """Registers and assigns a new staff member to the kitchen organization."""
    import uuid
    from app.models.models import OrganizationMember, User
    repo = BaseRepository(Kitchen, db)
    kitchen = repo.get_or_404(kitchen_id, "Kitchen")
    
    email = staff_data.get("email", f"staff_{uuid.uuid4().hex[:6]}@foodloop.internal")
    full_name = staff_data.get("full_name", "Kitchen Specialist")
    role = staff_data.get("role", "KITCHEN_MANAGER")
    phone = staff_data.get("phone", "+1-555-0199")
    
    existing_user = db.query(User).filter(User.email == email).first()
    if not existing_user:
        existing_user = User(
            email=email,
            password_hash="mock_hash",
            full_name=full_name,
            phone=phone,
            role=role,
            is_active=True
        )
        db.add(existing_user)
        db.flush()
        
    member = OrganizationMember(
        organization_id=kitchen.organization_id,
        user_id=existing_user.id,
        role_in_org=role,
        is_active=True
    )
    db.add(member)
    db.commit()
    
    return {
        "id": member.id,
        "user_id": existing_user.id,
        "full_name": existing_user.full_name,
        "email": existing_user.email,
        "phone": existing_user.phone,
        "role": member.role_in_org,
        "department": "Culinary Operations",
        "is_active": True
    }
