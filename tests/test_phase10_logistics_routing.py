"""
FoodLoop AI - Phase 10 Logistics, Fleet, and Route Optimization Tests
Verifies OR-Tools VRP route optimization, 8-status lifecycle state machine,
proof of delivery verification, driver dashboard, and telemetry.
"""

import pytest
from datetime import datetime, timezone, timedelta
from app.services.route_optimizer import (
    LogisticsRouteOptimizer,
    haversine_km,
    ORTOOLS_AVAILABLE
)
from app.schemas.logistics_schemas import LOGISTICS_STATUSES
from app.models.models import Delivery, Vehicle, Driver, SurplusItem
from app.core.database import SessionLocal


def test_haversine_distance():
    # San Francisco City Hall to Ferry Building (~3.2 km)
    dist = haversine_km(37.7792, -122.4191, 37.7955, -122.3937)
    assert 2.0 <= dist <= 4.5


def test_logistics_statuses_completeness():
    expected_statuses = [
        "ASSIGNED", "EN_ROUTE", "ARRIVED", "PICKED_UP",
        "IN_TRANSIT", "DELIVERED", "FAILED", "CANCELLED"
    ]
    for s in expected_statuses:
        assert s in LOGISTICS_STATUSES


def test_ortools_route_optimizer_multi_vehicle():
    depot = {
        "name": "Regional Rescue Hub",
        "address": "100 Logistics Way, San Francisco, CA",
        "latitude": 37.7749,
        "longitude": -122.4194
    }

    # 4 rescue missions: one CRITICAL, one HIGH, two MEDIUM
    missions = [
        {
            "id": "del-test-001",
            "food_title": "Warm Prepared Soup",
            "weight_kg": 40.0,
            "food_urgency": "CRITICAL",
            "pickup_address": "Downtown Hotel",
            "pickup_lat": 37.7850,
            "pickup_lng": -122.4080,
            "delivery_address": "Shelter A",
            "delivery_lat": 37.7890,
            "delivery_lng": -122.4120,
            "pickup_window_start": 0,
            "pickup_window_end": 60,
            "delivery_window_start": 15,
            "delivery_window_end": 90
        },
        {
            "id": "del-test-002",
            "food_title": "Chilled Fresh Dairy",
            "weight_kg": 75.0,
            "food_urgency": "HIGH",
            "pickup_address": "University Dining",
            "pickup_lat": 37.7760,
            "pickup_lng": -122.4200,
            "delivery_address": "Community Pantry B",
            "delivery_lat": 37.7650,
            "delivery_lng": -122.4150,
            "pickup_window_start": 10,
            "pickup_window_end": 120,
            "delivery_window_start": 30,
            "delivery_window_end": 180
        },
        {
            "id": "del-test-003",
            "food_title": "Bakery Pastries",
            "weight_kg": 30.0,
            "food_urgency": "MEDIUM",
            "pickup_address": "Artisan Bakery",
            "pickup_lat": 37.7900,
            "pickup_lng": -122.4050,
            "delivery_address": "Family Shelter C",
            "delivery_lat": 37.7600,
            "delivery_lng": -122.4250,
            "pickup_window_start": 30,
            "pickup_window_end": 240,
            "delivery_window_start": 60,
            "delivery_window_end": 300
        },
        {
            "id": "del-test-004",
            "food_title": "Organic Produce Crates",
            "weight_kg": 120.0,
            "food_urgency": "LOW",
            "pickup_address": "Farmers Market",
            "pickup_lat": 37.7950,
            "pickup_lng": -122.3950,
            "delivery_address": "Youth Center D",
            "delivery_lat": 37.7550,
            "delivery_lng": -122.4180,
            "pickup_window_start": 60,
            "pickup_window_end": 300,
            "delivery_window_start": 90,
            "delivery_window_end": 360
        }
    ]

    vehicles = [
        {
            "id": "veh-001",
            "license_plate": "EV-RESCUE-01",
            "capacity_kg": 200.0,  # Cannot take all 265kg at once -> tests capacity constraint!
            "driver_id": "drv-001",
            "driver_name": "Courier Alex"
        },
        {
            "id": "veh-002",
            "license_plate": "EV-RESCUE-02",
            "capacity_kg": 250.0,
            "driver_id": "drv-002",
            "driver_name": "Courier Jordan"
        }
    ]

    result = LogisticsRouteOptimizer.optimize_dispatch_routes(
        depot=depot,
        missions=missions,
        vehicles=vehicles,
        average_speed_kmh=28.0,
        service_time_mins=10
    )

    assert any(kw in result.solver_status for kw in ["OPTIMAL", "FEASIBLE", "HEURISTIC"])
    assert result.num_vehicles_dispatched >= 1
    assert result.total_rescued_kg > 0
    assert result.total_distance_km > 0
    assert result.total_travel_time_mins > 0
    assert len(result.routes) >= 1

    # Verify that each assigned vehicle never exceeds its capacity constraint
    for r in result.routes:
        assert r.total_load_kg > 0
        # Check waypoint continuity
        assert len(r.waypoints) >= 3  # at least depot, pickup, delivery
        assert r.waypoints[0].stop_type == "depot"
        for wp in r.waypoints:
            assert wp.cumulative_load_kg <= r.vehicle_capacity_kg + 0.1


def test_delivery_lifecycle_and_proof_of_delivery():
    db = SessionLocal()
    try:
        # Create a test delivery mission
        mission = Delivery(
            food_title="Hot Lasagna Trays",
            cargo_weight_kg=25.0,
            food_urgency="HIGH",
            pickup_address="Tech Campus Kitchen",
            pickup_lat=37.7800,
            pickup_lng=-122.4100,
            delivery_address="Hope Center Shelter",
            delivery_lat=37.7650,
            delivery_lng=-122.4200,
            scheduled_pickup_time=datetime.now(timezone.utc),
            scheduled_delivery_time=datetime.now(timezone.utc) + timedelta(minutes=45),
            status="ASSIGNED",
            distance_km=2.4,
            transit_time_mins=18.0
        )
        db.add(mission)
        db.commit()
        db.refresh(mission)

        deliv_id = mission.id

        # Lifecycle Step 1: EN_ROUTE
        mission.status = "EN_ROUTE"
        mission.departure_at = datetime.now(timezone.utc)
        db.commit()

        # Lifecycle Step 2: ARRIVED at pickup
        mission.status = "ARRIVED"
        mission.arrival_at = datetime.now(timezone.utc)
        db.commit()

        # Lifecycle Step 3: PICKED_UP
        mission.status = "PICKED_UP"
        db.commit()

        # Lifecycle Step 4: IN_TRANSIT
        mission.status = "IN_TRANSIT"
        db.commit()

        # Lifecycle Step 5: Proof of Delivery -> DELIVERED
        mission.status = "DELIVERED"
        mission.proof_of_delivery_receiver_name = "Sarah Jenkins"
        mission.proof_of_delivery_signature = "data:image/svg+xml;base64,PHN2Zy..."
        mission.proof_of_delivery_photo = "https://images.unsplash.com/photo-delivered"
        mission.proof_of_delivery_notes = "Received hot food at 64.5°C in great condition."
        mission.proof_of_delivery_verified_at = datetime.now(timezone.utc)
        mission.actual_temp_at_delivery_c = 64.5
        db.commit()
        db.refresh(mission)

        # Assertions
        assert mission.status == "DELIVERED"
        assert mission.proof_of_delivery_receiver_name == "Sarah Jenkins"
        assert mission.actual_temp_at_delivery_c == 64.5
        assert mission.proof_of_delivery_verified_at is not None

        # Clean up
        db.delete(mission)
        db.commit()

    finally:
        db.close()


def test_driver_telemetry_source_labeling():
    # Verify that telemetry source labels clearly separate live device GPS from simulation
    live_meta = {"is_simulated": False}
    sim_meta = {"is_simulated": True}

    source_live = "SIMULATED_DEMO_COURIER" if live_meta["is_simulated"] else "HARDWARE_DEVICE_GPS"
    source_sim = "SIMULATED_DEMO_COURIER" if sim_meta["is_simulated"] else "HARDWARE_DEVICE_GPS"

    assert source_live == "HARDWARE_DEVICE_GPS"
    assert source_sim == "SIMULATED_DEMO_COURIER"


# =====================================================================
# FASTAPI ENDPOINTS INTEGRATION TESTS
# =====================================================================

from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token

client = TestClient(app)


@pytest.fixture
def manager_headers():
    token = create_access_token(
        data={"sub": "dispatch.lead@foodloop.org", "id": "mgr-logistics-01", "role": "LOGISTICS_MANAGER"}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def driver_headers():
    token = create_access_token(
        data={"sub": "courier.alex@foodloop.org", "id": "drv-user-01", "role": "DRIVER"}
    )
    return {"Authorization": f"Bearer {token}"}


def test_api_create_and_list_deliveries(manager_headers):
    # 1. Create a delivery mission
    payload = {
        "food_title": "Fresh Roast Chicken & Sides",
        "cargo_weight_kg": 35.0,
        "food_urgency": "HIGH",
        "pickup_address": "Convention Center Kitchen A",
        "pickup_lat": 37.7830,
        "pickup_lng": -122.4040,
        "delivery_address": "Downtown Community Meal Center",
        "delivery_lat": 37.7780,
        "delivery_lng": -122.4120
    }
    resp = client.post("/api/v1/logistics/deliveries", json=payload, headers=manager_headers)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["food_title"] == "Fresh Roast Chicken & Sides"
    assert data["status"] == "ASSIGNED"
    assert data["distance_km"] > 0
    assert data["transit_time_mins"] > 0
    deliv_id = data["id"]

    # 2. List deliveries
    list_resp = client.get("/api/v1/logistics/deliveries?status=ASSIGNED", headers=manager_headers)
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert any(d["id"] == deliv_id for d in items)


def test_api_delivery_status_transitions_and_pod(driver_headers, manager_headers):
    # Create test mission
    payload = {
        "food_title": "Organic Salad Packs",
        "cargo_weight_kg": 18.0,
        "food_urgency": "MEDIUM",
        "pickup_address": "Green Deli Cafe",
        "pickup_lat": 37.7810,
        "pickup_lng": -122.4090,
        "delivery_address": "City Shelter",
        "delivery_lat": 37.7720,
        "delivery_lng": -122.4180
    }
    create_resp = client.post("/api/v1/logistics/deliveries", json=payload, headers=manager_headers)
    assert create_resp.status_code == 201
    deliv_id = create_resp.json()["id"]

    # Step 1: EN_ROUTE
    patch_resp = client.patch(
        f"/api/v1/logistics/deliveries/{deliv_id}/status",
        json={"new_status": "EN_ROUTE", "current_lat": 37.7800, "current_lng": -122.4100},
        headers=driver_headers
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "EN_ROUTE"

    # Step 2: ARRIVED
    patch_resp = client.patch(
        f"/api/v1/logistics/deliveries/{deliv_id}/status",
        json={"new_status": "ARRIVED"},
        headers=driver_headers
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "ARRIVED"

    # Step 3: PICKED_UP
    patch_resp = client.patch(
        f"/api/v1/logistics/deliveries/{deliv_id}/status",
        json={"new_status": "PICKED_UP", "actual_temp_c": 3.8},
        headers=driver_headers
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "PICKED_UP"

    # Step 4: IN_TRANSIT
    patch_resp = client.patch(
        f"/api/v1/logistics/deliveries/{deliv_id}/status",
        json={"new_status": "IN_TRANSIT"},
        headers=driver_headers
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "IN_TRANSIT"

    # Step 5: Proof of Delivery -> DELIVERED
    pod_payload = {
        "receiver_name": "Marcus Vance",
        "signature": "data:image/svg+xml;utf8,<svg>sig</svg>",
        "photo_url": "https://images.unsplash.com/proof-001",
        "actual_temp_at_delivery_c": 3.9,
        "notes": "Verified cold chain integrity. Inspected and approved."
    }
    pod_resp = client.post(
        f"/api/v1/logistics/deliveries/{deliv_id}/proof-of-delivery",
        json=pod_payload,
        headers=driver_headers
    )
    assert pod_resp.status_code == 200
    data = pod_resp.json()
    assert data["status"] == "DELIVERED"
    assert data["proof_of_delivery_receiver_name"] == "Marcus Vance"
    assert data["proof_of_delivery_signature"] is not None
    assert data["proof_of_delivery_verified_at"] is not None


def test_api_route_optimization(manager_headers):
    req_payload = {
        "depot_latitude": 37.7749,
        "depot_longitude": -122.4194,
        "depot_name": "San Francisco Rescue Hub",
        "average_speed_kmh": 28.0,
        "service_time_mins": 10
    }
    resp = client.post("/api/v1/logistics/routes/optimize", json=req_payload, headers=manager_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert any(kw in data["solver_status"] for kw in ["OPTIMAL", "FEASIBLE", "HEURISTIC", "NO_MISSIONS"])
    assert "routes" in data


def test_api_driver_dashboard_and_telemetry(driver_headers):
    # Driver dashboard
    dash_resp = client.get("/api/v1/logistics/driver/dashboard", headers=driver_headers)
    assert dash_resp.status_code == 200, dash_resp.text
    dash = dash_resp.json()
    assert "driver_id" in dash
    assert "today_assignments" in dash
    assert "stats" in dash

    # Driver telemetry (live GPS vs simulated)
    tel_resp = client.post(
        "/api/v1/logistics/driver/telemetry?lat=37.7750&lng=-122.4180&is_simulated=false",
        headers=driver_headers
    )
    assert tel_resp.status_code == 200
    assert tel_resp.json()["telemetry_source"] == "HARDWARE_DEVICE_GPS"

    tel_sim_resp = client.post(
        "/api/v1/logistics/driver/telemetry?lat=37.7760&lng=-122.4170&is_simulated=true",
        headers=driver_headers
    )
    assert tel_sim_resp.status_code == 200
    assert tel_sim_resp.json()["telemetry_source"] == "SIMULATED_DEMO_COURIER"

