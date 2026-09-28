"""
FoodLoop AI - Phase 14 Food Processing Unit (FPU) Pydantic Schemas
Defines data validation contracts for:
1. Raw material inventory with FEFO expiry tracking & quality status
2. Production batches with yield, damaged packaging, and quality rejections
3. FEFO (First Expire, First Out) material allocation and pick sequencing
4. Configurable threshold alert rules (7d, 3d, 1d or product/category custom rules)
5. Real-time automatic expiry and quality alerts
6. Batch traceability: Raw material -> Production batch -> Finished product -> Surplus/Donation -> Recipient
7. FPU Executive Dashboard KPI aggregations
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# =====================================================================
# 1. RAW MATERIAL INVENTORY SCHEMAS
# =====================================================================

class FpuRawMaterialCreate(BaseModel):
    processing_unit_id: Optional[str] = None
    material_name: str = Field(..., description="Raw material or feedstock name")
    category: str = Field("PRODUCE", description="PRODUCE, GRAINS, DAIRY, LIQUIDS, PACKAGING, SEASONINGS, BAKERY_TRIMMINGS, MEAT")
    lot_number: str = Field(..., description="Supplier or intake lot number")
    initial_quantity: float = Field(..., gt=0, description="Intake quantity")
    current_quantity: Optional[float] = Field(None, description="Available quantity (defaults to initial)")
    unit: str = Field("kg", description="Measurement unit (kg, L, units, bags)")
    storage_condition: str = Field("REFRIGERATED", description="REFRIGERATED, DRY_STORAGE, FROZEN, AMBIENT")
    storage_location: str = Field("Cold Storage Bay 1", description="Physical location or tank/shelf ID")
    harvest_or_mfg_date: datetime = Field(..., description="Date of harvest or supplier manufacture")
    expiry_date: datetime = Field(..., description="Expiration date for FEFO sequencing")
    quality_status: str = Field("APPROVED", description="APPROVED, UNDER_REVIEW, REJECTED, QUARANTINED")
    packaging_condition: str = Field("INTACT", description="INTACT, DAMAGED_PACKAGING, LEAKING, SEAL_COMPROMISED")
    damaged_quantity: float = Field(0.0, ge=0, description="Quantity in damaged packaging")
    rejection_reason: Optional[str] = Field(None, description="Specific defect reason if rejected")
    disposition_action: Optional[str] = Field(None, description="ANIMAL_FEED_VALORIZATION, COMPOSTING, SAFE_DISPOSAL, RETURN_SUPPLIER")
    supplier: Optional[str] = Field(None, description="Origin farm, commercial kitchen or vendor")
    cost_per_unit: float = Field(0.0, ge=0, description="Intake cost per unit")


class FpuRawMaterialUpdate(BaseModel):
    quality_status: Optional[str] = None
    packaging_condition: Optional[str] = None
    damaged_quantity: Optional[float] = None
    rejection_reason: Optional[str] = None
    disposition_action: Optional[str] = None
    status: Optional[str] = None
    current_quantity: Optional[float] = None
    storage_location: Optional[str] = None


class FpuRawMaterialOut(BaseModel):
    id: str
    processing_unit_id: str
    material_name: str
    category: str
    lot_number: str
    initial_quantity: float
    current_quantity: float
    unit: str
    storage_condition: str
    storage_location: str
    harvest_or_mfg_date: datetime
    expiry_date: datetime
    quality_status: str
    packaging_condition: str
    damaged_quantity: float
    rejection_reason: Optional[str] = None
    disposition_action: Optional[str] = None
    supplier: Optional[str] = None
    cost_per_unit: float
    status: str
    days_to_expiry: float
    expiry_urgency_tier: str  # EXPIRED, CRITICAL_1_DAY, URGENT_3_DAYS, WARNING_7_DAYS, OPTIMAL
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# =====================================================================
# 2. FEFO (FIRST EXPIRE, FIRST OUT) SCHEMAS
# =====================================================================

class FefoPickItem(BaseModel):
    raw_material_id: str
    lot_number: str
    material_name: str
    category: str
    storage_location: str
    expiry_date: datetime
    days_to_expiry: float
    lot_available_quantity: float
    allocated_quantity: float
    remaining_in_lot: float
    unit: str
    fefo_sequence: int


class FefoAllocationRequest(BaseModel):
    material_name: Optional[str] = Field(None, description="Specific raw material name to allocate")
    category: Optional[str] = Field(None, description="Category filter if generic")
    required_quantity: float = Field(..., gt=0, description="Total amount required for batch")
    unit: str = Field("kg", description="Unit of measurement")


class FefoAllocationResponse(BaseModel):
    material_name: Optional[str]
    required_quantity: float
    total_allocated: float
    is_fulfilled: bool
    shortage_quantity: float
    fefo_compliance_score: float = Field(100.0, description="Percentage score for FEFO optimization")
    pick_list: List[FefoPickItem] = []
    reasoning: List[str] = []


class FefoQueueItem(BaseModel):
    raw_material_id: str
    lot_number: str
    material_name: str
    category: str
    current_quantity: float
    unit: str
    storage_location: str
    expiry_date: datetime
    days_to_expiry: float
    urgency_tier: str
    fefo_priority_rank: int
    quality_status: str
    packaging_condition: str


# =====================================================================
# 3. PRODUCTION BATCH SCHEMAS
# =====================================================================

class MaterialUsageInput(BaseModel):
    raw_material_id: str
    quantity_used: float = Field(..., gt=0)
    fefo_sequence_order: int = Field(1, ge=1)


class FpuProductionBatchCreate(BaseModel):
    processing_unit_id: Optional[str] = None
    batch_number: str = Field(..., description="Unique production batch code, e.g. FPU-PB-2026-041")
    product_name: str = Field(..., description="Finished / upcycled product name")
    category: str = Field("PROCESSED_CANNING", description="PROCESSED_CANNING, DEHYDRATED, PUREE, BAKERY_REPROCESSED, JUICE_BEVERAGE, VALUE_ADDED")
    planned_quantity: float = Field(..., gt=0, description="Planned output quantity")
    actual_quantity: float = Field(..., ge=0, description="Actual prepared quantity yield")
    unit: str = Field("kg", description="Unit of yield (kg, jars, pouches, boxes)")
    manufacturing_date: datetime = Field(..., description="Batch manufacturing completion date")
    expiry_date: datetime = Field(..., description="Finished product best-before or expiration date")
    quality_status: str = Field("PASSED", description="PASSED, UNDER_REVIEW, REJECTED, DAMAGED_PACKAGING, QUARANTINED")
    packaging_condition: str = Field("INTACT", description="INTACT, DAMAGED_PACKAGING, SEAL_FAILURE, DEFECTIVE_LABEL, DENTED_CONTAINER")
    damaged_packaging_units: float = Field(0.0, ge=0, description="Count of units with packaging failure")
    rejected_quantity: float = Field(0.0, ge=0, description="Quantity rejected due to quality check")
    rejection_reason: Optional[str] = Field(None, description="pH out of bounds, seal breach, foreign particulate, etc.")
    disposition_action: Optional[str] = Field(None, description="RE_PROCESS, ANIMAL_FEED_VALORIZATION, COMPOST_BIOGAS, HAZARDOUS_DISPOSAL")
    surplus_quantity: float = Field(0.0, ge=0, description="Portion of finished batch exceeding demand, ready for redistribution")
    status: str = Field("COMPLETED", description="PLANNED, IN_PRODUCTION, QUALITY_CONTROL, COMPLETED, QUARANTINED, REJECTED")
    operator_notes: Optional[str] = None
    qc_officer: Optional[str] = None
    raw_materials: List[MaterialUsageInput] = Field([], description="Raw material lot allocations consumed by this batch")


class FpuBatchQualityUpdate(BaseModel):
    quality_status: str = Field(..., description="PASSED, UNDER_REVIEW, REJECTED, DAMAGED_PACKAGING, QUARANTINED")
    packaging_condition: Optional[str] = None
    damaged_packaging_units: Optional[float] = None
    rejected_quantity: Optional[float] = None
    rejection_reason: Optional[str] = None
    disposition_action: Optional[str] = None
    qc_officer: Optional[str] = None
    notes: Optional[str] = None


class FpuBatchMaterialUsageOut(BaseModel):
    id: str
    raw_material_id: str
    raw_material_name: str
    lot_number: str
    quantity_used: float
    unit: str
    fefo_sequence_order: int
    lot_expiry_at_consumption: datetime
    model_config = ConfigDict(from_attributes=True)


class FpuProductionBatchOut(BaseModel):
    id: str
    processing_unit_id: str
    batch_number: str
    product_name: str
    category: str
    planned_quantity: float
    actual_quantity: float
    unit: str
    manufacturing_date: datetime
    expiry_date: datetime
    quality_status: str
    packaging_condition: str
    damaged_packaging_units: float
    rejected_quantity: float
    rejection_reason: Optional[str] = None
    disposition_action: Optional[str] = None
    yield_percentage: float
    surplus_quantity: float
    redistributable_stock: float
    redistribution_status: str
    status: str
    operator_notes: Optional[str] = None
    qc_officer: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    raw_materials_used: List[FpuBatchMaterialUsageOut] = []
    days_to_expiry: float
    expiry_urgency_tier: str
    model_config = ConfigDict(from_attributes=True)


# =====================================================================
# 4. SURPLUS REDISTRIBUTION SCHEMAS
# =====================================================================

class FpuRedistributeRequest(BaseModel):
    redistribute_quantity: float = Field(..., gt=0, description="Amount of surplus batch to redistribute")
    recipient_id: Optional[str] = Field(None, description="Direct target recipient organization (NGO, food bank)")
    title: Optional[str] = Field(None, description="Listing title")
    notes: Optional[str] = None
    pickup_address: Optional[str] = None


class FpuRedistributeResponse(BaseModel):
    batch_id: str
    batch_number: str
    surplus_item_id: str
    redistributed_quantity: float
    unit: str
    remaining_stock: float
    status: str
    recipient_name: Optional[str] = None
    message: str


# =====================================================================
# 5. CONFIGURABLE ALERT THRESHOLD SCHEMAS
# =====================================================================

class FpuExpiryThresholdRuleCreate(BaseModel):
    target_type: str = Field("CATEGORY", description="CATEGORY, PRODUCT, RAW_MATERIAL")
    target_name: str = Field(..., description="Target category or product name (e.g. DAIRY, PRODUCE, Tomato Puree)")
    warning_threshold_days: float = Field(7.0, ge=0.1, description="Days before expiry to raise warning alert (Default: 7)")
    urgent_threshold_days: float = Field(3.0, ge=0.1, description="Days before expiry to raise urgent alert (Default: 3)")
    critical_threshold_days: float = Field(1.0, ge=0.1, description="Days before expiry to raise critical alert (Default: 1)")
    custom_safety_notes: Optional[str] = Field(None, description="Regulatory reference or storage guidelines")


class FpuExpiryThresholdRuleOut(FpuExpiryThresholdRuleCreate):
    id: str
    organization_id: Optional[str] = None
    processing_unit_id: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# =====================================================================
# 6. AUTOMATIC EXPIRY & QUALITY ALERTS SCHEMAS
# =====================================================================

class FpuAlertItem(BaseModel):
    alert_id: str
    item_type: str  # RAW_MATERIAL or PRODUCTION_BATCH
    item_id: str
    code: str  # Lot number or Batch number
    name: str
    category: str
    quantity: float
    unit: str
    manufacturing_or_harvest_date: datetime
    expiry_date: datetime
    days_remaining: float
    alert_severity: str  # EXPIRED, CRITICAL_1_DAY, URGENT_3_DAYS, WARNING_7_DAYS
    applicable_rule: str
    threshold_days_used: float
    quality_status: str
    packaging_condition: str
    recommended_action: str


class FpuAlertsSummary(BaseModel):
    total_alerts: int
    expired_count: int
    critical_count: int  # <= 1 day
    urgent_count: int    # <= 3 days
    warning_count: int   # <= 7 days
    quality_defects_count: int
    alerts: List[FpuAlertItem] = []


# =====================================================================
# 7. BATCH TRACEABILITY SCHEMAS
# =====================================================================

class TraceabilityNode(BaseModel):
    step: int
    stage: str  # RAW_MATERIAL, PRODUCTION_BATCH, FINISHED_PRODUCT, SURPLUS_DONATION, RECIPIENT
    identifier: str
    name: str
    quantity: float
    unit: str
    timestamp: Optional[datetime] = None
    quality_status: str
    packaging_condition: Optional[str] = None
    facility_or_org: str
    details: Dict[str, Any] = {}


class FpuBatchTraceabilityChain(BaseModel):
    query_identifier: str
    root_stage: str
    summary: str
    raw_materials: List[Dict[str, Any]] = []
    production_batch: Optional[Dict[str, Any]] = None
    finished_product: Optional[Dict[str, Any]] = None
    surplus_donation: Optional[Dict[str, Any]] = None
    recipient: Optional[Dict[str, Any]] = None
    linear_trace_steps: List[TraceabilityNode] = []


# =====================================================================
# 8. EXECUTIVE DASHBOARD SCHEMAS
# =====================================================================

class FpuDashboardInventoryMetrics(BaseModel):
    total_raw_material_kg: float
    total_finished_product_kg: float
    total_inventory_kg: float
    total_raw_lots_count: int
    total_active_batches_count: int
    estimated_inventory_value_usd: float


class FpuDashboardNearExpiryMetrics(BaseModel):
    total_near_expiry_count: int
    total_near_expiry_kg: float
    warning_7d_count: int
    urgent_3d_count: int
    critical_1d_count: int
    items: List[FpuAlertItem] = []


class FpuDashboardExpiredMetrics(BaseModel):
    total_expired_count: int
    total_expired_kg: float
    quarantined_count: int
    items: List[FpuAlertItem] = []


class FpuDashboardProductionMetrics(BaseModel):
    total_batches_all_time: int
    completed_batches_count: int
    active_in_production_count: int
    total_yield_kg: float
    average_yield_percentage: float
    fefo_adherence_percentage: float


class FpuDashboardRejectedMetrics(BaseModel):
    rejected_products_count: int
    total_rejected_kg: float
    damaged_packaging_incidents: int
    damaged_units_count: float
    by_disposition: Dict[str, float] = {}
    by_rejection_reason: Dict[str, int] = {}


class FpuDashboardRedistributionMetrics(BaseModel):
    total_surplus_generated_kg: float
    current_redistributable_stock_kg: float
    allocated_to_donations_kg: float
    dispatched_to_recipients_kg: float
    active_recipient_partners_count: int
    redistributable_batches_count: int


class FpuDashboardSummary(BaseModel):
    processing_unit_id: str
    processing_unit_name: str
    processing_type: str
    inventory: FpuDashboardInventoryMetrics
    near_expiry: FpuDashboardNearExpiryMetrics
    expired: FpuDashboardExpiredMetrics
    production: FpuDashboardProductionMetrics
    rejected: FpuDashboardRejectedMetrics
    redistributable_stock: FpuDashboardRedistributionMetrics
