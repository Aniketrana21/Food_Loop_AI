"""
FoodLoop AI - Sustainability Impact Analytics Schemas
Phase 15 - Multi-Granularity Environmental, Operational & Financial Metrics
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict


# ====================================================================
# 1. EMISSION FACTORS SCHEMAS
# ====================================================================

class EmissionFactorBase(BaseModel):
    category: str = Field("DEFAULT", description="Food category (e.g. PRODUCE, DAIRY, MEAT_POULTRY, BAKERY, PREPARED_MEALS, SEAFOOD, GRAINS_DRY, DEFAULT)")
    co2e_kg_per_kg_food: float = Field(2.5, description="Greenhouse gas emissions avoided per kg food diverted from landfill (kg CO2e / kg)")
    water_liters_per_kg_food: float = Field(1850.0, description="Lifecycle water footprint saved per kg food (Liters / kg)")
    landfill_diversion_m3_per_kg: float = Field(0.0015, description="Compacted landfill volume diverted per kg (m³ / kg)")
    meal_equivalent_kg: float = Field(0.42, description="Portion mass per standard meal equivalent (kg)")
    people_served_per_meal: float = Field(1.0, description="Estimated beneficiaries served per meal")
    economic_value_usd_per_kg: float = Field(5.50, description="Average retail/replacement value per kg ($)")
    production_cost_factor_per_kg: float = Field(3.25, description="Average avoided food production & labor cost per kg ($)")
    documentation_source: str = Field(
        "EPA WARM v15 (2023) / FAO Food Wastage Footprint / Feeding America Standard",
        description="Source document citation for audit compliance"
    )
    notes: Optional[str] = None


class EmissionFactorCreate(EmissionFactorBase):
    organization_id: Optional[str] = None


class EmissionFactorUpdate(BaseModel):
    co2e_kg_per_kg_food: Optional[float] = None
    water_liters_per_kg_food: Optional[float] = None
    landfill_diversion_m3_per_kg: Optional[float] = None
    meal_equivalent_kg: Optional[float] = None
    people_served_per_meal: Optional[float] = None
    economic_value_usd_per_kg: Optional[float] = None
    production_cost_factor_per_kg: Optional[float] = None
    documentation_source: Optional[str] = None
    notes: Optional[str] = None


class EmissionFactorOut(EmissionFactorBase):
    id: str
    organization_id: Optional[str] = None
    is_estimate: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ====================================================================
# 2. KPI METRICS SCHEMA
# ====================================================================

class ImpactKpiMetrics(BaseModel):
    # Core Volume & Physical Rescues
    food_rescued_kg: float = Field(..., description="Total mass of surplus edible food rescued and redistributed")
    food_waste_kg: float = Field(..., description="Total food waste recorded across facilities")
    waste_reduction_percentage: float = Field(..., description="Percentage of waste diverted/reduced relative to total handled")
    meals_equivalent: int = Field(..., description="Number of standard meals provided (rescued_kg / meal_equivalent_kg)")
    people_served: int = Field(..., description="Estimated food-insecure individuals fed")

    # Financial & Economic Metrics
    estimated_value_preserved_usd: float = Field(..., description="Total commercial/social value preserved from rescued food ($)")
    production_cost_saved_usd: float = Field(..., description="Avoided re-procurement, prep and production costs ($)")

    # Logistics & Operations
    redistribution_count: int = Field(..., description="Total completed redistribution and donation transfers")
    successful_deliveries: int = Field(..., description="Total verified completed deliveries")
    failed_deliveries: int = Field(..., description="Total aborted or failed deliveries")
    delivery_success_rate_pct: float = Field(..., description="Delivery success rate percentage")
    average_pickup_time_minutes: float = Field(..., description="Average minutes from ready-for-dispatch to driver pickup")

    # Environmental Estimates (Configurable Lifecycle Factors)
    co2e_avoided_kg: float = Field(..., description="ESTIMATE: Avoided GHG lifecycle emissions in kg CO2e")
    water_saved_liters: float = Field(..., description="ESTIMATE: Embedded agricultural freshwater conserved in liters")
    landfill_diverted_m3: float = Field(..., description="ESTIMATE: Landfill physical volume spared in cubic meters")
    is_environmental_estimate: bool = Field(True, description="Strict compliance indicator confirming environmental values are estimates")
    environmental_estimate_disclaimer: str = Field(
        "ESTIMATE NOTICE: Environmental metrics (GHG CO2e avoided, water conserved, landfill diverted) are calculated estimates based on documented lifecycle emission factors (EPA WARM v15 & FAO). They represent modeled potential environmental savings and are to be interpreted as operational estimates, not direct physical measurements.",
        description="Prominently labeled disclaimer for legal and audit compliance"
    )


# ====================================================================
# 3. CHART TIME-SERIES SCHEMAS (8 REQUIRED CHARTS)
# ====================================================================

class WasteTrendPoint(BaseModel):
    """Chart 1: Waste Trend over time"""
    date: str
    waste_kg: float
    target_threshold_kg: float
    diverted_kg: float


class FoodRescuedPoint(BaseModel):
    """Chart 2: Food Rescued over time"""
    date: str
    rescued_kg: float
    meals_equivalent: int
    people_served: int


class CategoryBreakdownItem(BaseModel):
    """Chart 3: Category Breakdown"""
    category: str
    rescued_kg: float
    waste_kg: float
    co2e_avoided_kg: float
    value_usd: float
    percentage_of_total: float


class KitchenComparisonItem(BaseModel):
    """Chart 4: Kitchen Comparison (Benchmarking)"""
    kitchen_id: str
    kitchen_name: str
    organization_name: str
    food_rescued_kg: float
    food_waste_kg: float
    waste_reduction_pct: float
    efficiency_score: float
    successful_deliveries: int


class RedistributionTrendPoint(BaseModel):
    """Chart 5: Redistribution Trend"""
    date: str
    redistribution_count: int
    volume_kg: float
    meals_provided: int


class ForecastVsActualPoint(BaseModel):
    """Chart 6: Forecast vs Actual"""
    date: str
    predicted_waste_kg: float
    actual_waste_kg: float
    variance_kg: float
    variance_pct: float


class CostTrendPoint(BaseModel):
    """Chart 7: Cost Trend (Financial Value)"""
    date: str
    value_preserved_usd: float
    production_cost_saved_usd: float
    waste_loss_usd: float
    net_benefit_usd: float


class OperationalEfficiencyPoint(BaseModel):
    """Chart 8: Operational Efficiency"""
    date: str
    avg_pickup_time_mins: float
    delivery_success_rate_pct: float
    total_deliveries: int
    failed_deliveries: int


class ImpactChartsData(BaseModel):
    waste_trend: List[WasteTrendPoint]
    food_rescued: List[FoodRescuedPoint]
    category_breakdown: List[CategoryBreakdownItem]
    kitchen_comparison: List[KitchenComparisonItem]
    redistribution_trend: List[RedistributionTrendPoint]
    forecast_vs_actual: List[ForecastVsActualPoint]
    cost_trend: List[CostTrendPoint]
    operational_efficiency: List[OperationalEfficiencyPoint]


# ====================================================================
# 4. FILTER OPTIONS & TOP-LEVEL ANALYTICS RESPONSE
# ====================================================================

class FilterOptionItem(BaseModel):
    id: str
    name: str


class ImpactFilterOptionsOut(BaseModel):
    organizations: List[FilterOptionItem]
    kitchens: List[FilterOptionItem]
    categories: List[str]
    granularities: List[str] = ["daily", "weekly", "monthly", "yearly"]


class ImpactAnalyticsResponse(BaseModel):
    time_granularity: str = Field("monthly", description="daily, weekly, monthly, yearly")
    date_range: Dict[str, Optional[str]]
    filters_applied: Dict[str, Any]
    kpis: ImpactKpiMetrics
    charts: ImpactChartsData
    emission_factors: List[EmissionFactorOut]
    environmental_estimate_disclaimer: str
