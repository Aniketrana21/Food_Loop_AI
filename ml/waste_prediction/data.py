"""
FoodLoop AI - Data Pipeline for Pre-Production Food Waste Prediction
Generates and manages multi-facility institutional pre-production kitchen batches
with authentic menu, station, and operational factors.
"""

import os
import math
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Optional, Tuple, Dict, Any


FOOD_CATALOG = [
    {"food_item": "Steamed Seasonal Market Vegetables", "food_category": "VEGETABLES", "base_waste_pct": 0.16, "shelf_life_hours": 4},
    {"food_item": "Roasted Mediterranean Ratatouille", "food_category": "VEGETABLES", "base_waste_pct": 0.14, "shelf_life_hours": 6},
    {"food_item": "Herb-Crusted Atlantic Salmon Fillet", "food_category": "MEAT_SEAFOOD", "base_waste_pct": 0.08, "shelf_life_hours": 3},
    {"food_item": "Braised Prime Beef Short Ribs", "food_category": "MEAT_SEAFOOD", "base_waste_pct": 0.06, "shelf_life_hours": 12},
    {"food_item": "Lemon Rosemary Grilled Chicken Breast", "food_category": "MEAT_SEAFOOD", "base_waste_pct": 0.09, "shelf_life_hours": 4},
    {"food_item": "Tuscan Penne alla Vodka", "food_category": "GRAINS_PASTA", "base_waste_pct": 0.11, "shelf_life_hours": 6},
    {"food_item": "Steamed Saffron Basmati Rice Pilaf", "food_category": "GRAINS_PASTA", "base_waste_pct": 0.13, "shelf_life_hours": 8},
    {"food_item": "Artisan Four-Cheese Beef Lasagna", "food_category": "GRAINS_PASTA", "base_waste_pct": 0.07, "shelf_life_hours": 8},
    {"food_item": "Creamy Wild Mushroom Soup", "food_category": "PREPARED_SOUP", "base_waste_pct": 0.12, "shelf_life_hours": 12},
    {"food_item": "Garden Mixed Greens & Baby Spinach", "food_category": "VEGETABLES", "base_waste_pct": 0.18, "shelf_life_hours": 2},
    {"food_item": "Artisan Sourdough Rolls & Baguettes", "food_category": "BAKERY", "base_waste_pct": 0.15, "shelf_life_hours": 24},
    {"food_item": "Greek Yogurt & Fresh Berry Parfait", "food_category": "DAIRY", "base_waste_pct": 0.09, "shelf_life_hours": 6}
]

MENUS = [
    "Classic American Comfort",
    "Mediterranean Harvest",
    "Asian Wok & Noodle Bar",
    "Chef's Daily Carvery Special",
    "Global Plant-Forward Fusion"
]

KITCHENS = [
    "Central University Dining Hall",
    "North Academic Commons",
    "Executive Conference Pavilion",
    "St. Mary Healthcare Nutrition Center"
]

MEAL_TYPES = ["BREAKFAST", "LUNCH", "DINNER", "BANQUET", "LUNCH_DINNER_COMBO"]
SEASONS = ["Winter", "Spring", "Summer", "Fall"]


def generate_waste_prediction_dataset(
    num_samples: int = 1200,
    random_seed: int = 42
) -> pd.DataFrame:
    """
    Generates realistic pre-production batches across institutional facilities.
    Incorporates:
    - Overproduction ratio (planned_production / predicted_demand)
    - Day-of-week dropouts (Friday plate scrap surge, weekend shifts)
    - Food category perishability (Vegetables vs braised short ribs)
    - Historical waste rates and feedback
    """
    np.random.seed(random_seed)
    records = []

    start_date = datetime(2025, 1, 1).date()

    for i in range(num_samples):
        cur_date = start_date + timedelta(days=i % 450)
        dow = cur_date.weekday() # 0 = Mon, 4 = Fri, 5 = Sat, 6 = Sun
        month = cur_date.month
        
        # Season
        if month in [12, 1, 2]:
            season = "Winter"
        elif month in [3, 4, 5]:
            season = "Spring"
        elif month in [6, 7, 8]:
            season = "Summer"
        else:
            season = "Fall"

        item_info = FOOD_CATALOG[i % len(FOOD_CATALOG)]
        food_item = item_info["food_item"]
        food_category = item_info["food_category"]
        base_waste_pct = item_info["base_waste_pct"]

        kitchen = KITCHENS[i % len(KITCHENS)]
        menu = MENUS[i % len(MENUS)]
        meal_type = MEAL_TYPES[i % len(MEAL_TYPES)]

        # Base attendance / covers
        attendance = int(np.random.normal(1600, 350))
        attendance = max(450, min(2800, attendance))

        # Predicted demand for this dish (portions)
        dish_popularity = 0.25 if meal_type == "LUNCH_DINNER_COMBO" else 0.35
        predicted_demand = int(attendance * dish_popularity + np.random.normal(0, 25))
        predicted_demand = max(50, predicted_demand)

        # Overproduction decision: institutional kitchens intentionally overproduce by 5% to 30%
        # Friday overproduction bias (chefs overprep before the weekend)
        if dow == 4:  # Friday
            prod_buffer = np.random.uniform(1.10, 1.32)
        elif dow in [1, 2]: # Midweek
            prod_buffer = np.random.uniform(1.03, 1.15)
        else: # Weekend / Monday
            prod_buffer = np.random.uniform(1.02, 1.12)

        planned_production = int(round(predicted_demand * prod_buffer))

        # Historical waste rate (exponential moving average of prior runs)
        hist_waste_pct = float(np.clip(base_waste_pct + np.random.normal(0, 0.03), 0.02, 0.30))
        hist_waste_kg = round(predicted_demand * hist_waste_pct * 0.35, 1)

        # Discrepancy between production and actual consumption
        # Friday historical consumption is often 10-18% below planned production
        dow_consumption_drop = 0.86 if dow == 4 else (0.92 if dow == 5 else 0.98)
        actual_consumed = int(predicted_demand * dow_consumption_drop + np.random.normal(0, 15))
        actual_consumed = max(20, min(planned_production, actual_consumed))

        # Surplus / unserved portions
        surplus_portions = max(0, planned_production - actual_consumed)

        # Portion-to-kg conversion (~0.32 kg per portion)
        portion_weight_kg = 0.32 if food_category != "PREPARED_SOUP" else 0.40
        waste_quantity_kg = round(max(0.0, surplus_portions * portion_weight_kg + np.random.normal(0, 1.2)), 1)

        # Binary waste label: Significant waste (> 5.0 kg or surplus > 12 portions)
        is_waste_event = int(waste_quantity_kg > 4.5 or surplus_portions > 14)

        # Overproduction gap %
        overprod_gap_pct = round(((planned_production - predicted_demand) / (predicted_demand + 1e-5)) * 100, 1)

        records.append({
            "date": cur_date.strftime("%Y-%m-%d"),
            "food_item": food_item,
            "menu": menu,
            "food_category": food_category,
            "kitchen": kitchen,
            "season": season,
            "meal_type": meal_type,
            "day_of_week": dow,
            "attendance": attendance,
            "predicted_demand": predicted_demand,
            "planned_production": planned_production,
            "overprod_gap_pct": overprod_gap_pct,
            "historical_waste_rate": round(hist_waste_pct, 4),
            "historical_waste_kg": hist_waste_kg,
            "waste_quantity_kg": waste_quantity_kg,  # Regression target
            "has_waste": is_waste_event               # Classification target
        })

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df


def load_waste_prediction_dataset(
    csv_path: Optional[str] = None,
    save_if_generated: bool = True
) -> pd.DataFrame:
    """Loads waste prediction training dataset from cache or generates it."""
    if csv_path and os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        df["date"] = pd.to_datetime(df["date"])
        return df.sort_values("date").reset_index(drop=True)

    default_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "data", "pre_production_waste_records.csv")
    )

    if os.path.exists(default_path):
        df = pd.read_csv(default_path)
        df["date"] = pd.to_datetime(df["date"])
        return df.sort_values("date").reset_index(drop=True)

    df = generate_waste_prediction_dataset(num_samples=1200)
    if save_if_generated:
        os.makedirs(os.path.dirname(default_path), exist_ok=True)
        df.to_csv(default_path, index=False)
        print(f"[FoodLoop Waste ML] Generated and cached {len(df)} pre-production waste records to {default_path}")

    return df
