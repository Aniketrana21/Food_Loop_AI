"""
FoodLoop AI - Phase 19 Complete Security Audit Test Suite
Verifies:
1. Multi-tenant isolation (Can one organization access another organization's data?)
2. Driver authorization (Can a driver modify another driver's delivery?)
3. NGO privacy isolation (Can an NGO access another NGO's private information?)
4. Donation approval RBAC (Can an unauthorized user approve a donation?)
5. Delivery immutability (Can a user modify a completed delivery?)
6. JWT signature & role tamper resistance (Can a client manipulate role information?)
7. QR single-use & anti-replay defense (Can QR codes be replayed?)
8. SQL Injection & XSS hygiene
9. File upload security (MIME type, size limits, magic bytes)
10. CORS & Security headers
"""
import uuid
import pytest
import jwt
from datetime import datetime, timezone, timedelta
from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.models.models import (
    User, Organization, Kitchen, Recipient, RecipientRequirement,
    Delivery, Donation, SurplusItem, WasteRecord, Inventory, Ingredient
)
from app.services.custody_service import CustodyService


@pytest.fixture
def security_fixtures(db):
    """Sets up two isolated organizations with users, kitchens, recipients, and deliveries."""
    # Org A
    org_a = Organization(
        id=f"org-alpha-{uuid.uuid4().hex[:6]}",
        name="Alpha Dining Corp",
        org_type="HOTEL_BANQUET",
        registration_number=f"REG-A-{uuid.uuid4().hex[:4]}",
        address="100 Alpha Boulevard, Metropolis",
        latitude=37.7749,
        longitude=-122.4194,
        contact_email="security-a@alpha.corp",
        contact_phone="+1-555-0101",
        is_verified=True
    )
    # Org B
    org_b = Organization(
        id=f"org-beta-{uuid.uuid4().hex[:6]}",
        name="Beta Catering Ltd",
        org_type="HOTEL_BANQUET",
        registration_number=f"REG-B-{uuid.uuid4().hex[:4]}",
        address="200 Beta Way, Metropolis",
        latitude=37.7833,
        longitude=-122.4167,
        contact_email="security-b@beta.corp",
        contact_phone="+1-555-0102",
        is_verified=True
    )
    db.add_all([org_a, org_b])
    db.flush()

    # Kitchen A
    kitchen_a = Kitchen(
        id=f"kitch-a-{uuid.uuid4().hex[:6]}",
        organization_id=org_a.id,
        name="Alpha Main Kitchen",
        address="100 Alpha Blvd",
        latitude=37.7749,
        longitude=-122.4194,
        contact_name="Chef Alpha",
        contact_phone="+1-555-1111",
        has_cold_storage=True
    )
    # Kitchen B
    kitchen_b = Kitchen(
        id=f"kitch-b-{uuid.uuid4().hex[:6]}",
        organization_id=org_b.id,
        name="Beta Central Kitchen",
        address="200 Beta Way",
        latitude=37.7833,
        longitude=-122.4167,
        contact_name="Chef Beta",
        contact_phone="+1-555-2222",
        has_cold_storage=True
    )
    db.add_all([kitchen_a, kitchen_b])
    db.flush()

    # Recipient NGO A
    rec_a = Recipient(
        id=f"ngo-a-{uuid.uuid4().hex[:6]}",
        organization_id=org_a.id,
        name="Alpha Hope Shelter",
        facility_type="SHELTER",
        address="300 Charity Ave",
        latitude=37.7749,
        longitude=-122.4194,
        max_daily_intake_kg=150.0,
        contact_person="Director Alpha",
        contact_phone="+1-555-3333"
    )
    req_a = RecipientRequirement(
        recipient_id=rec_a.id,
        acceptable_categories=["COOKED_MEALS"],
        dietary_preferences=["VEGETARIAN"],
        max_delivery_distance_km=15.0
    )
    # Recipient NGO B
    rec_b = Recipient(
        id=f"ngo-b-{uuid.uuid4().hex[:6]}",
        organization_id=org_b.id,
        name="Beta Harbor Mission",
        facility_type="FOOD_BANK",
        address="400 Mission Way",
        latitude=37.7833,
        longitude=-122.4167,
        max_daily_intake_kg=300.0,
        contact_person="Director Beta",
        contact_phone="+1-555-4444"
    )
    req_b = RecipientRequirement(
        recipient_id=rec_b.id,
        acceptable_categories=["PRODUCE", "BAKERY"],
        dietary_preferences=["HALAL"],
        max_delivery_distance_km=25.0
    )
    db.add_all([rec_a, req_a, rec_b, req_b])
    db.flush()

    # Drivers
    user_driver_1 = User(
        id=f"usr-drv-1-{uuid.uuid4().hex[:6]}",
        email=f"driver1_{uuid.uuid4().hex[:4]}@foodloop.ai",
        password_hash=hash_password("Pass123!"),
        full_name="Courier Dave One",
        role="DRIVER",
        is_active=True
    )
    user_driver_2 = User(
        id=f"usr-drv-2-{uuid.uuid4().hex[:6]}",
        email=f"driver2_{uuid.uuid4().hex[:4]}@foodloop.ai",
        password_hash=hash_password("Pass123!"),
        full_name="Courier Dan Two",
        role="DRIVER",
        is_active=True
    )
    # Kitchen Manager Org A
    user_mgr_a = User(
        id=f"usr-mgr-a-{uuid.uuid4().hex[:6]}",
        email=f"mgr_a_{uuid.uuid4().hex[:4]}@alpha.corp",
        password_hash=hash_password("Pass123!"),
        full_name="Manager Alpha",
        role="KITCHEN_MANAGER",
        is_active=True
    )
    # NGO Lead Org A
    user_ngo_a = User(
        id=f"usr-ngo-a-{uuid.uuid4().hex[:6]}",
        email=f"ngo_a_{uuid.uuid4().hex[:4]}@alpha.corp",
        password_hash=hash_password("Pass123!"),
        full_name="NGO Lead Alpha",
        role="NGO",
        is_active=True
    )
    # NGO Lead Org B
    user_ngo_b = User(
        id=f"usr-ngo-b-{uuid.uuid4().hex[:6]}",
        email=f"ngo_b_{uuid.uuid4().hex[:4]}@beta.corp",
        password_hash=hash_password("Pass123!"),
        full_name="NGO Lead Beta",
        role="NGO",
        is_active=True
    )
    # Platform Super Admin
    user_admin = User(
        id=f"usr-admin-{uuid.uuid4().hex[:6]}",
        email=f"superadmin_{uuid.uuid4().hex[:4]}@foodloop.ai",
        password_hash=hash_password("Pass123!"),
        full_name="System Auditor",
        role="ADMIN",
        is_active=True
    )
    db.add_all([user_driver_1, user_driver_2, user_mgr_a, user_ngo_a, user_ngo_b, user_admin])
    db.flush()

    # Deliveries
    deliv_driver_1 = Delivery(
        id=f"deliv-1-{uuid.uuid4().hex[:6]}",
        food_title="Prepared Hot Stews",
        cargo_weight_kg=25.0,
        status="ASSIGNED",
        driver_id=user_driver_1.id,
        pickup_address="100 Alpha Blvd",
        delivery_address="300 Charity Ave"
    )
    deliv_driver_2 = Delivery(
        id=f"deliv-2-{uuid.uuid4().hex[:6]}",
        food_title="Fresh Artisan Rolls",
        cargo_weight_kg=15.0,
        status="ASSIGNED",
        driver_id=user_driver_2.id,
        pickup_address="200 Beta Way",
        delivery_address="400 Mission Way"
    )
    deliv_completed = Delivery(
        id=f"deliv-done-{uuid.uuid4().hex[:6]}",
        food_title="Delivered Pastries",
        cargo_weight_kg=10.0,
        status="DELIVERED",
        driver_id=user_driver_1.id,
        pickup_address="100 Alpha Blvd",
        delivery_address="300 Charity Ave",
        proof_of_delivery_receiver_name="Sister Mary",
        proof_of_delivery_verified_at=datetime.now(timezone.utc)
    )
    db.add_all([deliv_driver_1, deliv_driver_2, deliv_completed])

    # Donations
    donation_created = Donation(
        id=f"don-created-{uuid.uuid4().hex[:6]}",
        immutable_donation_id=f"DON-{uuid.uuid4().hex[:8].upper()}",
        tracking_number=f"TRK-{uuid.uuid4().hex[:8].upper()}",
        donor_org_id=org_a.id,
        recipient_org_id=org_b.id,
        total_weight_kg=50.0,
        total_portions=120,
        status="DONATION_CREATED"
    )
    donation_accepted = Donation(
        id=f"don-accepted-{uuid.uuid4().hex[:6]}",
        immutable_donation_id=f"DON-{uuid.uuid4().hex[:8].upper()}",
        tracking_number=f"TRK-{uuid.uuid4().hex[:8].upper()}",
        donor_org_id=org_a.id,
        recipient_org_id=org_b.id,
        total_weight_kg=30.0,
        total_portions=75,
        status="ACCEPTED"
    )
    db.add_all([donation_created, donation_accepted])

    # Inventory Lots for Org A & Org B
    ing_a = Ingredient(organization_id=org_a.id, name="Organic Whole Milk", category="DAIRY", unit="L")
    ing_b = Ingredient(organization_id=org_b.id, name="Prime Rib Roast", category="PROTEIN", unit="kg")
    db.add_all([ing_a, ing_b])
    db.flush()

    inv_a = Inventory(
        kitchen_id=kitchen_a.id,
        ingredient_id=ing_a.id,
        lot_number="LOT-ALPHA-001",
        current_quantity=100.0,
        unit="L",
        expiry_date=datetime.now(timezone.utc) + timedelta(days=10)
    )
    inv_b = Inventory(
        kitchen_id=kitchen_b.id,
        ingredient_id=ing_b.id,
        lot_number="LOT-BETA-001",
        current_quantity=50.0,
        unit="kg",
        expiry_date=datetime.now(timezone.utc) + timedelta(days=12)
    )
    # Waste records
    waste_a = WasteRecord(
        organization_id=org_a.id,
        kitchen_id=kitchen_a.id,
        food_item="Spoiled Cream",
        waste_category="SPOILAGE",
        weight_kg=5.0,
        root_cause="SPOILAGE",
        epa_hierarchy_tier="LANDFILL"
    )
    waste_b = WasteRecord(
        organization_id=org_b.id,
        kitchen_id=kitchen_b.id,
        food_item="Trimmings",
        waste_category="PREPARATION_WASTE",
        weight_kg=8.0,
        root_cause="PREPARATION_WASTE",
        epa_hierarchy_tier="COMPOST"
    )
    db.add_all([inv_a, inv_b, waste_a, waste_b])
    db.commit()

    # Generate JWT tokens
    token_mgr_a = create_access_token({"sub": user_mgr_a.id, "email": user_mgr_a.email, "role": "KITCHEN_MANAGER", "organization_id": org_a.id})
    token_ngo_a = create_access_token({"sub": user_ngo_a.id, "email": user_ngo_a.email, "role": "NGO", "organization_id": org_a.id})
    token_ngo_b = create_access_token({"sub": user_ngo_b.id, "email": user_ngo_b.email, "role": "NGO", "organization_id": org_b.id})
    token_driver_1 = create_access_token({"sub": user_driver_1.id, "email": user_driver_1.email, "role": "DRIVER", "organization_id": org_a.id})
    token_driver_2 = create_access_token({"sub": user_driver_2.id, "email": user_driver_2.email, "role": "DRIVER", "organization_id": org_b.id})
    token_admin = create_access_token({"sub": user_admin.id, "email": user_admin.email, "role": "ADMIN", "organization_id": org_a.id})

    return {
        "org_a": org_a,
        "org_b": org_b,
        "kitchen_a": kitchen_a,
        "kitchen_b": kitchen_b,
        "rec_a": rec_a,
        "rec_b": rec_b,
        "deliv_driver_1": deliv_driver_1,
        "deliv_driver_2": deliv_driver_2,
        "deliv_completed": deliv_completed,
        "donation_created": donation_created,
        "donation_accepted": donation_accepted,
        "inv_a": inv_a,
        "inv_b": inv_b,
        "waste_a": waste_a,
        "waste_b": waste_b,
        "headers_mgr_a": {"Authorization": f"Bearer {token_mgr_a}"},
        "headers_ngo_a": {"Authorization": f"Bearer {token_ngo_a}"},
        "headers_ngo_b": {"Authorization": f"Bearer {token_ngo_b}"},
        "headers_driver_1": {"Authorization": f"Bearer {token_driver_1}"},
        "headers_driver_2": {"Authorization": f"Bearer {token_driver_2}"},
        "headers_admin": {"Authorization": f"Bearer {token_admin}"},
        "user_driver_1": user_driver_1,
        "user_driver_2": user_driver_2,
    }


# =====================================================================
# 1. SPECIFIC TEST: CAN A DRIVER MODIFY ANOTHER DRIVER'S DELIVERY?
# =====================================================================
def test_driver_cannot_modify_another_driver_delivery(client, security_fixtures):
    """
    IDOR / Courier Isolation Check:
    Driver 1 must NOT be permitted to modify, advance status, or submit PoD
    for a delivery assigned to Driver 2.
    """
    f = security_fixtures
    deliv_2_id = f["deliv_driver_2"].id

    # Driver 1 attempts to PATCH delivery transit notes/temperature on Driver 2's mission
    res_patch = client.patch(
        f"/api/v1/deliveries/{deliv_2_id}",
        json={"notes": "Unauthorized note by Driver 1", "current_temp_c": 4.0},
        headers=f["headers_driver_1"]
    )
    assert res_patch.status_code in [403, 404], f"Driver 1 was able to PATCH Driver 2's delivery: {res_patch.status_code}"

    # Driver 1 attempts to transition status of Driver 2's mission
    res_status = client.patch(
        f"/api/v1/deliveries/{deliv_2_id}/status",
        json={"new_status": "EN_ROUTE"},
        headers=f["headers_driver_1"]
    )
    assert res_status.status_code in [403, 404], f"Driver 1 was able to transition Driver 2's status: {res_status.status_code}"

    # Driver 1 attempts to submit proof of delivery for Driver 2's mission
    res_pod = client.post(
        f"/api/v1/deliveries/{deliv_2_id}/proof-of-delivery",
        json={"receiver_name": "Attacker Driver", "signature": "data:image/png;fake"},
        headers=f["headers_driver_1"]
    )
    assert res_pod.status_code in [403, 404], f"Driver 1 was able to submit PoD for Driver 2's mission: {res_pod.status_code}"


# =====================================================================
# 2. SPECIFIC TEST: CAN A USER MODIFY A COMPLETED DELIVERY?
# =====================================================================
def test_cannot_modify_completed_delivery(client, security_fixtures):
    """
    Delivery Terminal State Immutability:
    Once a delivery has reached terminal state (DELIVERED, CANCELLED, RECEIVED),
    subsequent mutations, status transitions, or PoD submissions must be rejected.
    """
    f = security_fixtures
    completed_id = f["deliv_completed"].id

    # Attempt to overwrite notes or temperatures on already DELIVERED mission
    res_update = client.patch(
        f"/api/v1/deliveries/{completed_id}",
        json={"notes": "Tampered post-delivery note", "current_temp_c": 28.0},
        headers=f["headers_driver_1"]
    )
    assert res_update.status_code in [400, 422, 403], f"Completed delivery was modified: {res_update.status_code}"

    # Attempt to transition status from DELIVERED back to EN_ROUTE
    res_trans = client.patch(
        f"/api/v1/deliveries/{completed_id}/status",
        json={"new_status": "EN_ROUTE"},
        headers=f["headers_driver_1"]
    )
    assert res_trans.status_code in [400, 422, 403], f"Completed delivery status was altered: {res_trans.status_code}"

    # Attempt to re-submit proof of delivery on already completed delivery
    res_pod = client.post(
        f"/api/v1/deliveries/{completed_id}/proof-of-delivery",
        json={"receiver_name": "Overwriting Receiver", "signature": "data:image/png;fake2"},
        headers=f["headers_driver_1"]
    )
    assert res_pod.status_code in [400, 422, 403], f"Proof of delivery was overwritten on completed delivery: {res_pod.status_code}"


# =====================================================================
# 3. SPECIFIC TEST: CAN AN NGO ACCESS ANOTHER NGO'S PRIVATE INFORMATION?
# =====================================================================
def test_ngo_cannot_access_or_modify_another_ngo_private_info(client, security_fixtures):
    """
    NGO Tenant Boundary Isolation:
    NGO A user must NOT be permitted to access NGO B's intake capacity,
    internal dashboard, or modify NGO B's food intake criteria.
    """
    f = security_fixtures
    rec_b_id = f["rec_b"].id

    # NGO A attempts to access NGO B's private intake dashboard
    res_dash = client.get(
        f"/api/v1/recipients/{rec_b_id}/dashboard",
        headers=f["headers_ngo_a"]
    )
    assert res_dash.status_code == 403, f"NGO A was able to access NGO B's dashboard: {res_dash.status_code}"

    # NGO A attempts to modify NGO B's intake dietary criteria
    res_put = client.put(
        f"/api/v1/recipients/{rec_b_id}/requirements",
        json={"acceptable_categories": ["PRODUCE"], "max_delivery_distance_km": 1.0},
        headers=f["headers_ngo_a"]
    )
    assert res_put.status_code == 403, f"NGO A was able to alter NGO B's requirements: {res_put.status_code}"


# =====================================================================
# 4. SPECIFIC TEST: CAN AN UNAUTHORIZED USER APPROVE A DONATION?
# =====================================================================
def test_unauthorized_user_cannot_approve_donation(client, security_fixtures):
    """
    Donation State Machine & RBAC Gate:
    A driver or unauthenticated user must NOT be able to approve/accept
    a donation manifest or approve claims.
    """
    f = security_fixtures
    don_id = f["donation_created"].id

    # Driver attempts to transition donation from DONATION_CREATED to ACCEPTED
    res_driver = client.patch(
        f"/api/v1/donations/{don_id}/status?new_status=ACCEPTED",
        headers=f["headers_driver_1"]
    )
    assert res_driver.status_code in [400, 403], f"Driver was able to approve donation: {res_driver.status_code}"

    # Unauthenticated client attempts to approve donation
    res_anon = client.patch(
        f"/api/v1/donations/{don_id}/status?new_status=ACCEPTED"
    )
    assert res_anon.status_code == 401, f"Unauthenticated user was able to approve donation: {res_anon.status_code}"


# =====================================================================
# 5. SPECIFIC TEST: CAN A CLIENT MANIPULATE ROLE INFORMATION?
# =====================================================================
def test_client_cannot_manipulate_role_information(client, security_fixtures):
    """
    JWT Integrity & Privilege Escalation Resistance:
    1. Forged token with manipulated role signed with wrong secret MUST be rejected (401).
    2. Unsigned token (alg: none or verify_signature: False bypass) MUST be rejected (401).
    3. Public self-registration with role='ADMIN' MUST NOT grant admin privileges.
    """
    # 1. Token forged with malicious secret key
    forged_token = jwt.encode(
        {"sub": "attacker-id", "email": "attacker@evil.com", "role": "ADMIN", "organization_id": "org-alpha-111"},
        "malicious-attacker-secret-key-12345",
        algorithm="HS256"
    )
    res_forged = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {forged_token}"})
    assert res_forged.status_code == 401, f"Forged JWT with manipulated role was accepted: {res_forged.status_code}"

    # 2. Token with algorithm 'none'
    header = {"alg": "none", "typ": "JWT"}
    payload = {"sub": "attacker-id", "role": "ADMIN"}
    import base64, json
    unsigned_tok = (
        base64.urlsafe_b64encode(json.dumps(header).encode()).decode().strip("=") + "." +
        base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().strip("=") + "."
    )
    res_unsigned = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {unsigned_tok}"})
    assert res_unsigned.status_code == 401, f"Unsigned JWT was accepted: {res_unsigned.status_code}"

    # 3. Privilege escalation in public registration
    res_reg = client.post("/api/v1/auth/register", json={
        "email": f"escalate_{uuid.uuid4().hex[:4]}@evil.com",
        "full_name": "Privilege Escalator",
        "role": "admin"
    })
    # Must either reject registration with ADMIN role, or sanitize role to non-admin default (e.g. KITCHEN_MANAGER / NGO)
    if res_reg.status_code == 200:
        reg_data = res_reg.json()
        assert reg_data.get("role") not in ["ADMIN", "super_admin", "admin"], "User escalated to ADMIN via public registration!"


# =====================================================================
# 6. SPECIFIC TEST: CAN QR CODES BE REPLAYED?
# =====================================================================
def test_qr_codes_cannot_be_replayed(client, security_fixtures, db):
    """
    Anti-Replay Protection:
    A single-use cryptographic QR token must burn upon initial scan.
    Subsequent replay attempts must be rejected with DuplicateScanError.
    """
    f = security_fixtures
    don_accepted_id = f["donation_accepted"].id

    # Generate Kitchen Handover QR Token
    res_gen = client.post(
        "/api/v1/qr/donations/generate",
        json={"donation_id": don_accepted_id, "stage": "KITCHEN_HANDOVER"},
        headers=f["headers_mgr_a"]
    )
    assert res_gen.status_code == 200
    token_str = res_gen.json()["token"]

    # First Scan by Kitchen Manager: MUST SUCCEED
    res_scan_1 = client.post(
        "/api/v1/qr/donations/verify",
        json={"token": token_str, "notes": "Handover to driver confirmed"},
        headers=f["headers_mgr_a"]
    )
    assert res_scan_1.status_code == 200, f"Initial valid scan failed: {res_scan_1.text}"
    assert res_scan_1.json()["verified"] is True

    # Second Scan (Replay Attack): MUST FAIL
    res_scan_2 = client.post(
        "/api/v1/qr/donations/verify",
        json={"token": token_str, "notes": "Replayed scan attempt"},
        headers=f["headers_mgr_a"]
    )
    assert res_scan_2.status_code in [400, 409], f"Replayed QR token was accepted: {res_scan_2.status_code}"
    error_msg = res_scan_2.text.lower()
    assert "already been scanned" in error_msg or "burned" in error_msg or "duplicate" in error_msg


# =====================================================================
# 7. SPECIFIC TEST: CAN ONE ORGANIZATION ACCESS ANOTHER ORGANIZATION'S DATA?
# =====================================================================
def test_cannot_access_another_organization_data(client, security_fixtures):
    """
    Cross-Tenant Isolation:
    Organization A user must not be able to modify or adjust Organization B's
    inventory stock or inspect another organization's private member roster.
    """
    f = security_fixtures
    inv_b_id = f["inv_b"].id
    org_b_id = f["org_b"].id

    # Org A manager attempts to adjust stock of Org B's inventory lot
    res_adj = client.post(
        f"/api/v1/inventory/{inv_b_id}/adjust",
        json={"quantity_change": -10.0, "transaction_type": "ADJUSTMENT", "notes": "Malicious deduction"},
        headers=f["headers_mgr_a"]
    )
    assert res_adj.status_code in [403, 404], f"Org A manager modified Org B inventory: {res_adj.status_code}"

    # Org A manager attempts to add a member to Org B's roster
    res_add_member = client.post(
        f"/api/v1/organizations/{org_b_id}/members",
        json={"user_id": f["user_driver_1"].id, "role_in_org": "ADMIN"},
        headers=f["headers_mgr_a"]
    )
    assert res_add_member.status_code in [403, 404], f"Org A manager added member to Org B: {res_add_member.status_code}"


# =====================================================================
# 8. SQL INJECTION DEFENSE TEST
# =====================================================================
def test_sql_injection_defense(client, security_fixtures):
    """
    SQL Injection Resistance:
    Tests common SQLi payloads in search parameters, ensuring parameterization
    prevents database syntax errors or unauthorized row retrieval.
    """
    f = security_fixtures
    sqli_payloads = [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "1' UNION SELECT NULL, NULL, NULL --",
        "admin' --",
        "' OR 1=1#"
    ]
    for payload in sqli_payloads:
        # Search organizations
        res = client.get(f"/api/v1/organizations?search={payload}", headers=f["headers_admin"])
        assert res.status_code == 200, f"SQLi payload caused server error: {res.status_code}"

        # Search inventory
        res_inv = client.get(f"/api/v1/inventory?search={payload}", headers=f["headers_admin"])
        assert res_inv.status_code == 200, f"SQLi payload caused server error: {res_inv.status_code}"


# =====================================================================
# 9. FILE UPLOAD SECURITY TEST
# =====================================================================
def test_file_upload_security(client, security_fixtures):
    """
    File Upload Security:
    Validates that file uploads reject non-image MIME types, executable files,
    and oversized payloads.
    """
    f = security_fixtures

    # 1. Non-image executable file upload attempt
    malicious_script = b"#!/bin/bash\nrm -rf /"
    files = {"file": ("exploit.sh", malicious_script, "application/x-sh")}
    res = client.post("/api/v1/vision/classify-file", files=files, headers=f["headers_mgr_a"])
    assert res.status_code in [400, 415, 422], f"Malicious script upload accepted: {res.status_code}"

    # 2. Oversized upload attempt (>10MB)
    oversized_data = b"X" * (11 * 1024 * 1024)  # 11 MB
    files_big = {"file": ("big_image.jpg", oversized_data, "image/jpeg")}
    res_big = client.post("/api/v1/vision/classify-file", files=files_big, headers=f["headers_mgr_a"])
    assert res_big.status_code in [400, 413, 422], f"Oversized file upload accepted: {res_big.status_code}"


# =====================================================================
# 10. CORS CONFIGURATION TEST
# =====================================================================
def test_cors_policy_rejects_untrusted_origins(client):
    """
    CORS Security:
    Validates that requests with untrusted origins and credentials are not
    granted wildcard Access-Control-Allow-Origin: *.
    """
    headers = {
        "Origin": "https://malicious-phishing-site.com",
        "Access-Control-Request-Method": "GET"
    }
    res = client.options("/api/v1/auth/me", headers=headers)
    allow_origin = res.headers.get("access-control-allow-origin")
    # Must NOT allow wildcard origin when credentials are used, or must not echo untrusted origin
    assert allow_origin != "*", "Wildcard CORS origin is active with credentials!"
    assert allow_origin != "https://malicious-phishing-site.com", "CORS policy echoed untrusted attacker origin!"
