"""
FoodLoop AI - Forecasting Inference Engine
Loads the trained champion model, constructs inference features,
and delivers calibrated demand predictions with prediction intervals.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List, Tuple

from .data import get_season, is_institutional_holiday
from .features import FEATURE_COLUMNS


MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models", "forecasting"))
REGISTRY_PATH = os.path.join(MODEL_DIR, "model_registry.json")
CHAMPION_MODEL_PATH = os.path.join(MODEL_DIR, "champion_demand_model.joblib")


class ForecastInferenceEngine:
    """
    Production inference engine for AI demand forecasting.
    Handles artifact loading, feature vector construction, confidence bounds,
    and transparent baseline fallbacks if historical observations are limited.
    """
    def __init__(self):
        self.model = None
        self.registry = None
        self._load_artifacts()

    def _load_artifacts(self):
        """Loads serialized model and registry metadata."""
        if os.path.exists(CHAMPION_MODEL_PATH) and os.path.exists(REGISTRY_PATH):
            try:
                self.model = joblib.load(CHAMPION_MODEL_PATH)
                with open(REGISTRY_PATH, "r") as f:
                    self.registry = json.load(f)
                return
            except Exception as e:
                print(f"[FoodLoop Forecast] Warning loading saved artifact: {e}")

        # If artifacts are missing, trigger training pipeline
        from .train import train_forecasting_pipeline
        print("[FoodLoop Forecast] Artifacts not found. Initializing training pipeline...")
        self.registry = train_forecasting_pipeline()
        self.model = joblib.load(CHAMPION_MODEL_PATH)

    def predict_demand(
        self,
        target_date: Optional[str] = None,
        planned_attendance: Optional[int] = None,
        historical_consumption: Optional[List[float]] = None,
        day_of_week: Optional[int] = None,
        meal_type: str = "LUNCH_DINNER_COMBO",
        is_special_event: int = 0,
        temperature_c: float = 21.0,
        precipitation_mm: float = 0.0,
        kitchen_id: Optional[str] = None,
        menu_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes ML demand forecast.
        Returns:
        - expected_demand
        - recommended_range (lower, upper)
        - confidence
        - model_version
        """
        # Ensure artifacts are loaded
        if self.model is None or self.registry is None:
            self._load_artifacts()

        # Parse date
        if target_date:
            try:
                target_dt = datetime.strptime(target_date, "%Y-%m-%d").date()
            except ValueError:
                target_dt = date.today() + timedelta(days=1)
        else:
            target_dt = date.today() + timedelta(days=1)

        dow = target_dt.weekday() if day_of_week is None else day_of_week
        month = target_dt.month
        season = get_season(month)
        holiday = is_institutional_holiday(target_dt)

        # 1. Handle Transparent Baseline if insufficient historical consumption is provided
        is_insufficient = (
            (historical_consumption is not None and len(historical_consumption) < 4)
            or (historical_consumption == [])
        )

        if is_insufficient:
            base_val = int(np.mean(historical_consumption)) if (historical_consumption and len(historical_consumption) > 0) else (planned_attendance or 1400)
            return {
                "expected_demand": base_val,
                "recommended_range": {
                    "lower": int(round(base_val * 0.90)),
                    "upper": int(round(base_val * 1.10))
                },
                "confidence": 0.65,
                "model_version": "baseline-transparent-v1",
                "recommended_production": int(round(base_val * 1.05)),
                "buffer_portions": int(round(base_val * 0.05)),
                "is_baseline": True,
                "baseline_explanation": (
                    "Insufficient historical observations (< 4 days recorded). "
                    "Serving a transparent moving average baseline while the AI model gathers operational dining telemetry."
                ),
                "target_date": target_dt.strftime("%Y-%m-%d"),
                "day_name": target_dt.strftime("%A"),
                "season": season,
                "kitchen_id": kitchen_id,
                "features_summary": {
                    "day_of_week": dow,
                    "planned_attendance": planned_attendance or base_val,
                    "is_special_event": is_special_event,
                    "is_holiday": holiday,
                    "weather_temp_c": temperature_c
                }
            }

        # 2. Extract or approximate historical lag inputs
        if historical_consumption and len(historical_consumption) >= 7:
            lag_1 = float(historical_consumption[-1])
            lag_2 = float(historical_consumption[-2]) if len(historical_consumption) > 1 else lag_1
            lag_3 = float(historical_consumption[-3]) if len(historical_consumption) > 2 else lag_2
            lag_7 = float(historical_consumption[-7]) if len(historical_consumption) >= 7 else lag_1
            lag_14 = float(historical_consumption[-14]) if len(historical_consumption) >= 14 else lag_7
            rolling_7 = float(np.mean(historical_consumption[-7:]))
            rolling_std_7 = float(np.std(historical_consumption[-7:]))
            rolling_14 = float(np.mean(historical_consumption[-14:])) if len(historical_consumption) >= 14 else rolling_7
            rolling_30 = float(np.mean(historical_consumption[-30:])) if len(historical_consumption) >= 30 else rolling_14
        else:
            # Default institutional priors
            base = planned_attendance or 1650
            lag_1 = base * (0.95 if dow == 0 else 1.02)
            lag_2 = base * 0.98
            lag_3 = base * 0.99
            lag_7 = base * (0.60 if dow >= 5 else 1.08)
            lag_14 = lag_7
            rolling_7 = base * 0.96
            rolling_std_7 = 48.0
            rolling_14 = base * 0.95
            rolling_30 = base * 0.94

        attendance = planned_attendance or int(rolling_7 * (1.25 if is_special_event else 1.0))
        prev_prod = int(lag_1 * 1.06)
        prev_waste = round(max(8.0, (prev_prod - lag_1) * 0.35), 1)

        # Normalize meal & menu strings
        m_type = (meal_type or "LUNCH_DINNER_COMBO").upper()
        menu_str = (menu_name or "STANDARD_BUFFET").upper()

        # 3. Construct single-row feature DataFrame
        feat_dict = {
            "day_of_week": dow,
            "day_of_month": target_dt.day,
            "month": month,
            "quarter": (month - 1) // 3 + 1,
            "is_weekend": int(dow >= 5),
            "is_holiday": holiday,
            "is_special_event": is_special_event,
            "sin_dow": np.sin(2 * np.pi * dow / 7.0),
            "cos_dow": np.cos(2 * np.pi * dow / 7.0),
            "sin_month": np.sin(2 * np.pi * (month - 1) / 12.0),
            "cos_month": np.cos(2 * np.pi * (month - 1) / 12.0),
            "planned_attendance": attendance,
            "prev_production_portions": prev_prod,
            "prev_waste_kg": prev_waste,
            "temperature_c": temperature_c,
            "precipitation_mm": precipitation_mm,
            "season_Fall": int(season == "Fall"),
            "season_Spring": int(season == "Spring"),
            "season_Summer": int(season == "Summer"),
            "season_Winter": int(season == "Winter"),
            "meal_BREAKFAST": int("BREAKFAST" in m_type),
            "meal_LUNCH": int("LUNCH" in m_type and "COMBO" not in m_type),
            "meal_DINNER": int("DINNER" in m_type and "COMBO" not in m_type),
            "meal_BANQUET": int("BANQUET" in m_type),
            "meal_COMBO": int("COMBO" in m_type),
            "menu_COMFORT": int("COMFORT" in menu_str),
            "menu_HEALTH": int("HEALTH" in menu_str),
            "menu_SPECIALTY": int("SPECIALTY" in menu_str),
            "menu_STANDARD": int("STANDARD" in menu_str or not any(k in menu_str for k in ["COMFORT", "HEALTH", "SPECIALTY"])),
            "lag_1_demand": lag_1,
            "lag_2_demand": lag_2,
            "lag_3_demand": lag_3,
            "lag_7_demand": lag_7,
            "lag_14_demand": lag_14,
            "rolling_mean_7": rolling_7,
            "rolling_std_7": rolling_std_7,
            "rolling_mean_14": rolling_14,
            "rolling_mean_30": rolling_30,
            "rolling_ratio_7_30": round(rolling_7 / (rolling_30 + 1e-5), 4)
        }

        X_df = pd.DataFrame([feat_dict])[FEATURE_COLUMNS]

        # 4. Model Prediction with Prediction Bounds
        if hasattr(self.model, "predict_with_bounds"):
            preds, lowers, uppers, conf = self.model.predict_with_bounds(X_df)
            exp_demand = int(round(preds[0]))
            lower_bound = int(round(lowers[0]))
            upper_bound = int(round(uppers[0]))
            confidence = conf
        else:
            preds = self.model.predict(X_df)
            exp_demand = int(round(preds[0]))
            std_err = getattr(self.model, "residual_std_", 40.0)
            lower_bound = max(0, int(round(exp_demand - 1.645 * std_err)))
            upper_bound = int(round(exp_demand + 1.645 * std_err))
            confidence = 0.88

        # Production safety recommendation (expected demand + buffer based on confidence)
        buffer_portions = int(round((1.0 - confidence) * 0.5 * exp_demand))
        recommended_production = exp_demand + max(20, min(80, buffer_portions))

        model_version = self.registry.get("model_version", "xgb-v3") if self.registry else "xgb-v3"

        return {
            "expected_demand": exp_demand,
            "recommended_range": {
                "lower": lower_bound,
                "upper": upper_bound
            },
            "confidence": confidence,
            "model_version": model_version,
            "recommended_production": recommended_production,
            "buffer_portions": recommended_production - exp_demand,
            "is_baseline": False,
            "target_date": target_dt.strftime("%Y-%m-%d"),
            "day_name": target_dt.strftime("%A"),
            "season": season,
            "kitchen_id": kitchen_id,
            "features_summary": {
                "day_of_week": dow,
                "planned_attendance": attendance,
                "is_special_event": is_special_event,
                "is_holiday": holiday,
                "weather_temp_c": temperature_c
            }
        }

    def get_model_leaderboard(self) -> List[Dict[str, Any]]:
        """Retrieves comparative performance leaderboard across all 4 models."""
        if not self.registry:
            self._load_artifacts()
        return self.registry.get("leaderboard", [])

    def get_historical_evaluations(self) -> List[Dict[str, Any]]:
        """Retrieves out-of-sample predicted vs actual sequence for charting."""
        if not self.registry:
            self._load_artifacts()
        return self.registry.get("test_evaluations", [])


# Singleton instance
forecast_engine = ForecastInferenceEngine()
