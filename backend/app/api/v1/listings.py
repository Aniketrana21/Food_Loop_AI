from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.models.models import FoodListing, Profile
from app.schemas.schemas import FoodListingCreate, FoodListingOut, FoodListingUpdate
from app.services.ml_service import ml_service

router = APIRouter(prefix="/listings", tags=["Food Surplus Marketplace"])


@router.get("", response_model=List[FoodListingOut])
def get_listings(
    category: Optional[str] = None,
    status: Optional[str] = Query(None, description="Filter by status, e.g., 'available'"),
    donor_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(FoodListing)
    if category:
        query = query.filter(FoodListing.category == category)
    if status:
        query = query.filter(FoodListing.status == status)
    if donor_id:
        query = query.filter(FoodListing.donor_id == donor_id)
    
    return query.order_by(FoodListing.created_at.desc()).limit(limit).all()


@router.get("/{listing_id}", response_model=FoodListingOut)
def get_listing(listing_id: str, db: Session = Depends(get_db)):
    listing = db.query(FoodListing).filter(FoodListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Food listing not found.")
    return listing


@router.post("", response_model=FoodListingOut, status_code=status.HTTP_201_CREATED)
def create_listing(
    listing_in: FoodListingCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Ensure donor profile exists
    donor_id = current_user["id"]
    profile = db.query(Profile).filter(Profile.id == donor_id).first()
    if not profile:
        profile = Profile(
            id=donor_id,
            email=current_user.get("email", "donor@foodloop.ai"),
            full_name=current_user.get("organization_name", "Donation Partner"),
            role="donor",
            organization_name=current_user.get("organization_name", "Donation Partner"),
            address=listing_in.pickup_address,
            latitude=listing_in.pickup_lat,
            longitude=listing_in.pickup_lng
        )
        db.add(profile)
        db.commit()

    # Automatically compute remaining safe shelf life
    shelf_res = ml_service.estimate_shelf_life({
        "category": listing_in.category,
        "storage_temp": listing_in.storage_temp,
        "packaging_type": listing_in.packaging_type,
        "ambient_temp_c": 22.0,
        "hours_since_prep": 1.0
    })

    listing = FoodListing(
        donor_id=donor_id,
        title=listing_in.title,
        description=listing_in.description,
        category=listing_in.category,
        quantity_kg=listing_in.quantity_kg,
        portions=listing_in.portions,
        packaging_type=listing_in.packaging_type,
        storage_temp=listing_in.storage_temp,
        prepared_at=listing_in.prepared_at or datetime.now(timezone.utc),
        expiry_at=listing_in.expiry_at,
        pickup_start=listing_in.pickup_start,
        pickup_end=listing_in.pickup_end,
        pickup_address=listing_in.pickup_address,
        pickup_lat=listing_in.pickup_lat,
        pickup_lng=listing_in.pickup_lng,
        dietary_tags=listing_in.dietary_tags,
        status="available",
        estimated_shelf_life_hours=shelf_res.get("remaining_safe_hours", 4.0),
        photo_url=listing_in.photo_url
    )

    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing


@router.patch("/{listing_id}", response_model=FoodListingOut)
def update_listing(
    listing_id: str,
    update_in: FoodListingUpdate,
    db: Session = Depends(get_db)
):
    listing = db.query(FoodListing).filter(FoodListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Food listing not found.")

    update_data = update_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(listing, field, value)

    db.commit()
    db.refresh(listing)
    return listing
