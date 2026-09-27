"""
FoodLoop AI - Automated API Test Suite (Phase 3 Backend)
Comprehensive test suite validating:
1. Health & readiness probes
2. Standardized error envelopes & Request ID propagation
3. RBAC role-based access control enforcement
4. Pagination, filtering, and sorting
5. Double-entry inventory transactions
6. Surplus marketplace & lot declarations
7. Heuristic AI matching engine
8. Cryptographic QR single-use burn tokens & replay attack prevention
9. AI forecasting & EPA environmental analytics
"""
import pytest
from datetime import datetime, timezone, timedelta
from app.core.security import create_access_token
from app.models.models import User, Organization, Kitchen, SurplusItem, Recipient, Delivery, Donation


@pytest.fixture
def admin_headers():
    token = create_access_token({
        "sub": "11111111-1111-1111-1111-111111111111",
        "email": "admin@foodloop.ai",
        "role": "ADMIN",
        "organization_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def chef_headers():
    token = create_access_token({
        "sub": "22222222-2222-2222-2222-222222222222",
        "email": "chef@grandhyatt.com",
        "role": "KITCHEN_MANAGER",
        "organization_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def driver_headers():
    token = create_access_token({
        "sub": "33333333-3333-3333-3333-333333333333",
        "email": "driver@foodloop.ai",
        "role": "DRIVER",
        "organization_id": "cccccccc-cccc-cccc-cccc-cccccccccccc"
    })
    return {"Authorization": f"Bearer {token}"}


# =====================================================================
# 1. SYSTEM & HEALTH PROBES
# =====================================================================
def test_health_and_readiness_endpoints(client):
    health_res = client.get("/health")
    assert health_res.status_code == 200
    assert health_res.json()["status"] == "healthy"

    ready_res = client.get("/ready")
    assert ready_res.status_code == 200
    assert ready_res.json()["status"] == "ready"


# =====================================================================
# 2. STANDARDIZED ERROR HANDLING & REQUEST ID
# =====================================================================
def test_standardized_error_format_and_request_id(client, admin_headers):
    # Query non-existent surplus lot
    res = client.get("/api/v1/surplus/non-existent-uuid-9999", headers=admin_headers)
    assert res.status_code == 404
    body = res.json()
    
    assert body["success"] is False
    assert "error" in body
    assert body["error"]["code"] == "SURPLUSITEM_NOT_FOUND"
    assert "request_id" in body
    assert res.headers.get("X-Request-ID") == body["request_id"]


# =====================================================================
# 3. RBAC ROLE RESTRICTIONS
# =====================================================================
def test_rbac_access_denied_for_unauthorized_role(client, driver_headers):
    # Driver attempting to register an organization (Admin only)
    org_payload = {
        "name": "Unauthorized Org Attempt",
        "org_type": "HOTEL_BANQUET",
        "address": "123 Main St",
        "city": "Metropolis",
        "state": "NY",
        "postal_code": "10001",
        "phone": "+1-555-0199",
        "email": "unauth@org.com"
    }
    res = client.post("/api/v1/organizations", json=org_payload, headers=driver_headers)
    assert res.status_code == 403
    body = res.json()
    assert body["success"] is False
    assert body["error"]["code"] == "FORBIDDEN"


# =====================================================================
# 4. ORGANIZATIONS & KITCHENS (PAGINATION & CRUD)
# =====================================================================
def test_organizations_and_kitchens_crud(client, admin_headers):
    # Create Organization
    org_payload = {
        "name": "Phase 3 Test Enterprise Hotel",
        "org_type": "HOTEL_BANQUET",
        "registration_number": f"REG-TEST-{datetime.now().timestamp()}",
        "address": "500 Test Avenue",
        "city": "San Francisco",
        "state": "CA",
        "postal_code": "94105",
        "phone": "+1-555-4001",
        "email": f"hotel_{datetime.now().timestamp()}@test.com"
    }
    org_res = client.post("/api/v1/organizations", json=org_payload, headers=admin_headers)
    assert org_res.status_code == 201
    org_data = org_res.json()
    org_id = org_data["id"]

    # List Organizations with Pagination
    list_res = client.get("/api/v1/organizations?page=1&limit=5", headers=admin_headers)
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert "items" in list_data
    assert "pagination" in list_data
    assert list_data["pagination"]["page"] == 1

    # Create Kitchen
    kitchen_payload = {
        "organization_id": org_id,
        "name": "Main Production Kitchen Bay 1",
        "facility_type": "COMMERCIAL_KITCHEN",
        "daily_meal_capacity": 650,
        "address": "500 Test Avenue, Bay 1",
        "latitude": 37.7892,
        "longitude": -122.4014,
        "contact_name": "Executive Chef Marco",
        "contact_phone": "+1-555-4002"
    }
    k_res = client.post("/api/v1/kitchens", json=kitchen_payload, headers=admin_headers)
    assert k_res.status_code == 201
    assert k_res.json()["daily_meal_capacity"] == 650


# =====================================================================
# 5. INVENTORY & DOUBLE-ENTRY LEDGER
# =====================================================================
def test_inventory_atomic_stock_adjustments(client, chef_headers, db):
    # Setup test org
    org = Organization(
        name="Inventory Test Org",
        org_type="HOTEL_BANQUET",
        registration_number="REG-INV-001",
        address="100 Test St, SF, CA 94100",
        latitude=37.7749,
        longitude=-122.4194,
        contact_phone="+1-555-5000",
        contact_email="inv@test.com"
    )
    db.add(org)
    db.commit()

    # Add Inventory
    inv_payload = {
        "organization_id": org.id,
        "item_name": "Organic Roma Tomatoes",
        "category": "PRODUCE",
        "quantity": 100.0,
        "unit": "kg",
        "storage_condition": "REFRIGERATED",
        "expiry_date": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    }
    inv_res = client.post("/api/v1/inventory", json=inv_payload, headers=chef_headers)
    assert inv_res.status_code == 201
    inv_id = inv_res.json()["id"]

    # Stock Adjustment (Valid Deduction)
    adj_payload = {
        "quantity_change": -35.0,
        "transaction_type": "PRODUCTION_CONSUMPTION",
        "notes": "Used for marinara sauce batch"
    }
    adj_res = client.post(f"/api/v1/inventory/{inv_id}/adjust", json=adj_payload, headers=chef_headers)
    assert adj_res.status_code == 200
    assert adj_res.json()["resulting_balance"] == 65.0

    # Stock Adjustment (Exceeding Balance -> Must Error)
    invalid_adj = {
        "quantity_change": -100.0,
        "transaction_type": "MANUAL_ADJUSTMENT"
    }
    fail_res = client.post(f"/api/v1/inventory/{inv_id}/adjust", json=invalid_adj, headers=chef_headers)
    assert fail_res.status_code == 400
    assert fail_res.json()["error"]["code"] == "INSUFFICIENT_INVENTORY"


# =====================================================================
# 6. SURPLUS MARKETPLACE & AI MATCHING
# =====================================================================
def test_surplus_declaration_and_smart_matching(client, chef_headers, db):
    org = Organization(
        name="Surplus Matching Donor",
        org_type="HOTEL_BANQUET",
        registration_number="REG-SURPLUS-001",
        address="200 Market St, SF, CA 94102",
        latitude=37.7890,
        longitude=-122.4010,
        contact_phone="+1-555-6000",
        contact_email="surplus@donor.com"
    )
    db.add(org)
    db.flush()

    recipient = Recipient(
        organization_id=org.id,
        name="Hope Harbor Meal Center",
        facility_type="COMMUNITY_KITCHEN",
        address="350 4th St, SF",
        latitude=37.7820,
        longitude=-122.4040,
        max_daily_intake_kg=300.0,
        cold_storage_available=True,
        contact_person="Sister Claire",
        contact_phone="+1-555-6001"
    )
    db.add(recipient)
    db.commit()

    now = datetime.now(timezone.utc)
    surplus_payload = {
        "organization_id": org.id,
        "item_name": "Gourmet Vegetable Lasagna & Herb Bread",
        "category": "COOKED_MEALS",
        "quantity_kg": 40.0,
        "estimated_portions": 80,
        "packaging_type": "SEALED_CAMBRO_TRAYS",
        "storage_temp_condition": "HOT_HOLDING_60C",
        "consumption_safe_until": (now + timedelta(hours=4)).isoformat(),
        "pickup_window_start": now.isoformat(),
        "pickup_window_end": (now + timedelta(hours=3)).isoformat(),
        "pickup_address": "200 Market St, Dock 2",
        "pickup_lat": 37.7890,
        "pickup_lng": -122.4010,
        "haccp_verified": True
    }

    surplus_res = client.post("/api/v1/surplus", json=surplus_payload, headers=chef_headers)
    assert surplus_res.status_code == 201
    surplus_id = surplus_res.json()["id"]

    # Test AI Matching
    match_res = client.get(f"/api/v1/matching/surplus/{surplus_id}", headers=chef_headers)
    assert match_res.status_code == 200
    match_data = match_res.json()
    assert "recommended_matches" in match_data
    assert len(match_data["recommended_matches"]) > 0
    top_match = match_data["recommended_matches"][0]
    assert top_match["compatibility_score"] > 50.0


# =====================================================================
# 7. CRYPTOGRAPHIC QR VERIFICATION & REPLAY DEFENSE
# =====================================================================
def test_qr_generation_burn_and_replay_attack_defense(client, chef_headers, driver_headers, db):
    # Setup test delivery
    org = Organization(
        name="Delivery Test Org",
        org_type="HOTEL_BANQUET",
        registration_number="REG-DELIV-001",
        address="100 Main St, SF, CA 94101",
        latitude=37.7892,
        longitude=-122.4064,
        contact_phone="+1-555-7000",
        contact_email="delivery@test.com"
    )
    db.add(org)
    db.flush()

    donation = Donation(
        donor_org_id=org.id,
        tracking_number=f"TRK-TEST-{datetime.now().timestamp()}",
        total_weight_kg=50.0,
        total_portions=100,
        status="COURIER_ASSIGNED",
        haccp_verified=True
    )
    db.add(donation)
    db.flush()

    delivery = Delivery(
        donation_id=donation.id,
        status="DISPATCHED",
        stop_sequence=1
    )
    db.add(delivery)
    db.commit()

    # 1. Generate Single-Use QR Token
    gen_payload = {
        "delivery_id": delivery.id,
        "handover_type": "PICKUP"
    }
    gen_res = client.post("/api/v1/qr/generate", json=gen_payload, headers=chef_headers)
    assert gen_res.status_code == 200
    token = gen_res.json()["token"]

    # 2. Verify QR Token (First Time: Success & Token Burned)
    verify_payload = {
        "token": token,
        "handover_type": "PICKUP",
        "current_lat": 37.7892,
        "current_lng": -122.4064,
        "measured_temp_c": 3.8
    }
    verify_res = client.post("/api/v1/qr/verify", json=verify_payload, headers=driver_headers)
    assert verify_res.status_code == 200
    assert verify_res.json()["verified"] is True

    # 3. Attempt Replay Attack (Second Time: Must Be Rejected)
    replay_res = client.post("/api/v1/qr/verify", json=verify_payload, headers=driver_headers)
    assert replay_res.status_code == 400
    assert replay_res.json()["error"]["code"] == "QR_TOKEN_INVALID_OR_BURNED"


# =====================================================================
# 8. AI FORECASTING & ANALYTICS
# =====================================================================
def test_ai_forecast_and_analytics_summary(client, chef_headers):
    # Forecast inference
    forecast_payload = {
        "kitchen_id": "test-kitchen-123",
        "target_date": (datetime.now().date() + timedelta(days=1)).isoformat(),
        "historical_covers": 450,
        "is_weekend": 0,
        "temp_c": 21.5
    }
    f_res = client.post("/api/v1/forecast/predict", json=forecast_payload, headers=chef_headers)
    assert f_res.status_code == 200
    f_data = f_res.json()
    assert "predicted_headcount" in f_data
    assert "predicted_surplus_kg" in f_data

    # Dynamic shelf-life
    sl_res = client.get("/api/v1/forecast/shelf-life?category=cooked_meals&storage_temp=refrigerated&hours_since_prep=3.0")
    assert sl_res.status_code == 200
    assert sl_res.json()["category"] == "cooked_meals"

    # Sustainability analytics summary
    ana_res = client.get("/api/v1/analytics/summary", headers=chef_headers)
    assert ana_res.status_code == 200
    ana_data = ana_res.json()
    assert "total_co2e_avoided_kg" in ana_data
    assert "diversion_rate_percentage" in ana_data
