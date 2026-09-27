"""
FoodLoop AI - Feature Engineering for Time-Series Demand Forecasting
Constructs temporal, lag, rolling window, and institutional features
with strict data leakage prevention.
"""

import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Any


FEATURE_COLUMNS = [
    # Calendar & Cyclical
    "day_of_week",
    "day_of_month",
    "month",
    "quarter",
    "is_weekend",
    "is_holiday",
    "is_special_event",
    "sin_dow",
    "cos_dow",
    "sin_month",
    "cos_month",

    # Planned / Institutional Context
    "planned_attendance",
    "prev_production_portions",
    "prev_waste_kg",
    "temperature_c",
    "precipitation_mm",

    # Season One-Hot
    "season_Fall",
    "season_Spring",
    "season_Summer",
    "season_Winter",

    # Meal Type One-Hot
    "meal_BREAKFAST",
    "meal_LUNCH",
    "meal_DINNER",
    "meal_BANQUET",
    "meal_COMBO",

    # Menu Type One-Hot
    "menu_COMFORT",
    "menu_HEALTH",
    "menu_SPECIALTY",
    "menu_STANDARD",

    # Historical Lags (Strictly shifted to prevent lookahead leakage)
    "lag_1_demand",
    "lag_2_demand",
    "lag_3_demand",
    "lag_7_demand",   # Same day last week
    "lag_14_demand",  # Same day two weeks ago

    # Rolling Statistics (Strictly shifted to prevent lookahead leakage)
    "rolling_mean_7",
    "rolling_std_7",
    "rolling_mean_14",
    "rolling_mean_30",
    "rolling_ratio_7_30"
]

TARGET_COLUMN = "actual_demand"


def build_forecasting_features(
    df: pd.DataFrame,
    is_training: bool = True
) -> pd.DataFrame:
    """
    Constructs feature matrix ensuring strict temporal causality:
    - All rolling calculations and lags use `.shift(1)` so current-day target
      is never in the feature set.
    - Encodes cyclical trigonometric transformations for day-of-week and month.
    - Encodes meal type, menu categories, and seasonal one-hot indicators.
    - Drops warm-up rows (first 30 days) that contain NaN lags during training.
    """
    data = df.copy()
    data["date"] = pd.to_datetime(data["date"])
    data = data.sort_values("date").reset_index(drop=True)

    # 1. Cyclical calendar encodings (captures continuous periodic smoothness)
    data["sin_dow"] = np.sin(2 * np.pi * data["day_of_week"] / 7.0)
    data["cos_dow"] = np.cos(2 * np.pi * data["day_of_week"] / 7.0)
    data["sin_month"] = np.sin(2 * np.pi * (data["month"] - 1) / 12.0)
    data["cos_month"] = np.cos(2 * np.pi * (data["month"] - 1) / 12.0)

    # 2. One-hot season encoding
    for s in ["Fall", "Spring", "Summer", "Winter"]:
        col_name = f"season_{s}"
        data[col_name] = (data.get("season", "") == s).astype(int)

    # 3. One-hot meal type encoding
    meal_series = data.get("meal_type", pd.Series("LUNCH_DINNER_COMBO", index=data.index)).astype(str).str.upper()
    data["meal_BREAKFAST"] = meal_series.str.contains("BREAKFAST").astype(int)
    data["meal_LUNCH"] = (meal_series.str.contains("LUNCH") & ~meal_series.str.contains("COMBO")).astype(int)
    data["meal_DINNER"] = (meal_series.str.contains("DINNER") & ~meal_series.str.contains("COMBO")).astype(int)
    data["meal_BANQUET"] = meal_series.str.contains("BANQUET").astype(int)
    data["meal_COMBO"] = meal_series.str.contains("COMBO").astype(int)

    # 4. One-hot menu category encoding
    menu_series = data.get("menu_type", pd.Series("STANDARD_BUFFET", index=data.index)).astype(str).str.upper()
    data["menu_COMFORT"] = menu_series.str.contains("COMFORT").astype(int)
    data["menu_HEALTH"] = menu_series.str.contains("HEALTH").astype(int)
    data["menu_SPECIALTY"] = menu_series.str.contains("SPECIALTY").astype(int)
    data["menu_STANDARD"] = menu_series.str.contains("STANDARD").astype(int)

    # 5. Lag features (STRICTLY shifted by at least 1 day to prevent lookahead)
    target_series = data[TARGET_COLUMN] if TARGET_COLUMN in data.columns else data.get("lag_1_demand", pd.Series(0, index=data.index))
    
    data["lag_1_demand"] = target_series.shift(1)
    data["lag_2_demand"] = target_series.shift(2)
    data["lag_3_demand"] = target_series.shift(3)
    data["lag_7_demand"] = target_series.shift(7)
    data["lag_14_demand"] = target_series.shift(14)

    # 6. Rolling Statistics on shifted series (Prevents target leakage)
    shifted_target = target_series.shift(1)
    data["rolling_mean_7"] = shifted_target.rolling(window=7, min_periods=1).mean()
    data["rolling_std_7"] = shifted_target.rolling(window=7, min_periods=1).std().fillna(0)
    data["rolling_mean_14"] = shifted_target.rolling(window=14, min_periods=1).mean()
    data["rolling_mean_30"] = shifted_target.rolling(window=30, min_periods=1).mean()

    # Momentum / Trend ratio (short-term 7-day vs long-term 30-day baseline)
    data["rolling_ratio_7_30"] = (data["rolling_mean_7"] / (data["rolling_mean_30"] + 1e-5)).round(4)

    # During training, drop initial warm-up rows where 14-day lags are unobserved
    if is_training and TARGET_COLUMN in data.columns:
        data = data.dropna(subset=["lag_14_demand", TARGET_COLUMN]).reset_index(drop=True)

    # Fill any remaining NaNs in test/inference rows using rolling approximations
    for col in FEATURE_COLUMNS:
        if col not in data.columns:
            data[col] = 0
        elif data[col].isna().any():
            data[col] = data[col].bfill().fillna(0)

    return data


def get_feature_and_target_matrices(
    df: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.Series, List[str]]:
    """Separates engineered DataFrame into X (features), y (target), and feature names list."""
    feat_df = build_forecasting_features(df, is_training=True)
    X = feat_df[FEATURE_COLUMNS].copy()
    y = feat_df[TARGET_COLUMN].copy()
    return X, y, FEATURE_COLUMNS
