"""
FoodLoop AI - Phase 9 AI Recipient Matching & Double-Booking Prevention Test Suite
Validates:
1. Multi-factor AI Recipient Matching Engine:
   - 7 Candidate factors:
     food compatibility, capacity, distance, urgency, pickup availability, storage compatibility, operational reliability.
   - Deterministic and auditable: ZERO black-box scores.
   - Transparent match explanation with clear human-readable bullet points.
2. Matching API:
   - GET /api/v1/surplus/{id}/matches
   - Verified ranking, factor breakdown, and food safety gating.
3. Strict Double-Booking Prevention via Database Transactions:
   - SELECT ... FOR UPDATE row-level locks.
   - Concurrent/subsequent request on already reserved/claimed surplus rejected with 409 Conflict.
4. Recipient Actions:
   - Request surplus
   - Accept surplus
   - Reject surplus (releases back to pool as AVAILABLE)
   - Schedule pickup (sets PICKUP_SCHEDULED with vehicle details)
5. Recipient Dashboard & Compatible Surplus Feed:
   - GET /api/v1/recipients/{id}/dashboard
   - GET /api/v1/recipients/{id}/available-surplus
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import create_access_token
from app.core.database import SessionLocal
from app.models.models import SurplusItem, Recipient, RecipientRequirement
from app.services.recipient_matching_engine import (
    RecipientMatchingEngine,
    haversine_distance_km,
    estimate_transit_time_minutes
)

client = TestClient(app)


@pytest.fixture
def auth_headers():
    token = create_access_token(
        data={"sub": "director@stjudefoodbank.org", "id": "rec-user-001", "role": "NGO"}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def kitchen_headers():
    token = create_access_token(
        data={"sub": "chef.elena@culinary.org", "id": "test-chef-002", "role": "KITCHEN_MANAGER"}
    )
    return {"Authorization": f"Bearer {token}"}


# =====================================================================
# 1. MATCHING ENGINE & 7 FACTORS TRANSPARENCY TESTS
# =====================================================================

def test_haversine_distance_and_transit_calculation():
    """Validates GPS distance and realistic transit time."""
    # San Francisco City Hall to Ferry Building (~3.2 km)
    dist = haversine_distance_km(37.7792, -122.4191, 37.7955, -122.3937)
    assert 2.5 <= dist <= 4.0
    transit_min = estimate_transit_time_minutes(dist)
    assert 10 <= transit_min <= 20


def test_matching_engine_evaluates_all_7_factors_transparently():
    """
    Validates that the matching engine evaluates all 7 candidate factors
    and generates clear, bulleted explanations without black-box scores.
    """
    db = SessionLocal()
    try:
        recipient = db.query(Recipient).filter(Recipient.id == "rec-001-st-jude").first()
        if not recipient:
            recipient = db.query(Recipient).first()
        assert recipient is not None

        # Mock a rice-based hot-hold surplus lot
        class MockSurplus:
            id = "mock-surplus-rice-01"
            food = "Steamed Saffron Basmati Rice Pilaf & Lentils"
            title = "Steamed Saffron Basmati Rice Pilaf & Lentils"
            category = "GRAINS"
            quantity = 25.0
            quantity_kg = 25.0
            portions = 70
            storage_type = "HOT_HOLD"
            storage_temp = "HOT_HOLD"
            pickup_lat = 37.7749
            pickup_lng = -122.4194
            remaining_safe_window_minutes = 180.0

        res = RecipientMatchingEngine.evaluate_match(MockSurplus(), recipient, recipient.requirements)

        # 1. Check all 7 factors are scored
        factors = res.factors
        assert 0.0 <= factors.food_compatibility <= 100.0
        assert 0.0 <= factors.capacity <= 100.0
        assert 0.0 <= factors.distance <= 100.0
        assert 0.0 <= factors.urgency <= 100.0
        assert 0.0 <= factors.pickup_availability <= 100.0
        assert 0.0 <= factors.storage_compatibility <= 100.0
        assert 0.0 <= factors.operational_reliability <= 100.0

        # 2. Check transparent bulleted explanation (Zero black-box score)
        assert len(res.explanation_bullets) >= 4
        bullets_text = " ".join(res.explanation_bullets).lower()
        assert "km away" in bullets_text
        assert "accepts" in bullets_text
        assert "capacity" in bullets_text
        assert "pickup" in bullets_text
        assert "verified organization" in bullets_text

        # 3. Check recommendation summary
        assert len(res.recommendation_summary) > 20
        assert res.overall_match_score > 70.0
    finally:
        db.close()


def test_matching_engine_penalizes_storage_incompatibility():
    """
    If surplus requires cold storage and recipient lacks refrigeration,
    storage compatibility score must be heavily penalized.
    """
    class IncompatibleRecipient:
        id = "mock-incompatible-rec"
        name = "Dry Goods Only Shelter"
        facility_type = "COMMUNITY_PANTRY"
        address = "100 Pine Street"
        contact_person = "John Doe"
        contact_phone = "+1-415-555-9999"
        latitude = 37.7800
        longitude = -122.4100
        max_daily_intake_kg = 100.0
        cold_storage_available = False  # LACKS REFRIGERATION
        walk_in_chiller_capacity_kg = 0.0
        pickup_available = True
        current_demand_portions = 50
        storage_capabilities = ["DRY"]
        verification_status = "VERIFIED"
        reliability_score = 0.95
        operating_hours_description = "09:00 - 17:00"

    class ColdSurplus:
        id = "mock-cold-surplus"
        food = "Fresh Chilled Yogurt Parfaits"
        title = "Fresh Chilled Yogurt Parfaits"
        category = "DAIRY"
        quantity = 15.0
        quantity_kg = 15.0
        portions = 40
        storage_type = "COLD_HOLD"
        storage_temp = "COLD_HOLD"
        pickup_lat = 37.7749
        pickup_lng = -122.4194
        remaining_safe_window_minutes = 300.0

    res = RecipientMatchingEngine.evaluate_match(ColdSurplus(), IncompatibleRecipient(), None)
    assert res.factors.storage_compatibility <= 30.0
    assert res.is_feasible is False
    assert any("lacks certified refrigerated storage" in b.lower() for b in res.explanation_bullets)


# =====================================================================
# 2. MATCHING API (GET /api/v1/surplus/{id}/matches)
# =====================================================================

def test_api_get_surplus_matches_endpoint(kitchen_headers):
    """
    Validates GET /api/v1/surplus/{id}/matches:
    Returns ranked candidates with transparent bulleted explanations.
    """
    # 1. Create fresh eligible surplus lot
    prep_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    payload = {
        "food": "Chef's Garden Vegetable Medley with Quinoa",
        "quantity": 20.0,
        "unit": "kg",
        "prepared_at": prep_time,
        "storage_type": "HOT_HOLD",
        "temperature": 64.5,
        "category": "VEGETABLES",
        "location": "Kitchen Warmer #2"
    }
    create_res = client.post("/api/v1/surplus", json=payload, headers=kitchen_headers)
    assert create_res.status_code == 201
    surplus_id = create_res.json()["id"]

    # 2. Query matches
    match_res = client.get(f"/api/v1/surplus/{surplus_id}/matches?limit=4", headers=kitchen_headers)
    assert match_res.status_code == 200
    data = match_res.json()

    assert data["surplus_id"] == surplus_id
    assert data["food"] == payload["food"]
    assert data["matches_count"] > 0
    assert len(data["matches"]) > 0

    top_match = data["matches"][0]
    assert "recipient_id" in top_match
    assert "organization_name" in top_match
    assert "distance_km" in top_match
    assert "overall_match_score" in top_match
    assert top_match["overall_match_score"] > 0

    # Verify all 7 factor breakdown scores exist
    factors = top_match["factors"]
    assert "food_compatibility" in factors
    assert "capacity" in factors
    assert "distance" in factors
    assert "urgency" in factors
    assert "pickup_availability" in factors
    assert "storage_compatibility" in factors
    assert "operational_reliability" in factors

    # Verify transparent explanation bullets
    assert len(top_match["explanation_bullets"]) >= 3
    bullets_combined = " ".join(top_match["explanation_bullets"]).lower()
    assert "km away" in bullets_combined


def test_api_matches_rejects_expired_surplus_with_waste_workflow(kitchen_headers):
    """
    If surplus is expired or temperature-abused, matching API must return 400
    with the institutional alternative waste workflow.
    """
    expired_prep = (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat()
    payload = {
        "food": "Lukewarm Macaroni Casserole",
        "quantity": 18.0,
        "unit": "kg",
        "prepared_at": expired_prep,
        "storage_type": "HOT_HOLD",
        "temperature": 48.0,  # Below 57°C safe limit
        "category": "GRAINS"
    }
    create_res = client.post("/api/v1/surplus", json=payload, headers=kitchen_headers)
    assert create_res.status_code == 201
    surplus_id = create_res.json()["id"]
    assert create_res.json()["status"] == "EXPIRED"

    # Attempt matches
    match_res = client.get(f"/api/v1/surplus/{surplus_id}/matches", headers=kitchen_headers)
    assert match_res.status_code == 400
    detail = match_res.json().get("detail", match_res.json().get("error", {}).get("details", {}))
    assert detail["eligibility"] == "INELIGIBLE_TEMPERATURE_ABUSE"
    assert detail["suggested_waste_workflow"] == "INDUSTRIAL_COMPOSTING"


# =====================================================================
# 3. DOUBLE-BOOKING TRANSACTION SAFEGUARD TESTS
# =====================================================================

def test_api_double_booking_prevention_on_surplus_request(auth_headers, kitchen_headers):
    """
    CRITICAL REQUIREMENT:
    "Prevent double booking using database transactions."
    When Recipient A requests a surplus lot, Recipient B's subsequent request
    must be strictly blocked with HTTP 409 Conflict.
    """
    # 1. Create surplus lot
    prep_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    payload = {
        "food": "Braised Beef Tips with Carrots",
        "quantity": 25.0,
        "unit": "kg",
        "prepared_at": prep_time,
        "storage_type": "HOT_HOLD",
        "temperature": 63.0,
        "category": "PROTEIN"
    }
    create_res = client.post("/api/v1/surplus", json=payload, headers=kitchen_headers)
    assert create_res.status_code == 201
    surplus_id = create_res.json()["id"]

    # 2. Recipient A requests the surplus lot -> SUCCESS (200)
    req_a = client.post(
        f"/api/v1/surplus/{surplus_id}/request",
        json={"recipient_id": "rec-001-st-jude", "notes": "We can serve dinner tonight"},
        headers=auth_headers
    )
    assert req_a.status_code == 200
    assert req_a.json()["new_status"] == "RESERVED"
    assert req_a.json()["claim_status"] == "REQUESTED"

    # 3. Recipient B attempts to request the same lot -> MUST FAIL WITH 409 CONFLICT!
    req_b = client.post(
        f"/api/v1/surplus/{surplus_id}/request",
        json={"recipient_id": "rec-002-hope-mission", "notes": "We also need this"},
        headers=auth_headers
    )
    assert req_b.status_code == 409
    msg = req_b.json().get("detail", req_b.json().get("error", {}).get("message", ""))
    assert "DOUBLE_BOOKING_PREVENTED" in msg or "already been reserved" in msg

    # 4. Recipient B attempts to accept the lot -> MUST FAIL WITH 409 CONFLICT!
    accept_b = client.post(
        f"/api/v1/surplus/{surplus_id}/accept",
        json={"recipient_id": "rec-002-hope-mission"},
        headers=auth_headers
    )
    assert accept_b.status_code == 409


# =====================================================================
# 4. RECIPIENT ACCEPT, REJECT, AND SCHEDULE PICKUP LIFECYCLE
# =====================================================================

def test_api_recipient_accept_and_schedule_pickup_lifecycle(auth_headers, kitchen_headers):
    """
    Validates complete lifecycle:
    1. Recipient requests lot.
    2. Recipient accepts lot.
    3. Recipient schedules pickup with driver and vehicle plate.
    """
    # 1. Create surplus lot
    prep_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    payload = {
        "food": "Vegetarian Lentil Shepherd's Pie",
        "quantity": 30.0,
        "unit": "kg",
        "prepared_at": prep_time,
        "storage_type": "HOT_HOLD",
        "temperature": 66.0,
        "category": "COOKED_MEALS"
    }
    create_res = client.post("/api/v1/surplus", json=payload, headers=kitchen_headers)
    assert create_res.status_code == 201
    surplus_id = create_res.json()["id"]

    # 2. Recipient requests
    req_res = client.post(
        f"/api/v1/surplus/{surplus_id}/request",
        json={"recipient_id": "rec-001-st-jude"},
        headers=auth_headers
    )
    assert req_res.status_code == 200

    # 3. Recipient accepts
    accept_res = client.post(
        f"/api/v1/surplus/{surplus_id}/accept",
        json={"recipient_id": "rec-001-st-jude", "notes": "Approved by food bank director"},
        headers=auth_headers
    )
    assert accept_res.status_code == 200
    assert accept_res.json()["claim_status"] == "ACCEPTED"

    # 4. Recipient schedules pickup
    pickup_time = (datetime.now(timezone.utc) + timedelta(hours=1, minutes=30)).isoformat()
    schedule_res = client.post(
        f"/api/v1/surplus/{surplus_id}/schedule-pickup",
        json={
            "recipient_id": "rec-001-st-jude",
            "pickup_time": pickup_time,
            "driver_name": "Marcus Kane",
            "vehicle_plate": "7XYZ991",
            "temperature_equipment_confirmed": True,
            "driver_notes": "Insulated hot transport Cambros on board"
        },
        headers=auth_headers
    )
    assert schedule_res.status_code == 200
    assert schedule_res.json()["new_status"] == "PICKUP_SCHEDULED"
    assert schedule_res.json()["claim_status"] == "PICKUP_SCHEDULED"


def test_api_recipient_reject_releases_lot_back_to_available(auth_headers, kitchen_headers):
    """
    When a recipient rejects an allocated surplus lot, the system releases
    the lot back to AVAILABLE status so other recipients can claim it.
    """
    # 1. Create surplus lot
    prep_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    payload = {
        "food": "Mixed Grain Bowls with Tofu",
        "quantity": 16.0,
        "unit": "kg",
        "prepared_at": prep_time,
        "storage_type": "ROOM_TEMP",
        "category": "GRAINS"
    }
    create_res = client.post("/api/v1/surplus", json=payload, headers=kitchen_headers)
    assert create_res.status_code == 201
    surplus_id = create_res.json()["id"]

    # 2. Recipient A requests
    client.post(
        f"/api/v1/surplus/{surplus_id}/request",
        json={"recipient_id": "rec-001-st-jude"},
        headers=auth_headers
    )

    # 3. Recipient A rejects lot (e.g. overstocked)
    reject_res = client.post(
        f"/api/v1/surplus/{surplus_id}/reject",
        json={"recipient_id": "rec-001-st-jude", "rejection_reason": "Storage at capacity for grains"},
        headers=auth_headers
    )
    assert reject_res.status_code == 200
    assert reject_res.json()["new_status"] == "AVAILABLE"
    assert reject_res.json()["claim_status"] == "REJECTED"

    # 4. Now Recipient B can request the released lot
    req_b = client.post(
        f"/api/v1/surplus/{surplus_id}/request",
        json={"recipient_id": "rec-002-hope-mission"},
        headers=auth_headers
    )
    assert req_b.status_code == 200
    assert req_b.json()["new_status"] == "RESERVED"


# =====================================================================
# 5. RECIPIENT DASHBOARD & AVAILABLE SURPLUS FEED TESTS
# =====================================================================

def test_api_recipient_dashboard_and_available_surplus(auth_headers):
    """
    Validates:
    - GET /api/v1/recipients/{id}/dashboard
    - GET /api/v1/recipients/{id}/available-surplus
    Both return tailored feeds with distance and transparent explanations.
    """
    dash_res = client.get("/api/v1/recipients/rec-001-st-jude/dashboard", headers=auth_headers)
    assert dash_res.status_code == 200
    data = dash_res.json()

    assert len(data["recipient_id"]) > 0
    assert "Downtown St. Jude" in data["organization_name"]
    assert data["daily_intake_capacity_kg"] > 0
    assert "available_surplus" in data
    assert isinstance(data["available_surplus"], list)

    if len(data["available_surplus"]) > 0:
        card = data["available_surplus"][0]
        assert "food" in card
        assert "distance_km" in card
        assert "match_score" in card
        assert "transparent_explanation" in card
        assert len(card["transparent_explanation"]) > 0

    # Also check feed endpoint
    feed_res = client.get("/api/v1/recipients/rec-001-st-jude/available-surplus", headers=auth_headers)
    assert feed_res.status_code == 200
    assert isinstance(feed_res.json(), list)
