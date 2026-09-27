"""
FoodLoop AI - Phase 11 Test Suite: QR Chain of Custody & Verification
Comprehensive automated test suite verifying:
1. Unique immutable donation ID assignment.
2. Cryptographic HMAC-SHA256 QR token generation.
3. Full 7-stage custody lifecycle:
   DONATION_CREATED -> ACCEPTED -> PICKUP_ASSIGNED -> PICKED_UP -> IN_TRANSIT -> DELIVERED -> RECEIVED
4. Role-specific QR scans:
   - Kitchen: Confirm handover
   - Driver: Confirm pickup
   - Recipient: Confirm receipt
5. Prevention of duplicate scanning (burned single-use nonces).
6. Prevention of unauthorized scanning (server-side RBAC validation).
7. Prevention of invalid state transitions (strict unidirectional state machine).
8. Prevention of tampered donation IDs (cryptographic HMAC signature checks).
9. Forensic audit trail with proof capture (temperature, GPS, signature, notes, SHA-256 chain).
"""
import pytest
import uuid
import hmac
import hashlib
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal
from app.core.config import settings
from app.core.security import create_access_token
from app.models.models import Donation, SurplusItem, Organization, User, DonationCustodyEvent, DonationQrToken
from app.services.custody_service import CustodyService

client = TestClient(app)


SEEDED_USERS = {
    "ADMIN": ("11111111-1111-1111-1111-111111111111", "admin@foodloop.ai"),
    "KITCHEN_MANAGER": ("22222222-2222-2222-2222-222222222222", "chef.vance@hyatt-culinary.com"),
    "NGO": ("44444444-4444-4444-4444-444444444444", "director@stjudefoodbank.org"),
    "DRIVER": ("55555555-5555-5555-5555-555555555555", "alex.driver@looplogistics.com"),
    "LOGISTICS_MANAGER": ("55555555-5555-5555-5555-555555555555", "alex.driver@looplogistics.com"),
    "RECIPIENT": ("44444444-4444-4444-4444-444444444444", "director@stjudefoodbank.org"),
}


def get_auth_header(role: str, user_id: str = None, org_id: str = None) -> dict:
    default_uid, default_email = SEEDED_USERS.get(role, ("11111111-1111-1111-1111-111111111111", f"{role.lower()}@foodloop.test"))
    uid = user_id or default_uid
    oid = org_id or "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    token = create_access_token(data={
        "sub": uid,
        "email": default_email,
        "role": role,
        "org_id": oid
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_donation():
    db = SessionLocal()
    # Find or create a test donor org
    donor_org = db.query(Organization).first()
    donor_id = donor_org.id if donor_org else "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    recipient_org = db.query(Organization).filter(Organization.id != donor_id).first()
    recipient_id = recipient_org.id if recipient_org else "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

    unique_num = uuid.uuid4().hex[:8].upper()
    immutable_id = f"DON-{unique_num}"
    tracking_no = f"TRK-{unique_num}"

    donation = Donation(
        donor_org_id=donor_id,
        recipient_org_id=recipient_id,
        immutable_donation_id=immutable_id,
        tracking_number=tracking_no,
        total_weight_kg=120.5,
        total_portions=180,
        status="DONATION_CREATED",
        haccp_verified=True
    )
    db.add(donation)
    db.flush()

    # Genesis custody event
    now = datetime.now(timezone.utc)
    prev_hash = "0" * 64
    genesis_raw = f"{prev_hash}|{now.isoformat()}|11111111-1111-1111-1111-111111111111|ADMIN|{donation.id}|DONATION_CREATED|weight=120.5kg"
    integrity_hash = hashlib.sha256(genesis_raw.encode("utf-8")).hexdigest()

    genesis_ev = DonationCustodyEvent(
        donation_id=donation.id,
        event="DONATION_CREATED",
        from_status="NONE",
        to_status="DONATION_CREATED",
        user_id="11111111-1111-1111-1111-111111111111",
        role="ADMIN",
        timestamp=now.replace(tzinfo=None),
        notes="Test donation initialized in test suite.",
        previous_hash=prev_hash,
        integrity_hash=integrity_hash
    )
    db.add(genesis_ev)
    db.commit()
    db.refresh(donation)

    donation_id = donation.id
    db.close()
    return {"id": donation_id, "immutable_id": immutable_id, "tracking_number": tracking_no}


# ====================================================================
# TEST 1: Unique Immutable Donation ID & Creation
# ====================================================================
def test_donation_unique_immutable_id(test_donation):
    headers = get_auth_header("ADMIN")
    resp = client.get(f"/api/v1/qr/donations/{test_donation['immutable_id']}/status", headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["immutable_donation_id"] == test_donation["immutable_id"]
    assert data["immutable_donation_id"].startswith("DON-")
    assert data["status"] == "DONATION_CREATED"


# ====================================================================
# TEST 2: Cryptographic QR Generation with HMAC-SHA256
# ====================================================================
def test_qr_token_generation_and_hmac_signature(test_donation):
    # Transition to ACCEPTED first so Kitchen Handover QR can be generated
    admin_headers = get_auth_header("ADMIN")
    tr_resp = client.post(
        f"/api/v1/qr/donations/{test_donation['id']}/transition",
        headers=admin_headers,
        json={"target_status": "ACCEPTED"}
    )
    assert tr_resp.status_code == 200, tr_resp.text

    # Generate Kitchen Handover QR
    kitchen_headers = get_auth_header("KITCHEN_MANAGER")
    gen_resp = client.post(
        "/api/v1/qr/donations/generate",
        headers=kitchen_headers,
        json={
            "donation_id": test_donation["immutable_id"],
            "stage": "KITCHEN_HANDOVER",
            "expires_in_minutes": 45
        }
    )
    assert gen_resp.status_code == 200, gen_resp.text
    token_data = gen_resp.json()
    assert "token" in token_data
    assert token_data["token"].startswith("FOODLOOP:DONATION:")
    assert token_data["stage"] == "KITCHEN_HANDOVER"
    assert len(token_data["nonce"]) == 32
    assert len(token_data["hmac_signature"]) == 64
    assert "KITCHEN_MANAGER" in token_data["allowed_scanner_roles"]


# ====================================================================
# TEST 3: Full 7-Stage Custody Lifecycle
# ====================================================================
def test_full_7_stage_custody_workflow(test_donation):
    admin_headers = get_auth_header("ADMIN")
    kitchen_headers = get_auth_header("KITCHEN_MANAGER")
    driver_headers = get_auth_header("DRIVER")
    ngo_headers = get_auth_header("NGO")

    # Step 1: DONATION_CREATED -> ACCEPTED (by NGO/Recipient)
    r1 = client.post(
        f"/api/v1/qr/donations/{test_donation['id']}/transition",
        headers=ngo_headers,
        json={"target_status": "ACCEPTED", "notes": "NGO accepted manifest."}
    )
    assert r1.status_code == 200, r1.text
    assert r1.json()["status"] == "ACCEPTED"

    # Step 2: ACCEPTED -> PICKUP_ASSIGNED (by Logistics Manager / Admin)
    r2 = client.post(
        f"/api/v1/qr/donations/{test_donation['id']}/transition",
        headers=admin_headers,
        json={"target_status": "PICKUP_ASSIGNED", "notes": "Assigned courier vehicle VAN-402."}
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["status"] == "PICKUP_ASSIGNED"

    # Step 3: Kitchen confirms handover via QR scan -> PICKED_UP
    gen_kitchen = client.post(
        "/api/v1/qr/donations/generate",
        headers=kitchen_headers,
        json={"donation_id": test_donation["id"], "stage": "KITCHEN_HANDOVER"}
    ).json()

    verify_kitchen = client.post(
        "/api/v1/qr/donations/verify",
        headers=kitchen_headers,
        json={
            "token": gen_kitchen["token"],
            "proof_type": "TEMPERATURE_READING",
            "measured_temp_c": 3.8,
            "current_lat": 40.7128,
            "current_lng": -74.0060,
            "notes": "Food stored at 3.8°C. Seals intact."
        }
    )
    assert verify_kitchen.status_code == 200, verify_kitchen.text
    assert verify_kitchen.json()["current_status"] == "PICKED_UP"
    assert verify_kitchen.json()["event"] == "KITCHEN_HANDOVER_CONFIRMED"

    # Step 4: Driver confirms pickup and starts transit -> IN_TRANSIT
    gen_driver_pickup = client.post(
        "/api/v1/qr/donations/generate",
        headers=driver_headers,
        json={"donation_id": test_donation["id"], "stage": "DRIVER_PICKUP"}
    ).json()

    verify_pickup = client.post(
        "/api/v1/qr/donations/verify",
        headers=driver_headers,
        json={
            "token": gen_driver_pickup["token"],
            "measured_temp_c": 3.9,
            "current_lat": 40.7129,
            "current_lng": -74.0061,
            "signature_data": "Driver Alex Mercer - Sig Verified",
            "notes": "Cargo loaded into refrigerated hold."
        }
    )
    assert verify_pickup.status_code == 200, verify_pickup.text
    assert verify_pickup.json()["current_status"] == "IN_TRANSIT"

    # Step 5: Driver arrives and confirms delivery -> DELIVERED
    gen_delivery = client.post(
        "/api/v1/qr/donations/generate",
        headers=driver_headers,
        json={"donation_id": test_donation["id"], "stage": "COURIER_DELIVERY"}
    ).json()

    verify_delivery = client.post(
        "/api/v1/qr/donations/verify",
        headers=driver_headers,
        json={
            "token": gen_delivery["token"],
            "measured_temp_c": 4.1,
            "current_lat": 40.7306,
            "current_lng": -73.9352,
            "notes": "Unloaded at recipient receiving dock."
        }
    )
    assert verify_delivery.status_code == 200, verify_delivery.text
    assert verify_delivery.json()["current_status"] == "DELIVERED"

    # Step 6: Recipient confirms receipt via QR scan -> RECEIVED
    gen_receipt = client.post(
        "/api/v1/qr/donations/generate",
        headers=ngo_headers,
        json={"donation_id": test_donation["id"], "stage": "RECIPIENT_RECEIPT"}
    ).json()

    verify_receipt = client.post(
        "/api/v1/qr/donations/verify",
        headers=ngo_headers,
        json={
            "token": gen_receipt["token"],
            "measured_temp_c": 4.2,
            "signature_data": "Dr. Sarah Lin, Director of Food Rescue",
            "notes": "All 180 portions received in excellent condition. Digital custody signoff complete."
        }
    )
    assert verify_receipt.status_code == 200, verify_receipt.text
    receipt_data = verify_receipt.json()
    assert receipt_data["current_status"] == "RECEIVED"
    assert receipt_data["event"] == "RECIPIENT_RECEIPT_CONFIRMED"

    # Verify audit trail has recorded every single event in chronological sequence
    audit_resp = client.get(f"/api/v1/qr/donations/{test_donation['id']}/audit-trail", headers=admin_headers)
    assert audit_resp.status_code == 200
    trail_data = audit_resp.json()
    assert trail_data["chain_intact"] is True
    assert trail_data["total_events"] >= 6
    events = [e["event"] for e in trail_data["audit_trail"]]
    assert "DONATION_CREATED" in events
    assert "TRANSITION_TO_ACCEPTED" in events
    assert "TRANSITION_TO_PICKUP_ASSIGNED" in events
    assert "KITCHEN_HANDOVER_CONFIRMED" in events
    assert "DRIVER_PICKUP_CONFIRMED" in events
    assert "COURIER_DELIVERY_CONFIRMED" in events
    assert "RECIPIENT_RECEIPT_CONFIRMED" in events


# ====================================================================
# TEST 4: Prevent Duplicate Scanning (Single-Use Burn Tokens)
# ====================================================================
def test_prevent_duplicate_scanning(test_donation):
    admin_headers = get_auth_header("ADMIN")
    kitchen_headers = get_auth_header("KITCHEN_MANAGER")

    # Set status to ACCEPTED
    client.post(
        f"/api/v1/qr/donations/{test_donation['id']}/transition",
        headers=admin_headers,
        json={"target_status": "ACCEPTED"}
    )

    gen = client.post(
        "/api/v1/qr/donations/generate",
        headers=kitchen_headers,
        json={"donation_id": test_donation["id"], "stage": "KITCHEN_HANDOVER"}
    ).json()

    # First scan succeeds
    scan1 = client.post(
        "/api/v1/qr/donations/verify",
        headers=kitchen_headers,
        json={"token": gen["token"]}
    )
    assert scan1.status_code == 200, scan1.text

    # Second scan with SAME token MUST FAIL (409 Conflict - Duplicate Scan)
    scan2 = client.post(
        "/api/v1/qr/donations/verify",
        headers=kitchen_headers,
        json={"token": gen["token"]}
    )
    assert scan2.status_code in [409, 400], scan2.text
    err = scan2.json()
    assert "already been scanned" in str(err).lower() or "burned" in str(err).lower()


# ====================================================================
# TEST 5: Prevent Unauthorized Scanning (Server-Side RBAC)
# ====================================================================
def test_prevent_unauthorized_scanning(test_donation):
    admin_headers = get_auth_header("ADMIN")
    kitchen_headers = get_auth_header("KITCHEN_MANAGER")
    driver_headers = get_auth_header("DRIVER")
    ngo_headers = get_auth_header("NGO")

    client.post(
        f"/api/v1/qr/donations/{test_donation['id']}/transition",
        headers=admin_headers,
        json={"target_status": "ACCEPTED"}
    )

    # Kitchen generates handover QR
    gen = client.post(
        "/api/v1/qr/donations/generate",
        headers=kitchen_headers,
        json={"donation_id": test_donation["id"], "stage": "KITCHEN_HANDOVER"}
    ).json()

    # DRIVER tries to confirm KITCHEN handover -> MUST BE 403 FORBIDDEN
    unauth_scan = client.post(
        "/api/v1/qr/donations/verify",
        headers=driver_headers,
        json={"token": gen["token"]}
    )
    assert unauth_scan.status_code == 403, unauth_scan.text
    assert "not authorized" in unauth_scan.text.lower() or "UNAUTHORIZED_SCANNER_ROLE" in unauth_scan.text

    # NGO tries to confirm KITCHEN handover -> MUST BE 403 FORBIDDEN
    unauth_ngo = client.post(
        "/api/v1/qr/donations/verify",
        headers=ngo_headers,
        json={"token": gen["token"]}
    )
    assert unauth_ngo.status_code == 403, unauth_ngo.text


# ====================================================================
# TEST 6: Prevent Invalid State Transitions
# ====================================================================
def test_prevent_invalid_state_transitions(test_donation):
    admin_headers = get_auth_header("ADMIN")

    # Trying to jump directly from DONATION_CREATED to DELIVERED -> MUST FAIL (422)
    invalid_jump = client.post(
        f"/api/v1/qr/donations/{test_donation['id']}/transition",
        headers=admin_headers,
        json={"target_status": "DELIVERED"}
    )
    assert invalid_jump.status_code in [400, 422], invalid_jump.text

    # Trying to jump directly to RECEIVED -> MUST FAIL (422)
    invalid_jump2 = client.post(
        f"/api/v1/qr/donations/{test_donation['id']}/transition",
        headers=admin_headers,
        json={"target_status": "RECEIVED"}
    )
    assert invalid_jump2.status_code in [400, 422], invalid_jump2.text


# ====================================================================
# TEST 7: Prevent Tampered Donation IDs
# ====================================================================
def test_prevent_tampered_donation_ids(test_donation):
    admin_headers = get_auth_header("ADMIN")
    kitchen_headers = get_auth_header("KITCHEN_MANAGER")

    client.post(
        f"/api/v1/qr/donations/{test_donation['id']}/transition",
        headers=admin_headers,
        json={"target_status": "ACCEPTED"}
    )

    gen = client.post(
        "/api/v1/qr/donations/generate",
        headers=kitchen_headers,
        json={"donation_id": test_donation["id"], "stage": "KITCHEN_HANDOVER"}
    ).json()

    original_token = gen["token"]
    # Tamper with token: swap donation ID with a fake reference
    parts = original_token.split(":")
    parts[2] = "DON-FAKEHACK"
    tampered_token = ":".join(parts)

    scan_resp = client.post(
        "/api/v1/qr/donations/verify",
        headers=kitchen_headers,
        json={"token": tampered_token}
    )
    assert scan_resp.status_code in [400, 404], scan_resp.text
    assert "tampered" in scan_resp.text.lower() or "not found" in scan_resp.text.lower() or "TAMPERED_DONATION_ID" in scan_resp.text


# ====================================================================
# TEST 8: Forensic Audit Trail & Proof Telemetry Verification
# ====================================================================
def test_custody_audit_trail_and_proof_capture(test_donation):
    admin_headers = get_auth_header("ADMIN")
    trail_resp = client.get(
        f"/api/v1/qr/donations/{test_donation['immutable_id']}/audit-trail",
        headers=admin_headers
    )
    assert trail_resp.status_code == 200, trail_resp.text
    data = trail_resp.json()
    assert "audit_trail" in data
    assert len(data["audit_trail"]) >= 1
    genesis = data["audit_trail"][0]
    assert genesis["event"] == "DONATION_CREATED"
    assert genesis["previous_hash"] == "0" * 64
    assert len(genesis["integrity_hash"]) == 64
    assert data["chain_intact"] is True
