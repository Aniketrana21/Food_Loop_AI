"""
FoodLoop AI - Production Batches & OR-Tools Production Optimizer Router
Tracks kitchen prep workflows, planned vs actual portion yields, and HACCP holding temperatures.
Exposes Google OR-Tools multi-criteria stochastic batch optimizer and What-If simulator.
"""
import os
import sys
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

# Ensure workspace root is in sys.path for ML / optimization modules
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.models.models import ProductionBatch
from app.schemas.enterprise_schemas import ProductionBatchCreate, ProductionBatchOut
from app.repositories.base import BaseRepository
from app.utils.pagination import PaginationParams

from ml.production_optimization import production_optimizer, simulate_production_scenario


# ==========================================
# PHASE 7 SCHEMAS
# ==========================================

class ConfidenceIntervalSchema(BaseModel):
    lower: float = Field(..., description="Lower bound of demand confidence interval")
    upper: float = Field(..., description="Upper bound of demand confidence interval")


class ProductionOptimizeRequest(BaseModel):
    dish_name: Optional[str] = Field("Steamed Seasonal Market Vegetables", description="Name of dish or menu item")
    menu: Optional[str] = Field("Classic American Comfort", description="Active menu cycle theme")
    demand_forecast: float = Field(200.0, description="Forecasted portion demand from AI model")
    confidence_interval: Optional[ConfidenceIntervalSchema] = Field(None, description="Demand confidence interval")
    inventory: float = Field(0.0, description="On-hand ready inventory in portions")
    ingredient_availability: float = Field(300.0, description="Max portions available from raw ingredients")
    kitchen_capacity: float = Field(260.0, description="Max cooking equipment/station capacity in portions")
    historical_waste: float = Field(0.12, description="Baseline historical waste rate")
    food_cost: float = Field(3.50, description="Production cost per portion in USD")
    minimum_required_demand: float = Field(0.0, description="Guaranteed minimum required demand in portions")
    maximum_production_capacity: float = Field(350.0, description="Facility maximum production ceiling")
    holding_time_limit_hours: float = Field(4.0, description="HACCP time-temperature limit in hours")
    inventory_age_hours: float = Field(0.0, description="Age of on-hand inventory in hours")
    food_category: Optional[str] = Field("VEGETABLES", description="Category for portion yield and holding rules")
    unit_waste_cost: Optional[float] = Field(None, description="Disposal & footprint penalty per wasted portion")
    unit_shortage_cost: Optional[float] = Field(None, description="Penalty per unserved diner portion")


class ProductionOptimizeResponse(BaseModel):
    feasible: bool
    status: str
    recommended_production: int
    total_available_portions: int
    expected_demand: int
    expected_surplus: float
    expected_shortage_risk: float
    estimated_waste: float
    estimated_waste_kg: float
    estimated_cost: Dict[str, float]
    reasoning: List[str]
    constraints_summary: Dict[str, Any]
    infeasibility_details: Optional[Dict[str, Any]] = None
    scenarios_evaluated: Optional[List[Dict[str, Any]]] = None
    solver: Optional[str] = None


class WhatIfSimulationRequest(BaseModel):
    attendance: int = Field(1850, description="Projected diner turnout")
    menu: str = Field("Classic American Comfort", description="Menu cycle name")
    production: int = Field(240, description="Operator's planned batch production in portions")
    inventory: int = Field(20, description="Current usable inventory in portions")
    dish_name: Optional[str] = Field("Steamed Seasonal Market Vegetables")
    food_category: Optional[str] = Field("VEGETABLES")
    food_cost: Optional[float] = Field(3.50)
    kitchen_capacity: Optional[float] = Field(300.0)
    ingredient_availability: Optional[float] = Field(320.0)
    minimum_required_demand: Optional[float] = Field(None)
    maximum_production_capacity: Optional[float] = Field(350.0)
    holding_time_limit_hours: Optional[float] = Field(4.0)
    inventory_age_hours: Optional[float] = Field(1.0)


router = APIRouter(prefix="/production", tags=["7. Production & Batch Yields"])


@router.get("", response_model=dict)
def list_production_batches(
    kitchen_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    params: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Lists kitchen production batches with pagination."""
    repo = BaseRepository(ProductionBatch, db)
    filters = {}
    if kitchen_id:
        filters["kitchen_id"] = kitchen_id
    if status_filter:
        filters["status"] = status_filter

    return repo.list(params, filters=filters, search_columns=["batch_number"])


@router.post("", response_model=ProductionBatchOut, status_code=status.HTTP_201_CREATED)
def create_production_batch(
    batch_in: ProductionBatchCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "KITCHEN_MANAGER"]))
):
    """Creates a new institutional kitchen production batch."""
    repo = BaseRepository(ProductionBatch, db)
    return repo.create(**batch_in.model_dump())


@router.get("/{batch_id}", response_model=ProductionBatchOut)
def get_production_batch(
    batch_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Retrieves production batch details and HACCP holding metrics."""
    repo = BaseRepository(ProductionBatch, db)
    return repo.get_or_404(batch_id, "ProductionBatch")


@router.patch("/{batch_id}/status", response_model=ProductionBatchOut)
def update_batch_status(
    batch_id: str,
    new_status: str = Query(..., pattern="^(PLANNED|IN_PREPARATION|COOKED_HOLDING|SERVICE_COMPLETED|CLOSED|SCHEDULED|PREPPING|COOKING|HOLDING|COMPLETED|DISCARDED)$"),
    holding_temp_c: Optional[float] = Query(None),
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "KITCHEN_MANAGER"]))
):
    """Updates batch operational status and HACCP holding temperatures."""
    repo = BaseRepository(ProductionBatch, db)
    update_data = {"status": new_status}
    if holding_temp_c is not None:
        update_data["holding_temperature_c"] = holding_temp_c
    return repo.update(batch_id, **update_data)


@router.post("/{batch_id}/complete", response_model=ProductionBatchOut)
def complete_production_batch(
    batch_id: str,
    completion_data: dict,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "KITCHEN_MANAGER"]))
):
    """Marks batch completed, updates actual portions prepared, holding temp, and completed timestamp."""
    repo = BaseRepository(ProductionBatch, db)
    batch = repo.get_or_404(batch_id, "ProductionBatch")
    
    actual_portions = completion_data.get("actual_portions_prepped") or completion_data.get("actual_prepared_quantity") or batch.planned_portions
    holding_temp = completion_data.get("holding_temperature_c") or completion_data.get("current_temp_c", 65.0)
    
    batch.status = "COMPLETED"
    batch.actual_prepared_quantity = float(actual_portions)
    batch.current_temp_c = float(holding_temp)
    batch.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(batch)
    return batch


# =====================================================================
# PHASE 7 — GOOGLE OR-TOOLS PRODUCTION OPTIMIZER ENDPOINTS
# =====================================================================

@router.post("/optimize", response_model=ProductionOptimizeResponse)
def optimize_production_batch(
    req: ProductionOptimizeRequest,
    user: dict = Depends(get_current_user)
):
    """
    POST /api/v1/production/optimize
    Executes Google OR-Tools multi-criteria stochastic production optimization.
    Recommends optimal production quantities minimizing food waste + shortage risk + production cost.
    Gracefully handles infeasible scenarios with root-cause diagnostic feedback.
    """
    ci_dict = None
    if req.confidence_interval:
        ci_dict = {"lower": req.confidence_interval.lower, "upper": req.confidence_interval.upper}

    result = production_optimizer.optimize(
        demand_forecast=req.demand_forecast,
        confidence_interval=ci_dict,
        inventory=req.inventory,
        ingredient_availability=req.ingredient_availability,
        kitchen_capacity=req.kitchen_capacity,
        historical_waste=req.historical_waste,
        food_cost=req.food_cost,
        minimum_required_demand=req.minimum_required_demand,
        maximum_production_capacity=req.maximum_production_capacity,
        holding_time_limit_hours=req.holding_time_limit_hours,
        inventory_age_hours=req.inventory_age_hours,
        dish_name=req.dish_name or "Steamed Seasonal Market Vegetables",
        menu=req.menu or "Classic American Comfort",
        food_category=req.food_category or "VEGETABLES",
        unit_waste_cost=req.unit_waste_cost,
        unit_shortage_cost=req.unit_shortage_cost
    )
    return result


@router.post("/simulate", response_model=Dict[str, Any])
def run_production_what_if_simulation(
    req: WhatIfSimulationRequest,
    user: dict = Depends(get_current_user)
):
    """
    POST /api/v1/production/simulate
    Interactive What-If Simulation.
    User adjusts attendance, menu, production, inventory and immediately observes
    expected demand, recommended production, predicted waste, and estimated cost.
    """
    result = simulate_production_scenario(
        attendance=req.attendance,
        menu=req.menu,
        production=req.production,
        inventory=req.inventory,
        dish_name=req.dish_name or "Steamed Seasonal Market Vegetables",
        food_category=req.food_category or "VEGETABLES",
        food_cost=req.food_cost or 3.50,
        kitchen_capacity=req.kitchen_capacity or 300.0,
        ingredient_availability=req.ingredient_availability or 320.0,
        minimum_required_demand=req.minimum_required_demand,
        maximum_production_capacity=req.maximum_production_capacity or 350.0,
        holding_time_limit_hours=req.holding_time_limit_hours or 4.0,
        inventory_age_hours=req.inventory_age_hours or 1.0
    )
    return result
