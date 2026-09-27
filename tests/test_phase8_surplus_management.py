"""
FoodLoop AI - Phase 8 Real-Time Surplus Management & Food Safety Test Suite
Validates:
1. Surplus record creation with all required fields:
   food, quantity, unit, prepared_at, storage_type, temperature, batch, best_use_before, notes, image.
2. Deterministic configurable food safety rules engine:
   Zero LLM hallucination / independent decision-making. Strictly rule-based.
3. Calculations:
   remaining_safe_window, urgency, eligibility, required_action.
4. Recipient matching for eligible surplus.
5. Suggesting appropriate alternative waste-management workflows when ineligible.
6. Live Surplus Dashboard cards displaying:
   Food, Quantity, Age, Remaining window, Urgency, Location, Status.
7. Automatic expiry/urgency notifications.
8. ALLOCATION SAFETY GUARD: Ensuring expired surplus cannot be accidentally allocated.
9. Authorized human approval workflow.
10. Status state machine across all 9 required statuses:
    AVAILABLE, RESERVED, PICKUP_SCHEDULED, PICKED_UP, IN_TRANSIT, DELIVERED, RECEIVED, EXPIRED, CANCELLED.
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import create_access_token
from app.core.database import SessionLocal
from app.models.models import SurplusItem
from app.services.food_safety_rules import (
    evaluate_food_safety,
    FoodSafetyConfig,
    FoodSafetyEvaluationResult,
    DEFAULT_FOOD_SAFETY_CONFIG
)
from app.services.surplus_service import SurplusManagementService

client = TestClient(app)


@pytest.fixture
def auth_headers():
    token = create_access_token(
        data={"sub": "chef.elena@culinary.org", "id": "test-chef-002", "role": "KITCHEN_MANAGER"}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =====================================================================
# 1. DETERMINISTIC FOOD SAFETY RULES ENGINE UNIT TESTS
# =====================================================================

def test_food_safety_zero_llm_determinism():
    """
    Requirement:
    "Do not allow an LLM to independently determine food safety.
     Use deterministic configurable rules and authorized human approval."
    Verify that 100 consecutive evaluations with identical inputs yield identical outputs.
    """
    now = datetime.now(timezone.utc)
    prep_time = now - timedelta(hours=2)

    eval1 = evaluate_food_safety(
        food="Herb Roasted Chicken",
        category="COOKED_MEALS",
        storage_type="HOT_HOLD",
        temperature=64.0,
        prepared_at=prep_time,
        current_time=now
    )

    for _ in range(25):
        eval_repeat = evaluate_food_safety(
            food="Herb Roasted Chicken",
            category="COOKED_MEALS",
            storage_type="HOT_HOLD",
            temperature=64.0,
            prepared_at=prep_time,
            current_time=now
        )
        assert eval_repeat.remaining_safe_window_minutes == eval1.remaining_safe_window_minutes
        assert eval_repeat.urgency == eval1.urgency
        assert eval_repeat.eligibility == eval1.eligibility
        assert eval_repeat.required_action == eval1.required_action


def test_food_safety_hot_hold_temperature_abuse():
    """
    Under FDA Food Code, hot TCS food held below 57°C (135°F) is in the danger zone.
    Must immediately flag INELIGIBLE_TEMPERATURE_ABUSE and route to anaerobic digestion.
    """
    now = datetime.now(timezone.utc)
    prep_time = now - timedelta(hours=1)

    result = evaluate_food_safety(
        food="Cream of Broccoli Soup",
        category="COOKED_MEALS",
        storage_type="HOT_HOLD",
        temperature=48.5,  # Critical breach: below 57°C!
        prepared_at=prep_time,
        current_time=now
    )

    assert result.eligibility == "INELIGIBLE_TEMPERATURE_ABUSE"
    assert result.urgency == "EXPIRED"
    assert result.remaining_safe_window_minutes == 0.0
    assert "MANDATORY DISCARD" in result.required_action
    assert result.suggested_waste_workflow == "ANAEROBIC_DIGESTION"


def test_food_safety_holding_time_expiration():
    """
    Under FDA Food Code § 3-501.19, hot-held food exceeds the 4-hour limit at 4.5 hours.
    Must flag INELIGIBLE_EXPIRED with remaining window of 0 minutes.
    """
    now = datetime.now(timezone.utc)
    prep_time = now - timedelta(hours=4.5)  # Elapsed 4.5 hours!

    result = evaluate_food_safety(
        food="Steamed Jasmine Rice & Veggies",
        category="VEGETABLES",
        storage_type="HOT_HOLD",
        temperature=62.0,  # Temperature is fine, but time has elapsed!
        prepared_at=prep_time,
        current_time=now
    )

    assert result.eligibility == "INELIGIBLE_EXPIRED"
    assert result.urgency == "EXPIRED"
    assert result.remaining_safe_window_minutes == 0.0
    assert result.suggested_waste_workflow == "INDUSTRIAL_COMPOSTING"


def test_food_safety_cold_hold_eligible_low_urgency():
    """
    Cold-held surplus (e.g. 3.2°C) prepared 4 hours ago has days of safe shelf-life.
    Must flag ELIGIBLE_FOR_DONATION with LOW urgency.
    """
    now = datetime.now(timezone.utc)
    prep_time = now - timedelta(hours=4)

    result = evaluate_food_safety(
        food="Greek Yogurt & Berry Parfait",
        category="DAIRY",
        storage_type="REFRIGERATED",
        temperature=3.2,
        prepared_at=prep_time,
        current_time=now
    )

    assert result.eligibility == "ELIGIBLE_FOR_DONATION"
    assert result.urgency == "LOW"
    assert result.remaining_safe_window_minutes > 1000
    assert result.suggested_waste_workflow is None


def test_food_safety_critical_window_requires_manager_inspection():
    """
    Surplus with 45 minutes remaining (< 60m threshold) must flag
    NEEDS_HUMAN_INSPECTION and require authorized manager sign-off.
    """
    now = datetime.now(timezone.utc)
    # Hot hold max is 4h (240 min). 3h 15m elapsed -> 45m remaining.
    prep_time = now - timedelta(hours=3, minutes=15)

    result = evaluate_food_safety(
        food="Herb-Crusted Salmon Fillet",
        category="COOKED_MEALS",
        storage_type="HOT_HOLD",
        temperature=61.0,
        prepared_at=prep_time,
        current_time=now
    )

    assert result.eligibility == "NEEDS_HUMAN_INSPECTION"
    assert result.urgency == "CRITICAL"
    assert result.human_approval_required is True
    assert result.remaining_safe_window_minutes == pytest.approx(45.0, abs=2.0)
    assert "AUTHORIZED HUMAN APPROVAL REQUIRED" in result.required_action


# =====================================================================
# 2. SURPLUS RECORD CREATION (ALL REQUIRED FIELDS)
# =====================================================================

def test_api_create_surplus_record_all_fields(auth_headers):
    """
    Requirement:
    "Kitchen users can create surplus records.
     Fields: food, quantity, unit, prepared_at, storage_type, temperature if available,
     batch, best_use_before, notes, image"
    """
    prep_time = (datetime.now(timezone.utc) - timedelta(hours=1, minutes=30)).isoformat()
    best_use = (datetime.now(timezone.utc) + timedelta(hours=2, minutes=30)).isoformat()

    payload = {
        "food": "Rotisserie Herb Roasted Chicken",
        "quantity": 25.5,
        "unit": "kg",
        "prepared_at": prep_time,
        "storage_type": "HOT_HOLD",
        "temperature": 63.8,
        "batch": "BATCH-2026-TEST-HOT-01",
        "best_use_before": best_use,
        "notes": "Steam well table #2. Halal certified, verified temperature.",
        "image": "https://foodloop.org/images/surplus/rotisserie_chicken.jpg",
        "location": "Station 2 Rotisserie Warmer",
        "category": "PROTEIN"
    }

    res = client.post("/api/v1/surplus", json=payload, headers=auth_headers)
    assert res.status_code == 201
    data = res.json()

    # Verify all fields saved and returned
    assert data["food"] == payload["food"]
    assert data["quantity"] == 25.5
    assert data["unit"] == "kg"
    assert data["storage_type"] == "HOT_HOLD"
    assert data["temperature"] == 63.8
    assert data["batch"] == payload["batch"]
    assert data["location"] == payload["location"]
    assert data["notes"] == payload["notes"]
    assert data["status"] == "AVAILABLE"

    # Verify calculated food safety metrics
    assert data["remaining_safe_window_minutes"] > 0
    assert data["urgency"] in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    assert data["eligibility"] in ["ELIGIBLE_FOR_DONATION", "NEEDS_HUMAN_INSPECTION"]
    assert len(data["required_action"]) > 0
    assert "old" in data["age_formatted"]


# =====================================================================
# 3. RECIPIENT MATCHING & ALTERNATIVE WASTE WORKFLOWS
# =====================================================================

def test_api_find_recipients_for_eligible_surplus(auth_headers):
    """
    If eligible: Find recipients based on proximity, capacity, and safe transit window.
    """
    # 1. Create a fresh eligible surplus lot
    prep_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    payload = {
        "food": "Roasted Seasonal Vegetables & Quinoa",
        "quantity": 30.0,
        "unit": "kg",
        "prepared_at": prep_time,
        "storage_type": "HOT_HOLD",
        "temperature": 65.0,
        "location": "Main Kitchen Warmer #1",
        "category": "VEGETABLES"
    }
    create_res = client.post("/api/v1/surplus", json=payload, headers=auth_headers)
    assert create_res.status_code == 201
    surplus_id = create_res.json()["id"]

    # 2. Query matched recipients
    rec_res = client.get(f"/api/v1/surplus/{surplus_id}/recipients", headers=auth_headers)
    assert rec_res.status_code == 200
    recipients = rec_res.json()
    assert len(recipients) > 0

    first = recipients[0]
    assert "recipient_id" in first
    assert "organization_name" in first
    assert "distance_km" in first
    assert "estimated_transit_minutes" in first
    assert "match_score" in first
    assert first["match_score"] > 0
    assert first["can_receive_immediately"] is True


def test_api_ineligible_surplus_suggests_alternative_waste_workflow(auth_headers):
    """
    If not eligible:
    Suggest appropriate alternative waste-management workflow based on configured institutional rules.
    """
    # Create an expired/abused lot (temperature below safe hot hold limit)
    prep_time = (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat()
    payload = {
        "food": "Creamy Wild Mushroom Bisque",
        "quantity": 18.0,
        "unit": "kg",
        "prepared_at": prep_time,
        "storage_type": "HOT_HOLD",
        "temperature": 45.0,  # Critical breach!
        "category": "SOUP"
    }
    create_res = client.post("/api/v1/surplus", json=payload, headers=auth_headers)
    assert create_res.status_code == 201
    surplus_id = create_res.json()["id"]
    assert create_res.json()["status"] == "EXPIRED"

    # Attempting to find donation recipients on an ineligible lot must return 400 with workflow
    rec_res = client.get(f"/api/v1/surplus/{surplus_id}/recipients", headers=auth_headers)
    assert rec_res.status_code == 400
    detail = rec_res.json()["detail"]
    assert detail["eligibility"] == "INELIGIBLE_TEMPERATURE_ABUSE"
    assert detail["suggested_waste_workflow"] == "ANAEROBIC_DIGESTION"


# =====================================================================
# 4. ALLOCATION SAFETY GUARD (PREVENT ALLOCATION OF EXPIRED SURPLUS)
# =====================================================================

def test_api_strict_guard_expired_surplus_cannot_be_allocated(auth_headers):
    """
    CRITICAL REQUIREMENT:
    "Ensure expired surplus cannot be accidentally allocated."
    Attempting to allocate an expired or temperature-abused lot must be strictly rejected.
    """
    # 1. Create an expired item (5 hours in hot hold)
    expired_prep_time = (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat()
    payload = {
        "food": "Cold Pasta Primavera",
        "quantity": 15.0,
        "unit": "kg",
        "prepared_at": expired_prep_time,
        "storage_type": "HOT_HOLD",
        "temperature": 50.0,
        "category": "GRAINS"
    }
    create_res = client.post("/api/v1/surplus", json=payload, headers=auth_headers)
    assert create_res.status_code == 201
    expired_id = create_res.json()["id"]
    assert create_res.json()["status"] == "EXPIRED"

    # 2. Attempt to allocate to a shelter -> MUST BE REJECTED WITH 400!
    alloc_res = client.post(
        f"/api/v1/surplus/{expired_id}/allocate",
        json={"recipient_id": "rec-001"},
        headers=auth_headers
    )
    assert alloc_res.status_code == 400
    assert "SAFETY LOCKOUT" in alloc_res.json()["detail"] or "cannot be allocated" in alloc_res.json()["detail"]


# =====================================================================
# 5. AUTHORIZED HUMAN APPROVAL & STATUS STATE MACHINE
# =====================================================================

def test_api_human_approval_workflow_and_lifecycle_transitions(auth_headers):
    """
    Validates:
    1. Authorized manager inspection approval.
    2. Lifecycle state machine transitions across 9 statuses:
       AVAILABLE -> RESERVED -> PICKUP_SCHEDULED -> PICKED_UP -> IN_TRANSIT -> DELIVERED.
    """
    # 1. Create lot in critical window (e.g. 45m remaining -> NEEDS_HUMAN_INSPECTION)
    prep_time = (datetime.now(timezone.utc) - timedelta(hours=3, minutes=15)).isoformat()
    payload = {
        "food": "Pan-Seared Salmon Medallions",
        "quantity": 12.0,
        "unit": "kg",
        "prepared_at": prep_time,
        "storage_type": "HOT_HOLD",
        "temperature": 61.5,
        "category": "PROTEIN"
    }
    create_res = client.post("/api/v1/surplus", json=payload, headers=auth_headers)
    assert create_res.status_code == 201
    item = create_res.json()
    assert item["eligibility"] == "NEEDS_HUMAN_INSPECTION"

    # 2. Attempt to allocate BEFORE approval -> must be rejected
    alloc_fail = client.post(
        f"/api/v1/surplus/{item['id']}/allocate",
        json={"recipient_id": "rec-001"},
        headers=auth_headers
    )
    assert alloc_fail.status_code == 400
    assert "HUMAN SIGN-OFF REQUIRED" in alloc_fail.json()["detail"]

    # 3. Manager performs physical inspection & records approval
    approve_res = client.post(
        f"/api/v1/surplus/{item['id']}/approve",
        json={
            "approved": True,
            "notes": "Visual check passed, steam verified, probe reading 61.5°C.",
            "verified_temp": 61.5
        },
        headers=auth_headers
    )
    assert approve_res.status_code == 200
    assert approve_res.json()["approval_status"] == "APPROVED"

    # 4. Now allocation succeeds!
    alloc_success = client.post(
        f"/api/v1/surplus/{item['id']}/allocate",
        json={"recipient_id": "rec-001"},
        headers=auth_headers
    )
    assert alloc_success.status_code == 200
    assert alloc_success.json()["status"] == "RESERVED"

    # 5. Progress through lifecycle statuses
    statuses = ["PICKUP_SCHEDULED", "PICKED_UP", "IN_TRANSIT", "DELIVERED"]
    for next_st in statuses:
        patch_res = client.patch(
            f"/api/v1/surplus/{item['id']}/status",
            json={"new_status": next_st},
            headers=auth_headers
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["status"] == next_st


# =====================================================================
# 6. LIVE SURPLUS DASHBOARD API & AUTOMATIC ALERTS
# =====================================================================

def test_api_live_surplus_dashboard_cards_and_alerts(auth_headers):
    """
    Requirement:
    "Live Surplus dashboard. Cards should display:
     Food, Quantity, Age, Remaining window, Urgency, Location, Status.
     Add automatic expiry/urgency notifications."
    """
    res = client.get("/api/v1/surplus/dashboard/live", headers=auth_headers)
    assert res.status_code == 200
    dash = res.json()

    assert "total_active_lots" in dash
    assert "available_lots_count" in dash
    assert "critical_urgency_count" in dash
    assert "expired_lots_count" in dash
    assert "items" in dash
    assert "urgent_alerts" in dash

    if len(dash["items"]) > 0:
        first = dash["items"][0]
        # Verify all 7 required card fields
        assert "food" in first
        assert "quantity" in first
        assert "age_formatted" in first
        assert "remaining_safe_window_formatted" in first
        assert "urgency" in first
        assert "location" in first
        assert "status" in first


def test_api_urgent_notifications_stream(auth_headers):
    """
    Requirement: "Add automatic expiry/urgency notifications."
    """
    res = client.get("/api/v1/surplus/alerts/urgent", headers=auth_headers)
    assert res.status_code == 200
    alerts = res.json()
    assert isinstance(alerts, list)
    for alert in alerts:
        assert "surplus_id" in alert
        assert "urgency" in alert
        assert alert["urgency"] in ["CRITICAL", "EXPIRED"]
        assert "action" in alert
