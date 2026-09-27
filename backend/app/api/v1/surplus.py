"""
FoodLoop AI - Phase 8 Real-Time Surplus Management & Food Safety API
Manages kitchen surplus records, deterministic food safety evaluations,
recipient matching, and safe allocation lifecycle transitions.
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status, Query, HTTPException, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.models.models import SurplusItem, Organization, Recipient
from app.schemas.surplus_schemas import (
    SurplusRecordCreate,
    SurplusRecordUpdate,
    SurplusStatusTransitionRequest,
    HumanApprovalRequest,
    SurplusAllocationRequest,
    SurplusRecordOut,
    RecipientMatchItem,
    LiveSurplusDashboardSummary,
    SURPLUS_STATUSES
)
from app.schemas.recipient_matching_schemas import (
    MatchingFactorsSchema,
    RecipientMatchCandidateOut,
    SurplusMatchesResponse,
    RecipientSurplusActionResponse,
    RecipientRequestPayload,
    RecipientAcceptPayload,
    RecipientRejectPayload,
    RecipientSchedulePickupPayload
)
from app.services.food_safety_rules import (
    evaluate_food_safety,
    FoodSafetyConfig,
    FoodSafetyEvaluationResult,
    DEFAULT_FOOD_SAFETY_CONFIG
)
from app.services.surplus_service import SurplusManagementService
from app.services.recipient_matching_engine import RecipientMatchingEngine

router = APIRouter(prefix="/surplus", tags=["Phase 8 & 9: Surplus & Recipient Matching"])


def serialize_surplus_record(item: SurplusItem, safety_eval: Optional[FoodSafetyEvaluationResult] = None) -> SurplusRecordOut:
    """Helper formatting SurplusItem into the complete Phase 8 card schema."""
    now = datetime.now(timezone.utc)
    if not safety_eval:
        safety_eval = SurplusManagementService.evaluate_item(item)
        SurplusManagementService.sync_item_safety_fields(item, safety_eval)

    # Compute human-friendly age from prepared_at
    prep_dt = item.prepared_at or item.created_at
    if prep_dt:
        prep_dt = prep_dt.replace(tzinfo=timezone.utc) if prep_dt.tzinfo is None else prep_dt
        age_seconds = max(0.0, (now - prep_dt).total_seconds())
        age_hours = round(age_seconds / 3600.0, 1)
        if age_seconds < 3600:
            age_formatted = f"{int(age_seconds // 60)}m old"
        else:
            h = int(age_seconds // 3600)
            m = int((age_seconds % 3600) // 60)
            age_formatted = f"{h}h {m:02d}m old"
    else:
        age_hours = 0.5
        age_formatted = "30m old"

    return SurplusRecordOut(
        id=item.id,
        food=getattr(item, "food", None) or getattr(item, "title", "Prepared Food"),
        quantity=float(getattr(item, "quantity", None) or getattr(item, "quantity_kg", 10.0)),
        unit=getattr(item, "unit", "kg") or "kg",
        prepared_at=item.prepared_at,
        storage_type=getattr(item, "storage_type", None) or getattr(item, "storage_temp", "REFRIGERATED"),
        temperature=getattr(item, "temperature", None),
        batch=getattr(item, "batch", None) or getattr(item, "batch_id", None),
        best_use_before=getattr(item, "best_use_before", None) or getattr(item, "safe_consumption_deadline", None),
        notes=getattr(item, "notes", None) or getattr(item, "description", None),
        image=getattr(item, "image", None) or getattr(item, "photo_url", None),
        status=getattr(item, "status", "AVAILABLE"),
        location=getattr(item, "location_name", "Main Production Kitchen") or "Main Production Kitchen",
        age_hours=age_hours,
        age_formatted=age_formatted,
        remaining_safe_window_minutes=safety_eval.remaining_safe_window_minutes,
        remaining_safe_window_formatted=safety_eval.remaining_safe_window_formatted,
        urgency=safety_eval.urgency,
        eligibility=safety_eval.eligibility,
        required_action=safety_eval.required_action,
        suggested_waste_workflow=safety_eval.suggested_waste_workflow,
        human_approval_required=safety_eval.human_approval_required,
        approved_by=getattr(item, "approved_by", None),
        approval_status=getattr(item, "approval_status", None),
        approval_notes=getattr(item, "approval_notes", None),
        safety_rule_applied=safety_eval.safety_rule_applied,
        created_at=item.created_at,
        updated_at=item.updated_at
    )


# =====================================================================
# 1. LIVE SURPLUS DASHBOARD ENDPOINT
# =====================================================================

@router.get("/dashboard/live", response_model=LiveSurplusDashboardSummary)
def get_live_surplus_dashboard(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    urgency_filter: Optional[str] = Query(None, description="Filter by urgency"),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Live Surplus Dashboard Endpoint.
    Returns aggregated metrics, active alerts, and cards displaying:
    Food, Quantity, Age, Remaining window, Urgency, Location, Status.
    """
    query = db.query(SurplusItem).filter(SurplusItem.deleted_at.is_(None))

    if status_filter:
        query = query.filter(SurplusItem.status == status_filter.upper())

    items = query.order_by(SurplusItem.created_at.desc()).all()

    serialized_items: List[SurplusRecordOut] = []
    urgent_alerts: List[Dict[str, Any]] = []

    total_avail_kg = 0.0
    crit_count = 0
    expired_count = 0
    avail_count = 0

    for item in items:
        # Run real-time deterministic food safety evaluation
        safety_eval = SurplusManagementService.evaluate_item(item)
        SurplusManagementService.sync_item_safety_fields(item, safety_eval)

        # Apply urgency filter if specified
        if urgency_filter and safety_eval.urgency != urgency_filter.upper():
            continue

        serialized = serialize_surplus_record(item, safety_eval)
        serialized_items.append(serialized)

        # Compute summary aggregates
        if serialized.status == "AVAILABLE":
            avail_count += 1
            total_avail_kg += serialized.quantity

        if serialized.urgency == "CRITICAL" and serialized.status not in ["DELIVERED", "RECEIVED", "EXPIRED", "CANCELLED"]:
            crit_count += 1
            urgent_alerts.append({
                "surplus_id": serialized.id,
                "food": serialized.food,
                "urgency": "CRITICAL",
                "remaining_window": serialized.remaining_safe_window_formatted,
                "location": serialized.location,
                "action": serialized.required_action,
                "alert_type": "EXPIRATION_WARNING"
            })
        elif serialized.status == "EXPIRED" or serialized.urgency == "EXPIRED":
            expired_count += 1
            urgent_alerts.append({
                "surplus_id": serialized.id,
                "food": serialized.food,
                "urgency": "EXPIRED",
                "remaining_window": "0 min",
                "location": serialized.location,
                "action": serialized.required_action,
                "suggested_waste_workflow": serialized.suggested_waste_workflow,
                "alert_type": "EXPIRED_ALERT"
            })

    db.commit()

    return LiveSurplusDashboardSummary(
        total_active_lots=len(serialized_items),
        available_lots_count=avail_count,
        critical_urgency_count=crit_count,
        expired_lots_count=expired_count,
        total_available_quantity_kg=round(total_avail_kg, 1),
        items=serialized_items,
        urgent_alerts=urgent_alerts
    )


# =====================================================================
# 2. SURPLUS RECORD CREATION (BY KITCHEN USERS)
# =====================================================================

@router.post("", response_model=SurplusRecordOut, status_code=status.HTTP_201_CREATED)
def create_surplus_record(
    payload: SurplusRecordCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "KITCHEN_MANAGER", "STAFF"]))
):
    """
    Kitchen users create surplus records with required fields:
    food, quantity, unit, prepared_at, storage_type, temperature, batch,
    best_use_before, notes, image, location.

    Automatically calculates deterministic remaining safe window, urgency,
    eligibility, and required action.
    """
    # 1. Run deterministic food safety evaluation
    safety_eval = evaluate_food_safety(
        food=payload.food,
        category=payload.category or "COOKED_MEALS",
        storage_type=payload.storage_type,
        temperature=payload.temperature,
        prepared_at=payload.prepared_at,
        best_use_before=payload.best_use_before
    )

    initial_status = "AVAILABLE"
    if safety_eval.eligibility in ["INELIGIBLE_EXPIRED", "INELIGIBLE_TEMPERATURE_ABUSE"]:
        initial_status = "EXPIRED"

    # 2. Persist to database
    org_id = user.get("organization_id")
    surplus_item = SurplusItem(
        organization_id=org_id,
        title=payload.food,
        food=payload.food,
        category=payload.category or "COOKED_MEALS",
        description=payload.notes or "",
        notes=payload.notes,
        quantity_kg=payload.quantity if payload.unit.lower() == "kg" else payload.quantity * 0.35,
        quantity=payload.quantity,
        portions=int(payload.quantity) if payload.unit.lower() == "portions" else int(payload.quantity / 0.35),
        unit=payload.unit,
        storage_temp=payload.storage_type,
        storage_type=payload.storage_type,
        temperature=payload.temperature,
        batch=payload.batch,
        prepared_at=payload.prepared_at,
        safe_consumption_deadline=payload.best_use_before,
        best_use_before=payload.best_use_before,
        photo_url=payload.image,
        image=payload.image,
        pickup_address=payload.location or "Main Production Kitchen",
        location_name=payload.location or "Main Production Kitchen",
        pickup_lat=37.7749,
        pickup_lng=-122.4194,
        status=initial_status,
        remaining_safe_window_minutes=safety_eval.remaining_safe_window_minutes,
        urgency=safety_eval.urgency,
        eligibility=safety_eval.eligibility,
        required_action=safety_eval.required_action,
        suggested_waste_workflow=safety_eval.suggested_waste_workflow,
        approval_status="APPROVED" if not safety_eval.human_approval_required else "PENDING_REVIEW"
    )

    db.add(surplus_item)
    db.commit()
    db.refresh(surplus_item)

    return serialize_surplus_record(surplus_item, safety_eval)


# =====================================================================
# 3. LIST & GET SURPLUS RECORDS
# =====================================================================

@router.get("", response_model=List[SurplusRecordOut])
def list_surplus_records(
    category: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    urgency_filter: Optional[str] = Query(None),
    only_available: bool = Query(False),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Lists surplus records with real-time food safety window calculations."""
    query = db.query(SurplusItem).filter(SurplusItem.deleted_at.is_(None))

    if category:
        query = query.filter(SurplusItem.category == category)
    if status_filter:
        query = query.filter(SurplusItem.status == status_filter.upper())
    elif only_available:
        query = query.filter(SurplusItem.status == "AVAILABLE")

    items = query.order_by(SurplusItem.created_at.desc()).all()

    result = []
    for item in items:
        safety_eval = SurplusManagementService.evaluate_item(item)
        SurplusManagementService.sync_item_safety_fields(item, safety_eval)
        if urgency_filter and safety_eval.urgency != urgency_filter.upper():
            continue
        result.append(serialize_surplus_record(item, safety_eval))

    db.commit()
    return result


@router.get("/{surplus_id}", response_model=SurplusRecordOut)
def get_surplus_record(
    surplus_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Retrieves specific surplus record details with live safety calculations."""
    item = db.query(SurplusItem).filter(
        SurplusItem.id == surplus_id,
        SurplusItem.deleted_at.is_(None)
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Surplus record '{surplus_id}' was not found."
        )

    safety_eval = SurplusManagementService.evaluate_item(item)
    SurplusManagementService.sync_item_safety_fields(item, safety_eval)
    db.commit()
    return serialize_surplus_record(item, safety_eval)


# =====================================================================
# 4. RECIPIENT MATCHING FOR ELIGIBLE SURPLUS
# =====================================================================

@router.get("/{surplus_id}/recipients", response_model=List[RecipientMatchItem])
def find_matched_recipients(
    surplus_id: str,
    max_distance_km: float = Query(35.0, ge=1.0, le=100.0),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    If eligible: finds matched community recipients (shelters, food banks)
    ranking by proximity, capacity, and transit window feasibility.

    If not eligible: raises HTTP 400 explaining the safety reason and
    suggesting alternative institutional waste workflows.
    """
    item = db.query(SurplusItem).filter(
        SurplusItem.id == surplus_id,
        SurplusItem.deleted_at.is_(None)
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Surplus record not found.")

    safety_eval = SurplusManagementService.evaluate_item(item)
    SurplusManagementService.sync_item_safety_fields(item, safety_eval)
    db.commit()

    if safety_eval.eligibility in ["INELIGIBLE_EXPIRED", "INELIGIBLE_TEMPERATURE_ABUSE", "INELIGIBLE_HOLDING_TIME_EXCEEDED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Surplus lot is not eligible for donation distribution.",
                "eligibility": safety_eval.eligibility,
                "urgency": safety_eval.urgency,
                "required_action": safety_eval.required_action,
                "suggested_waste_workflow": safety_eval.suggested_waste_workflow,
                "reasons": safety_eval.reasons
            }
        )

    matches = SurplusManagementService.find_eligible_recipients(item, max_distance_km=max_distance_km)
    return matches


@router.get("/{surplus_id}/matches", response_model=SurplusMatchesResponse)
def get_surplus_matches(
    surplus_id: str,
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    PHASE 9 — AI RECIPIENT MATCHING ENGINE
    Evaluates available surplus food against active recipients using 7 transparent factors:
    1. food compatibility (category & dietary preferences)
    2. capacity (portions & daily intake limits)
    3. distance (Haversine km & transit estimation)
    4. urgency (remaining safe window vs transit margin)
    5. pickup availability (recipient internal fleet vs external dispatch)
    6. storage compatibility (chilled, hot, dry, frozen)
    7. operational reliability (show rate & verification)

    Does not return an unexplained black-box score.
    Returns transparent match explanations with clear bullet points.
    """
    item = db.query(SurplusItem).filter(SurplusItem.id == surplus_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Surplus item with ID '{surplus_id}' was not found."
        )

    safety_eval = SurplusManagementService.evaluate_item(item)
    SurplusManagementService.sync_item_safety_fields(item, safety_eval)
    db.commit()

    if safety_eval.eligibility in ["INELIGIBLE_EXPIRED", "INELIGIBLE_TEMPERATURE_ABUSE", "INELIGIBLE_HOLDING_TIME_EXCEEDED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Surplus lot is NOT eligible for human donation due to food safety expiration or temperature abuse.",
                "eligibility": safety_eval.eligibility,
                "urgency": safety_eval.urgency,
                "required_action": safety_eval.required_action,
                "suggested_waste_workflow": safety_eval.suggested_waste_workflow,
                "reasons": safety_eval.reasons
            }
        )

    recipients = db.query(Recipient).filter(Recipient.is_active == True).all()
    ranked_results = RecipientMatchingEngine.rank_recipients_for_surplus(item, recipients, limit=limit)

    matches_out: List[RecipientMatchCandidateOut] = []
    for r in ranked_results:
        matches_out.append(RecipientMatchCandidateOut(
            recipient_id=r.recipient_id,
            organization_name=r.organization_name,
            facility_type=r.facility_type,
            address=r.address,
            contact_person=r.contact_person,
            contact_phone=r.contact_phone,
            distance_km=r.distance_km,
            estimated_transit_minutes=r.estimated_transit_minutes,
            overall_match_score=r.overall_match_score,
            factors=MatchingFactorsSchema(
                food_compatibility=r.factors.food_compatibility,
                capacity=r.factors.capacity,
                distance=r.factors.distance,
                urgency=r.factors.urgency,
                pickup_availability=r.factors.pickup_availability,
                storage_compatibility=r.factors.storage_compatibility,
                operational_reliability=r.factors.operational_reliability
            ),
            explanation_bullets=r.explanation_bullets,
            recommendation_summary=r.recommendation_summary,
            is_feasible=r.is_feasible,
            can_intake_immediately=r.can_intake_immediately,
            requires_delivery=r.requires_delivery,
            operating_hours=r.operating_hours,
            verification_status=r.verification_status
        ))

    return SurplusMatchesResponse(
        surplus_id=item.id,
        food=item.food or item.title or "Surplus Food",
        quantity=item.quantity or item.quantity_kg or 0.0,
        unit=item.unit or "kg",
        storage_type=item.storage_type or "ROOM_TEMP",
        temperature=item.temperature,
        urgency=item.urgency or "MEDIUM",
        remaining_safe_window_minutes=item.remaining_safe_window_minutes or 0.0,
        status=item.status,
        matches_count=len(matches_out),
        matches=matches_out
    )


# =====================================================================
# 5. RECIPIENT ACTIONS & DOUBLE-BOOKING TRANSACTION SAFEGUARDS
# =====================================================================

@router.post("/{surplus_id}/request", response_model=RecipientSurplusActionResponse)
def recipient_request_surplus(
    surplus_id: str,
    payload: RecipientRequestPayload,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "NGO", "KITCHEN_MANAGER"]))
):
    """
    Recipient requests an available surplus lot.
    Strictly prevents double booking using row-level transactional lock (SELECT ... FOR UPDATE).
    """
    now = datetime.now(timezone.utc)
    item = db.query(SurplusItem).filter(SurplusItem.id == surplus_id).with_for_update().first()
    if not item:
        raise HTTPException(status_code=404, detail="Surplus item not found")

    if item.status in ["EXPIRED", "CANCELLED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Surplus lot is '{item.status}' and cannot be requested for human consumption."
        )

    # Double-booking guard
    if item.status != "AVAILABLE":
        if item.allocated_recipient_id and item.allocated_recipient_id != payload.recipient_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"DOUBLE_BOOKING_PREVENTED: Surplus lot '{item.food}' has already been reserved by another recipient."
            )

    item.status = "RESERVED"
    item.allocated_recipient_id = payload.recipient_id
    item.recipient_claim_status = "REQUESTED"
    db.commit()
    db.refresh(item)

    return RecipientSurplusActionResponse(
        success=True,
        surplus_id=item.id,
        recipient_id=payload.recipient_id,
        new_status=item.status,
        claim_status=item.recipient_claim_status,
        message=f"Request submitted for '{item.food}'. Lot is locked and reserved for your organization.",
        timestamp=now
    )


@router.post("/{surplus_id}/accept", response_model=RecipientSurplusActionResponse)
def recipient_accept_surplus(
    surplus_id: str,
    payload: RecipientAcceptPayload,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "NGO", "KITCHEN_MANAGER"]))
):
    """
    Recipient confirms acceptance of an allocated surplus lot.
    Row-level lock prevents race conditions and duplicate claims.
    """
    now = datetime.now(timezone.utc)
    item = db.query(SurplusItem).filter(SurplusItem.id == surplus_id).with_for_update().first()
    if not item:
        raise HTTPException(status_code=404, detail="Surplus item not found")

    if item.status in ["EXPIRED", "CANCELLED"]:
        raise HTTPException(status_code=400, detail="Cannot accept expired surplus.")

    if item.allocated_recipient_id and item.allocated_recipient_id != payload.recipient_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="DOUBLE_BOOKING_PREVENTED: Surplus lot is already allocated to another organization."
        )

    item.status = "RESERVED"
    item.allocated_recipient_id = payload.recipient_id
    item.recipient_claim_status = "ACCEPTED"
    db.commit()
    db.refresh(item)

    return RecipientSurplusActionResponse(
        success=True,
        surplus_id=item.id,
        recipient_id=payload.recipient_id,
        new_status=item.status,
        claim_status=item.recipient_claim_status,
        message=f"Surplus lot '{item.food}' confirmed and accepted.",
        timestamp=now
    )


@router.post("/{surplus_id}/reject", response_model=RecipientSurplusActionResponse)
def recipient_reject_surplus(
    surplus_id: str,
    payload: RecipientRejectPayload,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "NGO", "KITCHEN_MANAGER"]))
):
    """
    Recipient declines a surplus lot.
    Releases the lot back to AVAILABLE status so other recipients can match.
    """
    now = datetime.now(timezone.utc)
    item = db.query(SurplusItem).filter(SurplusItem.id == surplus_id).with_for_update().first()
    if not item:
        raise HTTPException(status_code=404, detail="Surplus item not found")

    if item.allocated_recipient_id == payload.recipient_id:
        item.allocated_recipient_id = None
        item.recipient_claim_status = "REJECTED"
        item.status = "AVAILABLE"

    db.commit()
    db.refresh(item)

    return RecipientSurplusActionResponse(
        success=True,
        surplus_id=item.id,
        recipient_id=payload.recipient_id,
        new_status=item.status,
        claim_status="REJECTED",
        message="Surplus lot declined. Released back to regional marketplace for other recipients.",
        timestamp=now
    )


@router.post("/{surplus_id}/schedule-pickup", response_model=RecipientSurplusActionResponse)
def recipient_schedule_pickup(
    surplus_id: str,
    payload: RecipientSchedulePickupPayload,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "NGO", "KITCHEN_MANAGER", "DRIVER"]))
):
    """
    Recipient schedules pickup for an allocated lot.
    Row-level lock prevents double-scheduling or collision with courier dispatch.
    Transitions status to PICKUP_SCHEDULED.
    """
    now = datetime.now(timezone.utc)
    item = db.query(SurplusItem).filter(SurplusItem.id == surplus_id).with_for_update().first()
    if not item:
        raise HTTPException(status_code=404, detail="Surplus item not found")

    if item.status in ["EXPIRED", "CANCELLED"]:
        raise HTTPException(status_code=400, detail="Cannot schedule pickup on expired surplus.")

    if item.allocated_recipient_id and item.allocated_recipient_id != payload.recipient_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="DOUBLE_BOOKING_PREVENTED: Surplus lot is reserved by a different recipient."
        )

    item.status = "PICKUP_SCHEDULED"
    item.allocated_recipient_id = payload.recipient_id
    item.recipient_claim_status = "PICKUP_SCHEDULED"
    item.pickup_scheduled_time = payload.pickup_time
    item.pickup_driver_notes = (
        f"Driver: {payload.driver_name or 'Volunteer'} | "
        f"Vehicle: {payload.vehicle_plate or 'Standard'} | "
        f"Temp Gear: {'Verified' if payload.temperature_equipment_confirmed else 'Pending'} | "
        f"Notes: {payload.driver_notes or 'Recipient scheduled direct pickup'}"
    )
    db.commit()
    db.refresh(item)

    return RecipientSurplusActionResponse(
        success=True,
        surplus_id=item.id,
        recipient_id=payload.recipient_id,
        new_status=item.status,
        claim_status=item.recipient_claim_status,
        message=f"Pickup successfully scheduled for {payload.pickup_time.strftime('%I:%M %p on %b %d')}.",
        timestamp=now
    )


# =====================================================================
# 5. ALLOCATE SURPLUS (WITH STRICT EXPIRATION GUARD)
# =====================================================================

@router.post("/{surplus_id}/allocate", response_model=Dict[str, Any])
def allocate_surplus_lot(
    surplus_id: str,
    payload: SurplusAllocationRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "KITCHEN_MANAGER", "STAFF"]))
):
    """
    Allocates surplus to a recipient organization.
    CRITICAL FOOD SAFETY GUARD:
    Guarantees expired surplus CANNOT be accidentally allocated!
    """
    try:
        actor_name = user.get("email", "Kitchen Operator")
        result = SurplusManagementService.allocate_surplus(
            surplus_id=surplus_id,
            recipient_id=payload.recipient_id,
            db=db,
            actor_name=actor_name
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# =====================================================================
# 6. AUTHORIZED HUMAN APPROVAL (MANAGER SIGN-OFF)
# =====================================================================

@router.post("/{surplus_id}/approve", response_model=Dict[str, Any])
def approve_surplus_lot(
    surplus_id: str,
    payload: HumanApprovalRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "KITCHEN_MANAGER"]))
):
    """
    Authorized human approval gate for lots requiring physical inspection
    (sensory, smell, temperature verification).
    """
    try:
        approver_name = user.get("email", "Kitchen Manager")
        result = SurplusManagementService.record_human_approval(
            surplus_id=surplus_id,
            approved=payload.approved,
            approver_name=approver_name,
            notes=payload.notes,
            verified_temp=payload.verified_temp,
            db=db
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# =====================================================================
# 7. STATUS TRANSITION STATE MACHINE
# =====================================================================

@router.patch("/{surplus_id}/status", response_model=SurplusRecordOut)
def update_surplus_status(
    surplus_id: str,
    payload: SurplusStatusTransitionRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "KITCHEN_MANAGER", "NGO", "DRIVER"]))
):
    """
    Updates surplus lot status across the 9 lifecycle states:
    AVAILABLE -> RESERVED -> PICKUP_SCHEDULED -> PICKED_UP -> IN_TRANSIT -> DELIVERED -> RECEIVED
    or EXPIRED / CANCELLED.

    Strictly forbids transitioning expired surplus into active distribution states.
    """
    try:
        actor_name = user.get("email", "Operator")
        updated_item = SurplusManagementService.transition_status(
            surplus_id=surplus_id,
            new_status=payload.new_status,
            db=db,
            actor_name=actor_name
        )
        return serialize_surplus_record(updated_item)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# =====================================================================
# 8. URGENT NOTIFICATIONS STREAM & FOOD SAFETY CONFIG
# =====================================================================

@router.get("/alerts/urgent", response_model=List[Dict[str, Any]])
def get_urgent_surplus_alerts(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Returns active alerts for surplus lots entering the critical window (< 60 min) or expired."""
    items = db.query(SurplusItem).filter(
        SurplusItem.deleted_at.is_(None),
        SurplusItem.status.in_(["AVAILABLE", "RESERVED", "PICKUP_SCHEDULED", "EXPIRED"])
    ).all()

    alerts = []
    for item in items:
        safety_eval = SurplusManagementService.evaluate_item(item)
        SurplusManagementService.sync_item_safety_fields(item, safety_eval)

        if safety_eval.urgency == "CRITICAL" and item.status != "EXPIRED":
            alerts.append({
                "surplus_id": item.id,
                "food": getattr(item, "food", None) or item.title,
                "urgency": "CRITICAL",
                "remaining_window": safety_eval.remaining_safe_window_formatted,
                "location": getattr(item, "location_name", "Kitchen"),
                "status": item.status,
                "action": safety_eval.required_action,
                "alert_type": "EXPIRATION_WARNING",
                "human_approval_required": safety_eval.human_approval_required
            })
        elif item.status == "EXPIRED" or safety_eval.urgency == "EXPIRED":
            alerts.append({
                "surplus_id": item.id,
                "food": getattr(item, "food", None) or item.title,
                "urgency": "EXPIRED",
                "remaining_window": "0 min",
                "location": getattr(item, "location_name", "Kitchen"),
                "status": "EXPIRED",
                "action": safety_eval.required_action,
                "suggested_waste_workflow": safety_eval.suggested_waste_workflow,
                "alert_type": "EXPIRED_ALERT"
            })

    db.commit()
    return alerts


@router.get("/rules/config", response_model=FoodSafetyConfig)
def get_food_safety_rules_config(
    user: dict = Depends(get_current_user)
):
    """Retrieves current configurable institutional food safety parameters."""
    return DEFAULT_FOOD_SAFETY_CONFIG


@router.put("/rules/config", response_model=FoodSafetyConfig)
def update_food_safety_rules_config(
    new_config: FoodSafetyConfig,
    user: dict = Depends(RoleChecker(["ADMIN"]))
):
    """Configures institutional food safety rules (Admin only)."""
    global DEFAULT_FOOD_SAFETY_CONFIG
    DEFAULT_FOOD_SAFETY_CONFIG = new_config
    return DEFAULT_FOOD_SAFETY_CONFIG
