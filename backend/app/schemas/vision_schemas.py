"""
FoodLoop AI - Computer Vision Schemas (Phase 13)
Defines request and response contracts for image preprocessing, food category detection,
confidence scoring, human-in-the-loop corrections, and waste/surplus dispatching.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

VALID_FOOD_CATEGORIES = [
    "Rice",
    "Dal",
    "Vegetables",
    "Chapati",
    "Bread",
    "Fruit",
    "Dessert",
    "Other"
]

WEIGHT_DISCLAIMER = (
    "Computer Vision Notice: Monocular standard RGB imaging cannot determine true volumetric mass or food density. "
    "Certified kitchen digital scales must be used for final weight validation before recording financial or environmental impact."
)

MODEL_LABEL = "FoodLoop Vision v1.0-alpha (Controlled Reference Calibration)"


class DetectedBoundingBox(BaseModel):
    x: float = Field(..., description="Normalized bounding box top-left X (0.0 to 1.0)")
    y: float = Field(..., description="Normalized bounding box top-left Y (0.0 to 1.0)")
    width: float = Field(..., description="Normalized width (0.0 to 1.0)")
    height: float = Field(..., description="Normalized height (0.0 to 1.0)")
    label: str = Field(..., description="Detected category label")
    confidence: float = Field(..., description="Detection confidence 0.0 - 1.0")


class CategoryCandidate(BaseModel):
    category: str
    confidence: float
    description: Optional[str] = None


class FoodClassificationRequest(BaseModel):
    image_base64: Optional[str] = Field(None, description="Base64-encoded image string (PNG, JPEG, WebP)")
    sample_id: Optional[str] = Field(None, description="Optional sample image identifier for testing")
    kitchen_id: Optional[str] = Field(None, description="Originating kitchen ID")
    organization_id: Optional[str] = Field(None, description="Organization ID")


class FoodClassificationResponse(BaseModel):
    scan_id: str
    prediction: str
    confidence: float
    confidence_tier: str  # HIGH (>=0.85), MODERATE (0.65-0.84), LOW (<0.65)
    requires_manual_confirmation: bool
    bounding_box: Optional[DetectedBoundingBox] = None
    top_candidates: List[CategoryCandidate] = Field(default_factory=list)
    model_architecture: str = MODEL_LABEL
    dataset_info: str = "Prototype Controlled Reference Dataset (8 core culinary categories)"
    disclaimer: str = WEIGHT_DISCLAIMER
    preprocessing_metadata: Dict[str, Any] = Field(default_factory=dict)
    image_preview_url: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class VisionConfirmRequest(BaseModel):
    scan_id: str
    confirmed_label: str = Field(..., description="Worker confirmed or corrected food category")
    action: Optional[str] = Field("CONFIRM_ONLY", description="Action: CONFIRM_ONLY, LOG_WASTE, DECLARE_SURPLUS")
    weight_kg: Optional[float] = Field(None, ge=0.0, description="Manual verified weight from physical scale")
    notes: Optional[str] = Field(None, description="Operator notes or kitchen station comments")
    destination_kitchen_id: Optional[str] = None


class VisionConfirmResponse(BaseModel):
    scan_id: str
    is_confirmed: bool
    original_prediction: str
    final_label: str
    was_corrected: bool
    confidence: float
    created_record_type: Optional[str] = None
    created_record_id: Optional[str] = None
    confirmed_at: datetime
    message: str


class VisionScanHistoryItem(BaseModel):
    id: str
    prediction: str
    confidence: float
    confidence_tier: str
    is_confirmed: bool
    corrected_label: Optional[str] = None
    created_record_type: Optional[str] = None
    created_record_id: Optional[str] = None
    created_at: datetime
    confirmed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VisionBenchmarkResponse(BaseModel):
    model_name: str
    version: str
    dataset_type: str
    total_eval_samples: int
    overall_accuracy: float
    macro_f1_score: float
    average_latency_ms: float
    categories: List[str]
    per_class_metrics: Dict[str, Dict[str, float]]
    disclaimer: str
