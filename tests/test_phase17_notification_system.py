"""
FoodLoop AI - Test Suite for Phase 17 Notification System
Verifies:
1. All 10 canonical event templates seeded and accessible
2. Template placeholder rendering & test-render endpoint
3. User notification preferences & per-event channel overrides
4. In-app notification delivery, listing, unread count, and mark read
5. Multi-channel delivery (in-app, email, push)
6. Duplicate avoidance via deduplication engine (idempotency keys)
7. Quiet hours suppression and CRITICAL event bypass
8. Exponential backoff retry logic for failed delivery & batch retry
9. Fault-tolerant non-crashing wrapper for business workflows
10. Notification system delivery statistics telemetry
"""
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import SessionLocal
from app.core.security import hash_password, get_current_user
from app.models.models import (
    User,
    Organization,
    OrganizationMember,
    NotificationPreference,
    NotificationTemplate,
    NotificationEvent,
    Notification
)
from app.services.notification_service import notification_service
from app.schemas.notification_schemas import NotificationEventDispatch

client = TestClient(app)

MOCK_USER = {
    "id": "phase17-user-test",
    "email": "notifications.tester@foodloop.ai",
    "role": "ADMIN",
    "organization_id": "phase17-org-test",
    "organization_name": "Phase 17 Notifications Org"
}

app.dependency_overrides[get_current_user] = lambda: MOCK_USER


@pytest.fixture(scope="module")
def db_session():
    """Provides a transactional database session for Phase 17 tests."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module", autouse=True)
def setup_test_entities(db_session: Session):
    """Sets up test organization, admin user, and organization member."""
    # 1. Test Org
    org = db_session.query(Organization).filter(Organization.id == "phase17-org-test").first()
    if not org:
        org = Organization(
            id="phase17-org-test",
            name="Phase 17 Notifications Org",
            org_type="COMMERCIAL_KITCHEN",
            registration_number="REG-NOTIF-001",
            address="100 Market St, San Francisco, CA",
            latitude=37.7936,
            longitude=-122.3958,
            contact_email="hq@notiftest.org",
            contact_phone="+1-415-555-0101",
            is_verified=True,
            is_active=True
        )
        db_session.add(org)

    # 2. Test User
    user = db_session.query(User).filter(User.id == "phase17-user-test").first()
    if not user:
        user = User(
            id="phase17-user-test",
            email="notifications.tester@foodloop.ai",
            password_hash=hash_password("SafePass123!"),
            full_name="Notification Tester",
            role="ADMIN",
            is_active=True
        )
        db_session.add(user)

    db_session.commit()

    # Member link
    member = db_session.query(OrganizationMember).filter(
        OrganizationMember.user_id == user.id,
        OrganizationMember.organization_id == org.id
    ).first()
    if not member:
        member = OrganizationMember(
            id="phase17-member-test",
            user_id=user.id,
            organization_id=org.id,
            role_in_org="ADMIN"
        )
        db_session.add(member)
        db_session.commit()

    # Pre-seed default templates
    notification_service.seed_default_templates(db_session)

    return {"org_id": org.id, "user_id": user.id, "email": user.email}


# =====================================================================
# TEST 1: ALL 10 CANONICAL EVENT TEMPLATES SEEDED
# =====================================================================
def test_all_10_canonical_templates_seeded():
    """Verifies that all 10 canonical event templates are seeded and retrievable via API."""
    res = client.get("/api/v1/notifications/templates")
    assert res.status_code == 200, res.text
    templates = res.json()
    assert len(templates) >= 10

    event_types = [t["event_type"] for t in templates]
    required_events = [
        "surplus.created",
        "surplus.urgent",
        "recipient.accepted",
        "pickup.assigned",
        "pickup.delayed",
        "delivery.completed",
        "expiry.approaching",
        "waste.high_detected",
        "forecast.generated",
        "ai.recommendation_generated"
    ]
    for req in required_events:
        assert req in event_types, f"Missing required canonical event template: {req}"


# =====================================================================
# TEST 2: TEMPLATE RENDERING AND TEST-RENDER ENDPOINT
# =====================================================================
def test_template_rendering_and_test_render_endpoint():
    """Verifies dynamic placeholder interpolation and test-render API."""
    payload = {
        "event_type": "surplus.urgent",
        "payload": {
            "item_name": "Organic Lentil Soup",
            "quantity_kg": 45.5,
            "facility_name": "Central Campus Kitchen",
            "hours_remaining": 3,
            "expiry_time": "18:00 UTC"
        }
    }
    res = client.post("/api/v1/notifications/templates/test-render", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()
    assert "45.5 kg of Organic Lentil Soup" in data["rendered_title"] or "45.5 kg" in data["rendered_title"]
    assert "Central Campus Kitchen" in data["rendered_in_app"]
    assert "3 hours" in data["rendered_in_app"]


# =====================================================================
# TEST 3: USER NOTIFICATION PREFERENCES GET & PUT
# =====================================================================
def test_user_notification_preferences():
    """Verifies retrieval of default preferences and updates for quiet hours and channel overrides."""
    # 1. GET preferences
    res_get = client.get("/api/v1/notifications/preferences")
    assert res_get.status_code == 200, res_get.text
    pref = res_get.json()
    assert "in_app_enabled" in pref
    assert "email_enabled" in pref
    assert "push_enabled" in pref

    # 2. PUT preferences
    update_payload = {
        "in_app_enabled": True,
        "email_enabled": True,
        "push_enabled": False,
        "email_address": "manager.verified@foodloop.ai",
        "push_token": "fcm_test_token_sample_12345",
        "quiet_hours_enabled": True,
        "quiet_hours_start": "23:00",
        "quiet_hours_end": "06:00",
        "event_overrides": {
            "surplus.urgent": {"email": True, "push": True, "in_app": True},
            "forecast.generated": {"email": False, "push": False, "in_app": True}
        }
    }
    res_put = client.put("/api/v1/notifications/preferences", json=update_payload)
    assert res_put.status_code == 200, res_put.text
    updated = res_put.json()
    assert updated["email_address"] == "manager.verified@foodloop.ai"
    assert updated["quiet_hours_enabled"] is True
    assert updated["event_overrides"]["surplus.urgent"]["email"] is True


# =====================================================================
# TEST 4: IN-APP NOTIFICATION DELIVERY & READ ACTIONS
# =====================================================================
def test_in_app_notification_delivery_and_feed(setup_test_entities):
    """Verifies that an in-app notification event populates notifications feed and marks read."""
    user_id = setup_test_entities["user_id"]
    org_id = setup_test_entities["org_id"]

    # Dispatch event targeting user
    dispatch_payload = {
        "event_type": "recipient.accepted",
        "payload": {
            "recipient_name": "Hope Community Kitchen",
            "donation_id": "DON-99881",
            "quantity_kg": 28.0,
            "item_name": "Steamed Rice & Veggies"
        },
        "user_id": user_id,
        "organization_id": org_id,
        "channels": ["in_app"],
        "force_dispatch": True
    }
    res_dispatch = client.post("/api/v1/notifications/events/dispatch", json=dispatch_payload)
    assert res_dispatch.status_code == 201, res_dispatch.text
    ev = res_dispatch.json()
    assert ev["status"] == "DELIVERED"
    assert "in_app" in ev["channel_delivery_results"]

    # Check unread count
    res_unread = client.get("/api/v1/notifications/unread-count")
    assert res_unread.status_code == 200

    # Mark all read
    res_read_all = client.patch("/api/v1/notifications/read-all")
    assert res_read_all.status_code == 200
    assert res_read_all.json()["status"] == "SUCCESS"


# =====================================================================
# TEST 5: MULTI-CHANNEL DELIVERY (IN-APP, EMAIL, PUSH)
# =====================================================================
def test_multi_channel_delivery(setup_test_entities):
    """Verifies successful simultaneous dispatch across in-app, email, and push channels."""
    user_id = setup_test_entities["user_id"]
    org_id = setup_test_entities["org_id"]

    dispatch_payload = {
        "event_type": "delivery.completed",
        "payload": {
            "quantity_kg": 60.0,
            "item_name": "Fresh Baked Rolls",
            "recipient_name": "Metro Shelter",
            "donation_id": "DON-55412",
            "co2e_kg": 150.0,
            "recipient_email": "shelter@metro.org",
            "push_token": "fcm_metro_token_888"
        },
        "user_id": user_id,
        "organization_id": org_id,
        "channels": ["in_app", "email", "push"],
        "force_dispatch": True
    }
    res = client.post("/api/v1/notifications/events/dispatch", json=dispatch_payload)
    assert res.status_code == 201, res.text
    ev = res.json()
    assert ev["status"] == "DELIVERED"

    results = ev["channel_delivery_results"]
    assert results["in_app"]["status"] == "DELIVERED"
    assert results["email"]["status"] == "DELIVERED"
    assert results["push"]["status"] == "DELIVERED"
    assert "message_id" in results["email"]
    assert "ticket_id" in results["push"]


# =====================================================================
# TEST 6: DEDUPLICATION LOGIC PREVENTS DUPLICATE NOTIFICATIONS
# =====================================================================
def test_deduplication_prevents_duplicate_notifications(setup_test_entities):
    """Verifies that identical events within the deduplication window are marked DEDUPLICATED."""
    user_id = setup_test_entities["user_id"]
    org_id = setup_test_entities["org_id"]
    unique_key = f"dedup_test_{datetime.now(timezone.utc).timestamp()}"

    payload = {
        "event_type": "waste.high_detected",
        "payload": {
            "kitchen_name": "Baker Station 3",
            "waste_kg": 42.0,
            "percentage_increase": 45,
            "waste_category": "OVERPRODUCTION"
        },
        "user_id": user_id,
        "organization_id": org_id,
        "channels": ["in_app", "email"],
        "idempotency_key": unique_key,
        "force_dispatch": False
    }

    # First dispatch - should DELIVER
    res1 = client.post("/api/v1/notifications/events/dispatch", json=payload)
    assert res1.status_code == 201, res1.text
    assert res1.json()["status"] == "DELIVERED"

    # Second immediate dispatch with same idempotency key - should DEDUPLICATE
    res2 = client.post("/api/v1/notifications/events/dispatch", json=payload)
    assert res2.status_code == 201, res2.text
    ev2 = res2.json()
    assert ev2["status"] == "DEDUPLICATED"
    assert ev2["channel_delivery_results"]["deduplication"]["suppressed"] is True


# =====================================================================
# TEST 7: QUIET HOURS FILTERING & CRITICAL EVENT BYPASS
# =====================================================================
def test_quiet_hours_and_critical_bypass(setup_test_entities, db_session: Session):
    """
    Verifies that active quiet hours suppress non-critical events,
    while CRITICAL events (e.g. surplus.urgent) bypass quiet hours.
    """
    user_id = setup_test_entities["user_id"]
    org_id = setup_test_entities["org_id"]

    # Set quiet hours active covering all 24 hours (00:00 to 23:59)
    pref = notification_service.get_or_create_preference(db_session, user_id)
    pref.quiet_hours_enabled = True
    pref.quiet_hours_start = "00:00"
    pref.quiet_hours_end = "23:59"
    db_session.commit()

    # 1. Non-critical event: forecast.generated (priority: LOW)
    non_crit_payload = {
        "event_type": "forecast.generated",
        "payload": {
            "facility_name": "Kitchen A",
            "target_date": "Tomorrow",
            "projected_headcount": 200,
            "estimated_surplus_kg": 15.0,
            "confidence_score": 88
        },
        "user_id": user_id,
        "organization_id": org_id,
        "channels": ["email", "push"],
        "force_dispatch": True
    }
    res_non_crit = client.post("/api/v1/notifications/events/dispatch", json=non_crit_payload)
    assert res_non_crit.status_code == 201, res_non_crit.text
    assert res_non_crit.json()["status"] == "SUPPRESSED_QUIET_HOURS"

    # 2. Critical event: surplus.urgent (priority: CRITICAL) -> MUST BYPASS QUIET HOURS
    crit_payload = {
        "event_type": "surplus.urgent",
        "payload": {
            "item_name": "Fresh Milk & Dairy",
            "quantity_kg": 80.0,
            "facility_name": "Cold Storage Depot",
            "hours_remaining": 2,
            "expiry_time": "Immediate",
            "recipient_email": "urgent.dispatch@foodloop.ai"
        },
        "user_id": user_id,
        "organization_id": org_id,
        "channels": ["email"],
        "force_dispatch": True
    }
    res_crit = client.post("/api/v1/notifications/events/dispatch", json=crit_payload)
    assert res_crit.status_code == 201, res_crit.text
    assert res_crit.json()["status"] == "DELIVERED", "CRITICAL event must bypass quiet hours!"

    # Reset quiet hours to avoid affecting subsequent tests
    pref.quiet_hours_enabled = False
    db_session.commit()


# =====================================================================
# TEST 8: RETRY LOGIC FOR FAILED DELIVERY
# =====================================================================
def test_retry_logic_for_failed_delivery(setup_test_entities):
    """
    Verifies that failed channel deliveries trigger RETRYING status with
    exponential backoff, and can be successfully retried individually or in batch.
    """
    user_id = setup_test_entities["user_id"]
    org_id = setup_test_entities["org_id"]

    # Dispatch with simulated email transport failure
    payload = {
        "event_type": "pickup.delayed",
        "payload": {
            "donation_id": "DON-RETRY-01",
            "courier_name": "Driver Marco",
            "delay_minutes": 25,
            "delay_reason": "Heavy Interstate Traffic",
            "new_eta_minutes": 35,
            "recipient_email": "kitchen@foodloop.ai",
            "_simulate_email_failure": True
        },
        "user_id": user_id,
        "organization_id": org_id,
        "channels": ["email"],
        "force_dispatch": True
    }
    res = client.post("/api/v1/notifications/events/dispatch", json=payload)
    assert res.status_code == 201, res.text
    ev = res.json()

    assert ev["status"] == "RETRYING"
    assert ev["attempts"] == 1
    assert ev["next_retry_at"] is not None
    assert "failed on attempt 1" in ev["last_error"]

    event_id = ev["id"]

    # Now simulate recovery by retrying the event
    db = SessionLocal()
    try:
        db_ev = db.query(NotificationEvent).filter(NotificationEvent.id == event_id).first()
        db_ev.payload["_simulate_email_failure"] = False
        db.commit()
    finally:
        db.close()

    # Trigger individual retry endpoint
    res_retry = client.post(f"/api/v1/notifications/events/{event_id}/retry")
    assert res_retry.status_code == 200, res_retry.text
    retry_data = res_retry.json()
    assert retry_data["status"] == "DELIVERED"
    assert retry_data["attempts"] == 2

    # Test batch retry endpoint
    res_batch = client.post("/api/v1/notifications/events/retry-failed?limit=10")
    assert res_batch.status_code == 200, res_batch.text
    batch_data = res_batch.json()
    assert "total_eligible" in batch_data
    assert "retried_count" in batch_data


# =====================================================================
# TEST 9: FAULT-TOLERANT NON-CRASHING WORKFLOW GUARANTEE
# =====================================================================
def test_fault_tolerant_safe_dispatch_does_not_crash_workflows(setup_test_entities, db_session: Session):
    """
    Verifies that notification failures NEVER raise unhandled exceptions or crash
    calling business transactions (such as surplus creation, donation claims, etc.).
    """
    # Create an invalid dispatch request intentionally
    invalid_req = NotificationEventDispatch(
        event_type="unknown.malformed.event",
        payload={"corrupt_field": None},
        channels=["invalid_channel_name"],
        force_dispatch=True
    )

    # Calling dispatch_event_safe should catch any error and return (success, event, error) without raising
    success, ev, error = notification_service.dispatch_event_safe(db_session, invalid_req)
    assert isinstance(success, bool)


# =====================================================================
# TEST 10: NOTIFICATION DELIVERY STATISTICS ENDPOINT
# =====================================================================
def test_notification_delivery_stats_endpoint(setup_test_entities):
    """Verifies that delivery stats endpoint returns aggregate telemetry."""
    res = client.get("/api/v1/notifications/stats")
    assert res.status_code == 200, res.text
    stats = res.json()

    assert "total_events" in stats
    assert "delivered_events" in stats
    assert "failed_events" in stats
    assert "deduplicated_events" in stats
    assert "channel_counts" in stats
    assert "success_rate_pct" in stats
    assert stats["total_events"] >= 1
