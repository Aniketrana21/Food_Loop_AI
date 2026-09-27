"""
FoodLoop AI - Phase 9 Recipient Matching & Dashboard Schemas
Typed Pydantic contracts for transparent multi-factor matching,
double-booking safe requests, accept/reject workflows, and pickup scheduling.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class MatchingFactorsSchema(BaseModel):
    food_compatibility: float = Field(..., description="0-100 category & dietary fit")
    capacity: float = Field(..., description="0-100 intake volume fit")
    distance: float = Field(..., description="0-100 proximity fit")
    urgency: float = Field(..., description="0-100 remaining window vs transit margin")
    pickup_availability: float = Field(..., description="0-100 self-pickup readiness")
    storage_compatibility: float = Field(..., description="0-100 cold/hot/dry capability")
    operational_reliability: float = Field(..., description="0-100 show rate & verification")


class RecipientMatchCandidateOut(BaseModel):
    recipient_id: str
    organization_name: str
    facility_type: str
    address: str
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    distance_km: float
    estimated_transit_minutes: int
    overall_match_score: float
    factors: MatchingFactorsSchema
    explanation_bullets: List[str]
    recommendation_summary: str
    is_feasible: bool
    can_intake_immediately: bool
    requires_delivery: bool
    operating_hours: str
    verification_status: str


class SurplusMatchesResponse(BaseModel):
    surplus_id: str
    food: str
    quantity: float
    unit: str
    storage_type: str
    temperature: Optional[float] = None
    urgency: str
    remaining_safe_window_minutes: float
    status: str
    matches_count: int
    matches: List[RecipientMatchCandidateOut]


class RecipientSurplusActionResponse(BaseModel):
    success: bool
    surplus_id: str
    recipient_id: str
    new_status: str
    claim_status: str
    message: str
    timestamp: datetime


class RecipientRequestPayload(BaseModel):
    recipient_id: str
    requested_portions: Optional[int] = None
    notes: Optional[str] = None


class RecipientAcceptPayload(BaseModel):
    recipient_id: str
    notes: Optional[str] = None


class RecipientRejectPayload(BaseModel):
    recipient_id: str
    rejection_reason: Optional[str] = None


class RecipientSchedulePickupPayload(BaseModel):
    recipient_id: str
    pickup_time: datetime
    driver_name: Optional[str] = None
    vehicle_plate: Optional[str] = None
    temperature_equipment_confirmed: bool = True
    driver_notes: Optional[str] = None


class RecipientAvailableSurplusItem(BaseModel):
    id: str
    food: str
    quantity: float
    unit: str
    portions: int
    storage_type: str
    temperature: Optional[float] = None
    prepared_at: Optional[datetime] = None
    best_use_before: Optional[datetime] = None
    age_formatted: str
    remaining_safe_window_minutes: float
    safe_window_formatted: str
    urgency: str
    location: str
    status: str
    claim_status: Optional[str] = None
    image: Optional[str] = None
    distance_km: float
    match_score: float
    transparent_explanation: List[str]


class RecipientDashboardSummary(BaseModel):
    recipient_id: str
    organization_name: str
    facility_type: str
    verification_status: str
    daily_intake_capacity_kg: float
    current_demand_portions: int
    storage_capabilities: List[str]
    pickup_available: bool
    available_lots_count: int
    active_requests_count: int
    scheduled_pickups_count: int
    total_rescued_kg: float
    available_surplus: List[RecipientAvailableSurplusItem]
