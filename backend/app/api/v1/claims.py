from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import RescueClaim, FoodListing, Profile, Delivery
from app.schemas.schemas import RescueClaimCreate, RescueClaimOut, RescueClaimUpdate

router = APIRouter(prefix="/claims", tags=["Food Rescue Claims"])


@router.get("", response_model=List[RescueClaimOut])
def get_claims(
    status: Optional[str] = None,
    recipient_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(RescueClaim)
    if status:
        query = query.filter(RescueClaim.status == status)
    if recipient_id:
        query = query.filter(RescueClaim.recipient_id == recipient_id)
    return query.order_by(RescueClaim.created_at.desc()).limit(limit).all()


@router.post("", response_model=RescueClaimOut, status_code=status.HTTP_201_CREATED)
def claim_food_listing(
    claim_in: RescueClaimCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    listing = db.query(FoodListing).filter(FoodListing.id == claim_in.listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Food listing not found.")
    if listing.status != "available":
        raise HTTPException(status_code=400, detail=f"Listing is already {listing.status}.")

    recipient_id = current_user["id"]
    profile = db.query(Profile).filter(Profile.id == recipient_id).first()
    if not profile:
        profile = Profile(
            id=recipient_id,
            email=current_user.get("email", "shelter@foodloop.ai"),
            full_name=current_user.get("organization_name", "Recipient NGO"),
            role="recipient",
            organization_name=current_user.get("organization_name", "Recipient NGO"),
            latitude=37.7818,
            longitude=-122.4057
        )
        db.add(profile)
        db.commit()

    claim = RescueClaim(
        listing_id=listing.id,
        recipient_id=recipient_id,
        status="approved",
        claimed_portions=claim_in.claimed_portions,
        claimed_quantity_kg=claim_in.claimed_quantity_kg,
        delivery_type=claim_in.delivery_type,
        notes=claim_in.notes
    )

    # Reserve the listing
    listing.status = "reserved"

    db.add(claim)
    db.commit()
    db.refresh(claim)
    return claim


@router.patch("/{claim_id}", response_model=RescueClaimOut)
def update_claim_status(
    claim_id: str,
    update_in: RescueClaimUpdate,
    db: Session = Depends(get_db)
):
    claim = db.query(RescueClaim).filter(RescueClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found.")

    if update_in.status:
        claim.status = update_in.status
        if update_in.status == "delivered":
            claim.listing.status = "completed"
        elif update_in.status == "rejected":
            claim.listing.status = "available"

    if update_in.notes:
        claim.notes = update_in.notes

    db.commit()
    db.refresh(claim)
    return claim
