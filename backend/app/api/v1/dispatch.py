import uuid
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Delivery, RescueClaim, FoodListing, Profile
from app.schemas.schemas import (
    OptimizeRouteRequest, OptimizeRouteResponse, DeliveryOut, DeliveryUpdate
)
from app.services.optimizer import solve_dispatch_vrp

router = APIRouter(prefix="/dispatch", tags=["Dispatch & Route Optimization (OR-Tools)"])


@router.post("/optimize", response_model=OptimizeRouteResponse)
def run_dispatch_optimization(
    opt_request: OptimizeRouteRequest,
    db: Session = Depends(get_db)
):
    """
    Runs Google OR-Tools Capacitated Vehicle Routing Problem with Time Windows (CVRPTW).
    Assigns multi-stop pickup and dropoff routes to volunteer drivers.
    """
    # 1. Fetch available drivers
    driver_query = db.query(Profile).filter(Profile.role == "driver")
    if opt_request.driver_ids:
        driver_query = driver_query.filter(Profile.id.in_(opt_request.driver_ids))
    drivers = driver_query.all()

    if not drivers:
        # Fallback default drivers
        drivers = [
            Profile(
                id=str(uuid.uuid4()),
                email="courier1@foodloop.ai",
                full_name="Alex Mercer (Express)",
                role="driver",
                vehicle_type="refrigerated_van",
                capacity_kg=250.0,
                latitude=37.7871,
                longitude=-122.4332
            ),
            Profile(
                id=str(uuid.uuid4()),
                email="courier2@foodloop.ai",
                full_name="Sarah Chen (Eco Van)",
                role="driver",
                vehicle_type="van",
                capacity_kg=150.0,
                latitude=37.7609,
                longitude=-122.4350
            )
        ]

    # 2. Fetch active claims or listings needing dispatch
    claims = db.query(RescueClaim).filter(RescueClaim.status.in_(["pending", "approved"])).all()

    # If no active claims in DB, use available listings paired with nearest recipients
    pickup_nodes = []
    dropoff_nodes = []

    if claims:
        for c in claims:
            l = c.listing
            r = c.recipient
            pickup_nodes.append({
                "name": l.donor.organization_name if l.donor else l.title,
                "address": l.pickup_address,
                "latitude": l.pickup_lat,
                "longitude": l.pickup_lng,
                "quantity_kg": c.claimed_quantity_kg,
                "food_title": l.title,
                "shelf_life_urgency": "URGENT" if (l.estimated_shelf_life_hours or 5) < 4 else "NORMAL",
                "time_window_start_mins": 0,
                "time_window_end_mins": int(min(240, (l.estimated_shelf_life_hours or 4) * 60)),
                "claim_id": c.id
            })
            dropoff_nodes.append({
                "name": r.organization_name if r else "Community Shelter",
                "address": r.address if r else "Food Bank Hub",
                "latitude": r.latitude if r and r.latitude else (l.pickup_lat + 0.015),
                "longitude": r.longitude if r and r.longitude else (l.pickup_lng + 0.012),
                "quantity_kg": c.claimed_quantity_kg,
                "time_window_start_mins": 30,
                "time_window_end_mins": 360,
                "claim_id": c.id
            })
    else:
        # Generate sample pickup/dropoff pairs from active listings
        active_listings = db.query(FoodListing).filter(FoodListing.status == "available").limit(4).all()
        for i, l in enumerate(active_listings):
            pickup_nodes.append({
                "name": l.title,
                "address": l.pickup_address,
                "latitude": l.pickup_lat,
                "longitude": l.pickup_lng,
                "quantity_kg": l.quantity_kg,
                "food_title": l.title,
                "shelf_life_urgency": "URGENT" if (l.estimated_shelf_life_hours or 5) < 4 else "NORMAL",
                "time_window_start_mins": 0,
                "time_window_end_mins": int(min(240, (l.estimated_shelf_life_hours or 4) * 60))
            })
            dropoff_nodes.append({
                "name": f"Recipient Food Bank #{i+1}",
                "address": f"Hub Drop #{i+1}, Bay Area",
                "latitude": l.pickup_lat + 0.012 * (1 if i % 2 == 0 else -1),
                "longitude": l.pickup_lng + 0.010 * (1 if i > 1 else -1),
                "quantity_kg": l.quantity_kg,
                "time_window_start_mins": 30,
                "time_window_end_mins": 360
            })

    depot = {
        "name": "FoodLoop Central Dispatch Hub",
        "address": "1 Market St, San Francisco, CA",
        "latitude": 37.7955,
        "longitude": -122.3937
    }

    driver_dicts = [{
        "id": d.id,
        "full_name": d.full_name,
        "vehicle_type": d.vehicle_type or "van",
        "capacity_kg": d.capacity_kg or 150.0
    } for d in drivers]

    optimization_result = solve_dispatch_vrp(
        depot_location=depot,
        pickup_nodes=pickup_nodes,
        dropoff_nodes=dropoff_nodes,
        drivers=driver_dicts
    )

    return optimization_result


@router.get("/active-deliveries", response_model=List[DeliveryOut])
def get_active_deliveries(db: Session = Depends(get_db)):
    deliveries = db.query(Delivery).filter(
        Delivery.status.in_(["assigned", "en_route_pickup", "picked_up", "en_route_dropoff"])
    ).all()
    return deliveries


@router.patch("/delivery/{delivery_id}", response_model=DeliveryOut)
def update_delivery_progress(
    delivery_id: str,
    update_in: DeliveryUpdate,
    db: Session = Depends(get_db)
):
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery record not found.")

    update_data = update_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(delivery, field, value)

    if update_in.status == "delivered":
        delivery.actual_delivered_at = datetime.now(timezone.utc)
        if delivery.claim:
            delivery.claim.status = "delivered"
            if delivery.claim.listing:
                delivery.claim.listing.status = "completed"

    db.commit()
    db.refresh(delivery)
    return delivery
