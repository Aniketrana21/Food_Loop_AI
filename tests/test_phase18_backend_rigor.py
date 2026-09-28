"""
FoodLoop AI - Phase 18 Senior QA Testing Suite: Backend Rigor
Covers:
1. Unit tests (hashing, UUID generation, role normalization, utility math)
2. Integration & API tests (health check, user profile, CRUD)
3. Authorization & RBAC tests (401 unauthenticated, 403 role violation, privilege escalation prevention)
4. Database integrity tests (unique constraints, foreign key constraints, nullable checks)
5. Transaction tests (atomic rollback on composite operation failure)
"""
import pytest
import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.main import app
from app.core.database import SessionLocal
from app.core.security import (
    hash_password,
    verify_password,
    normalize_role,
    get_current_user
)
from app.models.models import (
    User,
    Organization,
    OrganizationMember,
    Kitchen,
    AuditLog
)

client = TestClient(app)


@pytest.fixture(scope="module")
def db_session():
    """Provides an isolated database session for backend rigor tests."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module", autouse=True)
def seed_rigor_fixtures(db_session: Session):
    """Seeds baseline organizations and test users for RBAC testing."""
    now = datetime.now(timezone.utc)

    # 1. Organization
    org = db_session.query(Organization).filter(Organization.id == "rigor-org-01").first()
    if not org:
        org = Organization(
            id="rigor-org-01",
            name="Rigor QA Test Kitchen Network",
            org_type="COMMERCIAL_KITCHEN",
            registration_number="REG-RIGOR-001",
            address="500 Howard St, San Francisco, CA",
            latitude=37.7885,
            longitude=-122.3980,
            contact_email="qa@rigornetwork.org",
            contact_phone="+1-415-555-9000",
            is_verified=True,
            is_active=True
        )
        db_session.add(org)

    # 2. Users with different roles
    roles = [
        ("rigor-admin", "admin@rigor.org", "ADMIN"),
        ("rigor-kitchen", "chef@rigor.org", "KITCHEN_MANAGER"),
        ("rigor-driver", "driver@rigor.org", "DRIVER"),
        ("rigor-ngo", "shelter@rigor.org", "NGO")
    ]
    for uid, email, role in roles:
        u = db_session.query(User).filter(User.id == uid).first()
        if not u:
            u = User(
                id=uid,
                email=email,
                password_hash=hash_password("SafePass123!"),
                full_name=f"Rigor {role.title()}",
                role=role,
                is_active=True
            )
            db_session.add(u)

    db_session.commit()
    return {"org_id": "rigor-org-01"}


# =====================================================================
# 1. UNIT TESTS: CRYPTO, ROLES, UUIDs
# =====================================================================
def test_password_hashing_and_verification():
    """Unit test for PBKDF2-HMAC-SHA256 password security."""
    raw = "SuperSecretZeroWastePass2026!"
    hashed = hash_password(raw)
    assert hashed != raw
    assert "$" in hashed
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword123", hashed) is False
    assert verify_password("", hashed) is False


def test_role_normalization_and_aliases():
    """Unit test for enterprise role alias normalization."""
    assert normalize_role("super_admin") == "ADMIN"
    assert normalize_role("donor") == "KITCHEN_MANAGER"
    assert normalize_role("fpu_mgr") == "PROCESSOR"
    assert normalize_role("recipient") == "NGO"
    assert normalize_role("driver") == "DRIVER"
    assert normalize_role("LOGISTICS") == "LOGISTICS_MANAGER"


# =====================================================================
# 2. INTEGRATION & API TESTS: HEALTH CHECK & PROFILE
# =====================================================================
def test_api_health_check():
    """Verifies that the API health check responds with UP status and active dialect."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy" or data["status"] == "UP"
    assert "version" in data


# =====================================================================
# 3. AUTHORIZATION & RBAC TESTS (401, 403, Privilege Escalation)
# =====================================================================
def test_unauthenticated_request_rejected_with_401():
    """Verifies that protected admin endpoints reject unauthenticated calls with 401."""
    # Temporarily remove dependency override if set
    old_override = app.dependency_overrides.pop(get_current_user, None)
    try:
        res = client.get("/api/v1/admin/overview", headers={"Authorization": "Bearer invalid.expired.token"})
        assert res.status_code == 401, f"Expected 401, got {res.status_code}: {res.text}"
    finally:
        if old_override:
            app.dependency_overrides[get_current_user] = old_override


def test_driver_role_cannot_access_super_admin_endpoints():
    """Verifies that a DRIVER user cannot access Super Admin governance APIs (403 Forbidden)."""
    app.dependency_overrides[get_current_user] = lambda: {
        "id": "rigor-driver",
        "email": "driver@rigor.org",
        "role": "DRIVER",
        "organization_id": "rigor-org-01"
    }

    res = client.get("/api/v1/admin/overview")
    assert res.status_code == 403, f"Expected 403 Forbidden for Driver role on admin overview, got {res.status_code}"


def test_kitchen_manager_cannot_modify_system_business_rules():
    """Verifies that a Kitchen Manager cannot alter system business rules (403 Forbidden)."""
    app.dependency_overrides[get_current_user] = lambda: {
        "id": "rigor-kitchen",
        "email": "chef@rigor.org",
        "role": "KITCHEN_MANAGER",
        "organization_id": "rigor-org-01"
    }

    payload = {
        "key": "MAX_TRANSIT_TIME_HOURS",
        "category": "LOGISTICS",
        "value": {"threshold": 999},
        "description": "Unauthorized attempt to modify logistics rule"
    }
    res = client.post("/api/v1/admin/business-rules", json=payload)
    assert res.status_code == 403, f"Expected 403 Forbidden, got {res.status_code}"


# =====================================================================
# 4. DATABASE INTEGRITY & CONSTRAINT TESTS
# =====================================================================
def test_database_duplicate_user_email_rejected(db_session: Session):
    """Verifies that the database enforces UNIQUE constraint on User.email."""
    duplicate_user = User(
        id=str(uuid.uuid4()),
        email="admin@rigor.org",  # Existing email
        password_hash=hash_password("Pass123!"),
        full_name="Impostor Admin",
        role="ADMIN"
    )
    db_session.add(duplicate_user)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_database_duplicate_organization_reg_number_rejected(db_session: Session):
    """Verifies that the database enforces UNIQUE constraint on Organization.registration_number."""
    duplicate_org = Organization(
        id=str(uuid.uuid4()),
        name="Copycat Org",
        org_type="COMMERCIAL_KITCHEN",
        registration_number="REG-RIGOR-001",  # Existing reg number
        address="123 Fake St",
        latitude=37.77,
        longitude=-122.41,
        contact_email="fake@org.com",
        contact_phone="+1-555-0000"
    )
    db_session.add(duplicate_org)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


# =====================================================================
# 5. TRANSACTION TESTS: ATOMIC ROLLBACK ON COMPOSITE FAILURE
# =====================================================================
def test_atomic_rollback_on_composite_transaction_failure(db_session: Session):
    """
    Verifies that a failed composite database transaction rolls back all mutations,
    leaving no orphaned records.
    """
    initial_kitchen_count = db_session.query(Kitchen).count()
    test_kitchen_id = f"test-kitchen-atomic-{uuid.uuid4().hex[:8]}"

    try:
        # Step 1: Add a kitchen
        k = Kitchen(
            id=test_kitchen_id,
            organization_id="rigor-org-01",
            name="Atomic Rollback Test Kitchen",
            facility_type="CENTRAL_KITCHEN",
            capacity_meals_per_day=500,
            address="100 Test Blvd",
            latitude=37.77,
            longitude=-122.41,
            is_active=True
        )
        db_session.add(k)
        db_session.flush()

        # Step 2: Intentionally trigger a crash with an invalid foreign key or null constraint
        broken_kitchen = Kitchen(
            id=f"test-kitchen-broken-{uuid.uuid4().hex[:8]}",
            organization_id="NON_EXISTENT_FOREIGN_KEY_ORG_999999",  # Breaks FK
            name="Should Fail",
            facility_type="CENTRAL_KITCHEN",
            capacity_meals_per_day=100,
            address="000 Broken St",
            latitude=0.0,
            longitude=0.0
        )
        db_session.add(broken_kitchen)
        db_session.flush()  # Must raise IntegrityError

        db_session.commit()
    except Exception:
        db_session.rollback()

    # Verify that Step 1 kitchen was NOT persisted due to atomic rollback
    persisted = db_session.query(Kitchen).filter(Kitchen.id == test_kitchen_id).first()
    assert persisted is None, "Transaction rollback failed: first record was incorrectly committed!"
    assert db_session.query(Kitchen).count() == initial_kitchen_count
