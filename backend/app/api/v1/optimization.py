"""
FoodLoop AI - Route & Fleet Optimization API Router
Utilizes Google OR-Tools constraint programming for multi-stop vehicle routing with cold-chain limits.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.models.models import Vehicle, Driver
from app.schemas.schemas import OptimizeRouteRequest, OptimizeRouteResponse
from app.ai.engine import ai_engine

router = APIRouter(prefix="/optimization", tags=["11. Logistics & Route Optimization (OR-Tools)"])


@router.post("/routes", response_model=OptimizeRouteResponse)
def solve_optimized_routes(
    req: OptimizeRouteRequest,
    user: dict = Depends(RoleChecker(["ADMIN", "KITCHEN_MANAGER", "DRIVER"]))
):
    """
    Executes Google OR-Tools VRP solver to compute optimal multi-stop pickup and delivery schedules.
    Enforces time windows, refrigerated vehicle capacity, and shelf-life urgency constraints.
    """
    return ai_engine.solve_logistics_vrp(driver_ids=req.driver_ids, listing_ids=req.listing_ids)


@router.get("/fleet-capacity")
def get_fleet_capacity(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Summarizes available transport fleet and refrigerated payload headroom."""
    vehicles = db.query(Vehicle).filter(Vehicle.is_active == True).all()
    drivers = db.query(Driver).filter(Driver.current_status == "AVAILABLE").all()

    total_capacity = sum(v.max_payload_kg for v in vehicles)
    reefer_capacity = sum(v.max_payload_kg for v in vehicles if v.has_active_cooling)

    return {
        "active_vehicles_count": len(vehicles),
        "available_drivers_count": len(drivers),
        "total_fleet_payload_capacity_kg": round(total_capacity, 1),
        "cold_chain_chilled_capacity_kg": round(reefer_capacity, 1),
        "vehicles": [
            {
                "id": v.id,
                "license_plate": v.license_plate,
                "type": v.vehicle_type,
                "payload_kg": v.max_payload_kg,
                "active_cooling": v.has_active_cooling
            }
            for v in vehicles
        ]
    }
