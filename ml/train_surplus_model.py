"""
FoodLoop AI - ML Surplus & Risk Model Training Pipeline
Trains Scikit-Learn & XGBoost models to forecast food surplus volume (kg)
and evaluate spoilage risk severity.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import xgboost as xgb

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from dataset_generator import generate_surplus_dataset


def train_models():
    os.makedirs("models", exist_ok=True)
    print("[*] Generating synthetic food surplus training dataset (5,000 samples)...")
    df = generate_surplus_dataset(n_samples=5000, random_seed=42)

    # Features and Targets
    feature_cols = [
        "business_type", "category", "day_of_week", "is_weekend",
        "temp_c", "rainfall_mm", "is_rainy", "event_nearby",
        "planned_covers", "prepared_volume_kg"
    ]
    categorical_cols = ["business_type", "category"]
    numeric_cols = [
        "day_of_week", "is_weekend", "temp_c", "rainfall_mm",
        "is_rainy", "event_nearby", "planned_covers", "prepared_volume_kg"
    ]

    X = df[feature_cols]
    y_surplus = df["surplus_kg"]
    y_risk = df["spoilage_risk_score"]

    X_train, X_test, y_s_train, y_s_test, y_r_train, y_r_test = train_test_split(
        X, y_surplus, y_risk, test_size=0.2, random_state=42
    )

    # Preprocessor
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_cols),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_cols)
        ]
    )

    # 1. Train Surplus Regressor (XGBoost)
    print("[*] Training XGBoost Surplus Volume Regressor...")
    surplus_pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("regressor", xgb.XGBRegressor(
            n_estimators=150,
            learning_rate=0.08,
            max_depth=5,
            subsample=0.85,
            colsample_bytree=0.85,
            random_state=42
        ))
    ])
    surplus_pipeline.fit(X_train, y_s_train)

    y_s_pred = surplus_pipeline.predict(X_test)
    rmse = float(np.sqrt(mean_squared_error(y_s_test, y_s_pred)))
    mae = float(mean_absolute_error(y_s_test, y_s_pred))
    r2 = float(r2_score(y_s_test, y_s_pred))

    print(f"[OK] Surplus Regressor -> RMSE: {rmse:.3f} kg | MAE: {mae:.3f} kg | R2: {r2:.3f}")

    # 2. Train Spoilage Risk Regressor
    print("[*] Training Spoilage Risk Regressor...")
    risk_pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("regressor", xgb.XGBRegressor(
            n_estimators=100,
            learning_rate=0.05,
            max_depth=4,
            random_state=42
        ))
    ])
    risk_pipeline.fit(X_train, y_r_train)

    y_r_pred = risk_pipeline.predict(X_test)
    risk_mae = float(mean_absolute_error(y_r_test, y_r_pred))
    print(f"[OK] Spoilage Risk Model -> MAE: {risk_mae:.4f}")

    # Save artifacts
    model_path = os.path.join("models", "surplus_predictor.joblib")
    risk_path = os.path.join("models", "spoilage_risk.joblib")
    joblib.dump(surplus_pipeline, model_path)
    joblib.dump(risk_pipeline, risk_path)

    metadata = {
        "surplus_model": {
            "algorithm": "XGBoost Regressor",
            "rmse_kg": round(rmse, 3),
            "mae_kg": round(mae, 3),
            "r2_score": round(r2, 3),
            "features": feature_cols
        },
        "risk_model": {
            "algorithm": "XGBoost Regressor",
            "mae": round(risk_mae, 4)
        },
        "training_samples": len(df)
    }

    with open(os.path.join("models", "metrics.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    print("[SUCCESS] Saved ML artifacts to models/ directory successfully!")
    return metadata


if __name__ == "__main__":
    train_models()
