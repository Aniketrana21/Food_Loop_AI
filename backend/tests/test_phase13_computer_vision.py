"""
FoodLoop AI - Phase 13 Test Suite: Computer Vision Food Classification
Automated test suite verifying:
1. 8 Canonical Food Categories: Rice, Dal, Vegetables, Chapati, Bread, Fruit, Dessert, Other.
2. Controlled Reference Calibration & Sample Test Bench.
3. Strict Weight Constraint: RGB image cannot deduce mass/density; scale required.
4. Preprocessing: aspect-ratio fit, format handling, dimension metadata.
5. Confidence Tiering: HIGH (>=0.85), MODERATE (0.65-0.84), LOW (<0.65).
6. Human-in-the-Loop Confirmation & Label Correction.
7. Safety Guardrail: Low-confidence (<0.70) predictions never trigger automated decisions.
8. Operational Conversion: Seamless dispatch to WasteRecord or SurplusItem.
9. Scan Audit Trail: image, prediction, confidence, corrected_label, timestamp.
10. Evaluation Benchmark Report (Macro F1, Accuracy, Latency).
"""
import io
import uuid
import base64
import pytest
from PIL import Image
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal
from app.core.security import create_access_token
from app.models.models import VisionScan, WasteRecord, SurplusItem, Organization, User
from app.schemas.vision_schemas import VALID_FOOD_CATEGORIES
from app.services.vision_service import vision_service, ComputerVisionService

client = TestClient(app)

SEEDED_USERS = {
    "ADMIN": ("11111111-1111-1111-1111-111111111111", "admin@foodloop.ai"),
    "KITCHEN_MANAGER": ("22222222-2222-2222-2222-222222222222", "chef.vance@hyatt-culinary.com"),
}


def get_auth_header(role: str = "KITCHEN_MANAGER") -> dict:
    default_uid, default_email = SEEDED_USERS.get(role, ("22222222-2222-2222-2222-222222222222", "chef@foodloop.test"))
    token = create_access_token(data={
        "sub": default_uid,
        "email": default_email,
        "role": role,
        "org_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    })
    return {"Authorization": f"Bearer {token}"}


def test_vision_sample_catalog():
    """Verify the controlled reference sample images catalog covers all 8 canonical food classes."""
    resp = client.get("/api/v1/vision/sample-images")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data) >= 8
    
    found_categories = set(s["expected_category"] for s in data)
    for cat in VALID_FOOD_CATEGORIES:
        assert cat in found_categories, f"Missing sample for category {cat}"

    for sample in data:
        assert sample["sample_id"].startswith("sample_")
        assert sample["preview_svg"].startswith("data:image/svg+xml;base64,")
        assert 0.0 <= sample["expected_confidence"] <= 1.0


def test_vision_benchmark_report():
    """Verify evaluation benchmark metrics comply with model requirements."""
    resp = client.get("/api/v1/vision/benchmark")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert "FoodLoop Vision" in data["model_name"]
    assert data["overall_accuracy"] >= 0.88
    assert data["macro_f1_score"] >= 0.88
    assert data["average_latency_ms"] < 150
    assert "controlled" in data["dataset_type"].lower()
    assert "scale" in data["disclaimer"].lower()

    # Check per-class evaluation metrics
    for cat in VALID_FOOD_CATEGORIES:
        assert cat in data["per_class_metrics"], f"Missing class metrics for {cat}"
        metrics = data["per_class_metrics"][cat]
        assert metrics["f1"] >= 0.80
        assert metrics["samples"] > 0


def test_classify_sample_rice_high_confidence():
    """Verify classification of sample_rice achieves high confidence and stores audit scan."""
    auth = get_auth_header("KITCHEN_MANAGER")
    payload = {
        "sample_id": "sample_rice",
        "notes": "Testing basmati rice steam tray"
    }
    resp = client.post("/api/v1/vision/classify", json=payload, headers=auth)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["prediction"] == "Rice"
    assert data["confidence"] >= 0.85
    assert data["confidence_tier"] == "HIGH"
    assert data["requires_manual_confirmation"] is False
    assert "digital scale" in data["disclaimer"].lower()

    # Check bounding box
    assert data["bounding_box"] is not None
    assert data["bounding_box"]["label"] == "Rice"
    assert data["bounding_box"]["confidence"] >= 0.85

    # Check candidate breakdown
    assert len(data["top_candidates"]) >= 3
    assert data["top_candidates"][0]["category"] == "Rice"

    # Verify persisted in database
    db = SessionLocal()
    scan = db.query(VisionScan).filter(VisionScan.id == data["scan_id"]).first()
    assert scan is not None
    assert scan.prediction == "Rice"
    assert scan.confidence >= 0.85
    assert scan.is_confirmed is False
    db.close()


def test_classify_sample_dal_high_confidence():
    """Verify classification of yellow tadka dal."""
    auth = get_auth_header("KITCHEN_MANAGER")
    payload = {"sample_id": "sample_dal"}
    resp = client.post("/api/v1/vision/classify", json=payload, headers=auth)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["prediction"] == "Dal"
    assert data["confidence"] >= 0.85


def test_classify_sample_low_confidence_guardrail():
    """Verify low-confidence samples trigger mandatory manual confirmation flag."""
    auth = get_auth_header("KITCHEN_MANAGER")
    payload = {"sample_id": "sample_mixed_low_conf"}
    resp = client.post("/api/v1/vision/classify", json=payload, headers=auth)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["prediction"] == "Other"
    assert data["confidence"] < 0.70
    assert data["confidence_tier"] == "LOW"
    assert data["requires_manual_confirmation"] is True


def test_enforce_low_confidence_guardrail_logic():
    """Verify safety guardrail prevents unverified low-confidence operational execution."""
    db = SessionLocal()
    mock_scan = VisionScan(
        id=str(uuid.uuid4()),
        image_url="data:image/png;base64,mock",
        prediction="Other",
        confidence=0.55,
        confidence_tier="LOW",
        requires_manual_confirmation=True,
        is_confirmed=False,
    )
    db.add(mock_scan)
    db.commit()

    # Calling guardrail when not confirmed raises HTTPException 400
    with pytest.raises(HTTPException) as excinfo:
        vision_service.enforce_low_confidence_guardrail(mock_scan)
    assert excinfo.value.status_code == 400
    assert "Operational Guardrail Violation" in excinfo.value.detail

    # Once confirmed by human, guardrail does not raise
    mock_scan.is_confirmed = True
    vision_service.enforce_low_confidence_guardrail(mock_scan)

    db.delete(mock_scan)
    db.commit()
    db.close()


def test_confirm_with_correction_and_log_waste():
    """Verify human worker can review, correct label, and log record as kitchen waste."""
    auth = get_auth_header("KITCHEN_MANAGER")

    # 1. Classify low-conf sample
    c_resp = client.post("/api/v1/vision/classify", json={"sample_id": "sample_mixed_low_conf"}, headers=auth)
    assert c_resp.status_code == 200
    scan_id = c_resp.json()["scan_id"]
    initial_pred = c_resp.json()["prediction"]
    assert initial_pred == "Other"

    # 2. Worker inspects food: It's actually sauteed Vegetables, weighed on digital scale: 3.8 kg
    confirm_payload = {
        "scan_id": scan_id,
        "confirmed_label": "Vegetables",  # Correction from Other -> Vegetables
        "action": "LOG_WASTE",
        "weight_kg": 3.8,
        "notes": "Worker verified after AI prediction of Other. Certified digital scale reading: 3.8kg."
    }
    cf_resp = client.post("/api/v1/vision/confirm", json=confirm_payload, headers=auth)
    assert cf_resp.status_code == 200, cf_resp.text
    cf_data = cf_resp.json()

    assert cf_data["was_corrected"] is True
    assert cf_data["final_label"] == "Vegetables"
    assert cf_data["original_prediction"] == "Other"
    assert cf_data["created_record_type"] == "WASTE_RECORD"
    assert cf_data["created_record_id"] is not None

    # 3. Verify in database
    db = SessionLocal()
    scan = db.query(VisionScan).filter(VisionScan.id == scan_id).first()
    assert scan is not None
    assert scan.is_confirmed is True
    assert scan.corrected_label == "Vegetables"
    assert scan.created_record_id == cf_data["created_record_id"]

    # Verify WasteRecord row
    waste = db.query(WasteRecord).filter(WasteRecord.id == cf_data["created_record_id"]).first()
    assert waste is not None
    assert "Vegetables" in waste.food_item
    assert waste.weight_kg == 3.8
    db.close()


def test_confirm_without_correction_and_declare_surplus():
    """Verify worker can confirm correct prediction and declare as food surplus."""
    auth = get_auth_header("KITCHEN_MANAGER")

    # 1. Classify chapati sample
    c_resp = client.post("/api/v1/vision/classify", json={"sample_id": "sample_chapati"}, headers=auth)
    assert c_resp.status_code == 200
    scan_id = c_resp.json()["scan_id"]
    assert c_resp.json()["prediction"] == "Chapati"

    # 2. Worker confirms chapati and declares 15.0 kg surplus
    confirm_payload = {
        "scan_id": scan_id,
        "confirmed_label": "Chapati",  # Confirmed without change
        "action": "DECLARE_SURPLUS",
        "weight_kg": 15.0,
        "notes": "Hot fresh chapatis from dinner service"
    }
    cf_resp = client.post("/api/v1/vision/confirm", json=confirm_payload, headers=auth)
    assert cf_resp.status_code == 200, cf_resp.text
    cf_data = cf_resp.json()

    assert cf_data["was_corrected"] is False
    assert cf_data["final_label"] == "Chapati"
    assert cf_data["created_record_type"] == "SURPLUS_ITEM"
    assert cf_data["created_record_id"] is not None

    # 3. Verify in database
    db = SessionLocal()
    surplus = db.query(SurplusItem).filter(SurplusItem.id == cf_data["created_record_id"]).first()
    assert surplus is not None
    assert "Chapati" in surplus.food
    assert surplus.quantity == 15.0
    assert surplus.unit == "kg"
    assert surplus.status == "AVAILABLE"
    db.close()


def test_classify_synthetic_base64_image():
    """Verify preprocessing and classification on custom uploaded base64 image."""
    auth = get_auth_header("KITCHEN_MANAGER")

    # Generate a simple 120x120 test JPEG
    img = Image.new("RGB", (120, 120), color=(220, 180, 40))
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    b64_str = f"data:image/jpeg;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"

    payload = {
        "image_base64": b64_str,
        "notes": "Custom synthetic camera frame test"
    }
    resp = client.post("/api/v1/vision/classify", json=payload, headers=auth)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["prediction"] in VALID_FOOD_CATEGORIES
    assert 0.0 <= data["confidence"] <= 1.0
    assert data["scan_id"] is not None
    assert "preprocessing_metadata" in data
    assert data["preprocessing_metadata"]["original_width"] == 120
    assert data["preprocessing_metadata"]["original_height"] == 120
    assert data["preprocessing_metadata"]["preprocessed_resolution"] == [384, 384]


def test_vision_scan_history():
    """Verify audit log of past vision scans returns required storage fields."""
    auth = get_auth_header("KITCHEN_MANAGER")
    resp = client.get("/api/v1/vision/history?limit=10", headers=auth)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert isinstance(data, list)
    assert len(data) >= 1
    recent = data[0]

    # Required stored fields: image, prediction, confidence, corrected label, timestamp
    assert "id" in recent
    assert "prediction" in recent
    assert "confidence" in recent
    assert "created_at" in recent


def test_reject_invalid_food_category_correction():
    """Verify API rejects labels that do not belong to the 8 canonical categories."""
    auth = get_auth_header("KITCHEN_MANAGER")

    c_resp = client.post("/api/v1/vision/classify", json={"sample_id": "sample_bread"}, headers=auth)
    scan_id = c_resp.json()["scan_id"]

    confirm_payload = {
        "scan_id": scan_id,
        "confirmed_label": "PizzaNapoli",  # Invalid non-canonical category
        "action": "CONFIRM_ONLY"
    }
    resp = client.post("/api/v1/vision/confirm", json=confirm_payload, headers=auth)
    assert resp.status_code == 422 or resp.status_code == 400


def test_weight_disclaimer_strictly_enforced():
    """Verify the system strictly disclaims automated weight inference from standard RGB images."""
    auth = get_auth_header("KITCHEN_MANAGER")
    resp = client.post("/api/v1/vision/classify", json={"sample_id": "sample_fruit"}, headers=auth)
    assert resp.status_code == 200
    data = resp.json()
    assert "weight" in data["disclaimer"].lower()
    assert "digital scale" in data["disclaimer"].lower()
