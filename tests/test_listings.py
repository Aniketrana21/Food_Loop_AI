from datetime import datetime, timezone, timedelta


def test_get_empty_listings(client):
    response = client.get("/api/v1/listings")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_and_fetch_listing(client):
    now = datetime.now(timezone.utc)
    payload = {
        "title": "Fresh Brioche and Croissants",
        "description": "Bakery surplus packed in clean boxes",
        "category": "bakery",
        "quantity_kg": 15.5,
        "portions": 30,
        "packaging_type": "boxes",
        "storage_temp": "room_temp",
        "expiry_at": (now + timedelta(hours=18)).isoformat(),
        "pickup_start": now.isoformat(),
        "pickup_end": (now + timedelta(hours=4)).isoformat(),
        "pickup_address": "456 Market St, San Francisco, CA",
        "pickup_lat": 37.7900,
        "pickup_lng": -122.4000,
        "dietary_tags": ["vegetarian"]
    }
    response = client.post("/api/v1/listings", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Fresh Brioche and Croissants"
    assert data["quantity_kg"] == 15.5
    assert data["status"] == "available"
    assert "estimated_shelf_life_hours" in data
    assert data["estimated_shelf_life_hours"] > 0

    # Fetch by ID
    get_res = client.get(f"/api/v1/listings/{data['id']}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == data["id"]
