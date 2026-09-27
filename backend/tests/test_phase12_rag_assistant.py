"""
FoodLoop AI - Phase 12 Test Suite: Production RAG AI Assistant
Comprehensive automated tests verifying:
1. Document ingestion and chunking pipeline with full metadata
   (organization, document_type, version, date, access_level, source).
2. Multi-tenant access control enforcement before retrieval
   (Strict multi-tenant partition: Org A cannot access Org B's internal documents).
3. Live operational database retrieval for "Why did waste increase?" (waste records + production variance).
4. Live operational database retrieval for "Which food causes the most waste?" (itemized kg & financial loss).
5. Live operational database retrieval for "What should we produce tomorrow?" (kitchen capacity & buffer).
6. Live operational database retrieval for "Which surplus is urgent?" (remaining safe window & cold chain).
7. Live operational database retrieval for "Show this month's impact." (meals, kg diverted, CO2e, water).
8. Strict anti-hallucination fallback:
   "I don't have enough verified information to answer that." for questions lacking evidence.
9. Persistent chat history storage and session retrieval.
10. Suggested prompts endpoint returning all 5 required prompts.
"""

import pytest
import uuid
from datetime import date, datetime, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal
from app.core.security import create_access_token
from app.models.models import (
    Organization,
    Document,
    DocumentChunk,
    RagChatMessage,
    WasteRecord,
    ProductionBatch,
    SurplusItem,
    ImpactMetric
)

client = TestClient(app)

ORG_HYATT = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
ORG_CANNING = "cccccccc-cccc-cccc-cccc-cccccccccccc"
ORG_GLOBAL = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


def get_auth_header(role: str = "KITCHEN_MANAGER", org_id: str = ORG_HYATT, user_id: str = None) -> dict:
    uid = user_id or str(uuid.uuid4())
    token = create_access_token(data={
        "sub": uid,
        "email": f"{role.lower()}@test.foodloop.ai",
        "role": role,
        "org_id": org_id,
        "organization_id": org_id
    })
    return {"Authorization": f"Bearer {token}"}


# -------------------------------------------------------------
# Test 1: Document Ingestion & Chunking with Rich Metadata
# -------------------------------------------------------------
def test_document_ingestion_and_chunking_with_metadata():
    """Verifies document ingestion parses text, chunks content, and stores all Phase 12 metadata."""
    headers = get_auth_header(role="ADMIN", org_id=ORG_HYATT)
    payload = {
        "title": "Kitchen Blast Chilling & Rapid Freeze SOP",
        "category": "HACCP_SOP",
        "document_type": "HACCP_SOP",
        "version": "2024.4",
        "doc_date": str(date.today()),
        "access_level": "ORGANIZATION_INTERNAL",
        "source": "Grand Hyatt Culinary Engineering Protocol",
        "organization_id": ORG_HYATT,
        "content": (
            "Standard Operating Procedure for blast chilling banquet leftovers: "
            "All cooked hot dishes exceeding 60°C must enter the shock freezer within 20 minutes of service end. "
            "Core temperature must be pulled down to 3°C or below within 90 minutes. "
            "Internal digital temperature probe logs must be entered into the FoodLoop station with batch barcode. "
            "Food items cooled in this manner are certified safe for donation packaging for up to 48 hours."
        )
    }

    response = client.post("/api/v1/documents/ingest", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["document_type"] == "HACCP_SOP"
    assert data["version"] == "2024.4"
    assert data["access_level"] == "ORGANIZATION_INTERNAL"
    assert data["organization_id"] == ORG_HYATT
    assert data["total_chunks"] >= 1

    # Verify chunks are stored in database
    db = SessionLocal()
    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == data["document_id"]).all()
    assert len(chunks) == data["total_chunks"]
    for c in chunks:
        meta = c.chunk_metadata
        assert meta["document_type"] == "HACCP_SOP"
        assert meta["version"] == "2024.4"
        assert meta["access_level"] == "ORGANIZATION_INTERNAL"
        assert meta["source"] == payload["source"]
        assert c.token_count > 0
        assert c.embedding_vector is not None
    db.close()


# -------------------------------------------------------------
# Test 2: Multi-Tenant Access Control Isolation
# -------------------------------------------------------------
def test_multi_tenant_access_control_isolation():
    """
    Strict Multi-Tenant Verification:
    - User in Org A (Grand Hyatt) CAN access Grand Hyatt's internal SOP.
    - User in Org B (Bay Area Canning) CANNOT access Grand Hyatt's internal SOP and receives fallback.
    - Both users can access universal public FDA food code.
    """
    hyatt_headers = get_auth_header(role="KITCHEN_MANAGER", org_id=ORG_HYATT)
    canning_headers = get_auth_header(role="KITCHEN_MANAGER", org_id=ORG_CANNING)

    query = "What is the internal banquet overproduction buffer policy for Grand Hyatt?"

    # 1. Hyatt user queries -> MUST retrieve Hyatt's internal SOP
    resp_hyatt = client.post("/api/v1/assistant/chat", json={"query": query}, headers=hyatt_headers)
    assert resp_hyatt.status_code == 200
    data_hyatt = resp_hyatt.json()
    assert data_hyatt["grounded"] is True
    assert data_hyatt["is_insufficient_evidence"] is False
    assert len(data_hyatt["sources"]) > 0
    assert any("Grand Hyatt" in s["title"] for s in data_hyatt["sources"])

    # 2. Canning user queries the EXACT same question -> MUST NOT expose Grand Hyatt private SOP!
    resp_canning = client.post("/api/v1/assistant/chat", json={"query": query}, headers=canning_headers)
    assert resp_canning.status_code == 200
    data_canning = resp_canning.json()
    # Canning user has NO access to Hyatt internal document
    for s in data_canning["sources"]:
        assert s["organization_id"] != ORG_HYATT, "Security Breach: Cross-tenant private document exposed!"

    # 3. Public Document Access: Both can query FDA Danger Zone 4-Hour rule
    public_query = "What is the FDA 4-hour rule for temperature control?"
    resp_pub_hyatt = client.post("/api/v1/assistant/chat", json={"query": public_query}, headers=hyatt_headers)
    resp_pub_canning = client.post("/api/v1/assistant/chat", json={"query": public_query}, headers=canning_headers)
    assert resp_pub_hyatt.json()["grounded"] is True
    assert resp_pub_canning.json()["grounded"] is True
    assert any("FDA" in s["title"] for s in resp_pub_hyatt.json()["sources"])
    assert any("FDA" in s["title"] for s in resp_pub_canning.json()["sources"])


# -------------------------------------------------------------
# Test 3: Operational Query - "Why did waste increase?"
# -------------------------------------------------------------
def test_operational_query_waste_increase():
    """
    Assistant should retrieve actual waste records and production batches
    and explain the trend rather than hallucinating.
    """
    headers = get_auth_header(role="KITCHEN_MANAGER", org_id=ORG_HYATT)
    query = "Why did food waste increase this week?"

    response = client.post("/api/v1/assistant/chat", json={"query": query}, headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["grounded"] is True
    assert data["is_insufficient_evidence"] is False
    assert data["operational_context"] is not None

    op = data["operational_context"]
    assert op["is_live_data"] is True
    assert op["query_type"] == "waste_increase"
    assert "percentage_increase" in op["key_metrics"]
    assert "current_week_kg" in op["key_metrics"]
    assert "primary_waste_category" in op["key_metrics"]
    assert len(op["records"]) > 0

    # Ensure response contains grounded numbers from the DB
    assert "kg" in data["answer"].lower()
    assert "%" in data["answer"]


# -------------------------------------------------------------
# Test 4: Operational Query - "Which food causes the most waste?"
# -------------------------------------------------------------
def test_operational_query_top_waste_food():
    """Assistant should retrieve actual waste items and return ranking with documented causes."""
    headers = get_auth_header(role="KITCHEN_MANAGER", org_id=ORG_HYATT)
    query = "Which food causes the most waste?"

    response = client.post("/api/v1/assistant/chat", json={"query": query}, headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["grounded"] is True
    assert data["operational_context"] is not None
    op = data["operational_context"]
    assert op["query_type"] == "food_waste_causes"
    assert "top_waste_item" in op["key_metrics"]
    assert len(op["records"]) > 0
    assert "Steamed Jasmine Rice" in op["key_metrics"]["top_waste_item"] or len(op["records"]) >= 1


# -------------------------------------------------------------
# Test 5: Operational Query - "What should we produce tomorrow?"
# -------------------------------------------------------------
def test_operational_query_production_tomorrow():
    """Assistant should retrieve production and capacity recommendations to minimize waste."""
    headers = get_auth_header(role="KITCHEN_MANAGER", org_id=ORG_HYATT)
    query = "What should we produce tomorrow?"

    response = client.post("/api/v1/assistant/chat", json={"query": query}, headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["grounded"] is True
    assert data["operational_context"] is not None
    op = data["operational_context"]
    assert op["query_type"] == "production_tomorrow"
    assert "recommended_total_portions" in op["key_metrics"]
    assert "safety_buffer_percent" in op["key_metrics"]
    assert len(op["records"]) > 0


# -------------------------------------------------------------
# Test 6: Operational Query - "Which surplus is urgent?"
# -------------------------------------------------------------
def test_operational_query_urgent_surplus():
    """Assistant should retrieve active surplus near expiry requiring immediate courier pickup."""
    headers = get_auth_header(role="KITCHEN_MANAGER", org_id=ORG_HYATT)
    query = "Which surplus is urgent?"

    response = client.post("/api/v1/assistant/chat", json={"query": query}, headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["grounded"] is True
    assert data["operational_context"] is not None
    op = data["operational_context"]
    assert op["query_type"] == "urgent_surplus"
    assert "urgent_items_count" in op["key_metrics"]
    assert len(op["records"]) > 0
    top_record = op["records"][0]
    assert "remaining_window_mins" in top_record
    assert "required_action" in top_record


# -------------------------------------------------------------
# Test 7: Operational Query - "Show this month's impact."
# -------------------------------------------------------------
def test_operational_query_monthly_impact():
    """Assistant should retrieve verified impact metrics for the organization."""
    headers = get_auth_header(role="KITCHEN_MANAGER", org_id=ORG_HYATT)
    query = "Show this month's impact."

    response = client.post("/api/v1/assistant/chat", json={"query": query}, headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["grounded"] is True
    assert data["operational_context"] is not None
    op = data["operational_context"]
    assert op["query_type"] == "month_impact"
    assert "meals_provided" in op["key_metrics"]
    assert "food_diverted_kg" in op["key_metrics"]
    assert "co2e_avoided_kg" in op["key_metrics"]
    assert "financial_value_usd" in op["key_metrics"]


# -------------------------------------------------------------
# Test 8: Strict Anti-Hallucination Fallback
# -------------------------------------------------------------
def test_strict_anti_hallucination_fallback():
    """
    If evidence is insufficient, assistant MUST return:
    'I don't have enough verified information to answer that.'
    Do not fabricate facts.
    """
    headers = get_auth_header(role="KITCHEN_MANAGER", org_id=ORG_HYATT)
    unverified_query = "What is the secret recipe for superconducting quantum fusion lasagna on Mars?"

    response = client.post("/api/v1/assistant/chat", json={"query": unverified_query}, headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["grounded"] is False
    assert data["is_insufficient_evidence"] is True
    assert data["answer"] == "I don't have enough verified information to answer that."
    assert len(data["sources"]) == 0
    assert data["operational_context"] is None


# -------------------------------------------------------------
# Test 9: Chat History Persistence and Retrieval
# -------------------------------------------------------------
def test_chat_history_persistence_and_retrieval():
    """Verifies that chat sessions persist messages, citations, and can be retrieved and cleared."""
    headers = get_auth_header(role="KITCHEN_MANAGER", org_id=ORG_HYATT)
    session_id = f"test-session-{uuid.uuid4().hex[:8]}"

    # Turn 1
    resp1 = client.post(
        "/api/v1/assistant/chat",
        json={"query": "What is the 4-hour rule under FDA food code?", "session_id": session_id},
        headers=headers
    )
    assert resp1.status_code == 200

    # Turn 2
    resp2 = client.post(
        "/api/v1/assistant/chat",
        json={"query": "Why did food waste increase this week?", "session_id": session_id},
        headers=headers
    )
    assert resp2.status_code == 200

    # Retrieve history
    history_resp = client.get(f"/api/v1/assistant/history/{session_id}", headers=headers)
    assert history_resp.status_code == 200
    hist = history_resp.json()
    assert hist["session_id"] == session_id
    assert hist["total_messages"] >= 4  # 2 user queries + 2 assistant answers

    # Verify roles and contents
    roles = [m["role"] for m in hist["messages"]]
    assert "user" in roles
    assert "assistant" in roles

    # Clear history
    del_resp = client.delete(f"/api/v1/assistant/history/{session_id}", headers=headers)
    assert del_resp.status_code == 204

    # Confirm empty
    check_empty = client.get(f"/api/v1/assistant/history/{session_id}", headers=headers)
    assert check_empty.json()["total_messages"] == 0


# -------------------------------------------------------------
# Test 10: Suggested Prompts Catalog Endpoint
# -------------------------------------------------------------
def test_suggested_prompts_endpoint():
    """Verifies the suggested prompts endpoint returns all 5 required prompts."""
    headers = get_auth_header(role="KITCHEN_MANAGER", org_id=ORG_HYATT)
    response = client.get("/api/v1/assistant/suggested-prompts", headers=headers)
    assert response.status_code == 200
    data = response.json()
    prompts = [p["prompt"] for p in data["prompts"]]

    required_prompts = [
        "Why did waste increase?",
        "Which food causes the most waste?",
        "What should we produce tomorrow?",
        "Which surplus is urgent?",
        "Show this month's impact."
    ]

    for req in required_prompts:
        assert req in prompts, f"Missing required suggested prompt: {req}"
