"""
FoodLoop AI - Food Processing Units API Router (Phase 14)
Manages industrial food processing facilities, raw material inventory with FEFO,
production batches, damaged packaging & rejection stations, configurable expiry alerts,
batch traceability (raw material -> batch -> finished product -> surplus -> recipient),
and executive operational dashboards.
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.models.models import ProcessingUnit, FpuRawMaterial, FpuProductionBatch, FpuExpiryAlertThreshold
from app.schemas.enterprise_schemas import ProcessingUnitCreate, ProcessingUnitOut
from app.schemas.fpu_schemas import (
    FpuRawMaterialCreate,
    FpuRawMaterialUpdate,
    FpuRawMaterialOut,
    FefoAllocationRequest,
    FefoAllocationResponse,
    FefoQueueItem,
    FpuProductionBatchCreate,
    FpuProductionBatchOut,
    FpuBatchQualityUpdate,
    FpuRedistributeRequest,
    FpuRedistributeResponse,
    FpuExpiryThresholdRuleCreate,
    FpuExpiryThresholdRuleOut,
    FpuAlertsSummary,
    FpuBatchTraceabilityChain,
    FpuDashboardSummary
)
from app.services.fpu_service import FpuService
from app.repositories.base import BaseRepository
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/processing", tags=["14. Food Processing Unit & FEFO Operations"])


# =====================================================================
# 1. PROCESSING UNIT MANAGEMENT
# =====================================================================

@router.get("", response_model=dict)
def list_processing_units(
    organization_id: Optional[str] = Query(None),
    params: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Lists processing units with pagination."""
    repo = BaseRepository(ProcessingUnit, db)
    filters = {"organization_id": organization_id} if organization_id else {}
    return repo.list(params, filters=filters, search_columns=["name", "processing_type"])


@router.post("", response_model=ProcessingUnitOut, status_code=status.HTTP_201_CREATED)
def create_processing_unit(
    unit_in: ProcessingUnitCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "PROCESSOR", "SUPER_ADMIN", "KITCHEN_MANAGER"]))
):
    """Registers a food processing and upcycling facility."""
    repo = BaseRepository(ProcessingUnit, db)
    return repo.create(**unit_in.model_dump())


@router.get("/{unit_id}", response_model=ProcessingUnitOut)
def get_processing_unit(
    unit_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Retrieves processing unit details."""
    repo = BaseRepository(ProcessingUnit, db)
    return repo.get_or_404(unit_id, "ProcessingUnit")


# =====================================================================
# 2. RAW MATERIAL INVENTORY & FEFO
# =====================================================================

@router.get("/{unit_id}/raw-materials", response_model=List[FpuRawMaterialOut])
def list_raw_materials(
    unit_id: str,
    category: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    quality_status: Optional[str] = Query(None),
    packaging_condition: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort_by_fefo: bool = Query(True, description="Sort ascending by expiry date (FEFO)"),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Lists raw material inventory for a processing unit with expiry urgency calculations.
    Supports FEFO sorting, category filtering, quality status, and packaging checks.
    """
    return FpuService.list_raw_materials(
        db,
        unit_id,
        category=category,
        status_filter=status_filter,
        quality_status=quality_status,
        packaging_condition=packaging_condition,
        search=search,
        sort_by_fefo=sort_by_fefo
    )


@router.post("/{unit_id}/raw-materials", response_model=FpuRawMaterialOut, status_code=status.HTTP_201_CREATED)
def intake_raw_material(
    unit_id: str,
    material_in: FpuRawMaterialCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "PROCESSOR", "SUPER_ADMIN", "KITCHEN_MANAGER"]))
):
    """Intakes a new batch or lot of raw material feedstock into the processing unit."""
    try:
        material = FpuService.intake_raw_material(db, unit_id, material_in)
        days_rem, tier = FpuService.calculate_urgency_tier(material.expiry_date)
        return {
            "id": material.id,
            "processing_unit_id": material.processing_unit_id,
            "material_name": material.material_name,
            "category": material.category,
            "lot_number": material.lot_number,
            "initial_quantity": material.initial_quantity,
            "current_quantity": material.current_quantity,
            "unit": material.unit,
            "storage_condition": material.storage_condition,
            "storage_location": material.storage_location,
            "harvest_or_mfg_date": material.harvest_or_mfg_date,
            "expiry_date": material.expiry_date,
            "quality_status": material.quality_status,
            "packaging_condition": material.packaging_condition,
            "damaged_quantity": material.damaged_quantity,
            "rejection_reason": material.rejection_reason,
            "disposition_action": material.disposition_action,
            "supplier": material.supplier,
            "cost_per_unit": material.cost_per_unit,
            "status": material.status,
            "days_to_expiry": days_rem,
            "expiry_urgency_tier": tier,
            "created_at": material.created_at,
            "updated_at": material.updated_at
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/raw-materials/{material_id}", response_model=FpuRawMaterialOut)
def get_raw_material(
    material_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Retrieves specific raw material lot details with expiry countdown."""
    rm = db.query(FpuRawMaterial).filter(FpuRawMaterial.id == material_id).first()
    if not rm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Raw material '{material_id}' not found.")
    days_rem, tier = FpuService.calculate_urgency_tier(rm.expiry_date)
    return {
        "id": rm.id,
        "processing_unit_id": rm.processing_unit_id,
        "material_name": rm.material_name,
        "category": rm.category,
        "lot_number": rm.lot_number,
        "initial_quantity": rm.initial_quantity,
        "current_quantity": rm.current_quantity,
        "unit": rm.unit,
        "storage_condition": rm.storage_condition,
        "storage_location": rm.storage_location,
        "harvest_or_mfg_date": rm.harvest_or_mfg_date,
        "expiry_date": rm.expiry_date,
        "quality_status": rm.quality_status,
        "packaging_condition": rm.packaging_condition,
        "damaged_quantity": rm.damaged_quantity,
        "rejection_reason": rm.rejection_reason,
        "disposition_action": rm.disposition_action,
        "supplier": rm.supplier,
        "cost_per_unit": rm.cost_per_unit,
        "status": rm.status,
        "days_to_expiry": days_rem,
        "expiry_urgency_tier": tier,
        "created_at": rm.created_at,
        "updated_at": rm.updated_at
    }


@router.patch("/raw-materials/{material_id}/status", response_model=FpuRawMaterialOut)
def update_raw_material_status(
    material_id: str,
    update_in: FpuRawMaterialUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "PROCESSOR", "SUPER_ADMIN", "KITCHEN_MANAGER"]))
):
    """Updates quality status, damaged packaging condition, rejection reason, or disposition."""
    rm = db.query(FpuRawMaterial).filter(FpuRawMaterial.id == material_id).first()
    if not rm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Raw material '{material_id}' not found.")

    if update_in.quality_status:
        rm.quality_status = update_in.quality_status
    if update_in.packaging_condition:
        rm.packaging_condition = update_in.packaging_condition
    if update_in.damaged_quantity is not None:
        rm.damaged_quantity = update_in.damaged_quantity
    if update_in.rejection_reason:
        rm.rejection_reason = update_in.rejection_reason
    if update_in.disposition_action:
        rm.disposition_action = update_in.disposition_action
    if update_in.status:
        rm.status = update_in.status
    if update_in.current_quantity is not None:
        rm.current_quantity = update_in.current_quantity
    if update_in.storage_location:
        rm.storage_location = update_in.storage_location

    db.commit()
    db.refresh(rm)
    days_rem, tier = FpuService.calculate_urgency_tier(rm.expiry_date)
    return {
        "id": rm.id,
        "processing_unit_id": rm.processing_unit_id,
        "material_name": rm.material_name,
        "category": rm.category,
        "lot_number": rm.lot_number,
        "initial_quantity": rm.initial_quantity,
        "current_quantity": rm.current_quantity,
        "unit": rm.unit,
        "storage_condition": rm.storage_condition,
        "storage_location": rm.storage_location,
        "harvest_or_mfg_date": rm.harvest_or_mfg_date,
        "expiry_date": rm.expiry_date,
        "quality_status": rm.quality_status,
        "packaging_condition": rm.packaging_condition,
        "damaged_quantity": rm.damaged_quantity,
        "rejection_reason": rm.rejection_reason,
        "disposition_action": rm.disposition_action,
        "supplier": rm.supplier,
        "cost_per_unit": rm.cost_per_unit,
        "status": rm.status,
        "days_to_expiry": days_rem,
        "expiry_urgency_tier": tier,
        "created_at": rm.created_at,
        "updated_at": rm.updated_at
    }


# =====================================================================
# 3. FEFO (FIRST EXPIRE, FIRST OUT) ALLOCATION & QUEUE
# =====================================================================

@router.post("/{unit_id}/fefo/allocate", response_model=FefoAllocationResponse)
def allocate_fefo(
    unit_id: str,
    req: FefoAllocationRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Executes First Expire, First Out (FEFO) allocation.
    Evaluates available non-expired lots in ascending expiry order and provides
    optimal pick list, sequence breakdown, and compliance score.
    """
    return FpuService.allocate_fefo(db, unit_id, req)


@router.get("/{unit_id}/fefo/queue", response_model=List[FefoQueueItem])
def get_fefo_queue(
    unit_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Returns the real-time FEFO consumption queue for the processing unit.
    Lots are strictly ranked by earliest expiry date.
    """
    return FpuService.get_fefo_queue(db, unit_id)


# =====================================================================
# 4. PRODUCTION BATCHES & UP-CYCLING
# =====================================================================

@router.get("/{unit_id}/batches", response_model=List[FpuProductionBatchOut])
def list_production_batches(
    unit_id: str,
    status_filter: Optional[str] = Query(None, alias="status"),
    category: Optional[str] = Query(None),
    quality_status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Lists production batches for the facility with yield metrics and linked raw material usages."""
    query = db.query(FpuProductionBatch).filter(FpuProductionBatch.processing_unit_id == unit_id)

    if status_filter:
        query = query.filter(FpuProductionBatch.status == status_filter.upper())
    if category:
        query = query.filter(FpuProductionBatch.category == category.upper())
    if quality_status:
        query = query.filter(FpuProductionBatch.quality_status == quality_status.upper())

    batches = query.order_by(FpuProductionBatch.created_at.desc()).all()
    now = datetime.now(timezone.utc)
    results = []

    for b in batches:
        days_rem, tier = FpuService.calculate_urgency_tier(b.expiry_date, now)
        usages_out = []
        for u in b.raw_material_usages:
            usages_out.append({
                "id": u.id,
                "raw_material_id": u.raw_material_id,
                "raw_material_name": u.raw_material.material_name if u.raw_material else "Raw Feedstock",
                "lot_number": u.raw_material.lot_number if u.raw_material else "LOT-UNKNOWN",
                "quantity_used": u.quantity_used,
                "unit": u.unit,
                "fefo_sequence_order": u.fefo_sequence_order,
                "lot_expiry_at_consumption": u.lot_expiry_at_consumption
            })

        results.append({
            "id": b.id,
            "processing_unit_id": b.processing_unit_id,
            "batch_number": b.batch_number,
            "product_name": b.product_name,
            "category": b.category,
            "planned_quantity": b.planned_quantity,
            "actual_quantity": b.actual_quantity,
            "unit": b.unit,
            "manufacturing_date": b.manufacturing_date,
            "expiry_date": b.expiry_date,
            "quality_status": b.quality_status,
            "packaging_condition": b.packaging_condition,
            "damaged_packaging_units": b.damaged_packaging_units,
            "rejected_quantity": b.rejected_quantity,
            "rejection_reason": b.rejection_reason,
            "disposition_action": b.disposition_action,
            "yield_percentage": b.yield_percentage,
            "surplus_quantity": b.surplus_quantity,
            "redistributable_stock": b.redistributable_stock,
            "redistribution_status": b.redistribution_status,
            "status": b.status,
            "operator_notes": b.operator_notes,
            "qc_officer": b.qc_officer,
            "created_at": b.created_at,
            "updated_at": b.updated_at,
            "raw_materials_used": usages_out,
            "days_to_expiry": days_rem,
            "expiry_urgency_tier": tier
        })
    return results


@router.post("/{unit_id}/batches", response_model=FpuProductionBatchOut, status_code=status.HTTP_201_CREATED)
def create_production_batch(
    unit_id: str,
    batch_in: FpuProductionBatchCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "PROCESSOR", "SUPER_ADMIN", "KITCHEN_MANAGER"]))
):
    """
    Creates a new FPU production batch.
    Automatically consumes raw material lots in FEFO order, records material usages,
    and calculates output yield and surplus.
    """
    try:
        b = FpuService.create_production_batch(db, unit_id, batch_in)
        days_rem, tier = FpuService.calculate_urgency_tier(b.expiry_date)
        usages_out = [
            {
                "id": u.id,
                "raw_material_id": u.raw_material_id,
                "raw_material_name": u.raw_material.material_name if u.raw_material else "Feedstock",
                "lot_number": u.raw_material.lot_number if u.raw_material else "LOT-UNKNOWN",
                "quantity_used": u.quantity_used,
                "unit": u.unit,
                "fefo_sequence_order": u.fefo_sequence_order,
                "lot_expiry_at_consumption": u.lot_expiry_at_consumption
            }
            for u in b.raw_material_usages
        ]
        return {
            "id": b.id,
            "processing_unit_id": b.processing_unit_id,
            "batch_number": b.batch_number,
            "product_name": b.product_name,
            "category": b.category,
            "planned_quantity": b.planned_quantity,
            "actual_quantity": b.actual_quantity,
            "unit": b.unit,
            "manufacturing_date": b.manufacturing_date,
            "expiry_date": b.expiry_date,
            "quality_status": b.quality_status,
            "packaging_condition": b.packaging_condition,
            "damaged_packaging_units": b.damaged_packaging_units,
            "rejected_quantity": b.rejected_quantity,
            "rejection_reason": b.rejection_reason,
            "disposition_action": b.disposition_action,
            "yield_percentage": b.yield_percentage,
            "surplus_quantity": b.surplus_quantity,
            "redistributable_stock": b.redistributable_stock,
            "redistribution_status": b.redistribution_status,
            "status": b.status,
            "operator_notes": b.operator_notes,
            "qc_officer": b.qc_officer,
            "created_at": b.created_at,
            "updated_at": b.updated_at,
            "raw_materials_used": usages_out,
            "days_to_expiry": days_rem,
            "expiry_urgency_tier": tier
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/batches/{batch_id}", response_model=FpuProductionBatchOut)
def get_production_batch(
    batch_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Retrieves batch details including quality metrics, damaged packaging count, and input lots."""
    b = db.query(FpuProductionBatch).filter(FpuProductionBatch.id == batch_id).first()
    if not b:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Batch '{batch_id}' not found.")

    days_rem, tier = FpuService.calculate_urgency_tier(b.expiry_date)
    usages_out = [
        {
            "id": u.id,
            "raw_material_id": u.raw_material_id,
            "raw_material_name": u.raw_material.material_name if u.raw_material else "Feedstock",
            "lot_number": u.raw_material.lot_number if u.raw_material else "LOT-UNKNOWN",
            "quantity_used": u.quantity_used,
            "unit": u.unit,
            "fefo_sequence_order": u.fefo_sequence_order,
            "lot_expiry_at_consumption": u.lot_expiry_at_consumption
        }
        for u in b.raw_material_usages
    ]

    return {
        "id": b.id,
        "processing_unit_id": b.processing_unit_id,
        "batch_number": b.batch_number,
        "product_name": b.product_name,
        "category": b.category,
        "planned_quantity": b.planned_quantity,
        "actual_quantity": b.actual_quantity,
        "unit": b.unit,
        "manufacturing_date": b.manufacturing_date,
        "expiry_date": b.expiry_date,
        "quality_status": b.quality_status,
        "packaging_condition": b.packaging_condition,
        "damaged_packaging_units": b.damaged_packaging_units,
        "rejected_quantity": b.rejected_quantity,
        "rejection_reason": b.rejection_reason,
        "disposition_action": b.disposition_action,
        "yield_percentage": b.yield_percentage,
        "surplus_quantity": b.surplus_quantity,
        "redistributable_stock": b.redistributable_stock,
        "redistribution_status": b.redistribution_status,
        "status": b.status,
        "operator_notes": b.operator_notes,
        "qc_officer": b.qc_officer,
        "created_at": b.created_at,
        "updated_at": b.updated_at,
        "raw_materials_used": usages_out,
        "days_to_expiry": days_rem,
        "expiry_urgency_tier": tier
    }


@router.patch("/batches/{batch_id}/quality", response_model=FpuProductionBatchOut)
def update_batch_quality(
    batch_id: str,
    update_in: FpuBatchQualityUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "PROCESSOR", "SUPER_ADMIN", "KITCHEN_MANAGER"]))
):
    """Updates quality status, reports damaged packaging or rejected products, and records valorization."""
    try:
        b = FpuService.update_batch_quality(db, batch_id, update_in)
        days_rem, tier = FpuService.calculate_urgency_tier(b.expiry_date)
        usages_out = [
            {
                "id": u.id,
                "raw_material_id": u.raw_material_id,
                "raw_material_name": u.raw_material.material_name if u.raw_material else "Feedstock",
                "lot_number": u.raw_material.lot_number if u.raw_material else "LOT-UNKNOWN",
                "quantity_used": u.quantity_used,
                "unit": u.unit,
                "fefo_sequence_order": u.fefo_sequence_order,
                "lot_expiry_at_consumption": u.lot_expiry_at_consumption
            }
            for u in b.raw_material_usages
        ]
        return {
            "id": b.id,
            "processing_unit_id": b.processing_unit_id,
            "batch_number": b.batch_number,
            "product_name": b.product_name,
            "category": b.category,
            "planned_quantity": b.planned_quantity,
            "actual_quantity": b.actual_quantity,
            "unit": b.unit,
            "manufacturing_date": b.manufacturing_date,
            "expiry_date": b.expiry_date,
            "quality_status": b.quality_status,
            "packaging_condition": b.packaging_condition,
            "damaged_packaging_units": b.damaged_packaging_units,
            "rejected_quantity": b.rejected_quantity,
            "rejection_reason": b.rejection_reason,
            "disposition_action": b.disposition_action,
            "yield_percentage": b.yield_percentage,
            "surplus_quantity": b.surplus_quantity,
            "redistributable_stock": b.redistributable_stock,
            "redistribution_status": b.redistribution_status,
            "status": b.status,
            "operator_notes": b.operator_notes,
            "qc_officer": b.qc_officer,
            "created_at": b.created_at,
            "updated_at": b.updated_at,
            "raw_materials_used": usages_out,
            "days_to_expiry": days_rem,
            "expiry_urgency_tier": tier
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# =====================================================================
# 5. SURPLUS REDISTRIBUTION
# =====================================================================

@router.post("/batches/{batch_id}/redistribute", response_model=FpuRedistributeResponse)
def redistribute_batch_surplus(
    batch_id: str,
    req: FpuRedistributeRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "PROCESSOR", "SUPER_ADMIN", "KITCHEN_MANAGER"]))
):
    """
    Redistributes surplus products from an FPU batch into the food rescue platform.
    Can directly assign to a recipient food bank/charity.
    """
    try:
        user_org_id = user.get("organization_id")
        return FpuService.redistribute_surplus(db, batch_id, req, current_user_org_id=user_org_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# =====================================================================
# 6. CONFIGURABLE THRESHOLD RULES & AUTOMATIC ALERTS
# =====================================================================

@router.get("/{unit_id}/thresholds", response_model=List[FpuExpiryThresholdRuleOut])
def list_threshold_rules(
    unit_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Lists configurable alert threshold rules for the facility (by product or category)."""
    return db.query(FpuExpiryAlertThreshold).filter(
        FpuExpiryAlertThreshold.processing_unit_id == unit_id
    ).all()


@router.post("/{unit_id}/thresholds", response_model=FpuExpiryThresholdRuleOut, status_code=status.HTTP_201_CREATED)
def configure_threshold_rule(
    unit_id: str,
    rule_in: FpuExpiryThresholdRuleCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "PROCESSOR", "SUPER_ADMIN"]))
):
    """
    Sets or updates alert threshold rules for a category or specific product.
    Allows configuring warning (7d), urgent (3d), and critical (1d) periods.
    """
    return FpuService.create_or_update_threshold_rule(db, unit_id, rule_in)


@router.get("/{unit_id}/alerts", response_model=FpuAlertsSummary)
def get_automatic_alerts(
    unit_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Evaluates raw materials and finished products against threshold rules
    and returns real-time alerts (7-day, 3-day, 1-day, expired, damaged packaging).
    """
    return FpuService.get_automatic_alerts(db, unit_id)


# =====================================================================
# 7. BATCH TRACEABILITY
# =====================================================================

@router.get("/traceability/{identifier}", response_model=FpuBatchTraceabilityChain)
def get_batch_traceability(
    identifier: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Builds full 5-hop batch traceability:
    Raw Material -> Production Batch -> Finished Product -> Surplus/Donation -> Recipient.
    Searchable by Batch Code, Raw Material Lot Code, or Surplus ID.
    """
    try:
        return FpuService.get_batch_traceability(db, identifier)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# =====================================================================
# 8. EXECUTIVE DASHBOARD SUMMARY
# =====================================================================

@router.get("/{unit_id}/dashboard", response_model=FpuDashboardSummary)
def get_fpu_dashboard(
    unit_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Returns executive dashboard metrics across 6 key pillars:
    1. Inventory (raw materials & finished goods kg/value)
    2. Near Expiry (count & kg at 7d, 3d, 1d)
    3. Expired (quarantined and discard pending)
    4. Production (batches, yields, FEFO adherence)
    5. Rejected (quality rejections, damaged packaging, valorization)
    6. Redistributable Stock (surplus declared, donations, recipient reach)
    """
    try:
        return FpuService.get_dashboard_summary(db, unit_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
