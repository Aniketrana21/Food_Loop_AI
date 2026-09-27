"""
FoodLoop AI - Time-Series Evaluation & Model Comparison
Implements temporal train/test split, TimeSeriesSplit walk-forward validation,
and computes MAE, RMSE, MAPE, and R2 metrics across all 4 models.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, List
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit


def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Computes MAE, RMSE, MAPE (with div-by-zero protection), and R2.
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    
    # MAPE with epsilon guard
    mask = y_true > 0
    if np.any(mask):
        mape = float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100.0)
    else:
        mape = 0.0

    r2 = float(r2_score(y_true, y_pred))

    return {
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "mape_pct": round(mape, 2),
        "r2_score": round(r2, 4)
    }


def temporal_train_test_split(
    df: pd.DataFrame,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Performs strictly chronological, time-based split to prevent temporal leakage.
    Earliest 70% -> Train
    Next 15%     -> Validation
    Final 15%    -> Out-of-Sample Test
    """
    sorted_df = df.sort_values("date").reset_index(drop=True)
    n = len(sorted_df)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))

    train_df = sorted_df.iloc[:train_end].copy()
    val_df = sorted_df.iloc[train_end:val_end].copy()
    test_df = sorted_df.iloc[val_end:].copy()

    return train_df, val_df, test_df


def compare_models(
    models: Dict[str, Any],
    X_test: pd.DataFrame,
    y_test: pd.Series
) -> Dict[str, Any]:
    """
    Evaluates all 4 models on out-of-sample temporal test data.
    Returns comparison matrix, leaderboard ranking, and residual statistics.
    """
    results = {}
    predictions_map = {}

    for name, model in models.items():
        preds = model.predict(X_test)
        metrics = calculate_metrics(y_test.values, preds)
        results[name] = metrics
        predictions_map[name] = preds

    # Sort leaderboard by MAE (lowest error first)
    leaderboard = sorted(results.items(), key=lambda x: x[1]["mae"])
    champion_name, champion_metrics = leaderboard[0]

    # Calculate baseline reduction benchmarks
    naive_mae = results.get("naive_baseline", {}).get("mae", champion_metrics["mae"])
    ma_mae = results.get("moving_average_7d", {}).get("mae", champion_metrics["mae"])

    pct_reduction_vs_naive = round(max(0.0, (naive_mae - champion_metrics["mae"]) / (naive_mae + 1e-5) * 100), 1)
    pct_reduction_vs_ma = round(max(0.0, (ma_mae - champion_metrics["mae"]) / (ma_mae + 1e-5) * 100), 1)

    return {
        "leaderboard": [
            {"model": name, **metrics} for name, metrics in leaderboard
        ],
        "champion_model": champion_name,
        "champion_metrics": champion_metrics,
        "detailed_metrics": results,
        "baseline_benchmarks": {
            "pct_reduction_vs_naive": pct_reduction_vs_naive,
            "pct_reduction_vs_moving_average": pct_reduction_vs_ma
        },
        "test_sample_count": len(X_test)
    }


def walk_forward_cv_validation(
    model_factory,
    X: pd.DataFrame,
    y: pd.Series,
    n_splits: int = 4
) -> List[Dict[str, float]]:
    """
    Performs walk-forward temporal cross-validation using expanding training windows.
    Strictly forbids random shuffling or future lookahead.
    """
    tscv = TimeSeriesSplit(n_splits=n_splits)
    fold_metrics = []

    for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
        X_tr, y_tr = X.iloc[train_idx], y.iloc[train_idx]
        X_val, y_val = X.iloc[val_idx], y.iloc[val_idx]

        model = model_factory()
        model.fit(X_tr, y_tr)
        preds = model.predict(X_val)

        metrics = calculate_metrics(y_val.values, preds)
        metrics["fold"] = fold + 1
        metrics["train_size"] = len(train_idx)
        metrics["val_size"] = len(val_idx)
        fold_metrics.append(metrics)

    return fold_metrics
