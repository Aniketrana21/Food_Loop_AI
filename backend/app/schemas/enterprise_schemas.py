"""
FoodLoop AI - Enterprise Pydantic Schemas
Comprehensive, strongly-typed request and response contracts across all 30 platform domains.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict, Field, EmailStr, model_validator


# =====================================================================
# 1. AUTH & USER SCHEMAS
# =====================================================================
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: Dict[str, Any]


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    role: str = "KITCHEN_MANAGER"
    organization_name: Optional[str] = None
    organization_type: Optional[str] = "HOTEL_BANQUET"
    phone: Optional[str] = None


class UserOut(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: str
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


# =====================================================================
# 2. ORGANIZATION SCHEMAS
# =====================================================================
class OrganizationCreate(BaseModel):
    name: str
    org_type: str = "COMMERCIAL_KITCHEN"  # HOTEL_BANQUET, UNIVERSITY_DINING, CORPORATE_CAFETERIA, HOSPITAL, FOOD_PROCESSING_UNIT, NGO_CHARITY, LOGISTICS_PARTNER
    registration_number: Optional[str] = None
    tax_id: Optional[str] = None
    address: str
    latitude: Optional[float] = 37.7749
    longitude: Optional[float] = -122.4194
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    org_type: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    is_verified: Optional[bool] = None


class OrganizationOut(BaseModel):
    id: str
    name: str
    org_type: str
    registration_number: Optional[str] = None
    tax_id: Optional[str] = None
    address: str
    latitude: float
    longitude: float
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class OrgMemberCreate(BaseModel):
    user_id: str
    role_in_org: str = "MANAGER"
    title: Optional[str] = None
    can_dispatch_donations: bool = True
    can_accept_deliveries: bool = True


class OrgMemberOut(BaseModel):
    id: str
    organization_id: str
    user_id: str
    role_in_org: str
    title: Optional[str] = None
    can_dispatch_donations: bool
    can_accept_deliveries: bool
    created_at: datetime
    user: Optional[UserOut] = None
    model_config = ConfigDict(from_attributes=True)


# =====================================================================
# 3. KITCHEN & PROCESSING UNIT SCHEMAS
# =====================================================================
class KitchenCreate(BaseModel):
    organization_id: str
    name: str
    facility_type: str = "COMMERCIAL_KITCHEN"
    daily_meal_capacity: int = 500
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    contact_name: str
    contact_phone: str
    has_cold_storage: bool = True
    has_hot_holding: bool = True


class KitchenUpdate(BaseModel):
    name: Optional[str] = None
    facility_type: Optional[str] = None
    daily_meal_capacity: Optional[int] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    has_cold_storage: Optional[bool] = None
    has_hot_holding: Optional[bool] = None
    is_active: Optional[bool] = None


class KitchenOut(KitchenCreate):
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ProcessingUnitCreate(BaseModel):
    organization_id: str
    name: str
    unit_type: str = "DEHYDRATION_CANNING"
    daily_throughput_capacity_kg: float = 300.0
    accepted_feedstocks: List[str] = []
    output_products: List[str] = []
    contact_person: str
    contact_phone: str


class ProcessingUnitOut(ProcessingUnitCreate):
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# =====================================================================
# 4. MENUS & RECIPES SCHEMAS
# =====================================================================
class MenuItemCreate(BaseModel):
    name: str
    category: str = "MAIN_COURSE"  # APPETIZER, MAIN_COURSE, SIDE_DISH, DESSERT, BEVERAGE, BAKERY
    description: Optional[str] = None
    serving_size_grams: float = 350.0
    estimated_shelf_life_hours: float = 4.0
    storage_temp_requirement: str = "HOT_HOLDING_60C"
    dietary_tags: List[str] = []
    allergens: List[str] = []
    cost_per_serving_usd: float = 2.50


class MenuItemOut(MenuItemCreate):
    id: str
    menu_id: str
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class MenuCreate(BaseModel):
    organization_id: str
    kitchen_id: str
    name: str
    season_or_cycle: str = "SUMMER_CYCLE_WEEK_1"
    is_active: bool = True
    items: List[MenuItemCreate] = []


class MenuOut(BaseModel):
    id: str
    organization_id: str
    kitchen_id: str
    name: str
    season_or_cycle: str
    is_active: bool
    created_at: datetime
    items: List[MenuItemOut] = []
    model_config = ConfigDict(from_attributes=True)


# =====================================================================
# 5. INVENTORY & TRANSACTIONS SCHEMAS
# =====================================================================
class InventoryCreate(BaseModel):
    organization_id: str
    kitchen_id: Optional[str] = None
    item_name: str
    category: str = "PRODUCE"  # DRY_GOODS, PRODUCE, MEAT, DAIRY, PREPARED, CONDIMENT, BAKERY
    quantity: float = Field(..., gt=0)
    unit: str = "kg"
    storage_condition: str = "REFRIGERATED"  # DRY, REFRIGERATED, FROZEN, HOT_HOLDING
    storage_type: Optional[str] = None
    batch_number: Optional[str] = None
    batch: Optional[str] = None
    cost_per_unit_usd: float = 0.0
    cost: Optional[float] = None
    purchase_date: Optional[datetime] = None
    supplier: Optional[str] = None
    expiry_date: datetime
    status: str = "OPTIMAL"  # OPTIMAL, EXPIRING_SOON, CRITICAL, DEPLETED, QUARANTINED
    min_threshold_warning: float = 10.0

    @model_validator(mode="before")
    @classmethod
    def normalize_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "batch" in data and "batch_number" not in data:
                data["batch_number"] = data["batch"]
            if "batch_number" in data and "batch" not in data:
                data["batch"] = data["batch_number"]
            if "storage_type" in data and "storage_condition" not in data:
                data["storage_condition"] = data["storage_type"]
            if "storage_condition" in data and "storage_type" not in data:
                data["storage_type"] = data["storage_condition"]
            if "cost" in data and ("cost_per_unit_usd" not in data or data["cost_per_unit_usd"] == 0.0):
                data["cost_per_unit_usd"] = float(data["cost"])
            if "cost_per_unit_usd" in data and "cost" not in data:
                data["cost"] = data["cost_per_unit_usd"]
        return data


class InventoryUpdate(BaseModel):
    quantity: Optional[float] = None
    storage_condition: Optional[str] = None
    storage_type: Optional[str] = None
    expiry_date: Optional[datetime] = None
    supplier: Optional[str] = None
    cost_per_unit_usd: Optional[float] = None
    status: Optional[str] = None
    min_threshold_warning: Optional[float] = None


class InventoryOut(InventoryCreate):
    id: str
    is_quarantined: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PurchaseRecordCreate(BaseModel):
    organization_id: str
    kitchen_id: str
    supplier_name: str
    invoice_number: Optional[str] = None
    purchase_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    items: List[InventoryCreate]
    total_cost_usd: float = 0.0
    notes: Optional[str] = None


class PurchaseRecordOut(BaseModel):
    id: str
    organization_id: str
    kitchen_id: str
    supplier_name: str
    invoice_number: Optional[str] = None
    purchase_date: datetime
    total_cost_usd: float
    items_count: int
    notes: Optional[str] = None
    created_at: datetime


class StockAdjustRequest(BaseModel):
    quantity_change: float  # Positive to add, negative to consume/waste
    transaction_type: str = "ADJUSTMENT"  # PURCHASE, CONSUMPTION, PRODUCTION, ADJUSTMENT, WASTE, TRANSFER, DONATION
    reference_id: Optional[str] = None
    notes: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_tx_type(cls, data: Any) -> Any:
        if isinstance(data, dict) and "transaction_type" in data:
            tx = str(data["transaction_type"]).upper()
            mapping = {
                "INFLOW_PURCHASE": "PURCHASE",
                "OUTFLOW_PREP": "PRODUCTION",
                "MANUAL_ADJUSTMENT": "ADJUSTMENT",
                "SPOILAGE_DISCARD": "WASTE",
                "SURPLUS_DIVERTED": "DONATION"
            }
            data["transaction_type"] = mapping.get(tx, tx)
        return data


class InventoryTxOut(BaseModel):
    id: str
    inventory_id: str
    transaction_type: str
    quantity_change: float
    resulting_balance: float
    unit: Optional[str] = "kg"
    notes: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# =====================================================================
# 6. PRODUCTION & CONSUMPTION SCHEMAS
# =====================================================================
class ProductionBatchCreate(BaseModel):
    organization_id: str
    kitchen_id: str
    menu_item_id: Optional[str] = None
    batch_number: str
    planned_portions: int = Field(..., gt=0)
    actual_portions_prepped: int = Field(..., gt=0)
    total_batch_weight_kg: float = Field(..., gt=0)
    production_date: datetime
    prep_start_time: Optional[datetime] = None
    prep_end_time: Optional[datetime] = None
    holding_temperature_c: float = 65.0
    haccp_supervisor_user_id: Optional[str] = None


class ProductionBatchOut(ProductionBatchCreate):
    id: str
    status: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ConsumptionRecordCreate(BaseModel):
    organization_id: str
    kitchen_id: str
    production_batch_id: str
    meal_service: str = "LUNCH"  # BREAKFAST, LUNCH, DINNER, BANQUET_EVENT
    headcount_served: int = Field(..., ge=0)
    portions_consumed: int = Field(..., ge=0)
    portions_remaining_surplus: int = Field(..., ge=0)
    surplus_weight_kg: float = Field(..., ge=0)
    recorded_by_user_id: Optional[str] = None
    notes: Optional[str] = None


class ConsumptionRecordOut(ConsumptionRecordCreate):
    id: str
    service_date: datetime
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class LeftoverRouteRequest(BaseModel):
    action: str  # "DIVERT_TO_SURPLUS" or "LOG_AS_WASTE"
    quantity_kg: float = Field(..., gt=0)
    portions: int = Field(..., gt=0)
    notes: Optional[str] = None
    storage_temp_condition: Optional[str] = "REFRIGERATED_4C"


# =====================================================================
# 7. WASTE LOGGING & EPA TRACKING SCHEMAS
# =====================================================================
class WasteRecordCreate(BaseModel):
    organization_id: str
    kitchen_id: Optional[str] = None
    production_batch_id: Optional[str] = None
    production_batch: Optional[str] = None
    food_item: Optional[str] = "Prepared Food Items"
    quantity: Optional[float] = None
    quantity_kg: Optional[float] = None
    unit: str = "kg"
    reason: Optional[str] = None
    category: str = "OVERPRODUCTION"  # OVERPRODUCTION, PLATE_WASTE, SPOILAGE, EXPIRED, PREPARATION_WASTE, DAMAGED, QUALITY_REJECTION, OTHER
    date: Optional[datetime] = None
    logged_at: Optional[datetime] = None
    notes: Optional[str] = None
    image_url: Optional[str] = None
    waste_cost: Optional[float] = None
    financial_loss_usd: Optional[float] = 0.0
    epa_waste_tier: str = "COMPOSTING"
    corrective_action_taken: Optional[str] = None
    logged_by_user_id: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_waste_data(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Quantity normalization
            if "quantity" in data and ("quantity_kg" not in data or data["quantity_kg"] is None):
                data["quantity_kg"] = float(data["quantity"])
            elif "quantity_kg" in data and ("quantity" not in data or data["quantity"] is None):
                data["quantity"] = float(data["quantity_kg"])
            elif "quantity_kg" not in data and "quantity" not in data:
                data["quantity_kg"] = 1.0
                data["quantity"] = 1.0

            # Batch normalization
            if "production_batch" in data and "production_batch_id" not in data:
                data["production_batch_id"] = data["production_batch"]
            elif "production_batch_id" in data and "production_batch" not in data:
                data["production_batch"] = data["production_batch_id"]

            # Category / reason normalization
            if "category" in data and ("reason" not in data or data["reason"] is None):
                data["reason"] = data["category"]
            elif "reason" in data and ("category" not in data or data["category"] is None):
                data["category"] = data["reason"]

            # Cost normalization
            if "waste_cost" in data and ("financial_loss_usd" not in data or data["financial_loss_usd"] == 0.0):
                data["financial_loss_usd"] = float(data["waste_cost"])
            elif "financial_loss_usd" in data and "waste_cost" not in data:
                data["waste_cost"] = float(data["financial_loss_usd"])

            # Date normalization
            if "date" in data and "logged_at" not in data:
                data["logged_at"] = data["date"]
            elif "logged_at" in data and "date" not in data:
                data["date"] = data["logged_at"]
        return data


class WasteRecordOut(BaseModel):
    id: str
    organization_id: str
    kitchen_id: Optional[str] = None
    production_batch_id: Optional[str] = None
    food_item: Optional[str] = None
    quantity: float
    quantity_kg: float
    unit: str
    reason: str
    category: str
    date: datetime
    notes: Optional[str] = None
    image_url: Optional[str] = None
    financial_loss_usd: float
    waste_cost: float
    epa_waste_tier: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class WasteDataPoint(BaseModel):
    label: str
    date: Optional[str] = None
    quantity_kg: float
    cost_usd: float


class WasteCategoryBreakdown(BaseModel):
    category: str
    quantity_kg: float
    cost_usd: float
    percentage: float


class WasteItemBreakdown(BaseModel):
    food_item: str
    quantity_kg: float
    cost_usd: float
    occurrences: int


class WasteSummaryOut(BaseModel):
    total_waste_kg: float
    total_financial_loss_usd: float
    by_reason: Dict[str, float]
    by_epa_tier: Dict[str, float]


class WasteAnalyticsOut(BaseModel):
    daily_waste: List[WasteDataPoint]
    weekly_waste: List[WasteDataPoint]
    monthly_waste: List[WasteDataPoint]
    waste_by_category: List[WasteCategoryBreakdown]
    waste_by_food_item: List[WasteItemBreakdown]
    total_waste_kg: float
    waste_cost: float
    waste_trend_pct: float
    reduction_target_pct: float
    epa_tier_breakdown: Dict[str, float]


# =====================================================================
# 8. SURPLUS ITEMS & LOT DECLARATION SCHEMAS
# =====================================================================
class SurplusCreate(BaseModel):
    organization_id: str
    kitchen_id: Optional[str] = None
    production_batch_id: Optional[str] = None
    item_name: str
    category: str = "COOKED_MEALS"  # COOKED_MEALS, BAKERY, PRODUCE, DAIRY, MEAT_SEAFOOD, PACKAGED_GOODS
    quantity_kg: float = Field(..., gt=0)
    estimated_portions: int = Field(..., gt=0)
    packaging_type: str = "SEALED_CAMBRO_TRAYS"
    storage_temp_condition: str = "REFRIGERATED_4C"  # ROOM_TEMP, REFRIGERATED_4C, HOT_HOLDING_60C, FROZEN
    prepared_timestamp: Optional[datetime] = None
    consumption_safe_until: datetime
    pickup_window_start: datetime
    pickup_window_end: datetime
    pickup_address: str
    pickup_lat: float
    pickup_lng: float
    dietary_tags: List[str] = []
    allergens: List[str] = []
    haccp_verified: bool = True
    photo_url: Optional[str] = None


class SurplusUpdate(BaseModel):
    item_name: Optional[str] = None
    quantity_kg: Optional[float] = None
    estimated_portions: Optional[int] = None
    status: Optional[str] = None
    pickup_window_end: Optional[datetime] = None
    notes: Optional[str] = None


class SurplusOut(SurplusCreate):
    id: str
    status: str  # AVAILABLE, RESERVED, DISPATCHED, REDISTRIBUTED, EXPIRED, CANCELLED
    estimated_remaining_safe_hours: Optional[float] = None
    dispatch_priority_score: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# =====================================================================
# 9. RECIPIENTS & REQUIREMENTS SCHEMAS
# =====================================================================
class RecipientCreate(BaseModel):
    organization_id: str
    name: str
    recipient_type: str = "COMMUNITY_KITCHEN"  # FOOD_BANK, HOMELESS_SHELTER, COMMUNITY_KITCHEN, SENIOR_CENTER, RELIEF_CAMP
    address: str
    latitude: float
    longitude: float
    max_daily_intake_kg: float = 200.0
    cold_storage_available: bool = True
    walk_in_chiller_capacity_kg: float = 50.0
    verified_charity_id: Optional[str] = None
    contact_person: str
    contact_phone: str


class RecipientOut(RecipientCreate):
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class RecipientRequirementUpdate(BaseModel):
    acceptable_categories: List[str] = []
    dietary_preferences: List[str] = []
    required_storage_temp: str = "ANY"
    min_portions_per_drop: int = 10
    max_delivery_distance_km: float = 25.0


class RecipientRequirementOut(RecipientRequirementUpdate):
    id: str
    recipient_id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# =====================================================================
# 10. AI MATCHING & OPTIMIZATION SCHEMAS
# =====================================================================
class MatchCandidateOut(BaseModel):
    recipient_id: str
    recipient_name: str
    recipient_type: str
    distance_km: float
    compatibility_score: float  # 0.0 - 100.0
    dietary_match: bool
    capacity_sufficient: bool
    cold_chain_compatible: bool
    urgency_fit: str


class AutoMatchResponse(BaseModel):
    surplus_id: str
    item_name: str
    total_quantity_kg: float
    recommended_matches: List[MatchCandidateOut]
    match_engine_version: str = "FoodLoop-Heuristic-V2"


# =====================================================================
# 11. DONATIONS & LOGISTICS MANIFESTS SCHEMAS
# =====================================================================
class DonationItemCreate(BaseModel):
    surplus_item_id: str
    quantity_kg: float
    portions: int


class DonationItemOut(DonationItemCreate):
    id: str
    donation_id: str
    model_config = ConfigDict(from_attributes=True)


class DonationCreate(BaseModel):
    donor_org_id: str
    recipient_org_id: Optional[str] = None
    total_weight_kg: float
    total_portions: int
    haccp_verified: bool = True
    items: List[DonationItemCreate] = []


class DonationOut(BaseModel):
    id: str
    immutable_donation_id: Optional[str] = None
    donor_org_id: str
    recipient_org_id: Optional[str] = None
    tracking_number: str
    total_weight_kg: float
    total_portions: int
    status: str
    haccp_verified: bool
    declaration_timestamp: datetime
    created_at: datetime
    items: List[DonationItemOut] = []
    model_config = ConfigDict(from_attributes=True)


class VehicleCreate(BaseModel):
    organization_id: str
    license_plate: str
    vehicle_type: str = "REFRIGERATED_VAN"
    max_payload_kg: float = 400.0
    has_active_cooling: bool = True
    min_operating_temp_c: float = 2.0


class VehicleOut(VehicleCreate):
    id: str
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DriverCreate(BaseModel):
    user_id: str
    organization_id: str
    vehicle_id: Optional[str] = None
    license_number: str
    food_safety_certified: bool = True


class DriverOut(DriverCreate):
    id: str
    current_status: str
    current_lat: Optional[float] = None
    current_lng: Optional[float] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PickupRequestCreate(BaseModel):
    donation_id: str
    organization_id: str
    requested_window_start: datetime
    requested_window_end: datetime
    priority: str = "HIGH"
    special_handling_notes: Optional[str] = None


class PickupRequestOut(PickupRequestCreate):
    id: str
    status: str
    assigned_driver_id: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# =====================================================================
# 12. ROUTING & DELIVERIES SCHEMAS
# =====================================================================
class RouteCreate(BaseModel):
    organization_id: str
    driver_id: str
    vehicle_id: Optional[str] = None
    planned_start_time: datetime
    total_distance_km: float
    estimated_duration_minutes: float
    stops: List[Dict[str, Any]] = []


class RouteOut(RouteCreate):
    id: str
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DeliveryCreate(BaseModel):
    route_id: Optional[str] = None
    donation_id: str
    pickup_request_id: Optional[str] = None
    driver_id: Optional[str] = None
    stop_sequence: int = 1
    pickup_eta: Optional[datetime] = None
    dropoff_eta: Optional[datetime] = None


class DeliveryUpdate(BaseModel):
    status: Optional[str] = None
    actual_pickup_at: Optional[datetime] = None
    actual_dropoff_at: Optional[datetime] = None
    pickup_temp_c: Optional[float] = None
    dropoff_temp_c: Optional[float] = None
    proof_of_delivery_signature: Optional[str] = None
    notes: Optional[str] = None


class DeliveryOut(BaseModel):
    id: str
    route_id: Optional[str] = None
    donation_id: str
    driver_id: Optional[str] = None
    status: str
    stop_sequence: int
    pickup_temp_c: Optional[float] = None
    dropoff_temp_c: Optional[float] = None
    proof_of_delivery_signature: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# =====================================================================
# 13. QR VERIFICATION SCHEMAS
# =====================================================================
class QRGenerateRequest(BaseModel):
    delivery_id: str
    handover_type: str = "PICKUP"  # PICKUP, DROPOFF
    target_role: str = "DRIVER"


class QRGenerateResponse(BaseModel):
    token: str
    handover_type: str
    nonce: str
    hmac_signature: str
    expires_at: datetime
    qr_payload: Dict[str, Any]


class QRVerifyRequest(BaseModel):
    token: str
    handover_type: str
    current_lat: Optional[float] = None
    current_lng: Optional[float] = None
    measured_temp_c: Optional[float] = None


class QRVerifyResponse(BaseModel):
    verified: bool
    message: str
    delivery_id: str
    handover_type: str
    verified_at: datetime


# =====================================================================
# 14. NOTIFICATIONS SCHEMAS
# =====================================================================
class NotificationCreate(BaseModel):
    user_id: str
    organization_id: str
    title: str
    message: str
    category: str = "DISPATCH"  # URGENT_EXPIRY, DISPATCH, PRODUCTION, AUDIT, SYSTEM
    priority: str = "NORMAL"  # LOW, NORMAL, HIGH, CRITICAL
    action_url: Optional[str] = None


class NotificationOut(NotificationCreate):
    id: str
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# =====================================================================
# 15. ANALYTICS & IMPACT METRICS SCHEMAS
# =====================================================================
class ImpactOut(BaseModel):
    id: str
    organization_id: str
    donation_id: Optional[str] = None
    food_diverted_kg: float
    meals_provided: int
    co2e_avoided_kg: float
    water_saved_liters: float
    financial_value_usd: float
    calculation_methodology: str
    recorded_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AnalyticsSummaryOut(BaseModel):
    total_food_diverted_kg: float
    total_meals_provided: int
    total_co2e_avoided_kg: float
    total_water_saved_liters: float
    total_financial_value_usd: float
    active_donations_count: int
    active_surplus_lots_count: int
    diversion_rate_percentage: float


# =====================================================================
# 16. AI FORECAST & ASSISTANT SCHEMAS
# =====================================================================
class ForecastRequest(BaseModel):
    kitchen_id: str
    target_date: date
    historical_covers: Optional[int] = 400
    is_weekend: Optional[int] = 0
    event_flag: Optional[int] = 0
    temp_c: Optional[float] = 22.0


class ForecastResponse(BaseModel):
    kitchen_id: str
    target_date: date
    predicted_headcount: float
    predicted_surplus_kg: float
    confidence_interval: Dict[str, float]
    model_version: str = "v2.1"
    r2_score: float = 0.83


class AssistantQueryRequest(BaseModel):
    query: str
    category_filter: Optional[str] = None


class AssistantQueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[Dict[str, Any]] = []
    confidence_score: float = 0.95


class RecipeGenRequest(BaseModel):
    ingredients: List[str]
    servings: int = 50
    dietary_preference: str = "any"


class RecipeGenResponse(BaseModel):
    recipe_title: str
    prep_time_mins: int
    estimated_servings: int
    ingredients_used: List[str]
    instructions: List[str]
    safety_tips: List[str]


# =====================================================================
# 17. DOCUMENTS SCHEMAS
# =====================================================================
class DocumentCreate(BaseModel):
    title: str
    category: str = "FDA_FOOD_CODE"  # FDA_FOOD_CODE, GOOD_SAMARITAN_ACT, HACCP_SOP, COLD_CHAIN_STANDARD, MUNICIPAL_BYLAW
    content: str
    regulatory_source: Optional[str] = None
    document_version: str = "2024.1"
    is_public: bool = True


class DocumentOut(DocumentCreate):
    id: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# =====================================================================
# 18. ADMIN & AUDIT SCHEMAS
# =====================================================================
class AuditLogOut(BaseModel):
    id: str
    organization_id: Optional[str] = None
    user_id: Optional[str] = None
    module: str
    action: str
    entity_name: str
    entity_id: str
    client_ip: Optional[str] = None
    sha256_hash: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SystemHealthOut(BaseModel):
    service: str = "FoodLoop AI Backend"
    status: str = "operational"
    version: str = "1.0.0"
    database_connected: bool = True
    database_dialect: str = "postgresql"
    uptime_seconds: float
