"""
FoodLoop AI - Phase 10 Logistics, Fleet, and Route Optimization Schemas
Pydantic contracts for delivery missions, driver assignments,
8-state lifecycle transitions, proof of delivery, and OR-Tools optimization.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

LOGISTICS_STATUSES = [
    "ASSIGNED",
    "EN_ROUTE",
    "ARRIVED",
    "PICKED_UP",
    "IN_TRANSIT",
    "DELIVERED",
    "FAILED",
    "CANCELLED"
]


class WaypointOut(BaseModel):
    stop_sequence: int
    stop_type: str  # 'depot' | 'pickup' | 'delivery'
    name: str
    address: str
    latitude: float
    longitude: float
    cargo_weight_kg: float
    cumulative_load_kg: float
    arrival_time_mins: int
    departure_time_mins: int
    eta_time_str: str
    food_title: Optional[str] = None
    food_urgency: Optional[str] = None
    delivery_id: Optional[str] = None


class VehicleRouteOut(BaseModel):
    vehicle_id: str
    driver_id: str
    driver_name: str
    license_plate: str
    vehicle_capacity_kg: float
    total_load_kg: float
    total_distance_km: float
    total_duration_mins: float
    waypoints: List[WaypointOut]


class RouteOptimizationResponse(BaseModel):
    solver_status: str
    solver_model: str
    num_vehicles_dispatched: int
    total_rescued_kg: float
    total_distance_km: float
    total_travel_time_mins: float
    routes: List[VehicleRouteOut]
    unassigned_missions: List[str]


class RouteOptimizationRequest(BaseModel):
    depot_latitude: float = 37.7749
    depot_longitude: float = -122.4194
    depot_name: str = "Regional FoodLoop Dispatch Hub"
    depot_address: str = "100 Logistics Way, San Francisco, CA"
    delivery_ids: Optional[List[str]] = None
    average_speed_kmh: float = 28.0
    service_time_mins: int = 10


class DeliveryCreatePayload(BaseModel):
    food_title: str
    cargo_weight_kg: float
    food_urgency: str = "MEDIUM"
    pickup_address: str
    pickup_lat: float
    pickup_lng: float
    delivery_address: str
    delivery_lat: float
    delivery_lng: float
    scheduled_pickup_time: Optional[datetime] = None
    scheduled_delivery_time: Optional[datetime] = None
    surplus_item_id: Optional[str] = None
    driver_id: Optional[str] = None
    vehicle_id: Optional[str] = None


class DeliveryStatusTransitionPayload(BaseModel):
    new_status: str = Field(..., description="Must be one of the 8 logistics statuses")
    current_lat: Optional[float] = None
    current_lng: Optional[float] = None
    notes: Optional[str] = None
    actual_temp_c: Optional[float] = None


class ProofOfDeliveryPayload(BaseModel):
    receiver_name: str
    signature: Optional[str] = None
    photo_url: Optional[str] = None
    actual_temp_at_delivery_c: Optional[float] = None
    notes: Optional[str] = None


class DeliveryRecordOut(BaseModel):
    id: str
    food_title: str
    cargo_weight_kg: float
    food_urgency: str
    status: str
    pickup_address: str
    pickup_lat: float
    pickup_lng: float
    delivery_address: str
    delivery_lat: float
    delivery_lng: float
    scheduled_pickup_time: Optional[datetime] = None
    scheduled_delivery_time: Optional[datetime] = None
    estimated_arrival_time: Optional[datetime] = None
    distance_km: float
    transit_time_mins: float
    stop_sequence: int
    driver_id: Optional[str] = None
    vehicle_id: Optional[str] = None
    proof_of_delivery_receiver_name: Optional[str] = None
    proof_of_delivery_signature: Optional[str] = None
    proof_of_delivery_photo: Optional[str] = None
    proof_of_delivery_notes: Optional[str] = None
    proof_of_delivery_verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class DriverDashboardResponse(BaseModel):
    driver_id: str
    driver_name: str
    license_number: str
    driver_status: str
    current_lat: float
    current_lng: float
    vehicle: Optional[Dict[str, Any]] = None
    today_assignments: List[DeliveryRecordOut]
    active_route: Optional[VehicleRouteOut] = None
    stats: Dict[str, Any]
