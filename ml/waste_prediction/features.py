"""
FoodLoop AI - Feature Engineering for Pre-Production Food Waste Prediction
Constructs domain-specific features balancing production over-buffer ratios,
spoilage perishability, and cyclical calendar dynamics.
"""

import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Any


FEATURE_COLUMNS = [
    # 1. Production & Demand (predicted demand, planned production, attendance)
    "predicted_demand",
    "planned_production",
    "prod_to_demand_ratio",
    "planned_excess_portions",
    "attendance",

    # 2. Historical Waste
    "historical_waste_rate",
    "historical_waste_kg",

    # 3. Calendar & Weekly Dynamics (day of week)
    "day_of_week",
    "is_weekend",
    "is_friday",
    "sin_dow",
    "cos_dow",

    # 4. Food Category (food category)
    "cat_VEGETABLES",
    "cat_MEAT_SEAFOOD",
    "cat_GRAINS_PASTA",
    "cat_DAIRY",
    "cat_BAKERY",
    "cat_PREPARED_SOUP",

    # 5. Food Item Specifics (food item)
    "item_perishability_index",
    "item_short_holding_risk",

    # 6. Menu Theme (menu)
    "menu_Classic_Comfort",
    "menu_Mediterranean",
    "menu_Asian_Wok",
    "menu_Carvery_Special",
    "menu_Global_Plant",

    # 7. Meal Type (meal type)
    "meal_BREAKFAST",
    "meal_LUNCH",
    "meal_DINNER",
    "meal_BANQUET",
    "meal_COMBO",

    # 8. Season (season)
    "season_Fall",
    "season_Spring",
    "season_Summer",
    "season_Winter",

    # 9. Kitchen / Facility (kitchen)
    "kitchen_Central",
    "kitchen_North",
    "kitchen_Executive",
    "kitchen_Healthcare"
]

CLASSIFICATION_TARGET = "has_waste"
REGRESSION_TARGET = "waste_quantity_kg"


def build_waste_prediction_features(df: pd.DataFrame) -> pd.DataFrame:
    """Transforms raw pre-production records into numerical feature matrix."""
    data = df.copy()

    # 1. Operational Ratios
    pred_dem = data["predicted_demand"].astype(float)
    plan_prod = data["planned_production"].astype(float)

    data["prod_to_demand_ratio"] = (plan_prod / (pred_dem + 1e-5)).round(4)
    data["planned_excess_portions"] = (plan_prod - pred_dem).round(1)

    # 2. Day of Week Cyclical & Critical Drop Days
    dow = data["day_of_week"].astype(int)
    data["is_weekend"] = (dow >= 5).astype(int)
    data["is_friday"] = (dow == 4).astype(int)
    data["sin_dow"] = np.sin(2 * np.pi * dow / 7.0)
    data["cos_dow"] = np.cos(2 * np.pi * dow / 7.0)

    # 3. Category Encoding
    cat_series = data.get("food_category", pd.Series("VEGETABLES", index=data.index)).astype(str).str.upper()
    data["cat_VEGETABLES"] = cat_series.str.contains("VEG").astype(int)
    data["cat_MEAT_SEAFOOD"] = (cat_series.str.contains("MEAT") | cat_series.str.contains("SEAFOOD")).astype(int)
    data["cat_GRAINS_PASTA"] = (cat_series.str.contains("GRAIN") | cat_series.str.contains("PASTA")).astype(int)
    data["cat_DAIRY"] = cat_series.str.contains("DAIRY").astype(int)
    data["cat_BAKERY"] = cat_series.str.contains("BAKERY").astype(int)
    data["cat_PREPARED_SOUP"] = cat_series.str.contains("SOUP").astype(int)

    # 4. Food Item Specific Perishability & Holding Risk
    item_series = data.get("food_item", pd.Series("", index=data.index)).astype(str).str.lower()
    
    def _compute_item_perishability(row):
        cat = str(row.get("food_category", "")).upper()
        item = str(row.get("food_item", "")).lower()
        if any(w in item for w in ["salmon", "seafood", "fish", "shrimp"]):
            return 0.90
        if any(w in item for w in ["salad", "greens", "spinach", "lettuce"]):
            return 0.88
        if "VEG" in cat:
            return 0.82
        if "MEAT" in cat:
            return 0.70
        if "SOUP" in cat:
            return 0.58
        if "DAIRY" in cat:
            return 0.65
        if "GRAIN" in cat or "PASTA" in cat:
            return 0.45
        if "BAKERY" in cat:
            return 0.35
        return 0.60

    data["item_perishability_index"] = data.apply(_compute_item_perishability, axis=1).round(3)
    data["item_short_holding_risk"] = (
        (data["item_perishability_index"] >= 0.80) | (data["cat_VEGETABLES"] == 1)
    ).astype(int)

    # 5. Menu Theme Encoding
    menu_series = data.get("menu", pd.Series("Classic American Comfort", index=data.index)).astype(str).str.lower()
    data["menu_Classic_Comfort"] = (menu_series.str.contains("classic") | menu_series.str.contains("comfort")).astype(int)
    data["menu_Mediterranean"] = menu_series.str.contains("mediter").astype(int)
    data["menu_Asian_Wok"] = (menu_series.str.contains("asian") | menu_series.str.contains("wok")).astype(int)
    data["menu_Carvery_Special"] = (menu_series.str.contains("carvery") | menu_series.str.contains("chef")).astype(int)
    data["menu_Global_Plant"] = (menu_series.str.contains("plant") | menu_series.str.contains("fusion") | menu_series.str.contains("global")).astype(int)

    # 4. Meal Type Encoding
    meal_series = data.get("meal_type", pd.Series("LUNCH_DINNER_COMBO", index=data.index)).astype(str).str.upper()
    data["meal_BREAKFAST"] = meal_series.str.contains("BREAKFAST").astype(int)
    data["meal_LUNCH"] = (meal_series.str.contains("LUNCH") & ~meal_series.str.contains("COMBO")).astype(int)
    data["meal_DINNER"] = (meal_series.str.contains("DINNER") & ~meal_series.str.contains("COMBO")).astype(int)
    data["meal_BANQUET"] = meal_series.str.contains("BANQUET").astype(int)
    data["meal_COMBO"] = meal_series.str.contains("COMBO").astype(int)

    # 5. Season Encoding
    season_series = data.get("season", pd.Series("Fall", index=data.index)).astype(str)
    for s in ["Fall", "Spring", "Summer", "Winter"]:
        data[f"season_{s}"] = (season_series == s).astype(int)

    # 6. Kitchen / Facility Encoding
    kitchen_series = data.get("kitchen", pd.Series("Central", index=data.index)).astype(str)
    data["kitchen_Central"] = kitchen_series.str.contains("Central").astype(int)
    data["kitchen_North"] = kitchen_series.str.contains("North").astype(int)
    data["kitchen_Executive"] = kitchen_series.str.contains("Executive").astype(int)
    data["kitchen_Healthcare"] = (kitchen_series.str.contains("Health") | kitchen_series.str.contains("Mary")).astype(int)

    # Ensure all columns exist and have non-null values
    for col in FEATURE_COLUMNS:
        if col not in data.columns:
            data[col] = 0
        elif data[col].isna().any():
            data[col] = data[col].fillna(0)

    return data


def extract_features_and_targets(
    df: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.Series, pd.Series, List[str]]:
    """Separates feature matrix X, classification target y_clf, and regression target y_reg."""
    feat_df = build_waste_prediction_features(df)
    X = feat_df[FEATURE_COLUMNS].copy()
    y_clf = feat_df[CLASSIFICATION_TARGET].copy()
    y_reg = feat_df[REGRESSION_TARGET].copy()
    return X, y_clf, y_reg, FEATURE_COLUMNS
