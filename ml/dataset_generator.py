"""
FoodLoop AI - ML Surplus & Waste Risk Dataset Generator
Generates high-fidelity training data simulating real restaurant, grocery, bakery,
and catering surplus generation patterns based on weather, day of week, and event dynamics.
"""

import numpy as np
import pandas as pd
from typing import Tuple


def generate_surplus_dataset(n_samples: int = 5000, random_seed: int = 42) -> pd.DataFrame:
    np.random.seed(random_seed)

    business_types = ["restaurant", "supermarket", "bakery", "caterer", "hotel", "corporate_cafeteria"]
    food_categories = ["cooked_meals", "bakery", "dairy", "fresh_produce", "meat_seafood", "packaged_goods"]

    records = []
    for _ in range(n_samples):
        biz = np.random.choice(business_types)
        cat = np.random.choice(food_categories)
        day_of_week = np.random.randint(0, 7)  # 0: Mon, 6: Sun
        is_weekend = 1 if day_of_week in [4, 5, 6] else 0  # Fri-Sun surge
        
        # Weather variables
        temp_c = np.random.uniform(12.0, 36.0)
        rainfall_mm = np.random.exponential(scale=3.5) if np.random.random() > 0.65 else 0.0
        is_rainy = 1 if rainfall_mm > 5.0 else 0
        
        # Nearby event or holiday impact
        event_nearby = 1 if np.random.random() < 0.22 else 0

        # Production capacity
        if biz in ["hotel", "caterer"]:
            planned_covers = np.random.randint(80, 500)
            prepared_volume_kg = planned_covers * np.random.uniform(0.4, 0.75)
        elif biz == "supermarket":
            planned_covers = np.random.randint(400, 1500)
            prepared_volume_kg = planned_covers * np.random.uniform(0.2, 0.5)
        elif biz == "bakery":
            planned_covers = np.random.randint(150, 450)
            prepared_volume_kg = planned_covers * np.random.uniform(0.15, 0.35)
        else:
            planned_covers = np.random.randint(50, 250)
            prepared_volume_kg = planned_covers * np.random.uniform(0.35, 0.6)

        # Baseline surplus percentage calculation
        # Bad weather reduces footfall at restaurants/bakeries -> increased surplus
        # Events can increase attendance, but over-preparation also happens
        surplus_pct = 0.08  # Baseline 8% surplus
        if is_weekend:
            surplus_pct += 0.04
        if is_rainy and biz in ["restaurant", "bakery"]:
            surplus_pct += 0.07  # Drop in dine-in foot traffic
        if event_nearby:
            surplus_pct += np.random.uniform(-0.03, 0.06)

        # Perishable factor
        if cat in ["cooked_meals", "bakery"]:
            surplus_pct += 0.03

        # Add stochastic noise
        surplus_pct = max(0.02, min(0.35, surplus_pct + np.random.normal(0, 0.025)))
        surplus_kg = round(prepared_volume_kg * surplus_pct, 2)
        surplus_portions = int(surplus_kg * np.random.uniform(1.8, 2.5))

        # Risk score calculation (0.0 to 1.0)
        # Higher temperature + cooked/dairy = higher spoilage risk
        risk_score = 0.2
        if cat in ["cooked_meals", "meat_seafood"]:
            risk_score += 0.4
        elif cat == "dairy":
            risk_score += 0.3
        elif cat == "bakery":
            risk_score += 0.1
        
        if temp_c > 26.0:
            risk_score += 0.25
        risk_score = min(1.0, max(0.05, round(risk_score + np.random.normal(0, 0.05), 3)))

        records.append({
            "business_type": biz,
            "category": cat,
            "day_of_week": day_of_week,
            "is_weekend": is_weekend,
            "temp_c": round(temp_c, 1),
            "rainfall_mm": round(rainfall_mm, 1),
            "is_rainy": is_rainy,
            "event_nearby": event_nearby,
            "planned_covers": planned_covers,
            "prepared_volume_kg": round(prepared_volume_kg, 2),
            "surplus_kg": surplus_kg,
            "surplus_portions": surplus_portions,
            "spoilage_risk_score": risk_score
        })

    return pd.DataFrame(records)


if __name__ == "__main__":
    df = generate_surplus_dataset(2000)
    print(df.head())
    print("Dataset shape:", df.shape)
