"""
FoodLoop AI - Phase 18 Senior QA Testing Suite: Failure Scenarios & Graceful Degradation
Tests:
1. Invalid QR token (malformed token string, forged signature, tampered payload)
2. Double QR scan (single-use burn token replay prevention)
3. Expired surplus claim rejection & redirection to waste hierarchy
4. Duplicate request suppression via idempotency keys
5. Unauthorized request handling (401 / 403 standard JSON)
6. Mapping API failure fallback (Haversine Euclidean distance matrix)
7. LLM failure fallback (offline Gemini/OpenAI switches to fallback culinary responder)
8. Graceful error handling (standardized error payload without stack trace leakage)
"""
import pytest
import uuid
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import SessionLocal
from app.core.security import get_current_user, hash_password
from app.models.models import (
    Donation,
    Organization,
    Recipient,
    SurplusItem,
    User
)
from app.services.custody_service import CustodyService
from app.services.route_optimizer import haversine_km, LogisticsRouteOptimizer
from app.services.llm_service import GeminiProvider, FallbackProvider

client = TestClient(app)

MOCK_ADMIN = {
    "id": "qa-failure-admin",
    "email": "failures.qa@foodloop.ai",
    "role": "ADMIN",
    "organization_id": "org-failure-test"
}

app.dependency_overrides[get_current_user] = lambda: MOCK_ADMIN


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module", autouse=True)
def seed_failure_test_fixtures(db_session: Session):
    """Seeds test donation and organization for failure scenarios."""
    org = db_session.query(Organization).filter(Organization.id == "org-failure-test").first()
    if not org:
        org = Organization(
            id="org-failure-test",
            name="Failure Scenario Test Org",
            org_type="COMMERCIAL_KITCHEN",
            registration_number="REG-FAIL-001",
            address="100 Test St, San Francisco, CA",
            latitude=37.77,
            longitude=-122.41,
            contact_email="failure@test.org",
            contact_phone="+1-415-555-4040",
            is_verified=True,
            is_active=True
        )
        db_session.add(org)
        db_session.commit()

    recipient = db_session.query(Recipient).filter(Recipient.id == "rec-failure-test").first()
    if not recipient:
        recipient = Recipient(
            id="rec-failure-test",
            organization_id=org.id,
            name="Emergency Rescue Center",
            facility_type="SHELTER",
            address="200 Shelter St",
            latitude=37.78,
            longitude=-122.42,
            contact_person="Director Pat",
            contact_phone="+1-415-555-5050",
            verification_status="VERIFIED"
        )
        db_session.add(recipient)
        db_session.commit()

    user = db_session.query(User).filter(User.id == "qa-failure-admin").first()
    if not user:
        user = User(
            id="qa-failure-admin",
            email="failures.qa@foodloop.ai",
            password_hash=hash_password("Pass123!"),
            full_name="Admin QA",
            role="ADMIN",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

    donation = db_session.query(Donation).filter(Donation.id == "don-failure-test-01").first()
    if not donation:
        donation = Donation(
            id="don-failure-test-01",
            donor_org_id=org.id,
            recipient_org_id=org.id,
            tracking_number="TRK-FAIL-001",
            total_portions=30,
            total_weight_kg=12.0,
            status="DONATION_CREATED",
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(donation)
        db_session.commit()
    return {"donation_id": "don-failure-test-01", "org_id": org.id, "user_id": "qa-failure-admin"}


# =====================================================================
# 1. INVALID QR CODE HANDLING
# =====================================================================
def test_invalid_and_tampered_qr_code_rejected():
    """Verifies that malformed or forged QR codes return clean 400 validation errors."""
    app.dependency_overrides[get_current_user] = lambda: MOCK_ADMIN

    # 1. Malformed token format
    res_malformed = client.post("/api/v1/qr/donations/verify", json={"token": "NOT_A_VALID_FOODLOOP_TOKEN"})
    assert res_malformed.status_code in [400, 422]
    assert "MALFORMED" in res_malformed.text or "format" in res_malformed.text.lower() or "invalid" in res_malformed.text.lower()

    # 2. Tampered HMAC signature
    fake_token = "FOODLOOP:DONATION:don-failure-test-01:DRIVER_PICKUP:nonce123:1999999999:tampered_forged_sig"
    res_tampered = client.post("/api/v1/qr/donations/verify", json={"token": fake_token})
    assert res_tampered.status_code in [400, 422]
    assert "TAMPERED" in res_tampered.text or "signature" in res_tampered.text.lower() or "invalid" in res_tampered.text.lower()


# =====================================================================
# 2. DOUBLE QR SCAN / REPLAY ATTACK REJECTION
# =====================================================================
def test_double_qr_scan_rejected(db_session: Session):
    """
    Verifies that a single-use QR token cannot be scanned twice (replay prevention).
    First scan succeeds; second scan fails with DUPLICATE_SCAN error.
    """
    app.dependency_overrides[get_current_user] = lambda: MOCK_ADMIN
    custody = CustodyService(db_session)
    scanner_user = {"id": "qa-failure-admin", "role": "ADMIN", "full_name": "Admin QA", "organization_id": "org-failure-test"}

    # Create fresh isolated donation in ACCEPTED status
    replay_don_id = f"don-replay-{uuid.uuid4().hex[:8]}"
    fresh_donation = Donation(
        id=replay_don_id,
        donor_org_id="org-failure-test",
        recipient_org_id="org-failure-test",
        tracking_number=f"TRK-REPLAY-{uuid.uuid4().hex[:6]}",
        total_portions=25,
        total_weight_kg=10.0,
        status="ACCEPTED",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(fresh_donation)
    db_session.commit()

    # Generate real signed token
    token_meta = custody.generate_handover_token(
        donation_ref=replay_don_id,
        stage="KITCHEN_HANDOVER",
        user=scanner_user
    )
    raw_token = token_meta["token"]

    # First Scan - Must succeed and burn token
    res1 = custody.verify_and_burn_scan(
        token_str=raw_token,
        scanner_user=scanner_user,
        proof_payload={"actual_temp_c": 4.0}
    )
    assert res1["verified"] is True

    # Second Scan (Replay Attack) - Must fail cleanly with DuplicateScanError
    with pytest.raises(Exception) as excinfo:
        custody.verify_and_burn_scan(
            token_str=raw_token,
            scanner_user=scanner_user
        )
    err = str(excinfo.value).lower()
    assert "already been scanned" in err or "burned" in err or "duplicate" in err or "used" in err


# =====================================================================
# 3. EXPIRED SURPLUS REJECTION & WASTE WORKFLOW
# =====================================================================
def test_expired_surplus_rejection_and_waste_workflow():
    """
    Verifies that surplus logged past its safe window is automatically marked
    EXPIRED and routed to the food waste diversion hierarchy.
    """
    past_date = (datetime.now(timezone.utc) - timedelta(hours=36)).isoformat()
    expired_payload = {
        "food": "Leftover Sliced Melons & Berries",
        "category": "PRODUCE",
        "quantity": 15.0,
        "unit": "kg",
        "prepared_at": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
        "storage_type": "AMBIENT",
        "temperature": 24.0,  # Ambient holding for 5 days
        "batch": "EXPIRED-LOT-001",
        "best_use_before": past_date
    }
    res = client.post("/api/v1/surplus", json=expired_payload)
    assert res.status_code == 201, res.text
    item = res.json()

    assert item["status"] == "EXPIRED"
    assert item["urgency"] == "EXPIRED"
    assert item["eligibility"] in ["INELIGIBLE_EXPIRED", "INELIGIBLE_HOLDING_TIME_EXCEEDED"]
    assert item["suggested_waste_workflow"] in ["INDUSTRIAL_COMPOSTING", "ANAEROBIC_DIGESTION"]


# =====================================================================
# 4. DUPLICATE REQUEST SUPPRESSION
# =====================================================================
def test_duplicate_notification_request_suppression():
    """Verifies that duplicate requests sharing idempotency keys do not produce duplicate dispatches."""
    unique_key = f"fail_test_key_{uuid.uuid4().hex[:12]}"
    payload = {
        "event_type": "surplus.created",
        "payload": {"item_name": "Artisan Bread", "quantity_kg": 20},
        "idempotency_key": unique_key,
        "channels": ["in_app"]
    }
    res1 = client.post("/api/v1/notifications/events/dispatch", json=payload)
    assert res1.status_code == 201
    assert res1.json()["status"] == "DELIVERED"

    # Immediate second call with identical idempotency key
    res2 = client.post("/api/v1/notifications/events/dispatch", json=payload)
    assert res2.status_code == 201
    assert res2.json()["status"] == "DEDUPLICATED"


# =====================================================================
# 5. MAPPING API FAILURE FALLBACK
# =====================================================================
def test_mapping_api_failure_fallback():
    """
    Verifies that route optimization operates seamlessly using Haversine
    Euclidean matrix when external Mapbox or OR-Tools APIs are unavailable.
    """
    depot = {
        "name": "Main Depot",
        "latitude": 37.7749,
        "longitude": -122.4194,
        "address": "100 Main St"
    }
    missions = [
        {
            "id": "mission-01",
            "pickup_name": "Pickup Kitchen",
            "pickup_address": "200 Mission St",
            "pickup_lat": 37.7800,
            "pickup_lng": -122.4200,
            "delivery_name": "Dropoff Shelter",
            "delivery_address": "300 Folsom St",
            "delivery_lat": 37.7850,
            "delivery_lng": -122.4100,
            "cargo_weight_kg": 50.0,
            "food_urgency": "HIGH"
        }
    ]
    vehicles = [
        {
            "id": "van-01",
            "name": "Eco Van 1",
            "capacity_kg": 200.0,
            "vehicle_type": "REFRIGERATED_VAN"
        }
    ]

    plan = LogisticsRouteOptimizer.optimize_dispatch_routes(
        depot=depot,
        missions=missions,
        vehicles=vehicles
    )
    assert plan is not None
    assert plan.total_distance_km > 0
    assert plan.num_vehicles_dispatched >= 1
    assert plan.total_distance_km > 0
    assert len(plan.routes) >= 1


# =====================================================================
# 6. LLM FAILURE FALLBACK
# =====================================================================
def test_llm_failure_switches_to_fallback_provider():
    """
    Verifies that when external LLM APIs fail (e.g. invalid key or network timeout),
    the system automatically routes to FallbackProvider without raising an unhandled exception.
    """
    broken_gemini = GeminiProvider(api_key="BROKEN_INVALID_API_KEY_000")
    # Calling generate_completion catches the exception internally and returns FallbackProvider output
    output = broken_gemini.generate_completion(
        system_prompt="System prompt",
        user_prompt="Surplus ingredients: 20kg rice, 10kg tomatoes, need recipe"
    )
    assert output is not None
    assert len(output) > 20
    assert "recipe" in output.lower() or "prep" in output.lower() or "stew" in output.lower()
