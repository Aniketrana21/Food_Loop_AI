"""
FoodLoop AI - Pre-Production Waste Prediction Training Pipeline
Trains, evaluates, and registers Logistic Regression, Random Forest, and XGBoost models
with out-of-sample temporal validation.
"""

import os
import json
import joblib
from datetime import datetime
import numpy as np
import pandas as pd
from typing import Dict, Any

from sklearn.metrics import (
    accuracy_score,
    roc_auc_score,
    f1_score,
    precision_score,
    recall_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

from .data import load_waste_prediction_dataset
from .features import (
    build_waste_prediction_features,
    extract_features_and_targets,
    FEATURE_COLUMNS,
    CLASSIFICATION_TARGET,
    REGRESSION_TARGET
)
from .models import WasteModelSuite


MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models", "waste_prediction"))
REGISTRY_PATH = os.path.join(MODEL_DIR, "waste_model_registry.json")
CHAMPION_CLF_PATH = os.path.join(MODEL_DIR, "champion_waste_classifier.joblib")
CHAMPION_REG_PATH = os.path.join(MODEL_DIR, "champion_waste_regressor.joblib")


def evaluate_classifiers(
    classifiers: Dict[str, Any],
    X_test: pd.DataFrame,
    y_test: pd.Series
) -> Dict[str, Any]:
    """Computes Accuracy, ROC-AUC, Precision, Recall, and F1 on out-of-sample test data."""
    results = {}
    for name, clf in classifiers.items():
        preds = clf.predict(X_test)
        probs = clf.predict_proba(X_test)[:, 1] if hasattr(clf, "predict_proba") else preds

        acc = float(accuracy_score(y_test, preds))
        auc = float(roc_auc_score(y_test, probs))
        prec = float(precision_score(y_test, preds, zero_division=0))
        rec = float(recall_score(y_test, preds, zero_division=0))
        f1 = float(f1_score(y_test, preds, zero_division=0))

        results[name] = {
            "accuracy": round(acc, 4),
            "roc_auc": round(auc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4)
        }
    return results


def evaluate_regressors(
    regressors: Dict[str, Any],
    X_test: pd.DataFrame,
    y_test: pd.Series
) -> Dict[str, Any]:
    """Computes MAE, RMSE, and R2 on out-of-sample test data."""
    results = {}
    for name, reg in regressors.items():
        preds = reg.predict(X_test)
        preds = np.maximum(0.0, preds)

        mae = float(mean_absolute_error(y_test, preds))
        rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
        r2 = float(r2_score(y_test, preds))

        mask = y_test > 0
        mape = float(np.mean(np.abs((y_test[mask] - preds[mask]) / y_test[mask])) * 100.0) if np.any(mask) else 0.0

        results[name] = {
            "mae_kg": round(mae, 2),
            "rmse_kg": round(rmse, 2),
            "mape_pct": round(mape, 2),
            "r2_score": round(r2, 4)
        }
    return results


def train_waste_pipeline(
    data_path: str = None,
    model_version: str = "waste-xgb-v1"
) -> Dict[str, Any]:
    """
    Executes chronological training and evaluation pipeline for pre-production food waste prediction:
    1. Loads pre-production batch records.
    2. Builds non-leaking operational features.
    3. Chronological 70% Train, 15% Validation, 15% Holdout test split.
    4. Trains Logistic Regression, Random Forest, and XGBoost (Classification + Quantity Regression).
    5. Saves serialized champion models and persists model registry metadata.
    """
    os.makedirs(MODEL_DIR, exist_ok=True)
    print(f"[FoodLoop Waste ML] Commencing Pre-Production Waste Prediction Pipeline ({model_version})...")

    # 1. Load data
    raw_df = load_waste_prediction_dataset(data_path)
    print(f"[FoodLoop Waste ML] Loaded {len(raw_df)} pre-production records spanning {raw_df['date'].min().date()} to {raw_df['date'].max().date()}")

    # 2. Extract features and targets
    X, y_clf, y_reg, feature_cols = extract_features_and_targets(raw_df)

    # 3. Chronological Train / Val / Test Split
    n = len(X)
    train_end = int(n * 0.70)
    val_end = int(n * 0.85)

    X_train, y_train_clf, y_train_reg = X.iloc[:train_end], y_clf.iloc[:train_end], y_reg.iloc[:train_end]
    X_val, y_val_clf, y_val_reg = X.iloc[train_end:val_end], y_clf.iloc[train_end:val_end], y_reg.iloc[train_end:val_end]
    X_test, y_test_clf, y_test_reg = X.iloc[val_end:], y_clf.iloc[val_end:], y_reg.iloc[val_end:]

    print(f"[FoodLoop Waste ML] Chronological Split: Train={len(X_train)}, Val={len(X_val)}, Test={len(X_test)}")

    # 4. Instantiate & Train Model Suite
    suite = WasteModelSuite(random_state=42)
    suite.fit_all(X_train, y_train_clf, y_train_reg)

    # 5. Evaluate Classifiers & Regressors
    clf_metrics = evaluate_classifiers(suite.classifiers, X_test, y_test_clf)
    reg_metrics = evaluate_regressors(suite.regressors, X_test, y_test_reg)

    print("\n--- WASTE CLASSIFIER LEADERBOARD (Out-of-Sample Test) ---")
    for name, m in clf_metrics.items():
        print(f"[{name.upper()}]: Accuracy={m['accuracy']} | ROC-AUC={m['roc_auc']} | F1={m['f1_score']} | Precision={m['precision']}")

    print("\n--- WASTE QUANTITY REGRESSOR LEADERBOARD (Out-of-Sample Test) ---")
    for name, m in reg_metrics.items():
        print(f"[{name.upper()}]: MAE={m['mae_kg']} kg | RMSE={m['rmse_kg']} kg | R2={m['r2_score']}")

    # 6. Champion Selection
    champion_clf = suite.classifiers["xgboost"]
    champion_reg = suite.regressors["xgboost_reg"]

    # 7. Save serialized model artifacts
    joblib.dump(champion_clf, CHAMPION_CLF_PATH)
    joblib.dump(champion_reg, CHAMPION_REG_PATH)
    print(f"[FoodLoop Waste ML] Serialized champion artifacts saved to {MODEL_DIR}")

    # 8. Sample test evaluations for UI transparency
    test_evals = []
    y_test_probs = champion_clf.predict_proba(X_test)[:, 1]
    y_test_quantities = champion_reg.predict(X_test)
    test_rows = raw_df.iloc[val_end:].copy()

    for idx, (p_prob, p_qty) in enumerate(zip(y_test_probs, y_test_quantities)):
        row = test_rows.iloc[idx]
        test_evals.append({
            "date": pd.to_datetime(row["date"]).strftime("%Y-%m-%d"),
            "food_item": row["food_item"],
            "food_category": row["food_category"],
            "predicted_demand": int(row["predicted_demand"]),
            "planned_production": int(row["planned_production"]),
            "actual_waste_kg": float(row["waste_quantity_kg"]),
            "predicted_waste_kg": round(float(max(0.0, p_qty)), 1),
            "waste_probability": round(float(p_prob), 2),
            "risk_level": "HIGH" if p_prob >= 0.65 else ("MEDIUM" if p_prob >= 0.35 else "LOW")
        })

    # 9. Register in Model Registry
    registry_data = {
        "model_version": model_version,
        "champion_classifier": "XGBoost_Waste_Classifier",
        "champion_regressor": "XGBoost_Waste_Quantity_Regressor",
        "training_date": datetime.now().isoformat(),
        "dataset_version": "pre-production-waste-v1.0",
        "dataset_records_count": len(raw_df),
        "features": FEATURE_COLUMNS,
        "features_count": len(FEATURE_COLUMNS),
        "classifier_metrics": clf_metrics,
        "regressor_metrics": reg_metrics,
        "sample_evaluations": test_evals[-25:],
        "status": "PRODUCTION_ACTIVE"
    }

    with open(REGISTRY_PATH, "w") as f:
        json.dump(registry_data, f, indent=2)

    print(f"[FoodLoop Waste ML] Model registry updated at {REGISTRY_PATH}")
    return registry_data


if __name__ == "__main__":
    train_waste_pipeline()
