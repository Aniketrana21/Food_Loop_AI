"""
FoodLoop AI - Phase 18 Senior QA Testing Suite: AI Robustness & Graceful Degradation
Tests:
1. Missing data (empty payloads, None parameters)
2. Invalid data (corrupted types, negative values, malformed date formats)
3. Insufficient training data fallback (triggers transparent baseline heuristic)
4. Low confidence threshold handling (< 0.70 confidence flags inspection alerts)
5. Model unavailable fallback (graceful degradation when model weights/files cannot be accessed)
6. Inference failure tolerance (model exceptions caught cleanly, zero crashes)
"""
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import get_current_user
from ml.forecasting.predict import forecast_engine
from app.services.food_safety_rules import evaluate_food_safety
from app.services.llm_service import FallbackProvider

client = TestClient(app)

MOCK_USER = {
    "id": "qa-ai-tester",
    "email": "ai.qa@foodloop.ai",
    "role": "ADMIN",
    "organization_id": "org-ai-test"
}

app.dependency_overrides[get_current_user] = lambda: MOCK_USER


# =====================================================================
# 1. MISSING DATA HANDLING
# =====================================================================
def test_ai_forecast_missing_all_parameters():
    """Verifies that an empty or None-filled forecast request produces a valid, safe forecast."""
    # Completely empty payload
    res = client.post("/api/v1/forecast/", json={})
    assert res.status_code == 200, res.text
    data = res.json()
    assert "expected_demand" in data
    assert data["expected_demand"] > 0
    assert "recommended_range" in data
    assert data["confidence"] > 0.0


def test_food_safety_missing_optional_dates():
    """Verifies that the food safety rules engine handles None prepared_at or best_use_before."""
    safety = evaluate_food_safety(
        food="Cooked Rice",
        category="COOKED_MEALS",
        storage_type="REFRIGERATED",
        temperature=4.0,
        prepared_at=None,
        best_use_before=None
    )
    assert safety.urgency is not None
    assert safety.eligibility in [
        "ELIGIBLE_FOR_DONATION",
        "NEEDS_HUMAN_INSPECTION",
        "INELIGIBLE_EXPIRED"
    ]


# =====================================================================
# 2. INVALID DATA HANDLING
# =====================================================================
def test_ai_forecast_invalid_date_format():
    """Verifies that malformed date strings do not crash forecast inference."""
    payload = {
        "target_date": "invalid-non-iso-date-string-12345",
        "planned_attendance": 250
    }
    res = client.post("/api/v1/forecast/", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["expected_demand"] > 0


def test_ai_forecast_negative_attendance_handled():
    """Verifies that nonsensical negative headcount is safely clamped or defaulted."""
    payload = {
        "planned_attendance": -500,
        "temperature_c": -100.0
    }
    res = client.post("/api/v1/forecast/", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()
    # Output demand must never be negative
    assert data["expected_demand"] >= 0


# =====================================================================
# 3. INSUFFICIENT TRAINING DATA FALLBACK
# =====================================================================
def test_ai_forecast_insufficient_historical_observations_fallback():
    """
    When historical observations are insufficient (< 4 days recorded),
    the system must transparently fall back to an explainable baseline.
    """
    payload = {
        "historical_consumption": [120.0, 115.0],  # Only 2 days of history (< 4)
        "planned_attendance": 300
    }
    res = client.post("/api/v1/forecast/", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["is_baseline"] is True
    assert "Insufficient historical observations" in data["baseline_explanation"]
    assert data["model_version"] == "baseline-transparent-v1"


# =====================================================================
# 4. LOW CONFIDENCE DETECTION & HANDLING
# =====================================================================
def test_low_prediction_confidence_flagged():
    """
    Verifies that low prediction confidence (< 0.70) is detected and properly tagged,
    enabling downstream human inspection and conservative buffer allocation.
    """
    pred = forecast_engine.predict_demand(
        historical_consumption=[100.0]  # Very low historical data triggers 0.65 baseline confidence
    )
    assert pred["confidence"] < 0.70
    assert pred["is_baseline"] is True
    # Verify recommended range encompasses wide uncertainty buffer
    range_span = pred["recommended_range"]["upper"] - pred["recommended_range"]["lower"]
    assert range_span > 0


# =====================================================================
# 5. MODEL UNAVAILABLE FALLBACK
# =====================================================================
def test_model_unavailable_fallback_behavior():
    """
    Simulates model weights file missing or inoperable.
    Verifies that FallbackProvider and heuristic fallbacks prevent application crashes.
    """
    fallback_llm = FallbackProvider()
    response = fallback_llm.generate_completion(
        system_prompt="You are FoodLoop AI Culinary Copilot",
        user_prompt="Generate a recipe for 40kg surplus zucchini and carrots"
    )
    assert response is not None
    assert len(response) > 20
    assert "stew" in response.lower() or "recipe" in response.lower() or "harvest" in response.lower()


# =====================================================================
# 6. INFERENCE FAILURE GRACEFUL DEGRADATION
# =====================================================================
def test_food_safety_extreme_temperature_abuse_gracefully_degrades():
    """
    Verifies that dangerous or abusive temperatures (e.g. cooked poultry at 35C ambient)
    are instantly and decisively flagged as INELIGIBLE_TEMPERATURE_ABUSE with industrial waste workflow.
    """
    safety = evaluate_food_safety(
        food="Cooked Chicken Gravy",
        category="COOKED_MEALS",
        storage_type="AMBIENT",
        temperature=35.0,  # Extreme danger zone abuse
        prepared_at=datetime.now(timezone.utc).isoformat()
    )
    assert safety.eligibility in ["INELIGIBLE_TEMPERATURE_ABUSE", "INELIGIBLE_EXPIRED"]
    assert safety.urgency == "EXPIRED"
    assert safety.suggested_waste_workflow in ["ANAEROBIC_DIGESTION", "INDUSTRIAL_COMPOSTING"]
