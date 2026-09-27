from fastapi import APIRouter
from app.schemas.schemas import (
    SurplusPredictionRequest, SurplusPredictionResponse,
    ShelfLifeRequest, ShelfLifeResponse
)
from app.services.ml_service import ml_service

router = APIRouter(prefix="/ml", tags=["Machine Learning Inference"])


@router.post("/predict-surplus", response_model=SurplusPredictionResponse)
def predict_food_surplus(payload: SurplusPredictionRequest):
    """
    Predicts expected surplus food volume (kg), portions, and spoilage risk
    using the trained XGBoost model.
    """
    result = ml_service.forecast_surplus(payload.model_dump())
    return result


@router.post("/shelf-life", response_model=ShelfLifeResponse)
def estimate_food_shelf_life(payload: ShelfLifeRequest):
    """
    Calculates thermodynamic spoilage curves & remaining safe consumption hours
    based on FDA Food Code danger zone standards and packaging barriers.
    """
    result = ml_service.estimate_shelf_life(payload.model_dump())
    return result
