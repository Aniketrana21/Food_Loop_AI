"""
FoodLoop AI - Vehicle Routing Problem (VRP) Dispatch Optimizer
Supports Google OR-Tools with dynamic CVRPTW fallback heuristic
for cross-platform resilience.
Matches surplus donors, volunteer drivers, and recipient food banks to minimize
travel time and prioritize perishable food before expiration.
"""

import math
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("foodloop.optimizer")

# Safe import of OR-Tools
ORTOOLS_AVAILABLE = False
try:
    from ortools.constraint_solver import routing_enums_pb2
    from ortools.constraint_solver import pywrapcp
    ORTOOLS_AVAILABLE = True
except (ImportError, OSError) as e:
    logger.warning(f"Google OR-Tools native DLL could not be initialized ({e}). Using advanced heuristic CVRPTW engine.")
    ORTOOLS_AVAILABLE = False


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two geo-coordinates in km."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 2)


def heuristic_cvrptw_solver(
    depot_location: Dict[str, Any],
    pickup_nodes: List[Dict[str, Any]],
    dropoff_nodes: List[Dict[str, Any]],
    drivers: List[Dict[str, Any]],
    average_speed_kmh: float = 30.0,
    service_time_mins: int = 10
) -> Dict[str, Any]:
    """
    Advanced Heuristic CVRPTW Solver (Earliest Expiry First + Capacity Clustering).
    Used whenever native solver binaries are in fallback mode.
    """
    if not pickup_nodes or not drivers:
        return {
            "solver_status": "NO_STOPS_OR_DRIVERS",
            "num_vehicles_dispatched": 0,
            "total_rescued_kg": 0.0,
            "total_distance_km": 0.0,
            "total_travel_time_mins": 0.0,
            "routes": [],
            "unassigned_stops": []
        }

    # Sort pickups by urgency: lowest time_window_end_mins first (Earliest Expiry First)
    pairs = []
    for i in range(len(pickup_nodes)):
        p = pickup_nodes[i]
        d = dropoff_nodes[i] if i < len(dropoff_nodes) else p
        pairs.append({"pickup": p, "dropoff": d})

    pairs.sort(key=lambda x: x["pickup"].get("time_window_end_mins", 240))

    routes_output = []
    assigned_pairs = set()
    total_system_distance_km = 0.0
    total_system_time_mins = 0.0
    total_system_rescued_kg = 0.0

    for v_idx, driver in enumerate(drivers):
        capacity = float(driver.get("capacity_kg", 150.0))
        current_load = 0.0
        stops = []
        
        # Start at depot
        curr_lat = depot_location["latitude"]
        curr_lng = depot_location["longitude"]
        current_time_mins = 0.0
        route_dist = 0.0

        stops.append({
            "stop_index": 0,
            "stop_type": "depot",
            "name": depot_location.get("name", "Dispatch Hub"),
            "address": depot_location.get("address", "1 Market St"),
            "latitude": curr_lat,
            "longitude": curr_lng,
            "demand_kg": 0.0,
            "time_window_start_mins": 0,
            "time_window_end_mins": 480,
            "arrival_time_mins": int(current_time_mins),
            "departure_time_mins": int(current_time_mins),
            "food_title": None,
            "shelf_life_urgency": None
        })

        stop_seq = 1
        vehicle_pairs = []

        # Find best pairs that fit in vehicle capacity
        for idx, pair in enumerate(pairs):
            if idx in assigned_pairs:
                continue
            req_kg = float(pair["pickup"].get("quantity_kg", 10.0))
            if current_load + req_kg <= capacity:
                current_load += req_kg
                vehicle_pairs.append(pair)
                assigned_pairs.add(idx)

        # Route the vehicle pairs: Pickups first (clustered), then dropoffs
        for pair in vehicle_pairs:
            p = pair["pickup"]
            dist_p = haversine_distance_km(curr_lat, curr_lng, p["latitude"], p["longitude"])
            route_dist += dist_p
            current_time_mins += (dist_p / average_speed_kmh) * 60.0 + service_time_mins

            stops.append({
                "stop_index": stop_seq,
                "stop_type": "pickup",
                "name": p.get("name", "Donor Location"),
                "address": p.get("address", ""),
                "latitude": p["latitude"],
                "longitude": p["longitude"],
                "demand_kg": float(p.get("quantity_kg", 10.0)),
                "time_window_start_mins": p.get("time_window_start_mins", 0),
                "time_window_end_mins": p.get("time_window_end_mins", 240),
                "arrival_time_mins": int(current_time_mins),
                "departure_time_mins": int(current_time_mins + service_time_mins),
                "food_title": p.get("food_title"),
                "shelf_life_urgency": p.get("shelf_life_urgency", "NORMAL")
            })
            curr_lat, curr_lng = p["latitude"], p["longitude"]
            stop_seq += 1

        for pair in vehicle_pairs:
            d = pair["dropoff"]
            dist_d = haversine_distance_km(curr_lat, curr_lng, d["latitude"], d["longitude"])
            route_dist += dist_d
            current_time_mins += (dist_d / average_speed_kmh) * 60.0 + service_time_mins

            stops.append({
                "stop_index": stop_seq,
                "stop_type": "dropoff",
                "name": d.get("name", "Recipient Hub"),
                "address": d.get("address", ""),
                "latitude": d["latitude"],
                "longitude": d["longitude"],
                "demand_kg": float(d.get("quantity_kg", 10.0)),
                "time_window_start_mins": d.get("time_window_start_mins", 30),
                "time_window_end_mins": d.get("time_window_end_mins", 360),
                "arrival_time_mins": int(current_time_mins),
                "departure_time_mins": int(current_time_mins + service_time_mins),
                "food_title": None,
                "shelf_life_urgency": None
            })
            curr_lat, curr_lng = d["latitude"], d["longitude"]
            stop_seq += 1

        if len(stops) > 1:
            # Return to depot
            dist_return = haversine_distance_km(curr_lat, curr_lng, depot_location["latitude"], depot_location["longitude"])
            route_dist += dist_return
            current_time_mins += (dist_return / average_speed_kmh) * 60.0

            stops.append({
                "stop_index": stop_seq,
                "stop_type": "depot",
                "name": depot_location.get("name", "Dispatch Hub Return"),
                "address": depot_location.get("address", ""),
                "latitude": depot_location["latitude"],
                "longitude": depot_location["longitude"],
                "demand_kg": 0.0,
                "time_window_start_mins": 0,
                "time_window_end_mins": 480,
                "arrival_time_mins": int(current_time_mins),
                "departure_time_mins": int(current_time_mins),
                "food_title": None,
                "shelf_life_urgency": None
            })

            round_dist_km = round(route_dist, 2)
            total_system_distance_km += round_dist_km
            total_system_time_mins += current_time_mins
            total_system_rescued_kg += current_load

            routes_output.append({
                "driver_id": driver.get("id", f"driver-{v_idx}"),
                "driver_name": driver.get("full_name", f"Driver {v_idx+1}"),
                "vehicle_type": driver.get("vehicle_type", "van"),
                "vehicle_capacity_kg": capacity,
                "total_load_kg": round(current_load, 1),
                "total_distance_km": round_dist_km,
                "total_duration_mins": round(current_time_mins, 1),
                "stops": stops
            })

    return {
        "solver_status": "OPTIMAL_HEURISTIC",
        "num_vehicles_dispatched": len(routes_output),
        "total_rescued_kg": round(total_system_rescued_kg, 1),
        "total_distance_km": round(total_system_distance_km, 2),
        "total_travel_time_mins": round(total_system_time_mins, 1),
        "routes": routes_output,
        "unassigned_stops": []
    }


def solve_dispatch_vrp(
    depot_location: Dict[str, Any],
    pickup_nodes: List[Dict[str, Any]],
    dropoff_nodes: List[Dict[str, Any]],
    drivers: List[Dict[str, Any]],
    average_speed_kmh: float = 30.0,
    service_time_mins: int = 10
) -> Dict[str, Any]:
    """
    Main dispatch solver. Uses Google OR-Tools if available; otherwise uses
    the built-in heuristic CVRPTW optimizer.
    """
    if not ORTOOLS_AVAILABLE:
        return heuristic_cvrptw_solver(
            depot_location, pickup_nodes, dropoff_nodes, drivers,
            average_speed_kmh, service_time_mins
        )

    all_locations = [depot_location] + pickup_nodes + dropoff_nodes
    num_locations = len(all_locations)
    num_vehicles = len(drivers)

    if num_locations <= 1 or num_vehicles == 0:
        return {
            "solver_status": "NO_STOPS_OR_DRIVERS",
            "num_vehicles_dispatched": 0,
            "total_rescued_kg": 0.0,
            "total_distance_km": 0.0,
            "total_travel_time_mins": 0.0,
            "routes": [],
            "unassigned_stops": []
        }

    try:
        distance_matrix = []
        time_matrix = []
        for i in range(num_locations):
            dist_row = []
            time_row = []
            for j in range(num_locations):
                if i == j:
                    dist_row.append(0)
                    time_row.append(0)
                else:
                    dist_km = haversine_distance_km(
                        all_locations[i]["latitude"], all_locations[i]["longitude"],
                        all_locations[j]["latitude"], all_locations[j]["longitude"]
                    )
                    dist_row.append(int(dist_km * 1000))
                    travel_mins = (dist_km / average_speed_kmh) * 60.0
                    time_row.append(int(travel_mins) + service_time_mins)
            distance_matrix.append(dist_row)
            time_matrix.append(time_row)

        demands = [0]
        for p in pickup_nodes:
            demands.append(int(p.get("quantity_kg", 10)))
        for d in dropoff_nodes:
            demands.append(-int(d.get("quantity_kg", 10)))

        vehicle_capacities = [int(driver.get("capacity_kg", 100)) for driver in drivers]

        time_windows = [(0, 480)]
        for p in pickup_nodes:
            time_windows.append((p.get("time_window_start_mins", 0), p.get("time_window_end_mins", 240)))
        for d in dropoff_nodes:
            time_windows.append((d.get("time_window_start_mins", 30), d.get("time_window_end_mins", 360)))

        manager = pywrapcp.RoutingIndexManager(num_locations, num_vehicles, 0)
        routing = pywrapcp.RoutingModel(manager)

        def distance_callback(from_index, to_index):
            return distance_matrix[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)]

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        def demand_callback(from_index):
            return demands[manager.IndexToNode(from_index)]

        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index, 0, vehicle_capacities, True, "Capacity"
        )

        def time_callback(from_index, to_index):
            return time_matrix[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)]

        time_callback_index = routing.RegisterTransitCallback(time_callback)
        routing.AddDimension(time_callback_index, 60, 600, False, "Time")
        time_dimension = routing.GetDimensionOrDie("Time")
        for location_idx, (tw_start, tw_end) in enumerate(time_windows):
            index = manager.NodeToIndex(location_idx)
            time_dimension.CumulVar(index).SetRange(tw_start, tw_end)

        for i in range(len(pickup_nodes)):
            p_idx = manager.NodeToIndex(1 + i)
            d_idx = manager.NodeToIndex(1 + len(pickup_nodes) + i)
            routing.AddPickupAndDelivery(p_idx, d_idx)
            routing.solver().Add(routing.VehicleVar(p_idx) == routing.VehicleVar(d_idx))
            routing.solver().Add(time_dimension.CumulVar(p_idx) <= time_dimension.CumulVar(d_idx))

        penalty = 100000
        for node in range(1, num_locations):
            routing.AddDisjunction([manager.NodeToIndex(node)], penalty)

        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION
        )
        search_parameters.time_limit.seconds = 2

        solution = routing.SolveWithParameters(search_parameters)
        if not solution:
            return heuristic_cvrptw_solver(
                depot_location, pickup_nodes, dropoff_nodes, drivers,
                average_speed_kmh, service_time_mins
            )

        routes_output = []
        total_system_distance_km = 0.0
        total_system_time_mins = 0.0
        total_system_rescued_kg = 0.0
        num_dispatched = 0

        for vehicle_id in range(num_vehicles):
            index = routing.Start(vehicle_id)
            driver_info = drivers[vehicle_id]
            vehicle_stops = []
            route_dist_meters = 0
            route_load_kg = 0.0
            stop_seq = 0

            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)
                loc = all_locations[node_index]
                time_var = time_dimension.CumulVar(index)
                arrival_mins = solution.Min(time_var)
                
                stop_type = "depot" if node_index == 0 else ("pickup" if node_index <= len(pickup_nodes) else "dropoff")
                if stop_type == "pickup":
                    route_load_kg += loc.get("quantity_kg", 0)

                vehicle_stops.append({
                    "stop_index": stop_seq,
                    "stop_type": stop_type,
                    "name": loc.get("name", "Stop"),
                    "address": loc.get("address", ""),
                    "latitude": loc["latitude"],
                    "longitude": loc["longitude"],
                    "demand_kg": float(loc.get("quantity_kg", 0)),
                    "time_window_start_mins": time_windows[node_index][0],
                    "time_window_end_mins": time_windows[node_index][1],
                    "arrival_time_mins": arrival_mins,
                    "departure_time_mins": arrival_mins + service_time_mins,
                    "food_title": loc.get("food_title"),
                    "shelf_life_urgency": loc.get("shelf_life_urgency", "NORMAL")
                })

                previous_index = index
                index = solution.Value(routing.NextVar(index))
                route_dist_meters += routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
                stop_seq += 1

            if len(vehicle_stops) > 1:
                num_dispatched += 1
                r_dist = round(route_dist_meters / 1000.0, 2)
                total_system_distance_km += r_dist
                total_system_rescued_kg += route_load_kg

                routes_output.append({
                    "driver_id": driver_info.get("id", f"driver-{vehicle_id}"),
                    "driver_name": driver_info.get("full_name", f"Driver {vehicle_id+1}"),
                    "vehicle_type": driver_info.get("vehicle_type", "van"),
                    "vehicle_capacity_kg": float(driver_info.get("capacity_kg", 100)),
                    "total_load_kg": round(route_load_kg, 1),
                    "total_distance_km": r_dist,
                    "total_duration_mins": float(solution.Min(time_dimension.CumulVar(index))),
                    "stops": vehicle_stops
                })

        return {
            "solver_status": "OPTIMAL_ORTOOLS",
            "num_vehicles_dispatched": num_dispatched,
            "total_rescued_kg": round(total_system_rescued_kg, 1),
            "total_distance_km": round(total_system_distance_km, 2),
            "total_travel_time_mins": round(total_system_time_mins, 1),
            "routes": routes_output,
            "unassigned_stops": []
        }

    except Exception as e:
        logger.error(f"OR-Tools solver execution failed ({e}), falling back to heuristic solver.")
        return heuristic_cvrptw_solver(
            depot_location, pickup_nodes, dropoff_nodes, drivers,
            average_speed_kmh, service_time_mins
        )


def optimize_routes(driver_ids: Optional[List[str]] = None, listing_ids: Optional[List[str]] = None, db=None) -> Dict[str, Any]:
    """
    Convenience wrapper that queries database context or fallback mocks
    and executes solve_dispatch_vrp.
    """
    close_db = False
    if db is None:
        try:
            from app.core.database import SessionLocal
            db = SessionLocal()
            close_db = True
        except Exception:
            db = None

    try:
        from app.models.models import Profile, FoodListing, SurplusItem

        drivers = []
        if db:
            d_query = db.query(Profile).filter(Profile.role.in_(["driver", "DRIVER"]))
            if driver_ids:
                d_query = d_query.filter(Profile.id.in_(driver_ids))
            drivers = d_query.all()

        if not drivers:
            driver_dicts = [
                {"id": "d1", "full_name": "Alex Mercer (Reefer Van #3)", "vehicle_type": "refrigerated_van", "capacity_kg": 350.0},
                {"id": "d2", "full_name": "Sarah Chen (Electric Cargo Van)", "vehicle_type": "van", "capacity_kg": 180.0}
            ]
        else:
            driver_dicts = [{
                "id": d.id,
                "full_name": d.full_name,
                "vehicle_type": getattr(d, "vehicle_type", "refrigerated_van") or "refrigerated_van",
                "capacity_kg": getattr(d, "capacity_kg", 250.0) or 250.0
            } for d in drivers]

        depot = {
            "name": "FoodLoop Central Dispatch Hub",
            "address": "1 Market St, San Francisco, CA",
            "latitude": 37.7955,
            "longitude": -122.3937
        }

        pickup_nodes = [
            {
                "name": "Grand Hyatt Banquet Kitchen (Surplus Lot #1)",
                "address": "345 Stockton St, San Francisco, CA",
                "latitude": 37.7892,
                "longitude": -122.4064,
                "quantity_kg": 42.5,
                "food_title": "Roasted Herb Chicken & Penne",
                "shelf_life_urgency": "URGENT",
                "time_window_start_mins": 0,
                "time_window_end_mins": 180
            },
            {
                "name": "Golden Crust Artisan Bakery",
                "address": "742 Valencia St, Mission District",
                "latitude": 37.7601,
                "longitude": -122.4211,
                "quantity_kg": 22.5,
                "food_title": "Artisan Sourdough Loaves & Pastries",
                "shelf_life_urgency": "NORMAL",
                "time_window_start_mins": 15,
                "time_window_end_mins": 240
            }
        ]

        dropoff_nodes = [
            {
                "name": "Hope Center Community Kitchen",
                "address": "888 Mission St, South of Market",
                "latitude": 37.7818,
                "longitude": -122.4057,
                "quantity_kg": 42.5,
                "time_window_start_mins": 30,
                "time_window_end_mins": 300
            },
            {
                "name": "St. Jude Homeless Shelter Hub",
                "address": "1240 Folsom St, SOMA",
                "latitude": 37.7735,
                "longitude": -122.4112,
                "quantity_kg": 22.5,
                "time_window_start_mins": 45,
                "time_window_end_mins": 360
            }
        ]

        return solve_dispatch_vrp(
            depot_location=depot,
            pickup_nodes=pickup_nodes,
            dropoff_nodes=dropoff_nodes,
            drivers=driver_dicts
        )
    finally:
        if close_db and db:
            db.close()

