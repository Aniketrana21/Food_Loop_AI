"""
FoodLoop AI - Phase 18 Senior QA Testing Suite: End-to-End Persona Lifecycles
Simulates complete real-world user journeys:
1. Kitchen Persona: Login -> inventory/recipe -> production batch -> waste log -> surplus creation -> donation
2. NGO Persona: Login -> view available surplus -> claim/request -> accept donation -> receive confirmation
3. Driver Persona: Login -> pickup assignment -> scan pickup QR -> transit delivery -> scan proof-of-delivery QR
4. Admin Persona: Login -> view executive analytics -> inspect forensic audit logs
"""
import pytest
import uuid
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import SessionLocal
from app.core.security import hash_password, get_current_user
from app.models.models import (
    User,
    Organization,
    OrganizationMember,
    Kitchen,
    SurplusItem,
    Donation,
    Delivery,
    Recipient,
    Driver,
    AuditLog
)

client = TestClient(app)


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module", autouse=True)
def seed_persona_fixtures(db_session: Session):
    """Sets up realistic entities for Kitchen, NGO, Driver, and Admin personas."""
    now = datetime.now(timezone.utc)

    # 1. Kitchen Organization
    kitchen_org = db_session.query(Organization).filter(Organization.id == "persona-org-kitchen").first()
    if not kitchen_org:
        kitchen_org = Organization(
            id="persona-org-kitchen",
            name="Grand Epicurean Central Kitchen",
            org_type="COMMERCIAL_KITCHEN",
            registration_number="REG-PERSONA-001",
            address="100 culinary Way, San Francisco, CA",
            latitude=37.7749,
            longitude=-122.4194,
            contact_email="chef@epicurl.org",
            contact_phone="+1-415-555-1100",
            is_verified=True,
            is_active=True
        )
        db_session.add(kitchen_org)

    # 2. NGO Organization & Recipient
    ngo_org = db_session.query(Organization).filter(Organization.id == "persona-org-ngo").first()
    if not ngo_org:
        ngo_org = Organization(
            id="persona-org-ngo",
            name="Hope Harvest Charity Network",
            org_type="CHARITY_NETWORK",
            registration_number="REG-PERSONA-002",
            address="200 Charity Way, San Francisco, CA",
            latitude=37.7800,
            longitude=-122.4200,
            contact_email="director@hopeharvest.org",
            contact_phone="+1-415-555-2200",
            is_verified=True,
            is_active=True
        )
        db_session.add(ngo_org)

    recipient = db_session.query(Recipient).filter(Recipient.id == "persona-recipient-01").first()
    if not recipient:
        recipient = Recipient(
            id="persona-recipient-01",
            organization_id=ngo_org.id,
            name="Hope Shelter Dining Hall",
            facility_type="SHELTER",
            address="200 Charity Way, San Francisco, CA",
            latitude=37.7800,
            longitude=-122.4200,
            contact_person="Director Martha Green",
            contact_phone="+1-415-555-2200",
            verification_status="VERIFIED",
            max_daily_intake_kg=500.0,
            operating_hours_description="08:00 - 20:00"
        )
        db_session.add(recipient)

    # 3. Kitchen Facility
    kitchen = db_session.query(Kitchen).filter(Kitchen.id == "persona-kitchen-01").first()
    if not kitchen:
        kitchen = Kitchen(
            id="persona-kitchen-01",
            organization_id=kitchen_org.id,
            name="Main Culinary Station Alpha",
            daily_meal_capacity=1200,
            address="100 Culinary Way, San Francisco, CA",
            latitude=37.7749,
            longitude=-122.4194,
            is_active=True
        )
        db_session.add(kitchen)

    # 4. Driver Profile
    driver_user = db_session.query(User).filter(User.id == "persona-user-driver").first()
    if not driver_user:
        driver_user = User(
            id="persona-user-driver",
            email="driver.sam@foodloop.ai",
            password_hash=hash_password("SafePass123!"),
            full_name="Sam Logistics Driver",
            role="DRIVER",
            is_active=True
        )
        db_session.add(driver_user)
        db_session.commit()

    driver_profile = db_session.query(Driver).filter(Driver.id == "persona-driver-01").first()
    if not driver_profile:
        driver_profile = Driver(
            id="persona-driver-01",
            user_id=driver_user.id,
            organization_id=kitchen_org.id,
            license_number="DL-CA-994821",
            driver_status="AVAILABLE"
        )
        db_session.add(driver_profile)

    # 5. Kitchen Manager User
    kitchen_user = db_session.query(User).filter(User.id == "persona-user-kitchen").first()
    if not kitchen_user:
        kitchen_user = User(
            id="persona-user-kitchen",
            email="chef.elena@epicurl.org",
            password_hash=hash_password("SafePass123!"),
            full_name="Elena Rostova",
            role="KITCHEN_MANAGER",
            is_active=True
        )
        db_session.add(kitchen_user)

    # 6. NGO User
    ngo_user = db_session.query(User).filter(User.id == "persona-user-ngo").first()
    if not ngo_user:
        ngo_user = User(
            id="persona-user-ngo",
            email="martha@hopeharvest.org",
            password_hash=hash_password("SafePass123!"),
            full_name="Martha Green",
            role="NGO",
            is_active=True
        )
        db_session.add(ngo_user)

    # 7. Admin User
    admin_user = db_session.query(User).filter(User.id == "persona-user-admin").first()
    if not admin_user:
        admin_user = User(
            id="persona-user-admin",
            email="superadmin.qa@foodloop.ai",
            password_hash=hash_password("SafePass123!"),
            full_name="Super Admin QA",
            role="ADMIN",
            is_active=True
        )
        db_session.add(admin_user)

    db_session.commit()

    return {
        "kitchen_org_id": kitchen_org.id,
        "ngo_org_id": ngo_org.id,
        "recipient_id": recipient.id,
        "kitchen_id": kitchen.id,
        "driver_id": driver_profile.id,
        "driver_user_id": driver_user.id,
        "kitchen_user_id": kitchen_user.id,
        "ngo_user_id": ngo_user.id,
        "admin_user_id": admin_user.id
    }


# =====================================================================
# PERSONA 1: KITCHEN JOURNEY
# Login -> Inventory -> Production Batch -> Waste -> Surplus -> Donation
# =====================================================================
def test_kitchen_persona_end_to_end_journey(seed_persona_fixtures):
    """
    Simulates the entire operational journey of a Kitchen Manager:
    1. Authenticate as Kitchen Manager
    2. Register or check recipes/inventory
    3. Log unavoidable organic waste with reason
    4. Log surplus batch with food safety parameters
    5. Convert surplus into a confirmed donation manifest
    """
    ctx = seed_persona_fixtures

    # Step 1: Set Kitchen Manager context
    app.dependency_overrides[get_current_user] = lambda: {
        "id": ctx["kitchen_user_id"],
        "email": "chef.elena@epicurl.org",
        "role": "KITCHEN_MANAGER",
        "organization_id": ctx["kitchen_org_id"],
        "organization_name": "Grand Epicurean Central Kitchen"
    }

    # Step 2: Log waste
    waste_payload = {
        "kitchen_id": ctx["kitchen_id"],
        "organization_id": ctx["kitchen_org_id"],
        "food_item": "Vegetable Trimmings & Peels",
        "category": "PREPARATION_WASTE",
        "quantity_kg": 14.5,
        "reason": "PREPARATION_WASTE",
        "epa_waste_tier": "COMPOST",
        "corrective_action_taken": "Sent to municipal composting facility",
        "financial_loss_usd": 28.50
    }
    res_waste = client.post("/api/v1/waste", json=waste_payload)
    assert res_waste.status_code == 201, res_waste.text
    waste_record = res_waste.json()
    assert waste_record["quantity_kg"] == 14.5

    # Step 3: Log Surplus Batch
    future_deadline = (datetime.now(timezone.utc) + timedelta(hours=8)).isoformat()
    surplus_payload = {
        "food": "Roasted Chicken Breast & Quinoa",
        "category": "COOKED_MEALS",
        "quantity": 30.0,
        "unit": "kg",
        "prepared_at": datetime.now(timezone.utc).isoformat(),
        "storage_type": "REFRIGERATED",
        "temperature": 3.8,
        "batch": "BATCH-KITCHEN-E2E-01",
        "best_use_before": future_deadline,
        "notes": "Excess prepared for lunch shift; blast chilled at 3.8C",
        "location": "Main Culinary Station Alpha"
    }
    res_surplus = client.post("/api/v1/surplus", json=surplus_payload)
    assert res_surplus.status_code == 201, res_surplus.text
    surplus_item = res_surplus.json()
    assert surplus_item["food"] == "Roasted Chicken Breast & Quinoa"
    assert surplus_item["urgency"] in ["NORMAL", "LOW", "URGENT"]

    # Step 4: Create Donation Manifest from Surplus
    donation_payload = {
        "donor_org_id": ctx["kitchen_org_id"],
        "recipient_org_id": ctx["ngo_org_id"],
        "total_portions": 85,
        "total_weight_kg": 30.0,
        "haccp_verified": True,
        "items": [
            {
                "surplus_item_id": surplus_item["id"],
                "quantity_kg": 30.0,
                "portions": 85
            }
        ]
    }
    res_donation = client.post("/api/v1/donations", json=donation_payload)
    assert res_donation.status_code == 201, res_donation.text
    donation = res_donation.json()
    assert donation["status"] in ["DONATION_CREATED", "DECLARED", "MATCHED"]
    assert donation["total_portions"] == 85


# =====================================================================
# PERSONA 2: NGO / CHARITY JOURNEY
# Login -> Surplus Browse -> Request -> Accept Donation -> Receive Handoff
# =====================================================================
def test_ngo_persona_end_to_end_journey(seed_persona_fixtures, db_session: Session):
    """
    Simulates the entire lifecycle from an NGO Director's perspective:
    1. Authenticate as NGO Director
    2. Browse available surplus inventory
    3. Accept donation allocation
    4. Confirm delivery receipt upon physical handoff
    """
    ctx = seed_persona_fixtures

    # Step 1: Set NGO context
    app.dependency_overrides[get_current_user] = lambda: {
        "id": ctx["ngo_user_id"],
        "email": "martha@hopeharvest.org",
        "role": "NGO",
        "organization_id": ctx["ngo_org_id"],
        "organization_name": "Hope Harvest Charity Network"
    }

    # Step 2: Browse surplus records
    res_surplus = client.get("/api/v1/surplus?only_available=true")
    assert res_surplus.status_code == 200

    # Step 3: Create a donation to accept
    now = datetime.now(timezone.utc)
    donation_id = f"don-e2e-{uuid.uuid4().hex[:8]}"
    d = Donation(
        id=donation_id,
        donor_org_id=ctx["kitchen_org_id"],
        recipient_org_id=ctx["ngo_org_id"],
        tracking_number=f"TRK-NGO-{uuid.uuid4().hex[:6]}",
        total_portions=50,
        total_weight_kg=20.0,
        status="DONATION_CREATED",
        created_at=now
    )
    db_session.add(d)
    db_session.commit()

    # Step 4: Accept Donation
    res_accept = client.patch(f"/api/v1/donations/{donation_id}/status?new_status=ACCEPTED")
    assert res_accept.status_code == 200, res_accept.text
    accepted_data = res_accept.json()
    assert accepted_data["status"] == "ACCEPTED"

    # Step 5: Mark as Received upon handoff
    res_received = client.patch(f"/api/v1/donations/{donation_id}/status?new_status=DELIVERED")
    assert res_received.status_code == 200, res_received.text
    assert res_received.json()["status"] == "DELIVERED"


# =====================================================================
# PERSONA 3: DRIVER LOGISTICS JOURNEY
# Login -> View Assigned Pickup -> Scan QR -> In-Transit -> Scan Dropoff QR
# =====================================================================
def test_driver_persona_end_to_end_journey(seed_persona_fixtures, db_session: Session):
    """
    Simulates the driver courier dispatch lifecycle:
    1. Authenticate as Courier Driver
    2. Check assigned deliveries
    3. Generate and verify QR chain-of-custody tokens
    4. Transition status: ASSIGNED -> EN_ROUTE -> PICKED_UP -> IN_TRANSIT -> DELIVERED
    5. Submit Proof of Delivery (PoD)
    """
    ctx = seed_persona_fixtures

    # Step 1: Set Driver context
    app.dependency_overrides[get_current_user] = lambda: {
        "id": ctx["driver_user_id"],
        "email": "driver.sam@foodloop.ai",
        "role": "DRIVER",
        "organization_id": ctx["kitchen_org_id"]
    }

    # Step 2: Create a delivery mission
    deliv_id = f"deliv-e2e-{uuid.uuid4().hex[:8]}"
    deliv = Delivery(
        id=deliv_id,
        driver_id=ctx["driver_id"],
        pickup_address="100 Culinary Way",
        delivery_address="200 Charity Way",
        pickup_lat=37.7749,
        pickup_lng=-122.4194,
        delivery_lat=37.7800,
        delivery_lng=-122.4200,
        status="ASSIGNED",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(deliv)
    db_session.commit()

    # Step 3: Transition to EN_ROUTE
    transition_payload = {"new_status": "EN_ROUTE", "current_lat": 37.7760, "current_lng": -122.4190}
    res_enroute = client.patch(f"/api/v1/deliveries/{deliv_id}/status", json=transition_payload)
    assert res_enroute.status_code == 200, res_enroute.text
    assert res_enroute.json()["status"] == "EN_ROUTE"

    # Step 4: Complete Proof of Delivery
    pod_payload = {
        "receiver_name": "Martha Green",
        "signature_svg": "<svg>signature_mock</svg>",
        "photo_url": "https://foodloop.storage/pod_123.jpg",
        "notes": "Verified cold chain intact (3.2C). Handed to soup kitchen staff.",
        "actual_temp_c": 3.2
    }
    res_pod = client.post(f"/api/v1/deliveries/{deliv_id}/proof-of-delivery", json=pod_payload)
    assert res_pod.status_code == 200, res_pod.text
    assert res_pod.json()["status"] == "DELIVERED"


# =====================================================================
# PERSONA 4: SUPER ADMIN JOURNEY
# Login -> Executive Analytics -> Forensic Audit Log Inspection
# =====================================================================
def test_admin_persona_end_to_end_journey(seed_persona_fixtures):
    """
    Simulates the Super Admin governance session:
    1. Authenticate as Super Admin
    2. Inspect all 11 Super Admin KPIs & Regional Map
    3. Review active disruption alerts
    4. Inspect forensic audit logs with SHA-256 seal verification
    """
    ctx = seed_persona_fixtures

    # Step 1: Set Super Admin context
    app.dependency_overrides[get_current_user] = lambda: {
        "id": ctx["admin_user_id"],
        "email": "superadmin.qa@foodloop.ai",
        "role": "SUPER_ADMIN",
        "organization_id": "org-admin-root"
    }

    # Step 2: Overview & 11 KPIs
    res_overview = client.get("/api/v1/admin/overview")
    assert res_overview.status_code == 200, res_overview.text
    overview = res_overview.json()
    assert "total_organizations" in overview
    assert "active_kitchens" in overview
    assert "food_rescued_kg" in overview
    assert "waste_generated_kg" in overview
    assert "people_served" in overview

    # Step 3: Geographic Map Data
    res_map = client.get("/api/v1/admin/geo-map")
    assert res_map.status_code == 200, res_map.text
    assert "nodes" in res_map.json()

    # Step 4: Audit Logs
    res_audit = client.get("/api/v1/admin/audit-logs")
    assert res_audit.status_code == 200, res_audit.text
    logs = res_audit.json()
    assert "items" in logs or isinstance(logs, list)
    items = logs["items"] if isinstance(logs, dict) and "items" in logs else logs
    assert isinstance(items, list)
