from ml.predict import predict_surplus
from ml.shelf_life_estimator import calculate_shelf_life


def test_predict_surplus_inference():
    res = predict_surplus(
        business_type="restaurant",
        category="cooked_meals",
        day_of_week=4,
        is_weekend=1,
        temp_c=25.0,
        rainfall_mm=10.0,
        is_rainy=1,
        event_nearby=1,
        planned_covers=150,
        prepared_volume_kg=80.0
    )
    assert "predicted_surplus_kg" in res
    assert res["predicted_surplus_kg"] > 0
    assert "spoilage_risk_score" in res
    assert 0.0 <= res["spoilage_risk_score"] <= 1.0
    assert "recommendation" in res


def test_shelf_life_estimator():
    # Cooked meals at room temp should have 4h FDA limit
    res = calculate_shelf_life(
        category="cooked_meals",
        storage_temp="room_temp",
        packaging_type="sealed_trays",
        ambient_temp_c=22.0,
        hours_since_prep=1.0
    )
    assert res["total_safe_shelf_life_hours"] <= 5.0
    assert res["remaining_safe_hours"] <= 4.0
    assert res["urgency"] in ["IMMEDIATE_ACTION", "EXPEDITED"]
    assert len(res["guidelines"]) >= 1
