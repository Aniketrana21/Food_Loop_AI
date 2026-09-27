"""
FoodLoop AI - Shelf-Life & Spoilage Dynamics Estimator
Based on FDA Food Code safety curves & thermodynamic spoilage models.
Calculates remaining safe consumption window (hours) based on food category,
storage temperature, packaging type, and time since preparation.
"""

from typing import Dict, Any, List
from datetime import datetime, timezone


# Baseline shelf lives at recommended storage conditions (hours)
BASELINE_SHELF_LIFE_HOURS: Dict[str, Dict[str, float]] = {
    "cooked_meals": {
        "room_temp": 4.0,       # FDA 4-hour rule for TCS hot foods
        "refrigerated": 72.0,   # 3 days at <= 4°C
        "frozen": 720.0         # 30 days
    },
    "bakery": {
        "room_temp": 48.0,      # 2 days ambient
        "refrigerated": 96.0,
        "frozen": 720.0
    },
    "dairy": {
        "room_temp": 2.0,       # High risk above 4°C
        "refrigerated": 120.0,  # 5 days
        "frozen": 720.0
    },
    "fresh_produce": {
        "room_temp": 36.0,
        "refrigerated": 144.0,  # 6 days
        "frozen": 720.0
    },
    "packaged_goods": {
        "room_temp": 360.0,     # 15 days
        "refrigerated": 480.0,
        "frozen": 1440.0
    },
    "meat_seafood": {
        "room_temp": 1.5,       # Extreme microbial proliferation risk
        "refrigerated": 48.0,   # 2 days at <= 4°C
        "frozen": 720.0
    },
    "beverages": {
        "room_temp": 12.0,
        "refrigerated": 120.0,
        "frozen": 720.0
    }
}

# Packaging barrier factor (extends shelf life multiplier)
PACKAGING_MULTIPLIERS = {
    "sealed_trays": 1.15,
    "vacuum_sealed": 1.40,
    "individually_packaged": 1.20,
    "boxes": 1.00,
    "crates": 0.90,
    "bulk_containers": 0.95
}


def calculate_shelf_life(
    category: str,
    storage_temp: str,
    packaging_type: str = "sealed_trays",
    ambient_temp_c: float = 22.0,
    hours_since_prep: float = 0.0
) -> Dict[str, Any]:
    """
    Computes remaining safe shelf-life in hours, urgency level, and safety warnings.
    """
    cat_key = category.lower().replace(" ", "_")
    if cat_key not in BASELINE_SHELF_LIFE_HOURS:
        cat_key = "cooked_meals"

    storage_key = storage_temp.lower().replace(" ", "_")
    if storage_key not in BASELINE_SHELF_LIFE_HOURS[cat_key]:
        storage_key = "room_temp"

    base_hours = BASELINE_SHELF_LIFE_HOURS[cat_key][storage_key]
    pack_mult = PACKAGING_MULTIPLIERS.get(packaging_type.lower(), 1.0)

    # Ambient thermal decay penalty if stored at room temp in warm climates (>24°C)
    thermal_penalty = 1.0
    if storage_key == "room_temp" and ambient_temp_c > 24.0:
        thermal_penalty = max(0.4, 1.0 - (ambient_temp_c - 24.0) * 0.08)

    total_safe_hours = round(base_hours * pack_mult * thermal_penalty, 1)
    remaining_hours = max(0.0, round(total_safe_hours - hours_since_prep, 1))

    # Urgency classification
    if remaining_hours <= 0:
        urgency = "EXPIRED"
        risk_level = "CRITICAL"
        dispatch_priority = 0
    elif remaining_hours <= 3.0:
        urgency = "IMMEDIATE_ACTION"
        risk_level = "HIGH"
        dispatch_priority = 1
    elif remaining_hours <= 8.0:
        urgency = "EXPEDITED"
        risk_level = "MEDIUM"
        dispatch_priority = 2
    else:
        urgency = "STANDARD"
        risk_level = "LOW"
        dispatch_priority = 3

    # Safety guidelines advice
    guidelines = []
    if storage_key == "room_temp" and cat_key in ["cooked_meals", "dairy", "meat_seafood"]:
        guidelines.append("Food is in the FDA Danger Zone (4°C-60°C). Must be delivered & consumed within 4 hours of prep.")
    if storage_key == "refrigerated":
        guidelines.append("Maintain cold chain below 4°C during volunteer courier transit.")
    if packaging_type in ["crates", "bulk_containers"]:
        guidelines.append("Cover with clean food-grade lids/film during transit to avoid airborne cross-contamination.")

    return {
        "category": cat_key,
        "storage_temp": storage_key,
        "total_safe_shelf_life_hours": total_safe_hours,
        "hours_since_prep": hours_since_prep,
        "remaining_safe_hours": remaining_hours,
        "urgency": urgency,
        "risk_level": risk_level,
        "dispatch_priority": dispatch_priority,
        "guidelines": guidelines
    }


if __name__ == "__main__":
    test_result = calculate_shelf_life(
        category="cooked_meals",
        storage_temp="room_temp",
        packaging_type="sealed_trays",
        ambient_temp_c=25.0,
        hours_since_prep=1.5
    )
    print("Shelf life calculation:", test_result)
