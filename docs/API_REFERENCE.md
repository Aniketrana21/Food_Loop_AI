# FoodLoop AI - REST API Reference (v1.0.0)

Base URL: `http://localhost:8000/api/v1` or `https://<your-cloud-host>/api/v1`  
Interactive OpenAPI UI: `http://localhost:8000/docs`

---

## 1. Authentication & Profiles (`/auth`)

### `GET /auth/me`
Retrieves the profile of the authenticated user.
- **Headers**: `Authorization: Bearer <supabase_jwt>`
- **Response `200`**:
```json
{
  "id": "a1111111-1111-1111-1111-111111111111",
  "email": "chef@grandhotel.com",
  "full_name": "Chef Marcus Vance",
  "role": "donor",
  "organization_name": "Grand Continental Hotel & Banquets",
  "address": "100 Grand Avenue, Downtown",
  "latitude": 37.7749,
  "longitude": -122.4194,
  "is_verified": true
}
```

### `POST /auth/demo-login?role={donor|recipient|driver|admin}`
Instant role-swapping endpoint for local testing and presentations.

---

## 2. Food Listings Marketplace (`/listings`)

### `GET /listings`
Fetch available and historical surplus food donations.
- **Query Params**:
  - `category` (string, optional): `cooked_meals`, `bakery`, `dairy`, `fresh_produce`, `packaged_goods`, `meat_seafood`
  - `status` (string, optional): `available`, `reserved`, `completed`, `expired`
  - `limit` (int, default: 50)

### `POST /listings`
Create a surplus food donation listing. Automatically calculates remaining safe shelf-life.
- **Request Body**:
```json
{
  "title": "Roasted Vegetable Penne & Herb Chicken",
  "description": "Prepared hot banquet catering surplus. Kept in cambros above 60°C.",
  "category": "cooked_meals",
  "quantity_kg": 35.0,
  "portions": 70,
  "packaging_type": "sealed_trays",
  "storage_temp": "room_temp",
  "expiry_at": "2026-09-27T16:00:00Z",
  "pickup_start": "2026-09-27T12:00:00Z",
  "pickup_end": "2026-09-27T15:00:00Z",
  "pickup_address": "100 Grand Avenue, Banquet Kitchen Bay 4",
  "pickup_lat": 37.7749,
  "pickup_lng": -122.4194,
  "dietary_tags": ["halal", "nut_free"]
}
```

---

## 3. Rescue Claims (`/claims`)

### `POST /claims`
Non-profit / Food Bank claims surplus food.
- **Request Body**:
```json
{
  "listing_id": "f1111111-1111-1111-1111-111111111111",
  "claimed_portions": 70,
  "claimed_quantity_kg": 35.0,
  "delivery_type": "volunteer_courier",
  "notes": "Urgent dinner service request."
}
```

---

## 4. Dispatch & Route Optimization (`/dispatch`)

### `POST /dispatch/optimize`
Triggers Google OR-Tools CVRPTW solver with Time Windows and Vehicle Capacity.
- **Request Body**:
```json
{
  "driver_ids": ["c1111111-1111-1111-1111-111111111111"],
  "max_travel_time_mins": 180
}
```
- **Response `200`**:
```json
{
  "solver_status": "OPTIMAL",
  "num_vehicles_dispatched": 1,
  "total_rescued_kg": 35.0,
  "total_distance_km": 6.8,
  "total_travel_time_mins": 42.0,
  "routes": [
    {
      "driver_name": "Alex Mercer",
      "vehicle_type": "refrigerated_van",
      "total_load_kg": 35.0,
      "stops": [
        {"stop_index": 0, "stop_type": "depot", "name": "FoodLoop Central Hub"},
        {"stop_index": 1, "stop_type": "pickup", "name": "Grand Continental Hotel", "arrival_time_mins": 15},
        {"stop_index": 2, "stop_type": "dropoff", "name": "Hope Center Kitchen", "arrival_time_mins": 35},
        {"stop_index": 3, "stop_type": "depot", "name": "FoodLoop Central Hub", "arrival_time_mins": 42}
      ]
    }
  ]
}
```

---

## 5. Machine Learning & Shelf Life (`/ml`)

### `POST /ml/predict-surplus`
Forecasts surplus weight and spoilage probability via XGBoost.
- **Request Body**:
```json
{
  "business_type": "hotel",
  "category": "cooked_meals",
  "day_of_week": 5,
  "is_weekend": 1,
  "temp_c": 28.0,
  "rainfall_mm": 0.0,
  "is_rainy": 0,
  "event_nearby": 1,
  "planned_covers": 200,
  "prepared_volume_kg": 90.0
}
```

### `POST /ml/shelf-life`
Evaluates thermodynamic food decay curves and FDA Danger Zone urgency.

---

## 6. RAG Knowledge & LLM Recipes (`/rag`)

### `POST /rag/ask`
Semantic vector question-answering over food laws and safety guidelines.
- **Request Body**:
```json
{
  "query": "Are we legally protected from liability if we donate hot cooked food?"
}
```

### `POST /rag/generate-recipe`
Generates high-volume community kitchen rescue recipes.
- **Request Body**:
```json
{
  "ingredients": ["Surplus Roasted Chicken", "Cooked Rice", "Assorted Vegetables"],
  "dietary_preference": "halal",
  "servings": 60
}
```

---

## 7. Environmental Impact (`/impact/summary`)
Returns aggregated metrics: CO2 avoided (kg), meals diverted, water saved (liters), and financial value.
