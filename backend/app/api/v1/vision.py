"""
FoodLoop AI - Computer Vision API Router (Phase 13)
Exposes endpoints for food image preprocessing, classification, confidence tiering,
human-in-the-loop confirmation, label correction, and waste/surplus dispatching.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, status, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.vision_schemas import (
    FoodClassificationRequest,
    FoodClassificationResponse,
    VisionConfirmRequest,
    VisionConfirmResponse,
    VisionScanHistoryItem,
    VisionBenchmarkResponse
)
from app.services.vision_service import vision_service
from app.middleware.rate_limit import RateLimiter

router = APIRouter(prefix="/vision", tags=["24. Computer Vision Food Identification"])


@router.post("/classify", response_model=FoodClassificationResponse, dependencies=[Depends(RateLimiter(times=30, seconds=60))])
def classify_food_image(
    req: FoodClassificationRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Classifies a food image into one of 8 core categories:
    Rice, Dal, Vegetables, Chapati, Bread, Fruit, Dessert, Other.
    
    Returns:
    - Predicted category
    - Confidence score (0.0 to 1.0) and tier (HIGH, MODERATE, LOW)
    - Candidate category probability ranking
    - Bounding box coordinates
    - Disclaimer: RGB imaging cannot determine true food mass without digital scale telemetry.
    """
    org_id = req.organization_id or user.get("organization_id") or user.get("org_id")
    user_id = user.get("id") or user.get("sub")

    return vision_service.classify_food_image(
        db=db,
        image_base64=req.image_base64,
        sample_id=req.sample_id,
        kitchen_id=req.kitchen_id,
        organization_id=org_id,
        user_id=user_id
    )


@router.post("/classify-file", response_model=FoodClassificationResponse)
async def classify_food_file(
    file: UploadFile = File(...),
    kitchen_id: Optional[str] = Form(None),
    organization_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Multipart file upload endpoint for live camera capture or mobile photo submission."""
    import base64
    content = await file.read()
    b64_str = "data:image/jpeg;base64," + base64.b64encode(content).decode("utf-8")
    
    org_id = organization_id or user.get("organization_id") or user.get("org_id")
    user_id = user.get("id") or user.get("sub")

    return vision_service.classify_food_image(
        db=db,
        image_base64=b64_str,
        kitchen_id=kitchen_id,
        organization_id=org_id,
        user_id=user_id
    )


@router.post("/confirm", response_model=VisionConfirmResponse)
def confirm_or_correct_vision_result(
    req: VisionConfirmRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Human-in-the-loop confirmation or label correction.
    - Allows kitchen worker to accept AI prediction or correct it to any of the 8 valid categories.
    - Optionally routes confirmed classification to a WasteRecord or SurplusItem.
    - Enforces safety: low-confidence predictions cannot trigger automatic actions without human approval.
    """
    return vision_service.confirm_or_correct_scan(
        db=db,
        req=req,
        current_user=user
    )


@router.get("/history", response_model=List[VisionScanHistoryItem])
def get_vision_scan_history(
    limit: int = 20,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Lists recent vision scans, original AI predictions, confidence, and human corrections."""
    return vision_service.get_scan_history(db=db, limit=limit)


@router.get("/sample-images")
def get_sample_test_images(
    user: dict = Depends(get_current_user)
):
    """Returns calibrated sample kitchen images for instant testing in the UI."""
    return vision_service.get_sample_images_catalog()


@router.get("/benchmark", response_model=VisionBenchmarkResponse)
def get_model_benchmark_report(
    user: dict = Depends(get_current_user)
):
    """
    Returns prototype model evaluation metrics on the controlled reference dataset:
    Overall accuracy, macro F1, per-category precision/recall, and inference latency.
    """
    return vision_service.get_benchmark_report()
