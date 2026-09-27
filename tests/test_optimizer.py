from app.services.optimizer import solve_dispatch_vrp, haversine_distance_km


def test_haversine_distance():
    # SF to Oakland approx 12-15 km
    dist = haversine_distance_km(37.7749, -122.4194, 37.8044, -122.2712)
    assert 10.0 <= dist <= 18.0


def test_solve_dispatch_vrp():
    depot = {
        "name": "Central Food Hub",
        "latitude": 37.7749,
        "longitude": -122.4194
    }
    pickups = [
        {
            "name": "Catering Hall",
            "address": "100 Grand Ave",
            "latitude": 37.7800,
            "longitude": -122.4100,
            "quantity_kg": 25.0,
            "food_title": "Warm Pasta Trays",
            "time_window_start_mins": 0,
            "time_window_end_mins": 120
        },
        {
            "name": "Organic Bakery",
            "address": "250 Mission St",
            "latitude": 37.7850,
            "longitude": -122.4050,
            "quantity_kg": 20.0,
            "food_title": "Artisan Bread",
            "time_window_start_mins": 0,
            "time_window_end_mins": 180
        }
    ]
    dropoffs = [
        {
            "name": "Shelter North",
            "address": "800 Folsom St",
            "latitude": 37.7780,
            "longitude": -122.4030,
            "quantity_kg": 25.0,
            "time_window_start_mins": 30,
            "time_window_end_mins": 240
        },
        {
            "name": "Community Pantry",
            "address": "1200 Howard St",
            "latitude": 37.7750,
            "longitude": -122.4120,
            "quantity_kg": 20.0,
            "time_window_start_mins": 30,
            "time_window_end_mins": 240
        }
    ]
    drivers = [
        {
            "id": "drv-1",
            "full_name": "Volunteer Courier 1",
            "vehicle_type": "van",
            "capacity_kg": 100.0
        }
    ]

    result = solve_dispatch_vrp(
        depot_location=depot,
        pickup_nodes=pickups,
        dropoff_nodes=dropoffs,
        drivers=drivers
    )

    assert result["solver_status"] in ["OPTIMAL", "OPTIMAL_ORTOOLS", "OPTIMAL_HEURISTIC"]
    assert result["num_vehicles_dispatched"] >= 1
    assert result["total_rescued_kg"] == 45.0
    assert result["total_distance_km"] > 0
    assert len(result["routes"]) >= 1
    # Check stop sequences
    route = result["routes"][0]
    assert len(route["stops"]) >= 4
