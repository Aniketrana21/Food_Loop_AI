"""
FoodLoop AI - ML Prediction & Inference Pipeline
Provides real-time inference for food surplus volume and spoilage risk,
with graceful fallback if model artifacts are being initialized.
"""

import os
import joblib
import pandas as pd
from typing import Dict, Any, Optional

MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
SURPLUS_MODEL_PATH = os.path.join(MODEL_DIR, "surplus_predictor.joblib")
RISK_MODEL_PATH = os.path.join(MODEL_DIR, "spoilage_risk.joblib")

_surplus_model = None
_risk_model = None


def load_models():
    global _surplus_model, _risk_model
    if _surplus_model is None and os.path.exists(SURPLUS_MODEL_PATH):
        try:
            _surplus_model = joblib.load(SURPLUS_MODEL_PATH)
        except Exception as e:
            print(f"Warning: Failed to load surplus model: {e}")

    if _risk_model is None and os.path.exists(RISK_MODEL_PATH):
        try:
            _risk_model = joblib.load(RISK_MODEL_PATH)
        except Exception as e:
            print(f"Warning: Failed to load risk model: {e}")


def predict_surplus(
    business_type: str,
    category: str,
    day_of_week: int,
    is_weekend: int,
    temp_c: float,
    rainfall_mm: float,
    is_rainy: int,
    event_nearby: int,
    planned_covers: int,
    prepared_volume_kg: float
) -> Dict[str, Any]:
    """
    Predicts expected surplus volume (kg), portions, and spoilage risk score.
    """
    load_models()

    input_df = pd.DataFrame([{
        "business_type": business_type,
        "category": category,
        "day_of_week": day_of_week,
        "is_weekend": is_weekend,
        "temp_c": temp_c,
        "rainfall_mm": rainfall_mm,
        "is_rainy": is_rainy,
        "event_nearby": event_nearby,
        "planned_covers": planned_covers,
        "prepared_volume_kg": prepared_volume_kg
    }])

    # 1. Surplus Prediction
    if _surplus_model is not None:
        predicted_surplus_kg = float(_surplus_model.predict(input_df)[0])
        predicted_surplus_kg = max(0.5, round(predicted_surplus_kg, 2))
    else:
        # Fallback physics-based calculation
        base_rate = 0.10
        if is_weekend:
            base_rate += 0.04
        if is_rainy and business_type in ["restaurant", "bakery"]:
            base_rate += 0.06
        predicted_surplus_kg = round(prepared_volume_kg * base_rate, 2)

    # 2. Risk Prediction
    if _risk_model is not None:
        predicted_risk_score = float(_risk_model.predict(input_df)[0])
        predicted_risk_score = min(1.0, max(0.05, round(predicted_risk_score, 3)))
    else:
        # Fallback risk
        risk = 0.25
        if category in ["cooked_meals", "dairy", "meat_seafood"]:
            risk += 0.35
        if temp_c > 25.0:
            risk += 0.20
        predicted_risk_score = min(1.0, max(0.1, round(risk, 3)))

    portions = int(predicted_surplus_kg * 2.2)  # Average 450g per meal portion

    # Qualitative risk category
    if predicted_risk_score > 0.65:
        risk_tier = "CRITICAL_ATTENTION"
        recommendation = "Rapid dispatch within 2 hours. Prioritize refrigerated courier routing."
    elif predicted_risk_score > 0.40:
        risk_tier = "ELEVATED_RISK"
        recommendation = "Expedited dispatch recommended. Ensure packaging seals are intact."
    else:
        risk_tier = "MANAGEABLE"
        recommendation = "Standard distribution queue. Safe for standard delivery route."

    return {
        "predicted_surplus_kg": predicted_surplus_kg,
        "predicted_portions": portions,
        "spoilage_risk_score": predicted_risk_score,
        "risk_tier": risk_tier,
        "recommendation": recommendation,
        "model_version": "v1.2-xgboost-prod"
    }


if __name__ == "__main__":
    res = predict_surplus(
        business_type="hotel",
        category="cooked_meals",
        day_of_week=5,
        is_weekend=1,
        temp_c=28.5,
        rainfall_mm=0.0,
        is_rainy=0,
        event_nearby=1,
        planned_covers=250,
        prepared_volume_kg=120.0
    )
    print("Inference Result:", res)
