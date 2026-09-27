"""
FoodLoop AI - Phase 8 Real-Time Surplus Management Schemas
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator


SURPLUS_STATUSES = [
    "AVAILABLE",
    "RESERVED",
    "PICKUP_SCHEDULED",
    "PICKED_UP",
    "IN_TRANSIT",
    "DELIVERED",
    "RECEIVED",
    "EXPIRED",
    "CANCELLED"
]

STORAGE_TYPES = [
    "HOT_HOLD",
    "REFRIGERATED",
    "FROZEN",
    "ROOM_TEMP"
]


class SurplusRecordCreate(BaseModel):
    """Payload for kitchen users creating a surplus record."""
    food: str = Field(..., min_length=2, max_length=255, description="Name or title of surplus food item")
    quantity: float = Field(..., gt=0, description="Quantity of food available")
    unit: str = Field("kg", max_length=50, description="Unit of measurement (kg, portions, lbs, trays)")
    prepared_at: datetime = Field(..., description="Timestamp when food was prepared/cooked")
    storage_type: str = Field("REFRIGERATED", description="HOT_HOLD, REFRIGERATED, FROZEN, ROOM_TEMP")
    temperature: Optional[float] = Field(None, description="Current probe temperature in °C if available")
    batch: Optional[str] = Field(None, max_length=100, description="Batch number or prep line code")
    best_use_before: Optional[datetime] = Field(None, description="Explicit safe consumption deadline")
    notes: Optional[str] = Field(None, description="Sensory notes, allergens, packaging details")
    image: Optional[str] = Field(None, description="Photo or image URL")
    location: Optional[str] = Field("Main Production Kitchen", description="Current kitchen or station location")
    category: Optional[str] = Field("COOKED_MEALS", description="Food category (COOKED_MEALS, VEGETABLES, PROTEIN, etc.)")

    @field_validator("storage_type")
    @classmethod
    def validate_storage_type(cls, v: str) -> str:
        norm = v.upper().strip()
        if norm in ["HOT", "WARMER"]:
            return "HOT_HOLD"
        if norm in ["COLD", "CHILLED", "COOLER", "WALK_IN"]:
            return "REFRIGERATED"
        if norm in ["FREEZE", "DEEP_FREEZE"]:
            return "FROZEN"
        if norm in ["ROOM", "AMBIENT"]:
            return "ROOM_TEMP"
        if norm not in STORAGE_TYPES:
            raise ValueError(f"Invalid storage_type '{v}'. Allowed: {', '.join(STORAGE_TYPES)}")
        return norm


class SurplusRecordUpdate(BaseModel):
    food: Optional[str] = None
    quantity: Optional[float] = Field(None, gt=0)
    unit: Optional[str] = None
    storage_type: Optional[str] = None
    temperature: Optional[float] = None
    notes: Optional[str] = None
    image: Optional[str] = None
    location: Optional[str] = None


class SurplusStatusTransitionRequest(BaseModel):
    new_status: str = Field(..., description="New status across 9 allowed lifecycle states")
    reason: Optional[str] = Field(None, description="Reason or dispatch notes for the status change")

    @field_validator("new_status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        norm = v.upper().strip()
        if norm not in SURPLUS_STATUSES:
            raise ValueError(f"Invalid status '{v}'. Allowed statuses: {', '.join(SURPLUS_STATUSES)}")
        return norm


class HumanApprovalRequest(BaseModel):
    approved: bool = Field(..., description="Whether the kitchen manager approves this lot for donation")
    notes: str = Field(..., min_length=3, description="Inspection notes, visual sensory check, smell check")
    verified_temp: Optional[float] = Field(None, description="Manager verified temperature reading in °C")


class SurplusAllocationRequest(BaseModel):
    recipient_id: str = Field(..., description="ID of verified recipient shelter / food bank")
    notes: Optional[str] = Field(None, description="Dispatch instructions or driver notes")


class RecipientMatchItem(BaseModel):
    recipient_id: str
    organization_name: str
    organization_type: str
    address: str
    distance_km: float
    estimated_transit_minutes: float
    capacity_portions: int
    match_score: int
    contact_person: str
    phone: str
    readiness: str
    can_receive_immediately: bool
    safe_margin_minutes: float


class SurplusRecordOut(BaseModel):
    id: str
    food: str
    quantity: float
    unit: str
    prepared_at: Optional[datetime]
    storage_type: str
    temperature: Optional[float]
    batch: Optional[str]
    best_use_before: Optional[datetime]
    notes: Optional[str]
    image: Optional[str]
    status: str
    location: str

    # Real-Time Computed Card Metrics
    age_hours: float
    age_formatted: str
    remaining_safe_window_minutes: float
    remaining_safe_window_formatted: str
    urgency: str  # CRITICAL, HIGH, MEDIUM, LOW, EXPIRED
    eligibility: str  # ELIGIBLE_FOR_DONATION, NEEDS_HUMAN_INSPECTION, INELIGIBLE_EXPIRED, INELIGIBLE_TEMPERATURE_ABUSE
    required_action: str
    suggested_waste_workflow: Optional[str] = None
    human_approval_required: bool = False
    approved_by: Optional[str] = None
    approval_status: Optional[str] = None
    approval_notes: Optional[str] = None
    safety_rule_applied: Optional[str] = None

    created_at: datetime
    updated_at: datetime


class LiveSurplusDashboardSummary(BaseModel):
    total_active_lots: int
    available_lots_count: int
    critical_urgency_count: int
    expired_lots_count: int
    total_available_quantity_kg: float
    items: List[SurplusRecordOut]
    urgent_alerts: List[Dict[str, Any]]
