"""
FoodLoop AI - Super Admin Dashboard Schemas (Phase 16)
Pydantic contracts for Platform Overview KPIs, Geographic Maps, 6-Category Alerts,
Forensic Audit Logging, ML Telemetry, and Governed Administrative Actions.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


# -----------------------------------------------------------------------------
# 1. PLATFORM OVERVIEW & 11 KPIs
# -----------------------------------------------------------------------------
class AdminOverviewKpiOut(BaseModel):
    """
    Mandatory 11 Super Admin KPIs as specified in Phase 16:
    Total organizations, Active kitchens, Processing units, Registered recipients,
    Food rescued, Waste generated, Waste reduction, Successful donations,
    Active deliveries, People served, Estimated value preserved.
    """
    total_organizations: int = Field(..., description="Total platform registered organizations")
    active_kitchens: int = Field(..., description="Active commercial & institutional kitchens")
    processing_units: int = Field(..., description="Operational Food Processing Units (FPUs)")
    registered_recipients: int = Field(..., description="Total verified/registered charities & food banks")
    food_rescued_kg: float = Field(..., description="Total weight of food rescued (kg)")
    waste_generated_kg: float = Field(..., description="Total recorded food waste (kg)")
    waste_reduction_pct: float = Field(..., description="Percentage of waste diverted/reduced")
    successful_donations: int = Field(..., description="Number of fully completed and verified donations")
    active_deliveries: int = Field(..., description="Live courier deliveries currently in transit")
    people_served: int = Field(..., description="Estimated total meals / people served via rescued food")
    estimated_value_preserved_usd: float = Field(..., description="Economic value preserved from diversion ($)")
    calculated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------------------------
# 2. GEOGRAPHIC MAP SCHEMAS
# -----------------------------------------------------------------------------
class AdminMapNodeOut(BaseModel):
    """Geographic coordinate node for interactive platform map."""
    id: str
    name: str
    node_type: str = Field(..., description="'KITCHEN', 'PROCESSING_UNIT', 'RECIPIENT', or 'COURIER'")
    latitude: float
    longitude: float
    address: Optional[str] = None
    status: str = Field(..., description="'ACTIVE', 'INACTIVE', 'IN_TRANSIT', 'VERIFIED', etc.")
    contact_phone: Optional[str] = None
    organization_name: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class AdminGeoMapResponse(BaseModel):
    total_nodes: int
    kitchens_count: int
    fpus_count: int
    recipients_count: int
    couriers_count: int
    nodes: List[AdminMapNodeOut]


# -----------------------------------------------------------------------------
# 3. SYSTEM ALERTS (6 Categories)
# -----------------------------------------------------------------------------
class AdminAlertItemOut(BaseModel):
    """
    Platform alert conforming to the 6 mandated categories:
    - expired surplus
    - failed delivery
    - abnormal waste increase
    - model failure
    - low prediction confidence
    - system errors
    """
    id: str
    category: str = Field(..., description="expired_surplus | failed_delivery | abnormal_waste_increase | model_failure | low_prediction_confidence | system_errors")
    severity: str = Field(..., description="CRITICAL | HIGH | MEDIUM | LOW")
    title: str
    message: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AdminAlertsSummaryOut(BaseModel):
    total_active_alerts: int
    by_category: Dict[str, int]
    alerts: List[AdminAlertItemOut]


# -----------------------------------------------------------------------------
# 4. BUSINESS RULES SCHEMAS
# -----------------------------------------------------------------------------
class BusinessRuleCreate(BaseModel):
    rule_key: str = Field(..., min_length=3, max_length=100)
    rule_name: str = Field(..., min_length=3, max_length=255)
    category: str = Field("OPERATIONS", description="OPERATIONS | FOOD_SAFETY | ML_FORECAST | LOGISTICS | NOTIFICATIONS")
    value: Any = Field(..., description="Configurable rule value (scalar, dict, list)")
    description: Optional[str] = None
    is_active: bool = True


class BusinessRuleUpdate(BaseModel):
    rule_name: Optional[str] = None
    category: Optional[str] = None
    value: Optional[Any] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class BusinessRuleOut(BaseModel):
    id: str
    rule_key: str
    rule_name: str
    category: str
    value: Any
    description: Optional[str] = None
    is_active: bool
    updated_by_user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------------------------
# 5. GOVERNED ADMIN ACTIONS (All strictly audited)
# -----------------------------------------------------------------------------
class AdminOrgActionRequest(BaseModel):
    action: str = Field(..., pattern="^(ACTIVATE|SUSPEND|VERIFY)$")
    reason: str = Field(..., min_length=5, max_length=500, description="Mandatory audit justification")


class AdminRecipientApprovalRequest(BaseModel):
    status: str = Field(..., pattern="^(VERIFIED|REJECTED|PENDING)$")
    notes: Optional[str] = Field(None, max_length=500)


class AdminUserSuspensionRequest(BaseModel):
    is_active: bool = Field(..., description="True to activate, False to suspend")
    reason: str = Field(..., min_length=5, max_length=500, description="Mandatory audit justification")


# -----------------------------------------------------------------------------
# 6. ML & CV MODEL PERFORMANCE TELEMETRY
# -----------------------------------------------------------------------------
class ModelMetricDetail(BaseModel):
    model_name: str
    version: str
    task: str  # "DEMAND_FORECAST", "WASTE_PREDICTION", "COMPUTER_VISION"
    status: str  # "OPTIMAL", "DRIFT_DETECTED", "DEGRADED"
    r2_score: Optional[float] = None
    mae: Optional[float] = None
    rmse: Optional[float] = None
    accuracy_pct: Optional[float] = None
    mean_confidence: Optional[float] = None
    low_confidence_pct: Optional[float] = None
    inference_latency_ms: float
    total_predictions_analyzed: int
    last_updated: datetime


class AdminModelPerformanceOut(BaseModel):
    overall_health: str = Field("OPTIMAL", description="OPTIMAL | ATTENTION_REQUIRED | CRITICAL")
    models: List[ModelMetricDetail]


# -----------------------------------------------------------------------------
# 7. FORENSIC AUDIT LOG VIEWER SCHEMAS
# -----------------------------------------------------------------------------
class AdminAuditLogItemOut(BaseModel):
    id: str
    organization_id: Optional[str] = None
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    module: str
    action: str
    entity_name: str
    entity_id: str
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    client_ip: Optional[str] = None
    sha256_hash: str
    is_hash_valid: bool = True
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminAuditLogsResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[AdminAuditLogItemOut]
