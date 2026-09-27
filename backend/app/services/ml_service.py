import os
import sys
from typing import Dict, Any

# Ensure ml directory is on sys.path
ML_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml"))
if ML_DIR not in sys.path:
    sys.path.append(ML_DIR)

from predict import predict_surplus
from shelf_life_estimator import calculate_shelf_life


class MLService:
    @staticmethod
    def forecast_surplus(data: Dict[str, Any]) -> Dict[str, Any]:
        return predict_surplus(
            business_type=data.get("business_type", "restaurant"),
            category=data.get("category", "cooked_meals"),
            day_of_week=data.get("day_of_week", 4),
            is_weekend=data.get("is_weekend", 1),
            temp_c=data.get("temp_c", 22.0),
            rainfall_mm=data.get("rainfall_mm", 0.0),
            is_rainy=data.get("is_rainy", 0),
            event_nearby=data.get("event_nearby", 0),
            planned_covers=data.get("planned_covers", 100),
            prepared_volume_kg=data.get("prepared_volume_kg", 50.0)
        )

    @staticmethod
    def estimate_shelf_life(data: Dict[str, Any]) -> Dict[str, Any]:
        return calculate_shelf_life(
            category=data.get("category", "cooked_meals"),
            storage_temp=data.get("storage_temp", "room_temp"),
            packaging_type=data.get("packaging_type", "sealed_trays"),
            ambient_temp_c=data.get("ambient_temp_c", 22.0),
            hours_since_prep=data.get("hours_since_prep", 0.0)
        )


ml_service = MLService()
