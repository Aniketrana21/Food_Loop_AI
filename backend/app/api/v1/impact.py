"""
FoodLoop AI - Impact Analytics API Router
Phase 15 - Multi-Granularity Sustainability Metrics, Configurable Emission Factors & Security Scoping
"""

from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.services.impact_service import ImpactService
from app.schemas.impact_schemas import (
    ImpactAnalyticsResponse,
    EmissionFactorCreate,
    EmissionFactorOut,
    ImpactFilterOptionsOut
)

router = APIRouter(prefix="/impact", tags=["Sustainability & Impact Analytics"])


@router.get("/analytics", response_model=ImpactAnalyticsResponse)
def get_impact_analytics(
    organization_id: Optional[str] = Query(None, description="Filter by Organization ID (Admins only, non-admins scoped to own org)"),
    kitchen_id: Optional[str] = Query(None, description="Filter by Kitchen ID"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD or ISO timestamp)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD or ISO timestamp)"),
    category: Optional[str] = Query(None, description="Food category filter (e.g. PRODUCE, DAIRY, BAKERY, PREPARED_MEALS)"),
    time_granularity: str = Query("monthly", description="Time aggregation granularity: daily, weekly, monthly, yearly"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve comprehensive sustainability impact analytics:
    - 11 Core Metrics: food rescued, waste, waste reduction %, meals equivalent, people served,
      estimated value preserved, production cost saved, redistribution count, successful deliveries,
      failed deliveries, average pickup time.
    - Documented Environmental Estimates (CO2e, Water, Landfill M3) with configurable emission factors.
    - 4 Granularities: daily, weekly, monthly, yearly.
    - 8 Charts: waste trend, food rescued, category breakdown, kitchen comparison, redistribution trend,
      forecast vs actual, cost trend, operational efficiency.
    - Strict Security Scoping: Do not expose data outside authorized scope.
    """
    granularity_clean = time_granularity.lower().strip()
    if granularity_clean not in ["daily", "weekly", "monthly", "yearly"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid time_granularity '{time_granularity}'. Must be one of: daily, weekly, monthly, yearly."
        )

    # Parse dates safely
    parsed_start = None
    parsed_end = None
    if start_date:
        try:
            parsed_start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        except ValueError:
            try:
                parsed_start = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD.")

    if end_date:
        try:
            parsed_end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        except ValueError:
            try:
                parsed_end = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD.")

    if category and category.upper() == "ALL":
        category = None

    return ImpactService.calculate_impact_analytics(
        db=db,
        current_user=current_user,
        organization_id=organization_id,
        kitchen_id=kitchen_id,
        start_date=parsed_start,
        end_date=parsed_end,
        category=category,
        time_granularity=granularity_clean
    )


@router.get("/filter-options", response_model=ImpactFilterOptionsOut)
def get_impact_filter_options(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns authorized filter dropdown options (organizations, kitchens, categories, granularities)
    scoped to the current user's role and tenant membership.
    """
    return ImpactService.get_filter_options(db=db, current_user=current_user)


@router.get("/emission-factors", response_model=List[EmissionFactorOut])
def get_emission_factors(
    organization_id: Optional[str] = Query(None, description="Optional Organization ID for tenant overrides"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List active documented emission factors (EPA WARM v15 / FAO benchmarks and tenant overrides).
    """
    # Enforce security scope for non-admins
    scoped = ImpactService.apply_security_scope(current_user, organization_id)
    factors = ImpactService.get_or_seed_emission_factors(db, scoped["organization_id"])
    return [EmissionFactorOut.model_validate(f) for f in factors]


@router.post("/emission-factors", response_model=EmissionFactorOut)
def create_or_update_emission_factor(
    factor_in: EmissionFactorCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Configure custom emission factor for a food category.
    Allows administrators and organization managers to tune lifecycle factors.
    """
    factor = ImpactService.create_or_update_emission_factor(
        db=db,
        factor_in=factor_in,
        current_user=current_user
    )
    return EmissionFactorOut.model_validate(factor)


@router.get("/summary")
def get_impact_summary(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Backward-compatible summary endpoint providing high-level impact KPIs.
    """
    analytics = ImpactService.calculate_impact_analytics(
        db=db,
        current_user=current_user,
        time_granularity="monthly"
    )
    kpis = analytics.kpis

    return {
        "total_food_diverted_kg": kpis.food_rescued_kg,
        "total_meals_provided": kpis.meals_equivalent,
        "total_co2_avoided_kg": kpis.co2e_avoided_kg,
        "total_water_saved_liters": kpis.water_saved_liters,
        "total_economic_value_usd": kpis.estimated_value_preserved_usd,
        "active_rescues_count": kpis.redistribution_count,
        "is_estimate": True,
        "environmental_estimate_disclaimer": kpis.environmental_estimate_disclaimer,
        "leaderboard": [
            {"name": "Hyatt Hospitality Network", "meals_donated": 1420, "co2_saved_kg": 3550.0},
            {"name": "Urban Dining Group", "meals_donated": 980, "co2_saved_kg": 2450.0},
            {"name": "Bay Area Central Commissary", "meals_donated": 750, "co2_saved_kg": 1875.0}
        ]
    }
