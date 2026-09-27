from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, EmailStr


# ------------------ Profile Schemas ------------------
class ProfileBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str = "donor"  # 'admin', 'donor', 'recipient', 'driver'
    organization_name: Optional[str] = None
    organization_type: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    vehicle_type: Optional[str] = None
    capacity_kg: Optional[float] = 50.0
    avatar_url: Optional[str] = None


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    vehicle_type: Optional[str] = None
    capacity_kg: Optional[float] = None
    avatar_url: Optional[str] = None


class ProfileOut(ProfileBase):
    id: str
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ------------------ Food Listing Schemas ------------------
class FoodListingBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: str = "cooked_meals"  # cooked_meals, bakery, dairy, fresh_produce, packaged_goods, meat_seafood
    quantity_kg: float = Field(..., gt=0)
    portions: int = Field(..., gt=0)
    packaging_type: str = "sealed_trays"
    storage_temp: str = "room_temp"
    prepared_at: Optional[datetime] = None
    expiry_at: datetime
    pickup_start: datetime
    pickup_end: datetime
    pickup_address: str
    pickup_lat: float
    pickup_lng: float
    dietary_tags: List[str] = []
    photo_url: Optional[str] = None


class FoodListingCreate(FoodListingBase):
    pass


class FoodListingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    quantity_kg: Optional[float] = None
    portions: Optional[int] = None
    status: Optional[str] = None
    pickup_end: Optional[datetime] = None


class FoodListingOut(FoodListingBase):
    id: str
    donor_id: str
    status: str
    estimated_shelf_life_hours: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    donor: Optional[ProfileOut] = None

    model_config = ConfigDict(from_attributes=True)


# ------------------ Rescue Claim Schemas ------------------
class RescueClaimCreate(BaseModel):
    listing_id: str
    claimed_portions: int = Field(..., gt=0)
    claimed_quantity_kg: float = Field(..., gt=0)
    delivery_type: str = "volunteer_courier"
    notes: Optional[str] = None


class RescueClaimUpdate(BaseModel):
    status: Optional[str] = None  # pending, approved, driver_assigned, delivered, rejected
    notes: Optional[str] = None


class RescueClaimOut(BaseModel):
    id: str
    listing_id: str
    recipient_id: str
    status: str
    claimed_portions: int
    claimed_quantity_kg: float
    delivery_type: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    listing: Optional[FoodListingOut] = None
    recipient: Optional[ProfileOut] = None

    model_config = ConfigDict(from_attributes=True)


# ------------------ Delivery & Dispatch Schemas ------------------
class DeliveryCreate(BaseModel):
    claim_id: str
    driver_id: Optional[str] = None
    pickup_eta: Optional[datetime] = None
    dropoff_eta: Optional[datetime] = None


class DeliveryUpdate(BaseModel):
    status: Optional[str] = None
    temperature_log_c: Optional[float] = None
    proof_of_delivery_url: Optional[str] = None
    recipient_signature: Optional[str] = None
    actual_pickup_at: Optional[datetime] = None
    actual_delivered_at: Optional[datetime] = None


class DeliveryOut(BaseModel):
    id: str
    claim_id: str
    driver_id: Optional[str] = None
    route_batch_id: Optional[str] = None
    stop_sequence: int
    status: str
    pickup_eta: Optional[datetime] = None
    dropoff_eta: Optional[datetime] = None
    temperature_log_c: Optional[float] = None
    distance_km: float
    estimated_duration_mins: float
    created_at: datetime
    driver: Optional[ProfileOut] = None

    model_config = ConfigDict(from_attributes=True)


# ------------------ Optimization Schemas (OR-Tools) ------------------
class RouteStop(BaseModel):
    stop_index: int
    stop_type: str  # "depot", "pickup", "dropoff"
    name: str
    address: str
    latitude: float
    longitude: float
    demand_kg: float
    time_window_start_mins: int
    time_window_end_mins: int
    arrival_time_mins: int
    departure_time_mins: int
    food_title: Optional[str] = None
    shelf_life_urgency: Optional[str] = None


class DriverVehicleRoute(BaseModel):
    driver_id: str
    driver_name: str
    vehicle_type: str
    vehicle_capacity_kg: float
    total_load_kg: float
    total_distance_km: float
    total_duration_mins: float
    stops: List[RouteStop]


class OptimizeRouteRequest(BaseModel):
    driver_ids: Optional[List[str]] = None
    listing_ids: Optional[List[str]] = None
    max_travel_time_mins: Optional[int] = 180


class OptimizeRouteResponse(BaseModel):
    solver_status: str
    num_vehicles_dispatched: int
    total_rescued_kg: float
    total_distance_km: float
    total_travel_time_mins: float
    routes: List[DriverVehicleRoute]
    unassigned_stops: List[str]


# ------------------ ML & RAG Schemas ------------------
class SurplusPredictionRequest(BaseModel):
    business_type: str = "restaurant"
    category: str = "cooked_meals"
    day_of_week: int = 5
    is_weekend: int = 1
    temp_c: float = 24.0
    rainfall_mm: float = 0.0
    is_rainy: int = 0
    event_nearby: int = 1
    planned_covers: int = 150
    prepared_volume_kg: float = 75.0


class SurplusPredictionResponse(BaseModel):
    predicted_surplus_kg: float
    predicted_portions: int
    spoilage_risk_score: float
    risk_tier: str
    recommendation: str
    model_version: str


class ShelfLifeRequest(BaseModel):
    category: str
    storage_temp: str
    packaging_type: str = "sealed_trays"
    ambient_temp_c: float = 22.0
    hours_since_prep: float = 0.0


class ShelfLifeResponse(BaseModel):
    category: str
    storage_temp: str
    total_safe_shelf_life_hours: float
    hours_since_prep: float
    remaining_safe_hours: float
    urgency: str
    risk_level: str
    dispatch_priority: int
    guidelines: List[str]


class RAGQueryRequest(BaseModel):
    query: str
    category_filter: Optional[str] = None


class RAGQueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[Dict[str, Any]]
    confidence_score: float


class RecipeGenerationRequest(BaseModel):
    ingredients: List[str]
    dietary_preference: Optional[str] = "any"
    servings: Optional[int] = 50


class RecipeGenerationResponse(BaseModel):
    recipe_title: str
    prep_time_mins: int
    estimated_servings: int
    ingredients_used: List[str]
    instructions: List[str]
    safety_tips: List[str]
