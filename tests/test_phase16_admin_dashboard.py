"""
FoodLoop AI - Phase 16: Super Admin Dashboard Test Suite
Validates:
1. All 11 platform KPIs (Total organizations, Active kitchens, Processing units,
   Registered recipients, Food rescued, Waste generated, Waste reduction %,
   Successful donations, Active deliveries, People served, Estimated value preserved).
2. Multi-facility geographic map nodes (Kitchens, FPUs, Recipients, Live Couriers).
3. System Alerts covering all 6 mandated categories:
   - expired surplus
   - failed delivery
   - abnormal waste increase
   - model failure
   - low prediction confidence
   - system errors
4. Governed administrative actions with mandatory justification and SHA-256 audit logs:
   - manage organizations (activate / suspend)
   - approve recipients (verify / reject)
   - suspend accounts
   - configure business rules
5. Model performance telemetry (Demand forecast, waste predictor, optical food scanner).
6. Forensic tamper-evident audit log ledger viewer.
7. Strict RBAC authorization enforcement (Non-admins denied with 403).
"""
import pytest
from datetime import datetime, timedelta, timezone

from app.main import app
from app.models.models import (
    Organization,
    Kitchen,
    ProcessingUnit,
    Recipient,
    User,
    SurplusItem,
    WasteRecord,
    Donation,
    Delivery,
    ModelPrediction,
    VisionScan,
    AuditLog,
    SystemBusinessRule
)
from app.core.security import get_current_user


# Mock Auth Dependency Fixtures
def admin_user():
    return {
        "id": "super-admin-001",
        "email": "superadmin@foodloop.ai",
        "role": "SUPER_ADMIN",
        "organization_id": "org-admin-root",
        "organization_name": "FoodLoop Global Authority"
    }


def non_admin_user():
    return {
        "id": "kitchen-mgr-002",
        "email": "chef@culinaryhub.org",
        "role": "KITCHEN_MANAGER",
        "organization_id": "org-kitchen-101",
        "organization_name": "Culinary Hub"
    }


@pytest.fixture
def seed_base_environment(db):
    """Provides a consistent, isolated baseline database state for each test."""
    now = datetime.now(timezone.utc)

    # 1. Organizations
    org1 = Organization(
        id="org-test-alpha",
        name="Global Hospitality Org",
        org_type="COMMERCIAL_KITCHEN",
        registration_number="REG-KPI-001",
        address="100 Market St, San Francisco, CA",
        latitude=37.7936,
        longitude=-122.3958,
        contact_email="hq@globalhosp.org",
        contact_phone="+1-415-555-0101",
        is_verified=True,
        is_active=True
    )
    org2 = Organization(
        id="org-test-beta",
        name="Metro Food Bank Network",
        org_type="CHARITY_NETWORK",
        registration_number="REG-KPI-002",
        address="200 Mission St, San Francisco, CA",
        latitude=37.7915,
        longitude=-122.3970,
        contact_email="contact@metrofoodbank.org",
        contact_phone="+1-415-555-0202",
        is_verified=True,
        is_active=True
    )
    db.add_all([org1, org2])

    # 2. Kitchens
    k1 = Kitchen(
        id="k-test-1",
        organization_id="org-test-alpha",
        name="Grand Hyatt Culinary Center",
        address="345 Stockton St, San Francisco, CA",
        latitude=37.7892,
        longitude=-122.4068,
        daily_meal_capacity=1500,
        is_active=True
    )
    k2 = Kitchen(
        id="k-test-2",
        organization_id="org-test-alpha",
        name="Hilton Union Square Kitchen",
        address="333 O'Farrell St, San Francisco, CA",
        latitude=37.7861,
        longitude=-122.4103,
        daily_meal_capacity=1200,
        is_active=True
    )
    db.add_all([k1, k2])

    # 3. Processing Unit
    fpu = ProcessingUnit(
        id="fpu-test-1",
        organization_id="org-test-alpha",
        name="Bay Area Puree & Canning Plant",
        address="500 Industrial Way, Brisbane, CA",
        latitude=37.6811,
        longitude=-122.4014,
        processing_type="CANNING_AND_FREEZE_DRYING",
        daily_capacity_kg=2500.0,
        is_active=True
    )
    db.add(fpu)

    # 4. Registered Recipient
    rec = Recipient(
        id="rec-test-1",
        organization_id="org-test-beta",
        name="St. Anthony Dining Room",
        facility_type="SOUP_KITCHEN",
        address="121 Golden Gate Ave, San Francisco, CA",
        latitude=37.7825,
        longitude=-122.4132,
        max_daily_intake_kg=800.0,
        cold_storage_available=True,
        verification_status="VERIFIED",
        is_active=True,
        contact_person="Father Oliver",
        contact_phone="+1-415-555-7788"
    )
    db.add(rec)

    # 5. Surplus Items & Donations
    surplus = SurplusItem(
        id="surp-test-1",
        organization_id="org-test-alpha",
        kitchen_id="k-test-1",
        title="Prepared Mediterranean Stew",
        category="PREPARED_MEALS",
        quantity_kg=210.0,
        portions=500,
        status="DELIVERED",
        pickup_address="345 Stockton St, San Francisco, CA",
        pickup_lat=37.7892,
        pickup_lng=-122.4068,
        created_at=now
    )
    db.add(surplus)

    donation = Donation(
        id="don-test-1",
        immutable_donation_id="DON-KPI-001",
        donor_org_id="org-test-alpha",
        recipient_org_id="org-test-beta",
        tracking_number="TRK-KPI-9999",
        total_weight_kg=210.0,
        total_portions=500,
        status="DELIVERED",
        created_at=now
    )
    db.add(donation)

    # 6. Waste Record
    waste = WasteRecord(
        id="waste-test-1",
        organization_id="org-test-alpha",
        kitchen_id="k-test-1",
        food_item="Trimmings & Peelings",
        waste_category="PRODUCE",
        weight_kg=40.0,
        cost_loss_usd=90.0,
        recorded_at=now
    )
    db.add(waste)

    # 7. Delivery
    deliv = Delivery(
        id="deliv-test-1",
        surplus_item_id="surp-test-1",
        pickup_address=k1.address,
        pickup_lat=k1.latitude,
        pickup_lng=k1.longitude,
        delivery_address=rec.address,
        delivery_lat=rec.latitude,
        delivery_lng=rec.longitude,
        food_title="Prepared Mediterranean Stew",
        cargo_weight_kg=210.0,
        status="IN_TRANSIT",
        created_at=now
    )
    db.add(deliv)

    db.commit()
    return {
        "org1": org1,
        "org2": org2,
        "k1": k1,
        "k2": k2,
        "fpu": fpu,
        "rec": rec,
        "surplus": surplus,
        "donation": donation,
        "waste": waste,
        "deliv": deliv
    }


# ====================================================================
# TEST 1: ALL 11 PLATFORM OVERVIEW KPIS
# ====================================================================
def test_admin_overview_11_kpis(client, db, seed_base_environment):
    """
    Verifies that all 11 Super Admin KPIs are accurately calculated and returned.
    """
    app.dependency_overrides[get_current_user] = admin_user
    response = client.get("/api/v1/admin/overview")
    assert response.status_code == 200
    data = response.json()

    # Verify all 11 KPIs
    assert data["total_organizations"] >= 2
    assert data["active_kitchens"] >= 2
    assert data["processing_units"] >= 1
    assert data["registered_recipients"] >= 1
    assert data["food_rescued_kg"] >= 210.0
    assert data["waste_generated_kg"] >= 40.0
    assert data["waste_reduction_pct"] > 0.0
    assert data["successful_donations"] >= 1
    assert data["active_deliveries"] >= 1
    assert data["people_served"] == int(data["food_rescued_kg"] / 0.42)
    assert data["estimated_value_preserved_usd"] == round(data["food_rescued_kg"] * 5.50, 2)


# ====================================================================
# TEST 2: GEOGRAPHIC MAP MULTI-FACILITY NODES
# ====================================================================
def test_admin_geographic_map_nodes(client, db, seed_base_environment):
    """
    Verifies that the geographic map returns nodes for Kitchens, FPUs, Recipients, and Couriers.
    """
    app.dependency_overrides[get_current_user] = admin_user
    response = client.get("/api/v1/admin/geo-map")
    assert response.status_code == 200
    data = response.json()

    assert "total_nodes" in data
    assert "nodes" in data
    assert data["kitchens_count"] >= 2
    assert data["fpus_count"] >= 1
    assert data["recipients_count"] >= 1
    assert data["couriers_count"] >= 1

    node_types = {n["node_type"] for n in data["nodes"]}
    assert "KITCHEN" in node_types
    assert "PROCESSING_UNIT" in node_types
    assert "RECIPIENT" in node_types
    assert "COURIER" in node_types

    for node in data["nodes"]:
        assert "latitude" in node
        assert "longitude" in node
        assert "status" in node


# ====================================================================
# TEST 3: SYSTEM ALERTS - ALL 6 MANDATED CATEGORIES
# ====================================================================
def test_admin_alerts_all_6_categories(client, db, seed_base_environment):
    """
    Verifies alert generation across all 6 mandated categories:
    1. expired surplus
    2. failed delivery
    3. abnormal waste increase
    4. model failure
    5. low prediction confidence
    6. system errors
    """
    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(days=1)

    # 1. Expired Surplus Item
    exp_surplus = SurplusItem(
        id="surp-expired-001",
        organization_id="org-test-alpha",
        title="Unclaimed Fresh Sushi Rolls",
        category="SEAFOOD",
        quantity_kg=15.0,
        portions=40,
        status="AVAILABLE",
        safe_consumption_deadline=yesterday,
        pickup_address="345 Stockton St, San Francisco, CA",
        pickup_lat=37.7892,
        pickup_lng=-122.4068,
        created_at=yesterday
    )

    # 2. Failed Delivery
    failed_deliv = Delivery(
        id="deliv-failed-001",
        food_title="Hot Soup Consignment",
        cargo_weight_kg=50.0,
        status="FAILED",
        proof_of_delivery_notes="Van breakdown on freeway",
        created_at=now,
        updated_at=now
    )

    # 3. Abnormal Waste Increase
    spike_waste = WasteRecord(
        id="waste-spike-001",
        organization_id="org-test-alpha",
        kitchen_id="k-test-1",
        food_item="Chilled Broth Spoiled",
        waste_category="PREPARED_MEALS",
        weight_kg=120.0,
        cost_loss_usd=480.0,
        root_cause="Walk-in cooler thermostat failure",
        recorded_at=now
    )

    # 4. Model Failure
    failed_model = ModelPrediction(
        id="pred-fail-001",
        organization_id="org-test-alpha",
        model_name="Prophet-LightGBM Hybrid",
        model_version="v2.4.1",
        prediction_type="DEMAND_FORECAST",
        target_date=now.date(),
        r2_score=-0.42,
        predicted_value=12.5,
        created_at=now
    )

    # 5. Low Prediction Confidence Vision Scan
    low_conf_scan = VisionScan(
        id="scan-low-001",
        image_url="http://storage.foodloop.ai/scan1.jpg",
        prediction="Mixed Vegetable Scraps",
        confidence=0.48,
        confidence_tier="LOW",
        created_at=now
    )

    # 6. System Error Audit Log
    sys_err = AuditLog(
        id="audit-err-001",
        module="DATABASE_CLUSTER",
        action="ERROR_CONNECTION_TIMEOUT",
        entity_name="PostgresReplica",
        entity_id="node-db-03",
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        created_at=now
    )

    db.add_all([exp_surplus, failed_deliv, spike_waste, failed_model, low_conf_scan, sys_err])
    db.commit()

    app.dependency_overrides[get_current_user] = admin_user
    response = client.get("/api/v1/admin/alerts")
    assert response.status_code == 200
    data = response.json()

    assert data["total_active_alerts"] >= 6
    by_cat = data["by_category"]

    assert by_cat["expired_surplus"] >= 1
    assert by_cat["failed_delivery"] >= 1
    assert by_cat["abnormal_waste_increase"] >= 1
    assert by_cat["model_failure"] >= 1
    assert by_cat["low_prediction_confidence"] >= 1
    assert by_cat["system_errors"] >= 1


# ====================================================================
# TEST 4: GOVERNED ORGANIZATION MANAGEMENT (Audited)
# ====================================================================
def test_governed_organization_management_audited(client, db, seed_base_environment):
    """
    Tests administrative organization suspension and activation with mandatory justification
    and cryptographic SHA-256 audit entry.
    """
    app.dependency_overrides[get_current_user] = admin_user

    # 1. Suspend Organization
    suspend_payload = {
        "action": "SUSPEND",
        "reason": "Routine regulatory HACCP compliance audit"
    }
    resp1 = client.patch("/api/v1/admin/organizations/org-test-alpha/action", json=suspend_payload)
    assert resp1.status_code == 200
    body1 = resp1.json()
    assert body1["is_active"] is False

    # Check Audit Log in DB
    audit_entry = db.query(AuditLog).filter(
        AuditLog.entity_id == "org-test-alpha",
        AuditLog.action == "ORG_SUSPEND"
    ).first()
    assert audit_entry is not None
    assert len(audit_entry.sha256_hash) == 64
    assert audit_entry.module == "ORGANIZATION_MANAGEMENT"
    assert audit_entry.new_values["reason"] == "Routine regulatory HACCP compliance audit"

    # 2. Reactivate Organization
    activate_payload = {
        "action": "ACTIVATE",
        "reason": "HACCP audit cleared with 100% score"
    }
    resp2 = client.patch("/api/v1/admin/organizations/org-test-alpha/action", json=activate_payload)
    assert resp2.status_code == 200
    body2 = resp2.json()
    assert body2["is_active"] is True


# ====================================================================
# TEST 5: GOVERNED RECIPIENT APPROVAL WORKFLOW (Audited)
# ====================================================================
def test_governed_recipient_approval_audited(client, db, seed_base_environment):
    """
    Tests recipient approval/verification workflow with mandatory audit trail.
    """
    # Create Pending Recipient
    rec_pending = Recipient(
        id="rec-pending-001",
        organization_id="org-test-beta",
        name="Mission Community Pantry",
        facility_type="FOOD_PANTRY",
        address="890 Mission St, San Francisco, CA",
        latitude=37.7819,
        longitude=-122.4048,
        verification_status="PENDING",
        is_active=False,
        contact_person="Sister Mary",
        contact_phone="+1-415-555-8899"
    )
    db.add(rec_pending)
    db.commit()

    app.dependency_overrides[get_current_user] = admin_user

    approval_payload = {
        "status": "VERIFIED",
        "notes": "501(c)(3) verified, cold chain storage inspected"
    }
    resp = client.patch("/api/v1/admin/recipients/rec-pending-001/approval", json=approval_payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["verification_status"] == "VERIFIED"
    assert body["is_active"] is True

    # Verify Audit Entry
    audit = db.query(AuditLog).filter(
        AuditLog.entity_id == "rec-pending-001",
        AuditLog.action == "RECIPIENT_VERIFIED"
    ).first()
    assert audit is not None
    assert audit.module == "RECIPIENT_GOVERNANCE"
    assert len(audit.sha256_hash) == 64


# ====================================================================
# TEST 6: GOVERNED USER ACCOUNT SUSPENSION (Audited)
# ====================================================================
def test_governed_user_suspension_audited(client, db):
    """
    Tests administrative user suspension with mandatory reason and forensic audit log.
    """
    target_user = User(
        id="user-to-suspend-001",
        email="badactor@compromised.org",
        full_name="Bad Actor",
        role="KITCHEN_MANAGER",
        is_active=True
    )
    db.add(target_user)
    db.commit()

    app.dependency_overrides[get_current_user] = admin_user

    payload = {
        "is_active": False,
        "reason": "Suspected credential sharing and abnormal batch cancellations"
    }
    resp = client.patch(f"/api/v1/admin/users/{target_user.id}/status", json=payload)
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False

    # Check DB state
    db.refresh(target_user)
    assert target_user.is_active is False

    # Check Audit Log
    audit = db.query(AuditLog).filter(
        AuditLog.entity_id == target_user.id,
        AuditLog.action == "USER_SUSPENDED"
    ).first()
    assert audit is not None
    assert audit.new_values["reason"] == payload["reason"]


# ====================================================================
# TEST 7: CONFIGURE BUSINESS RULES (Audited)
# ====================================================================
def test_configure_business_rules_audited(client, db):
    """
    Tests configuration and retrieval of system business rules with audit trail.
    """
    app.dependency_overrides[get_current_user] = admin_user

    # 1. List default rules
    resp1 = client.get("/api/v1/admin/business-rules")
    assert resp1.status_code == 200
    rules = resp1.json()
    assert len(rules) >= 4

    # 2. Add / Update a Rule
    rule_payload = {
        "rule_key": "MAX_HOT_HOLDING_HOURS",
        "rule_name": "Maximum Hot Food Safe Holding Duration",
        "category": "FOOD_SAFETY",
        "value": {"hours": 3, "temp_c_min": 63.0},
        "description": "Updated strict hot food holding limit",
        "is_active": True
    }
    resp2 = client.post("/api/v1/admin/business-rules", json=rule_payload)
    assert resp2.status_code == 200
    saved_rule = resp2.json()
    assert saved_rule["value"]["hours"] == 3

    # Check Audit Log
    audit = db.query(AuditLog).filter(
        AuditLog.entity_id == "MAX_HOT_HOLDING_HOURS",
        AuditLog.module == "BUSINESS_RULES"
    ).first()
    assert audit is not None
    assert len(audit.sha256_hash) == 64


# ====================================================================
# TEST 8: ML & CV MODEL PERFORMANCE TELEMETRY
# ====================================================================
def test_model_performance_telemetry(client, db):
    """
    Tests ML model operational health, latency, and drift status endpoints.
    """
    app.dependency_overrides[get_current_user] = admin_user
    resp = client.get("/api/v1/admin/model-performance")
    assert resp.status_code == 200
    data = resp.json()

    assert data["overall_health"] in ["OPTIMAL", "ATTENTION_REQUIRED", "CRITICAL"]
    assert len(data["models"]) >= 3

    tasks = [m["task"] for m in data["models"]]
    assert "DEMAND_FORECAST" in tasks
    assert "WASTE_PREDICTION" in tasks
    assert "COMPUTER_VISION" in tasks

    for model in data["models"]:
        assert "inference_latency_ms" in model
        assert "status" in model
        assert model["inference_latency_ms"] > 0


# ====================================================================
# TEST 9: FORENSIC AUDIT LOG VIEWER
# ====================================================================
def test_forensic_audit_logs_viewer(client, db, seed_base_environment):
    """
    Tests retrieving forensic audit logs with pagination and SHA-256 seal verification.
    """
    app.dependency_overrides[get_current_user] = admin_user

    # Perform an audited action to guarantee audit logs exist in this test
    rule_payload = {
        "rule_key": "AUDIT_TEST_RULE",
        "rule_name": "Audit Test Rule",
        "category": "OPERATIONS",
        "value": {"test": True},
        "is_active": True
    }
    client.post("/api/v1/admin/business-rules", json=rule_payload)

    resp = client.get("/api/v1/admin/audit-logs?page=1&size=10")
    assert resp.status_code == 200
    data = resp.json()

    assert "total" in data
    assert "items" in data
    assert len(data["items"]) > 0

    for item in data["items"]:
        assert "sha256_hash" in item
        assert len(item["sha256_hash"]) == 64
        assert item["is_hash_valid"] is True
        assert "module" in item
        assert "action" in item


# ====================================================================
# TEST 10: STRICT RBAC AUTHORIZATION ENFORCEMENT
# ====================================================================
def test_admin_security_unauthorized_access(client, db, seed_base_environment):
    """
    Ensures non-admin users (e.g. KITCHEN_MANAGER) cannot access administrative governance endpoints.
    "Do not give admins unrestricted database mutation through the frontend. All sensitive actions must be authorized and audited."
    """
    app.dependency_overrides[get_current_user] = non_admin_user

    # Overview endpoint
    resp1 = client.get("/api/v1/admin/overview")
    assert resp1.status_code == 403

    # Organization suspension endpoint
    resp2 = client.patch("/api/v1/admin/organizations/org-test-alpha/action", json={"action": "SUSPEND", "reason": "Unauthorized test"})
    assert resp2.status_code == 403

    # Recipient approval endpoint
    resp3 = client.patch("/api/v1/admin/recipients/rec-test-1/approval", json={"status": "VERIFIED"})
    assert resp3.status_code == 403

    # User suspension endpoint
    resp4 = client.patch("/api/v1/admin/users/user-to-suspend-001/status", json={"is_active": False, "reason": "Unauthorized"})
    assert resp4.status_code == 403

    # Business rules endpoint
    resp5 = client.post("/api/v1/admin/business-rules", json={"rule_key": "HACK", "rule_name": "Test", "value": 1})
    assert resp5.status_code == 403
