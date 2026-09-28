export type UserRole = 'donor' | 'recipient' | 'driver' | 'admin';

export interface Profile {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  organization_name?: string;
  organization_type?: string;
  phone?: string;
  address?: string;
  latitude?: number;
  longitude?: number;
  vehicle_type?: string;
  capacity_kg?: number;
  avatar_url?: string;
}

export interface FoodListing {
  id: string;
  donor_id: string;
  title: string;
  description: string;
  category: 'cooked_meals' | 'bakery' | 'dairy' | 'fresh_produce' | 'packaged_goods' | 'meat_seafood';
  quantity_kg: number;
  portions: number;
  packaging_type: string;
  storage_temp: 'room_temp' | 'refrigerated' | 'frozen';
  expiry_at: string;
  pickup_start: string;
  pickup_end: string;
  pickup_address: string;
  pickup_lat: number;
  pickup_lng: number;
  dietary_tags: string[];
  status: 'available' | 'reserved' | 'completed' | 'expired';
  estimated_shelf_life_hours?: number;
  photo_url?: string;
  created_at: string;
  donor?: Profile;
}

export interface RescueClaim {
  id: string;
  listing_id: string;
  recipient_id: string;
  status: 'pending' | 'approved' | 'driver_assigned' | 'delivered' | 'rejected';
  claimed_portions: number;
  claimed_quantity_kg: number;
  delivery_type: string;
  notes?: string;
  created_at: string;
  listing?: FoodListing;
  recipient?: Profile;
}

export interface RouteStop {
  stop_index: number;
  stop_type: 'depot' | 'pickup' | 'dropoff';
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  demand_kg: number;
  arrival_time_mins: number;
  departure_time_mins: number;
  food_title?: string;
  shelf_life_urgency?: string;
}

export interface DriverVehicleRoute {
  driver_id: string;
  driver_name: string;
  vehicle_type: string;
  vehicle_capacity_kg: number;
  total_load_kg: number;
  total_distance_km: number;
  total_duration_mins: number;
  stops: RouteStop[];
}

export interface OptimizationResult {
  solver_status: string;
  num_vehicles_dispatched: number;
  total_rescued_kg: number;
  total_distance_km: number;
  total_travel_time_mins: number;
  routes: DriverVehicleRoute[];
}

export interface ImpactSummary {
  total_food_diverted_kg: number;
  total_meals_provided: number;
  total_co2_avoided_kg: number;
  total_water_saved_liters: number;
  total_economic_value_usd: number;
  active_rescues_count: number;
  leaderboard: Array<{
    name: string;
    meals_donated: number;
    co2_saved_kg: number;
  }>;
}

// ==========================================
// PHASE 4: INSTITUTIONAL KITCHEN OPERATIONS
// ==========================================

export interface KitchenProfile {
  id: string;
  name: string;
  organization_id?: string;
  facility_type: string;
  daily_meal_capacity: number;
  contact_email?: string;
  contact_phone?: string;
  operating_hours?: string;
  certifications?: string[];
  status?: string;
}

export interface KitchenStaffMember {
  id: string;
  name: string;
  email: string;
  role: string;
  department?: string;
  shift?: string;
  phone?: string;
}

export type StorageType = 'DRY' | 'REFRIGERATED' | 'FROZEN' | 'WARM_HOLDING' | 'HOT_HOLD' | 'ROOM_TEMP';
export type InventoryStatus = 'ACTIVE' | 'LOW_STOCK' | 'EXPIRED' | 'DEPLETED' | 'QUARANTINED';

export type InventoryTransactionType =
  | 'PURCHASE'
  | 'CONSUMPTION'
  | 'PRODUCTION'
  | 'ADJUSTMENT'
  | 'WASTE'
  | 'TRANSFER'
  | 'DONATION';

export interface InventoryItemLot {
  id: string;
  organization_id?: string;
  kitchen_id?: string;
  ingredient_name: string;
  ingredient_id?: string;
  category?: string;
  quantity: number;
  unit: string;
  batch_number: string;
  purchase_date?: string;
  expiry_date?: string;
  storage_type: StorageType | string;
  supplier?: string;
  cost_per_unit: number;
  status: InventoryStatus | string;
  minimum_threshold?: number;
  reorder_level?: number;
  created_at?: string;
}

export interface PurchaseOrderItem {
  ingredient_name: string;
  quantity: number;
  unit: string;
  cost_per_unit: number;
  batch_number?: string;
  supplier?: string;
  expiry_date?: string;
  storage_type?: string;
}

export interface PurchaseRecord {
  id: string;
  kitchen_id: string;
  supplier: string;
  purchase_date: string;
  invoice_number?: string;
  total_cost_usd: number;
  items_count: number;
  items?: PurchaseOrderItem[];
  created_at?: string;
}

export interface IngredientCatalogItem {
  id: string;
  name: string;
  category: string;
  default_unit: string;
  cost_per_unit?: number;
  storage_temp?: string;
  reorder_point?: number;
  supplier_name?: string;
}

export interface MenuItemRecord {
  id: string;
  menu_id?: string;
  name: string;
  category?: string;
  serving_size_grams: number;
  cost_per_serving_usd: number;
  description?: string;
  allergens?: string[];
  dietary_tags?: string[];
  storage_temp_requirement?: string;
  planned_portions?: number;
}

export interface MenuRecord {
  id: string;
  kitchen_id: string;
  name: string;
  season_or_cycle?: string;
  is_active: boolean;
  effective_date?: string;
  items: MenuItemRecord[];
  created_at?: string;
}

export interface ProductionBatchRecord {
  id: string;
  kitchen_id: string;
  batch_code: string;
  menu_item_id?: string;
  dish_name?: string;
  status: 'PLANNED' | 'PREPPING' | 'COOKING' | 'HOLDING' | 'COMPLETED' | 'CANCELLED';
  planned_portions: number;
  actual_portions_prepped?: number;
  cooking_start_time?: string;
  holding_temperature_c?: number;
  target_temp_c?: number;
  station_assigned?: string;
  head_chef?: string;
  notes?: string;
  created_at?: string;
}

export interface ConsumptionRecordItem {
  id: string;
  kitchen_id: string;
  production_batch_id?: string;
  dish_name?: string;
  meal_service: string;
  service_date: string;
  headcount_planned: number;
  headcount_served: number;
  portions_consumed: number;
  variance_pct: number;
  surplus_weight_kg: number;
  leftover_status?: 'ROUTED_TO_SURPLUS' | 'ROUTED_TO_WASTE' | 'PENDING';
  notes?: string;
  created_at?: string;
}

export type WasteCategory =
  | 'OVERPRODUCTION'
  | 'PLATE_WASTE'
  | 'SPOILAGE'
  | 'EXPIRED'
  | 'PREPARATION_WASTE'
  | 'DAMAGED'
  | 'QUALITY_REJECTION'
  | 'OTHER';

export interface WasteRecordItem {
  id: string;
  organization_id?: string;
  kitchen_id?: string;
  food_item: string;
  quantity: number;
  unit: string;
  reason: string;
  category: WasteCategory;
  date: string;
  production_batch?: string;
  notes?: string;
  image_url?: string;
  responsible_organization?: string;
  waste_cost?: number;
  epa_waste_tier?: string;
  created_at?: string;
}

export interface WasteAnalytics {
  daily_waste: Array<{ label: string; date: string; quantity_kg: number; cost_usd: number }>;
  weekly_waste: Array<{ label: string; quantity_kg: number; cost_usd: number }>;
  monthly_waste: Array<{ label: string; quantity_kg: number; cost_usd: number }>;
  waste_by_category: Array<{ category: string; quantity_kg: number; cost_usd: number; percentage: number }>;
  waste_by_food_item: Array<{ food_item: string; quantity_kg: number; cost_usd: number; occurrences: number }>;
  total_waste_kg: number;
  waste_cost: number;
  waste_trend: number;
  waste_trend_pct: number;
  reduction_target_pct: number;
  active_records_count: number;
  epa_tier_breakdown: Record<string, number>;
}

// ==========================================
// PHASE 5: AI DEMAND FORECASTING TYPES
// ==========================================

export interface DemandForecastRequest {
  kitchen_id?: string;
  target_date?: string;
  planned_attendance?: number;
  historical_consumption?: number[];
  day_of_week?: number;
  meal_type?: string;
  is_special_event?: number;
  temperature_c?: number;
  precipitation_mm?: number;
  menu_name?: string;
}

export interface DemandForecastResponse {
  expected_demand: number;
  recommended_range: {
    lower: number;
    upper: number;
  };
  confidence: number;
  model_version: string;
  recommended_production: number;
  buffer_portions: number;
  is_baseline: boolean;
  baseline_explanation?: string | null;
  target_date?: string;
  day_name?: string;
  season?: string;
  features_summary?: Record<string, any>;
}

export interface ModelMetricRow {
  model: string;
  mae: number;
  rmse: number;
  mape_pct: number;
  r2_score: number;
}

export interface ModelRegistryInfo {
  model_version: string;
  champion_model_name: string;
  training_date: string;
  dataset_version: string;
  dataset_records_count: number;
  split_counts?: {
    train: number;
    validation: number;
    out_of_sample_test: number;
  };
  features: string[];
  features_count: number;
  residual_std: number;
  leaderboard: ModelMetricRow[];
  metrics_summary: Record<string, any>;
  baseline_benchmarks?: {
    pct_reduction_vs_naive?: number;
    pct_reduction_vs_moving_average?: number;
  };
}

export interface EvaluationPoint {
  date: string;
  actual: number;
  predicted: number;
  lower_bound?: number;
  upper_bound?: number;
  error?: number;
  abs_error_pct?: number;
}

export interface ModelEvaluationsInfo {
  series: EvaluationPoint[];
  historical_accuracy: {
    mae_portions: number;
    rmse_portions: number;
    mape_percentage: number;
    accuracy_percentage: number;
    r2_score: number;
  };
  baseline_comparison: {
    naive_baseline_mae: number;
    moving_average_mae: number;
    random_forest_mae: number;
    xgboost_mae: number;
    reduction_in_error_pct: number;
  };
}

// ==========================================
// PHASE 6: AI PRE-PRODUCTION WASTE PREDICTION TYPES
// ==========================================

export interface PreProductionWastePredictRequest {
  food_item: string;
  food_category: string;
  menu?: string;
  kitchen?: string;
  predicted_demand: number;
  planned_production: number;
  historical_waste?: number;
  day_of_week?: number;
  meal_type?: string;
  attendance?: number;
  season?: string;
}

export interface PreProductionWastePredictResponse {
  waste_probability: number;
  predicted_waste_quantity: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  top_contributing_factors: string[];
  recommendation: string;
  model_architecture?: string;
  model_version?: string;
  prediction_type?: string;
  deterministic_rule_check?: {
    is_deterministic_rule: boolean;
    regulatory_code: string;
    standard_discard_hours: number;
    rule_statement: string;
    distinction_note: string;
  };
  batch_summary?: {
    food_item: string;
    food_category: string;
    planned_production: number;
    predicted_demand: number;
    excess_buffer_portions: number;
  };
}

export interface WasteModelBenchmarkInfo {
  model_version: string;
  classifier_metrics: {
    logistic_regression: { accuracy: number; roc_auc: number; precision: number; recall: number; f1_score: number };
    random_forest: { accuracy: number; roc_auc: number; precision: number; recall: number; f1_score: number };
    xgboost: { accuracy: number; roc_auc: number; precision: number; recall: number; f1_score: number };
  };
  regressor_metrics: {
    ridge_regression: { mae_kg: number; rmse_kg: number; mape_pct: number; r2_score: number };
    random_forest_reg: { mae_kg: number; rmse_kg: number; mape_pct: number; r2_score: number };
    xgboost_reg: { mae_kg: number; rmse_kg: number; mape_pct: number; r2_score: number };
  };
  features: string[];
  sample_evaluations?: Array<{
    date: string;
    food_item: string;
    food_category: string;
    predicted_demand: number;
    planned_production: number;
    actual_waste_kg: number;
    predicted_waste_kg: number;
    waste_probability: number;
    risk_level: string;
  }>;
}

// ==========================================
// PHASE 7: PRODUCTION OPTIMIZER TYPES (OR-TOOLS)
// ==========================================

export interface ProductionOptimizeRequest {
  dish_name?: string;
  menu?: string;
  demand_forecast: number;
  confidence_interval?: { lower?: number; upper?: number; low?: number; high?: number; confidence_level?: number };
  inventory: number;
  ingredient_availability: number;
  kitchen_capacity: number;
  historical_waste?: number;
  food_cost?: number;
  minimum_required_demand?: number;
  maximum_production_capacity?: number;
  holding_time_limit_hours?: number;
  inventory_age_hours?: number;
  food_category?: string;
  unit_waste_cost?: number;
  unit_shortage_cost?: number;
}

export interface ProductionOptimizeResponse {
  feasible: boolean;
  status: string;
  recommended_production: number;
  total_available_portions: number;
  expected_demand: number;
  expected_surplus: number;
  expected_shortage_risk: number;
  estimated_waste: number;
  estimated_waste_kg: number;
  estimated_cost: {
    production_cost_usd: number;
    expected_waste_cost_usd: number;
    expected_shortage_cost_usd: number;
    total_expected_cost_usd: number;
  };
  reasoning: string[];
  constraints_summary: {
    kitchen_capacity: number;
    ingredient_availability: number;
    minimum_required_demand: number;
    usable_inventory: number;
    maximum_production_capacity: number;
    is_capacity_binding?: boolean;
    is_ingredient_binding?: boolean;
    is_minimum_service_binding?: boolean;
    unmet_service_portions?: number;
  };
  infeasibility_details?: {
    is_infeasible: boolean;
    root_cause_conflicts: string[];
    actionable_bottleneck_resolutions: string[];
    warning_message: string;
  } | null;
  scenarios_evaluated?: Array<{
    demand: number;
    prob: number;
    label: string;
  }>;
  solver?: string;
}

export interface WhatIfSimulationRequest {
  attendance: number;
  menu: string;
  production: number;
  inventory: number;
  dish_name?: string;
  food_category?: string;
  food_cost?: number;
  kitchen_capacity?: number;
  ingredient_availability?: number;
  minimum_required_demand?: number;
  maximum_production_capacity?: number;
  holding_time_limit_hours?: number;
  inventory_age_hours?: number;
}

export interface WhatIfSimulationResponse {
  simulation_inputs: {
    attendance: number;
    menu: string;
    planned_production: number;
    inventory: number;
    dish_name: string;
    food_category: string;
    food_cost: number;
  };
  expected_demand: number;
  recommended_production: number;
  predicted_waste_portions: number;
  predicted_waste_kg: number;
  estimated_cost: {
    production_cost_usd: number;
    expected_waste_cost_usd: number;
    expected_shortage_cost_usd: number;
    total_expected_cost_usd: number;
  };
  shortage_risk_pct: number;
  comparison_vs_planned: {
    planned_production: number;
    planned_available_portions: number;
    planned_waste_kg: number;
    planned_cost_usd: number;
    waste_saved_kg: number;
    cost_saved_usd: number;
    is_optimizer_better: boolean;
  };
  optimization_result: ProductionOptimizeResponse;
  sensitivity_curve: Array<{
    shift_percentage: number;
    attendance: number;
    expected_demand: number;
    recommended_production: number;
    predicted_waste_kg: number;
    total_cost_usd: number;
    feasible: boolean;
  }>;
}

// ==========================================
// PHASE 8: REAL-TIME SURPLUS MANAGEMENT TYPES
// ==========================================

export type SurplusStatus = 
  | 'AVAILABLE'
  | 'RESERVED'
  | 'PICKUP_SCHEDULED'
  | 'PICKED_UP'
  | 'IN_TRANSIT'
  | 'DELIVERED'
  | 'RECEIVED'
  | 'EXPIRED'
  | 'CANCELLED';

export type SurplusUrgency = 
  | 'CRITICAL'
  | 'HIGH'
  | 'MEDIUM'
  | 'LOW'
  | 'EXPIRED';

export type SurplusEligibility = 
  | 'ELIGIBLE_FOR_DONATION'
  | 'NEEDS_HUMAN_INSPECTION'
  | 'INELIGIBLE_EXPIRED'
  | 'INELIGIBLE_TEMPERATURE_ABUSE'
  | 'INELIGIBLE_HOLDING_TIME_EXCEEDED';

export interface SurplusRecordCreate {
  food: string;
  quantity: number;
  unit: string;
  prepared_at: string;
  storage_type: StorageType;
  temperature?: number | null;
  batch?: string | null;
  best_use_before?: string | null;
  notes?: string | null;
  image?: string | null;
  location?: string | null;
  category?: string | null;
}

export interface SurplusRecordOut {
  id: string;
  food: string;
  quantity: number;
  unit: string;
  prepared_at?: string | null;
  storage_type: StorageType;
  temperature?: number | null;
  batch?: string | null;
  best_use_before?: string | null;
  notes?: string | null;
  image?: string | null;
  status: SurplusStatus;
  location: string;

  // Real-Time Computed Card Metrics
  age_hours: number;
  age_formatted: string;
  remaining_safe_window_minutes: number;
  remaining_safe_window_formatted: string;
  urgency: SurplusUrgency;
  eligibility: SurplusEligibility;
  required_action: string;
  suggested_waste_workflow?: string | null;
  human_approval_required: boolean;
  approved_by?: string | null;
  approval_status?: string | null;
  approval_notes?: string | null;
  safety_rule_applied?: string | null;

  created_at: string;
  updated_at: string;
}

export interface RecipientMatchItem {
  recipient_id: string;
  organization_name: string;
  organization_type: string;
  address: string;
  distance_km: number;
  estimated_transit_minutes: number;
  capacity_portions: number;
  match_score: number;
  contact_person: string;
  phone: string;
  readiness: string;
  can_receive_immediately: boolean;
  safe_margin_minutes: number;
}

export interface LiveSurplusDashboardSummary {
  total_active_lots: number;
  available_lots_count: number;
  critical_urgency_count: number;
  expired_lots_count: number;
  total_available_quantity_kg: number;
  items: SurplusRecordOut[];
  urgent_alerts: Array<{
    surplus_id: string;
    food: string;
    urgency: string;
    remaining_window: string;
    location: string;
    action: string;
    suggested_waste_workflow?: string;
    alert_type: string;
  }>;
}

export interface HumanApprovalRequest {
  approved: boolean;
  notes: string;
  verified_temp?: number | null;
}

export interface FoodSafetyRulesConfig {
  hot_hold_min_temp_c: number;
  hot_hold_max_hours: number;
  cold_hold_max_temp_c: number;
  cold_hold_cooked_max_hours: number;
  cold_hold_dairy_produce_max_hours: number;
  frozen_max_temp_c: number;
  frozen_max_hours: number;
  room_temp_max_hours: number;
  minimum_dispatch_window_minutes: number;
  manager_approval_threshold_minutes: number;
}

// ====================================================================
// PHASE 9: RECIPIENT MATCHING & DASHBOARD TYPES
// ====================================================================

export interface MatchingFactors {
  food_compatibility: number;
  capacity: number;
  distance: number;
  urgency: number;
  pickup_availability: number;
  storage_compatibility: number;
  operational_reliability: number;
}

export interface RecipientMatchCandidate {
  recipient_id: string;
  organization_name: string;
  facility_type: string;
  address: string;
  contact_person?: string;
  contact_phone?: string;
  distance_km: number;
  estimated_transit_minutes: number;
  overall_match_score: number;
  factors: MatchingFactors;
  explanation_bullets: string[];
  recommendation_summary: string;
  is_feasible: boolean;
  can_intake_immediately: boolean;
  requires_delivery: boolean;
  operating_hours: string;
  verification_status: string;
}

export interface SurplusMatchesResponse {
  surplus_id: string;
  food: string;
  quantity: number;
  unit: string;
  storage_type: string;
  temperature?: number | null;
  urgency: string;
  remaining_safe_window_minutes: number;
  status: string;
  matches_count: number;
  matches: RecipientMatchCandidate[];
}

export interface RecipientSurplusActionResponse {
  success: boolean;
  surplus_id: string;
  recipient_id: string;
  new_status: string;
  claim_status: string;
  message: string;
  timestamp: string;
}

export interface RecipientAvailableSurplusItem {
  id: string;
  food: string;
  quantity: number;
  unit: string;
  portions: number;
  storage_type: string;
  temperature?: number | null;
  prepared_at?: string | null;
  best_use_before?: string | null;
  age_formatted: string;
  remaining_safe_window_minutes: number;
  safe_window_formatted: string;
  urgency: string;
  location: string;
  status: string;
  claim_status?: string | null;
  image?: string | null;
  distance_km: number;
  match_score: number;
  transparent_explanation: string[];
}

export interface RecipientDashboardSummary {
  recipient_id: string;
  organization_name: string;
  facility_type: string;
  verification_status: string;
  daily_intake_capacity_kg: number;
  current_demand_portions: number;
  storage_capabilities: string[];
  pickup_available: boolean;
  available_lots_count: number;
  active_requests_count: number;
  scheduled_pickups_count: number;
  total_rescued_kg: number;
  available_surplus: RecipientAvailableSurplusItem[];
}

export interface SchedulePickupPayload {
  recipient_id: string;
  pickup_time: string;
  driver_name?: string;
  vehicle_plate?: string;
  temperature_equipment_confirmed?: boolean;
  driver_notes?: string;
}

// -------------------------------------------------------------
// PHASE 10: LOGISTICS, ROUTE OPTIMIZATION & COURIER DISPATCH
// -------------------------------------------------------------

export type LogisticsStatus = 
  | 'ASSIGNED'
  | 'EN_ROUTE'
  | 'ARRIVED'
  | 'PICKED_UP'
  | 'IN_TRANSIT'
  | 'DELIVERED'
  | 'FAILED'
  | 'CANCELLED';

export interface DeliveryWaypoint {
  stop_sequence: number;
  stop_type: 'depot' | 'pickup' | 'delivery';
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  cargo_weight_kg: number;
  cumulative_load_kg: number;
  arrival_time_mins: number;
  departure_time_mins: number;
  eta_time_str: string;
  food_title?: string | null;
  food_urgency?: string | null;
  delivery_id?: string | null;
}

export interface VehicleRoutePlan {
  vehicle_id: string;
  driver_id: string;
  driver_name: string;
  license_plate: string;
  vehicle_capacity_kg: number;
  total_load_kg: number;
  total_distance_km: number;
  total_duration_mins: number;
  waypoints: DeliveryWaypoint[];
}

export interface RouteOptimizationResult {
  solver_status: string;
  solver_model: string;
  num_vehicles_dispatched: number;
  total_rescued_kg: number;
  total_distance_km: number;
  total_travel_time_mins: number;
  routes: VehicleRoutePlan[];
  unassigned_missions: string[];
}

export interface DeliveryMissionRecord {
  id: string;
  food_title: string;
  cargo_weight_kg: number;
  food_urgency: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  status: LogisticsStatus;
  pickup_address: string;
  pickup_lat: number;
  pickup_lng: number;
  delivery_address: string;
  delivery_lat: number;
  delivery_lng: number;
  scheduled_pickup_time?: string | null;
  scheduled_delivery_time?: string | null;
  estimated_arrival_time?: string | null;
  distance_km: number;
  transit_time_mins: number;
  stop_sequence: number;
  driver_id?: string | null;
  vehicle_id?: string | null;
  proof_of_delivery_receiver_name?: string | null;
  proof_of_delivery_signature?: string | null;
  proof_of_delivery_photo?: string | null;
  proof_of_delivery_notes?: string | null;
  proof_of_delivery_verified_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface DriverDashboardPayload {
  driver_id: string;
  driver_name: string;
  license_number: string;
  driver_status: string;
  current_lat: number;
  current_lng: number;
  vehicle?: {
    id: string;
    license_plate: string;
    vehicle_type: string;
    capacity_kg: number;
    has_active_cooling: boolean;
  } | null;
  today_assignments: DeliveryMissionRecord[];
  active_route?: VehicleRoutePlan | null;
  stats: {
    total_missions_today: number;
    completed_count: number;
    active_count: number;
    total_kg_delivered: number;
    urgent_missions_count: number;
    on_time_rate_pct: number;
  };
}

export interface ProofOfDeliverySubmission {
  receiver_name: string;
  signature?: string;
  photo_url?: string;
  actual_temp_at_delivery_c?: number;
  notes?: string;
}

// =====================================================================
// PHASE 11: QR CHAIN OF CUSTODY & VERIFICATION
// =====================================================================

export type CustodyStage = 
  | 'DONATION_CREATED'
  | 'ACCEPTED'
  | 'PICKUP_ASSIGNED'
  | 'PICKED_UP'
  | 'IN_TRANSIT'
  | 'DELIVERED'
  | 'RECEIVED';

export type QRScanStage = 
  | 'KITCHEN_HANDOVER'
  | 'DRIVER_PICKUP'
  | 'COURIER_DELIVERY'
  | 'RECIPIENT_RECEIPT';

export interface DonationCustodyEvent {
  id: string;
  donation_id: string;
  event: string;
  from_status: string;
  to_status: string;
  user_id?: string | null;
  user_name?: string | null;
  role: string;
  timestamp: string;
  token_nonce?: string | null;
  proof_type?: string | null;
  verified_temp_c?: number | null;
  verified_lat?: number | null;
  verified_lng?: number | null;
  signature_data?: string | null;
  proof_image_url?: string | null;
  notes?: string | null;
  proof_metadata?: Record<string, any>;
  previous_hash?: string | null;
  integrity_hash: string;
  chain_verified?: boolean;
}

export interface CustodyAllowedAction {
  action: string;
  target_status?: string;
  target_stage?: string;
  method: 'MANUAL' | 'QR_SCAN' | 'MANUAL_OR_SCAN' | 'ARCHIVED';
  allowed_roles: string[];
  description: string;
}

export interface DonationAuditTrailResponse {
  donation_id: string;
  immutable_donation_id: string;
  current_status: CustodyStage;
  total_events: number;
  chain_intact: boolean;
  audit_trail: DonationCustodyEvent[];
  allowed_actions: CustodyAllowedAction[];
}

export interface DonationCustodyStatusResponse {
  donation_id: string;
  immutable_donation_id: string;
  tracking_number: string;
  status: CustodyStage;
  total_weight_kg: number;
  total_portions: number;
  donor_org_id: string;
  recipient_org_id?: string | null;
  allowed_actions: CustodyAllowedAction[];
}

export interface GenerateCustodyQRRequest {
  donation_id: string;
  stage: QRScanStage;
  expires_in_minutes?: number;
}

export interface GenerateCustodyQRResponse {
  donation_id: string;
  immutable_donation_id: string;
  stage: QRScanStage;
  token: string;
  nonce: string;
  hmac_signature: string;
  expires_at: string;
  current_status: CustodyStage;
  allowed_scanner_roles: string[];
  instructions: string;
}

export interface VerifyCustodyScanRequest {
  token: string;
  stage?: QRScanStage;
  proof_type?: string;
  measured_temp_c?: number;
  current_lat?: number;
  current_lng?: number;
  signature_data?: string;
  proof_image_url?: string;
  notes?: string;
  proof_metadata?: Record<string, any>;
}

export interface VerifyCustodyScanResponse {
  verified: boolean;
  message: string;
  donation_id: string;
  immutable_donation_id: string;
  previous_status: CustodyStage;
  current_status: CustodyStage;
  event: string;
  scanner_role: string;
  scanner_user_id: string;
  scanner_user_name?: string | null;
  timestamp: string;
  integrity_hash: string;
  proof_summary?: {
    proof_type?: string | null;
    verified_temp_c?: number | null;
    verified_lat?: number | null;
    verified_lng?: number | null;
    notes?: string | null;
  };
}

export interface ManualTransitionRequest {
  target_status: CustodyStage;
  notes?: string;
  proof_type?: string;
  verified_temp_c?: number;
  signature_data?: string;
  proof_image_url?: string;
}

// -------------------------------------------------------------
// Phase 12 — RAG AI Assistant & Document Management Types
// -------------------------------------------------------------
export interface SourceReferenceOut {
  document_id: string;
  chunk_id?: string | null;
  title: string;
  document_type: string;
  version: string;
  date?: string | null;
  access_level: string;
  source: string;
  organization_id?: string | null;
  relevance_score: number;
  snippet: string;
}

export interface OperationalContextOut {
  query_type: 'waste_increase' | 'food_waste_causes' | 'production_tomorrow' | 'urgent_surplus' | 'month_impact' | 'generic_operational';
  is_live_data: boolean;
  metric_count: number;
  summary: string;
  key_metrics: Record<string, any>;
  records: Array<Record<string, any>>;
}

export interface RAGQueryRequest {
  query: string;
  session_id?: string | null;
  category_filter?: string | null;
  top_k?: number;
}

export interface RAGQueryResponse {
  query: string;
  session_id: string;
  answer: string;
  grounded: boolean;
  is_insufficient_evidence: boolean;
  sources: SourceReferenceOut[];
  operational_context?: OperationalContextOut | null;
  suggested_prompts: string[];
  created_at: string;
}

export interface ChatMessageOut {
  id: string;
  session_id: string;
  user_id?: string | null;
  organization_id?: string | null;
  role: 'user' | 'assistant' | 'system';
  content: string;
  sources: SourceReferenceOut[];
  data_context?: Record<string, any> | null;
  created_at: string;
}

export interface ChatSessionOut {
  session_id: string;
  total_messages: number;
  messages: ChatMessageOut[];
}

export interface SuggestedPromptOut {
  prompt: string;
  category: string;
  description: string;
}

export interface SuggestedPromptsResponse {
  prompts: SuggestedPromptOut[];
}

export interface DocumentIngestRequest {
  title: string;
  content: string;
  category?: string;
  document_type: string;
  version: string;
  doc_date?: string;
  access_level: string;
  source: string;
  organization_id?: string | null;
}

export interface DocumentIngestResponse {
  document_id: string;
  title: string;
  document_type: string;
  version: string;
  access_level: string;
  source: string;
  organization_id?: string | null;
  total_chunks: number;
  created_at: string;
  message: string;
}

export interface DocumentChunkOut {
  id: string;
  document_id: string;
  chunk_index: number;
  content: string;
  token_count: number;
  chunk_metadata: Record<string, any>;
  created_at: string;
}

export interface DocumentListItem {
  id: string;
  title: string;
  category: string;
  document_type: string;
  version: string;
  access_level: string;
  regulatory_source: string;
  organization_id?: string | null;
  doc_date?: string | null;
  is_public: boolean;
  total_chunks: number;
  created_at: string;
}

// ==========================================
// Phase 13: Computer Vision Types
// ==========================================

export type CanonicalFoodCategory =
  | 'Rice'
  | 'Dal'
  | 'Vegetables'
  | 'Chapati'
  | 'Bread'
  | 'Fruit'
  | 'Dessert'
  | 'Other';

export interface VisionBoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
  label: string;
  confidence: number;
}

export interface VisionCandidate {
  category: string;
  confidence: number;
  description?: string;
}

export interface VisionClassificationResult {
  scan_id: string;
  prediction: CanonicalFoodCategory;
  confidence: number;
  confidence_tier: 'HIGH' | 'MODERATE' | 'LOW';
  requires_manual_confirmation: boolean;
  bounding_box?: VisionBoundingBox;
  top_candidates: VisionCandidate[];
  model_architecture: string;
  dataset_info: string;
  disclaimer: string;
  preprocessing_metadata: Record<string, any>;
  image_preview_url?: string;
  timestamp: string;
}

export interface VisionSampleImage {
  sample_id: string;
  title: string;
  expected_category: CanonicalFoodCategory;
  expected_confidence: number;
  is_low_confidence: boolean;
  preview_svg: string;
}

export interface VisionConfirmPayload {
  scan_id: string;
  confirmed_label: string;
  action: 'CONFIRM_ONLY' | 'LOG_WASTE' | 'DECLARE_SURPLUS';
  weight_kg?: number;
  notes?: string;
  destination_kitchen_id?: string;
}

export interface VisionConfirmResponse {
  scan_id: string;
  is_confirmed: boolean;
  original_prediction: string;
  final_label: string;
  was_corrected: boolean;
  confidence: number;
  created_record_type?: string;
  created_record_id?: string;
  confirmed_at: string;
  message: string;
}

export interface VisionScanHistoryItem {
  id: string;
  prediction: string;
  confidence: number;
  confidence_tier: string;
  is_confirmed: boolean;
  corrected_label?: string | null;
  created_record_type?: string | null;
  created_record_id?: string | null;
  created_at: string;
  confirmed_at?: string | null;
}

export interface VisionBenchmarkReport {
  model_name: string;
  version: string;
  dataset_type: string;
  total_eval_samples: number;
  overall_accuracy: number;
  macro_f1_score: number;
  average_latency_ms: number;
  categories: string[];
  per_class_metrics: Record<string, { precision: number; recall: number; f1: number; support: number }>;
  disclaimer: string;
}

// =====================================================================
// PHASE 14 — FOOD PROCESSING UNIT (FPU) & FEFO TYPES
// =====================================================================

export interface FpuRawMaterialItem {
  id: string;
  processing_unit_id: string;
  material_name: string;
  category: string;
  lot_number: string;
  initial_quantity: number;
  current_quantity: number;
  unit: string;
  storage_condition: string;
  storage_location: string;
  harvest_or_mfg_date: string;
  expiry_date: string;
  quality_status: 'APPROVED' | 'UNDER_REVIEW' | 'REJECTED' | 'QUARANTINED';
  packaging_condition: 'INTACT' | 'DAMAGED_PACKAGING' | 'LEAKING' | 'SEAL_COMPROMISED';
  damaged_quantity: number;
  rejection_reason?: string | null;
  disposition_action?: string | null;
  supplier?: string | null;
  cost_per_unit: number;
  status: 'AVAILABLE' | 'ALLOCATED' | 'DEPLETED' | 'EXPIRED' | 'QUARANTINED' | 'REJECTED';
  days_to_expiry: number;
  expiry_urgency_tier: 'EXPIRED' | 'CRITICAL_1_DAY' | 'URGENT_3_DAYS' | 'WARNING_7_DAYS' | 'OPTIMAL';
  created_at: string;
  updated_at: string;
}

export interface FpuBatchMaterialUsage {
  id: string;
  raw_material_id: string;
  raw_material_name: string;
  lot_number: string;
  quantity_used: number;
  unit: string;
  fefo_sequence_order: number;
  lot_expiry_at_consumption: string;
}

export interface FpuProductionBatchItem {
  id: string;
  processing_unit_id: string;
  batch_number: string;
  product_name: string;
  category: string;
  planned_quantity: number;
  actual_quantity: number;
  unit: string;
  manufacturing_date: string;
  expiry_date: string;
  quality_status: 'PASSED' | 'UNDER_REVIEW' | 'REJECTED' | 'DAMAGED_PACKAGING' | 'QUARANTINED';
  packaging_condition: 'INTACT' | 'DAMAGED_PACKAGING' | 'SEAL_FAILURE' | 'DEFECTIVE_LABEL' | 'DENTED_CONTAINER';
  damaged_packaging_units: number;
  rejected_quantity: number;
  rejection_reason?: string | null;
  disposition_action?: string | null;
  yield_percentage: number;
  surplus_quantity: number;
  redistributable_stock: number;
  redistribution_status: 'NOT_DECLARED' | 'AVAILABLE_FOR_REDISTRIBUTION' | 'ALLOCATED_TO_DONATION' | 'DISPATCHED' | 'DELIVERED';
  status: 'PLANNED' | 'IN_PRODUCTION' | 'QUALITY_CONTROL' | 'COMPLETED' | 'QUARANTINED' | 'REJECTED';
  operator_notes?: string | null;
  qc_officer?: string | null;
  created_at: string;
  updated_at: string;
  raw_materials_used: FpuBatchMaterialUsage[];
  days_to_expiry: number;
  expiry_urgency_tier: string;
}

export interface FefoPickItem {
  raw_material_id: string;
  lot_number: string;
  material_name: string;
  category: string;
  storage_location: string;
  expiry_date: string;
  days_to_expiry: number;
  lot_available_quantity: number;
  allocated_quantity: number;
  remaining_in_lot: number;
  unit: string;
  fefo_sequence: number;
}

export interface FefoAllocationResult {
  material_name?: string;
  required_quantity: number;
  total_allocated: number;
  is_fulfilled: boolean;
  shortage_quantity: number;
  fefo_compliance_score: number;
  pick_list: FefoPickItem[];
  reasoning: string[];
}

export interface FefoQueueItem {
  raw_material_id: string;
  lot_number: string;
  material_name: string;
  category: string;
  current_quantity: number;
  unit: string;
  storage_location: string;
  expiry_date: string;
  days_to_expiry: number;
  urgency_tier: string;
  fefo_priority_rank: number;
  quality_status: string;
  packaging_condition: string;
}

export interface FpuAlertItem {
  alert_id: string;
  item_type: 'RAW_MATERIAL' | 'PRODUCTION_BATCH';
  item_id: string;
  code: string;
  name: string;
  category: string;
  quantity: number;
  unit: string;
  manufacturing_or_harvest_date: string;
  expiry_date: string;
  days_remaining: number;
  alert_severity: 'EXPIRED' | 'CRITICAL_1_DAY' | 'URGENT_3_DAYS' | 'WARNING_7_DAYS' | 'DAMAGED_PACKAGING';
  applicable_rule: string;
  threshold_days_used: number;
  quality_status: string;
  packaging_condition: string;
  recommended_action: string;
}

export interface FpuAlertsSummary {
  total_alerts: number;
  expired_count: number;
  critical_count: number;
  urgent_count: number;
  warning_count: number;
  quality_defects_count: number;
  alerts: FpuAlertItem[];
}

export interface FpuThresholdRule {
  id: string;
  target_type: 'CATEGORY' | 'PRODUCT' | 'RAW_MATERIAL';
  target_name: string;
  warning_threshold_days: number;
  urgent_threshold_days: number;
  critical_threshold_days: number;
  custom_safety_notes?: string | null;
  is_active: boolean;
}

export interface TraceabilityNode {
  step: number;
  stage: 'RAW_MATERIAL' | 'PRODUCTION_BATCH' | 'FINISHED_PRODUCT' | 'SURPLUS_DONATION' | 'RECIPIENT';
  identifier: string;
  name: string;
  quantity: number;
  unit: string;
  timestamp?: string;
  quality_status: string;
  packaging_condition?: string;
  facility_or_org: string;
  details: Record<string, any>;
}

export interface FpuTraceabilityChain {
  query_identifier: string;
  root_stage: string;
  summary: string;
  raw_materials: Array<Record<string, any>>;
  production_batch?: Record<string, any>;
  finished_product?: Record<string, any>;
  surplus_donation?: Record<string, any>;
  recipient?: Record<string, any>;
  linear_trace_steps: TraceabilityNode[];
}

export interface FpuDashboardData {
  processing_unit_id: string;
  processing_unit_name: string;
  processing_type: string;
  inventory: {
    total_raw_material_kg: number;
    total_finished_product_kg: number;
    total_inventory_kg: number;
    total_raw_lots_count: number;
    total_active_batches_count: number;
    estimated_inventory_value_usd: number;
  };
  near_expiry: {
    total_near_expiry_count: number;
    total_near_expiry_kg: number;
    warning_7d_count: number;
    urgent_3d_count: number;
    critical_1d_count: number;
    items: FpuAlertItem[];
  };
  expired: {
    total_expired_count: number;
    total_expired_kg: number;
    quarantined_count: number;
    items: FpuAlertItem[];
  };
  production: {
    total_batches_all_time: number;
    completed_batches_count: number;
    active_in_production_count: number;
    total_yield_kg: number;
    average_yield_percentage: number;
    fefo_adherence_percentage: number;
  };
  rejected: {
    rejected_products_count: number;
    total_rejected_kg: number;
    damaged_packaging_incidents: number;
    damaged_units_count: number;
    by_disposition: Record<string, number>;
    by_rejection_reason: Record<string, number>;
  };
  redistributable_stock: {
    total_surplus_generated_kg: number;
    current_redistributable_stock_kg: number;
    allocated_to_donations_kg: number;
    dispatched_to_recipients_kg: number;
    active_recipient_partners_count: number;
    redistributable_batches_count: number;
  };
}

// -------------------------------------------------------------
// PHASE 15: SUSTAINABILITY IMPACT ANALYTICS ENGINE
// -------------------------------------------------------------

export interface EmissionFactorItem {
  id: string;
  organization_id?: string | null;
  category: string;
  co2e_kg_per_kg_food: number;
  water_liters_per_kg_food: number;
  landfill_diversion_m3_per_kg: number;
  meal_equivalent_kg: number;
  people_served_per_meal: number;
  economic_value_usd_per_kg: number;
  production_cost_factor_per_kg: number;
  documentation_source: string;
  notes?: string | null;
  is_estimate: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface EmissionFactorCreatePayload {
  organization_id?: string | null;
  category: string;
  co2e_kg_per_kg_food: number;
  water_liters_per_kg_food: number;
  landfill_diversion_m3_per_kg: number;
  meal_equivalent_kg: number;
  people_served_per_meal: number;
  economic_value_usd_per_kg: number;
  production_cost_factor_per_kg: number;
  documentation_source: string;
  notes?: string | null;
}

export interface ImpactKpiMetrics {
  food_rescued_kg: number;
  food_waste_kg: number;
  waste_reduction_percentage: number;
  meals_equivalent: number;
  people_served: number;
  estimated_value_preserved_usd: number;
  production_cost_saved_usd: number;
  redistribution_count: number;
  successful_deliveries: number;
  failed_deliveries: number;
  delivery_success_rate_pct: number;
  average_pickup_time_minutes: number;
  co2e_avoided_kg: number;
  water_saved_liters: number;
  landfill_diverted_m3: number;
  is_environmental_estimate: boolean;
  environmental_estimate_disclaimer: string;
}

export interface WasteTrendPoint {
  date: string;
  waste_kg: number;
  target_threshold_kg: number;
  diverted_kg: number;
}

export interface FoodRescuedPoint {
  date: string;
  rescued_kg: number;
  meals_equivalent: number;
  people_served: number;
}

export interface CategoryBreakdownItem {
  category: string;
  rescued_kg: number;
  waste_kg: number;
  co2e_avoided_kg: number;
  value_usd: number;
  percentage_of_total: number;
}

export interface KitchenComparisonItem {
  kitchen_id: string;
  kitchen_name: string;
  organization_name: string;
  food_rescued_kg: number;
  food_waste_kg: number;
  waste_reduction_pct: number;
  efficiency_score: number;
  successful_deliveries: number;
}

export interface RedistributionTrendPoint {
  date: string;
  redistribution_count: number;
  volume_kg: number;
  meals_provided: number;
}

export interface ForecastVsActualPoint {
  date: string;
  predicted_waste_kg: number;
  actual_waste_kg: number;
  variance_kg: number;
  variance_pct: number;
}

export interface CostTrendPoint {
  date: string;
  value_preserved_usd: number;
  production_cost_saved_usd: number;
  waste_loss_usd: number;
  net_benefit_usd: number;
}

export interface OperationalEfficiencyPoint {
  date: string;
  avg_pickup_time_mins: number;
  delivery_success_rate_pct: number;
  total_deliveries: number;
  failed_deliveries: number;
}

export interface ImpactChartsData {
  waste_trend: WasteTrendPoint[];
  food_rescued: FoodRescuedPoint[];
  category_breakdown: CategoryBreakdownItem[];
  kitchen_comparison: KitchenComparisonItem[];
  redistribution_trend: RedistributionTrendPoint[];
  forecast_vs_actual: ForecastVsActualPoint[];
  cost_trend: CostTrendPoint[];
  operational_efficiency: OperationalEfficiencyPoint[];
}

export interface ImpactFilterOptions {
  organizations: { id: string; name: string }[];
  kitchens: { id: string; name: string }[];
  categories: string[];
  granularities: string[];
}

export interface ImpactAnalyticsResponse {
  time_granularity: string;
  date_range: { start?: string; end?: string };
  filters_applied: Record<string, any>;
  kpis: ImpactKpiMetrics;
  charts: ImpactChartsData;
  emission_factors: EmissionFactorItem[];
  environmental_estimate_disclaimer: string;
}

