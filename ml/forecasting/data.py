"""
FoodLoop AI - Data Pipeline for Time-Series Demand Forecasting
Extracts historical consumption records from Supabase/PostgreSQL and builds
reproducible time-series training datasets with temporal integrity.
"""

import os
import math
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Optional, Tuple


def get_season(month: int) -> str:
    """Categorizes month into Northern Hemisphere seasonal cycle."""
    if month in [12, 1, 2]:
        return "Winter"
    elif month in [3, 4, 5]:
        return "Spring"
    elif month in [6, 7, 8]:
        return "Summer"
    else:
        return "Fall"


def is_institutional_holiday(d: date) -> int:
    """Flags major national and academic/institutional holidays."""
    # New Year, MLK Day, Memorial Day, July 4, Labor Day, Thanksgiving, Christmas
    month, day = d.month, d.day
    if (month == 1 and day in [1, 15, 16, 17, 18, 19, 20, 21]) and d.weekday() == 0:
        return 1
    if month == 7 and day == 4:
        return 1
    if month == 11 and (22 <= day <= 28) and d.weekday() == 3: # Thanksgiving
        return 1
    if month == 12 and day in [24, 25, 26, 31]:
        return 1
    return 0


def generate_synthetic_institutional_timeseries(
    start_date: str = "2024-06-01",
    num_days: int = 730,
    base_demand: int = 1600,
    random_seed: int = 42
) -> pd.DataFrame:
    """
    Generates a realistic, multi-seasonal institutional kitchen time-series dataset.
    Incorporates:
    - Weekly periodicity (high mid-week, lower weekend demand)
    - Annual seasonality (academic/corporate winter dips, autumn surge)
    - Meal type modulations (Breakfast, Lunch, Dinner, Banquet)
    - Menu category characteristics (Comfort, Health, Specialty, Standard)
    - Event shocks (banquets, conferences, campus athletics)
    - Weather sensitivity (cold/rain increase indoor cafeteria turnout)
    - Previous production & waste feedback loops
    """
    np.random.seed(random_seed)
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    records = []

    meal_types = ["BREAKFAST", "LUNCH", "DINNER", "BANQUET", "LUNCH_DINNER_COMBO"]
    menu_categories = ["COMFORT_FOOD", "HEALTH_BALANCED", "INTERNATIONAL_SPECIALTY", "STANDARD_BUFFET"]

    # State tracking for autoregressive feedback
    prev_production = base_demand
    prev_waste = 35.0

    for i in range(num_days):
        current_date = start + timedelta(days=i)
        day_of_week = current_date.weekday()
        month = current_date.month
        season = get_season(month)
        holiday = is_institutional_holiday(current_date)

        # Baseline day-of-week factor
        # Weekdays (Tue-Thu) peak around 1.12x, Weekends drop to 0.58x
        if day_of_week in [1, 2, 3]:  # Tue, Wed, Thu
            dow_factor = 1.14
        elif day_of_week in [0, 4]:    # Mon, Fri
            dow_factor = 0.98
        else:                          # Sat, Sun
            dow_factor = 0.58

        # Monthly / seasonal modulation
        month_factor = 1.0 + 0.12 * math.sin(2 * math.pi * (month - 3) / 12)
        if holiday:
            dow_factor *= 0.35

        # Special events (conferences, athletics, board banquets) ~ 9% probability
        is_special_event = int(np.random.rand() < 0.09 and day_of_week < 5 and not holiday)
        event_multiplier = 1.28 if is_special_event else 1.0

        # Weather simulation
        base_temp = 16.0 + 10.0 * math.sin(2 * math.pi * (month - 4) / 12)
        temp_c = float(np.round(base_temp + np.random.normal(0, 3.5), 1))
        precip_mm = float(np.round(max(0.0, np.random.exponential(2.0) if np.random.rand() < 0.28 else 0.0), 1))

        # Weather attendance boost (inclement weather concentrates diners on campus/institutional facility)
        weather_boost = 1.05 if (precip_mm > 5.0 or temp_c < 4.0) else 1.0

        # Meal type & menu assignment
        if is_special_event:
            meal_type = "BANQUET"
            menu_type = "INTERNATIONAL_SPECIALTY"
            service_type = "BANQUET_SERVICE"
        else:
            meal_type = "LUNCH_DINNER_COMBO"
            menu_type = menu_categories[i % len(menu_categories)]
            service_type = "HOT_BUFFET"

        # Menu factor
        menu_factor = 1.08 if menu_type == "COMFORT_FOOD" else (1.04 if menu_type == "INTERNATIONAL_SPECIALTY" else 1.0)

        # Planned RSVPs / attendance
        expected_attendance = int(base_demand * dow_factor * month_factor * event_multiplier * menu_factor)
        expected_attendance = max(200, int(expected_attendance + np.random.normal(0, 35)))

        # Actual meal demand (portions consumed)
        noise = np.random.normal(0, 38)
        actual_demand = int(expected_attendance * weather_boost + noise)
        actual_demand = max(150, actual_demand)

        # Production and waste feedback loop
        production_portions = int(actual_demand * np.random.uniform(1.02, 1.10))
        waste_kg = round(max(5.0, (production_portions - actual_demand) * 0.32 + np.random.normal(0, 2.5)), 1)

        records.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "day_of_week": day_of_week,
            "day_of_month": current_date.day,
            "month": month,
            "quarter": (month - 1) // 3 + 1,
            "is_weekend": int(day_of_week >= 5),
            "season": season,
            "is_holiday": holiday,
            "is_special_event": is_special_event,
            "meal_type": meal_type,
            "menu_type": menu_type,
            "service_type": service_type,
            "temperature_c": temp_c,
            "precipitation_mm": precip_mm,
            "planned_attendance": expected_attendance,
            "prev_production_portions": prev_production,
            "prev_waste_kg": prev_waste,
            "actual_demand": actual_demand,  # Target variable
        })

        # Update feedback state
        prev_production = production_portions
        prev_waste = waste_kg

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df


def load_forecasting_dataset(
    csv_path: Optional[str] = None,
    save_if_generated: bool = True
) -> pd.DataFrame:
    """
    Loads historical forecasting data from disk or generates an institutional
    500-day time-series if none exists.
    """
    if csv_path and os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        df["date"] = pd.to_datetime(df["date"])
        return df.sort_values("date").reset_index(drop=True)

    default_path = os.path.join(os.path.dirname(__file__), "..", "data", "institutional_demand_timeseries.csv")
    default_path = os.path.abspath(default_path)

    if os.path.exists(default_path):
        df = pd.read_csv(default_path)
        df["date"] = pd.to_datetime(df["date"])
        return df.sort_values("date").reset_index(drop=True)

    # Generate deterministic dataset
    df = generate_synthetic_institutional_timeseries(num_days=500)
    if save_if_generated:
        os.makedirs(os.path.dirname(default_path), exist_ok=True)
        df.to_csv(default_path, index=False)
        print(f"[FoodLoop Data] Generated and cached time-series dataset to {default_path} ({len(df)} rows)")

    return df
