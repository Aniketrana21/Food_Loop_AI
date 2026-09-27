"""
FoodLoop AI - Phase 5 Demand Forecasting Test Suite
Validates baseline models, XGBoost champion, feature engineering with strict leakage prevention,
time-based validation, model registry metadata, and FastAPI endpoints.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import date, timedelta
from fastapi.testclient import TestClient

from backend.app.main import app
from ml.forecasting.data import (
    generate_synthetic_institutional_timeseries,
    get_season,
    is_institutional_holiday
)
from ml.forecasting.features import (
    build_forecasting_features,
    FEATURE_COLUMNS,
    TARGET_COLUMN
)
from ml.forecasting.model import (
    NaiveBaselineModel,
    MovingAverageModel,
    RandomForestForecastModel,
    XGBoostForecastModel
)
from ml.forecasting.evaluate import (
    calculate_metrics,
    temporal_train_test_split,
    compare_models,
    walk_forward_cv_validation
)
from ml.forecasting.predict import forecast_engine

client = TestClient(app)


# =====================================================================
# 1. DATA PIPELINE & TEMPORAL INTEGRITY TESTS
# =====================================================================

def test_synthetic_data_generation():
    df = generate_synthetic_institutional_timeseries(num_days=60)
    assert len(df) == 60
    assert "date" in df.columns
    assert "actual_demand" in df.columns
    assert "planned_attendance" in df.columns
    assert "meal_type" in df.columns
    assert "menu_type" in df.columns
    assert (df["actual_demand"] > 0).all()
    # Verify strict ascending chronological ordering
    assert df["date"].is_monotonic_increasing


def test_calendar_and_holiday_logic():
    # Winter month
    assert get_season(1) == "Winter"
    # Summer month
    assert get_season(7) == "Summer"
    # July 4 holiday
    assert is_institutional_holiday(date(2025, 7, 4)) == 1
    # Random non-holiday date
    assert is_institutional_holiday(date(2025, 3, 11)) == 0


# =====================================================================
# 2. FEATURE ENGINEERING & LEAKAGE PREVENTION TESTS
# =====================================================================

def test_feature_engineering_data_leakage_prevention():
    raw_df = generate_synthetic_institutional_timeseries(num_days=90)
    featured = build_forecasting_features(raw_df, is_training=True)

    # 1. Ensure all expected columns are present
    for col in FEATURE_COLUMNS:
        assert col in featured.columns, f"Missing feature column: {col}"

    # 2. Verify lag_1_demand is strictly shifted by 1 relative to actual_demand
    # Row i's lag_1_demand must equal raw_df's actual_demand from previous timestamp
    raw_dates_to_demand = dict(zip(raw_df["date"], raw_df["actual_demand"]))
    for i in range(1, len(featured)):
        row_date = featured.iloc[i]["date"]
        prev_date = row_date - timedelta(days=1)
        if prev_date in raw_dates_to_demand:
            expected_lag_1 = raw_dates_to_demand[prev_date]
            actual_lag_1 = featured.iloc[i]["lag_1_demand"]
            assert actual_lag_1 == expected_lag_1, f"Data leakage in lag_1: expected {expected_lag_1}, got {actual_lag_1}"

    # 3. Cyclical sine and cosine bounds check
    assert (featured["sin_dow"] >= -1.0).all() and (featured["sin_dow"] <= 1.0).all()
    assert (featured["cos_dow"] >= -1.0).all() and (featured["cos_dow"] <= 1.0).all()


# =====================================================================
# 3. TIME-BASED VALIDATION & METRICS TESTS
# =====================================================================

def test_temporal_train_test_split():
    raw_df = generate_synthetic_institutional_timeseries(num_days=100)
    train_df, val_df, test_df = temporal_train_test_split(raw_df, train_ratio=0.70, val_ratio=0.15)

    assert len(train_df) == 70
    assert len(val_df) == 15
    assert len(test_df) == 15

    # Strict chronological causality: max(train) < min(val) < min(test)
    assert train_df["date"].max() < val_df["date"].min()
    assert val_df["date"].max() < test_df["date"].min()


def test_calculate_metrics():
    y_true = np.array([1000.0, 1500.0, 2000.0])
    y_pred = np.array([1050.0, 1450.0, 2020.0])

    metrics = calculate_metrics(y_true, y_pred)
    assert "mae" in metrics
    assert "rmse" in metrics
    assert "mape_pct" in metrics
    assert "r2_score" in metrics
    assert metrics["mae"] == 40.0
    assert metrics["mape_pct"] > 0.0


# =====================================================================
# 4. BASELINE AND ML MODELS COMPARISON TESTS
# =====================================================================

def test_all_four_models_fit_and_compare():
    raw_df = generate_synthetic_institutional_timeseries(num_days=120)
    featured = build_forecasting_features(raw_df, is_training=True)
    train_df, val_df, test_df = temporal_train_test_split(featured, 0.70, 0.15)

    X_train, y_train = train_df[FEATURE_COLUMNS], train_df[TARGET_COLUMN]
    X_test, y_test = test_df[FEATURE_COLUMNS], test_df[TARGET_COLUMN]

    models = {
        "naive_baseline": NaiveBaselineModel(),
        "moving_average_7d": MovingAverageModel(),
        "random_forest": RandomForestForecastModel(n_estimators=30, max_depth=6, random_state=42),
        "xgboost": XGBoostForecastModel(n_estimators=30, max_depth=4, random_state=42)
    }

    for model in models.values():
        model.fit(X_train, y_train)

    comparison = compare_models(models, X_test, y_test)
    leaderboard = comparison["leaderboard"]

    assert len(leaderboard) == 4
    model_names = [m["model"] for m in leaderboard]
    assert "xgboost" in model_names
    assert "random_forest" in model_names
    assert "naive_baseline" in model_names
    assert "moving_average_7d" in model_names

    # Check champion model has lowest MAE
    assert leaderboard[0]["mae"] <= leaderboard[-1]["mae"]


# =====================================================================
# 5. INFERENCE & TRANSPARENT BASELINE TESTS
# =====================================================================

def test_ml_demand_forecast_inference():
    res = forecast_engine.predict_demand(
        planned_attendance=1850,
        historical_consumption=[1750, 1800, 1820, 1790, 1840, 1810, 1835],
        day_of_week=2,
        meal_type="LUNCH",
        menu_name="COMFORT_FOOD",
        temperature_c=20.0
    )

    assert "expected_demand" in res
    assert "recommended_range" in res
    assert "lower" in res["recommended_range"]
    assert "upper" in res["recommended_range"]
    assert "confidence" in res
    assert "model_version" in res
    assert "recommended_production" in res
    assert res["is_baseline"] is False
    assert res["recommended_range"]["lower"] <= res["expected_demand"] <= res["recommended_range"]["upper"]
    assert res["confidence"] > 0.70


def test_transparent_baseline_when_insufficient_data():
    # Only 2 historical data points provided (< 4 threshold)
    res = forecast_engine.predict_demand(
        planned_attendance=1400,
        historical_consumption=[1380, 1420]
    )

    assert res["is_baseline"] is True
    assert res["model_version"] == "baseline-transparent-v1"
    assert "Insufficient historical observations" in res["baseline_explanation"]
    assert res["confidence"] == 0.65  # Transparent, non-inflated confidence
    assert res["expected_demand"] == 1400


# =====================================================================
# 6. FASTAPI ENDPOINT INTEGRATION TESTS
# =====================================================================

def test_api_post_forecast_endpoint():
    payload = {
        "planned_attendance": 1840,
        "historical_consumption": [1780, 1810, 1795, 1830, 1820, 1805, 1840],
        "day_of_week": 1,
        "meal_type": "LUNCH",
        "menu_name": "COMFORT_FOOD"
    }

    response = client.post("/api/v1/forecast", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Exact required output schema
    assert "expected_demand" in data
    assert "recommended_range" in data
    assert "lower" in data["recommended_range"]
    assert "upper" in data["recommended_range"]
    assert "confidence" in data
    assert "model_version" in data
    assert isinstance(data["expected_demand"], int)
    assert isinstance(data["confidence"], float)


def test_api_get_models_registry_endpoint():
    response = client.get("/api/v1/forecast/models")
    assert response.status_code == 200
    data = response.json()

    assert "model_version" in data
    assert "champion_model_name" in data
    assert "training_date" in data
    assert "dataset_version" in data
    assert "features" in data
    assert "leaderboard" in data
    assert len(data["leaderboard"]) >= 4


def test_api_get_evaluations_endpoint():
    response = client.get("/api/v1/forecast/evaluations")
    assert response.status_code == 200
    data = response.json()

    assert "series" in data
    assert "historical_accuracy" in data
    assert "mae_portions" in data["historical_accuracy"]
    assert "mape_percentage" in data["historical_accuracy"]
    assert "baseline_comparison" in data
