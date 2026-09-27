-- ====================================================================
-- FOODLOOP AI - Enterprise Production Database Schema (PostgreSQL 16)
-- Target Engine: Supabase Cloud PostgreSQL with PostGIS & pgvector
-- Covers All 30 Enterprise Platform Tables with Strict RBAC & RLS
-- ====================================================================

-- 1. EXTENSIONS
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

DO $$ BEGIN
    CREATE EXTENSION IF NOT EXISTS "postgis";
EXCEPTION WHEN OTHERS THEN NULL;
END $$;

DO $$ BEGIN
    CREATE EXTENSION IF NOT EXISTS "vector";
EXCEPTION WHEN OTHERS THEN NULL;
END $$;

-- 2. TRIGGER FUNCTION FOR UPDATED_AT
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 3. TABLES (1 to 30)

-- TABLE 1: USERS
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('ADMIN', 'KITCHEN_MANAGER', 'PROCESSOR', 'NGO', 'DRIVER', 'AUDITOR')),
    phone VARCHAR(50),
    avatar_url TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- TABLE 2: ORGANIZATIONS
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    org_type VARCHAR(50) NOT NULL CHECK (org_type IN ('COMMERCIAL_KITCHEN', 'FOOD_PROCESSOR', 'NGO', 'LOGISTICS_PROVIDER', 'GOVERNMENT_AUDITOR')),
    registration_number VARCHAR(100) UNIQUE NOT NULL,
    tax_id VARCHAR(100),
    license_fssai_fda VARCHAR(100),
    address TEXT NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    contact_email VARCHAR(255) NOT NULL,
    contact_phone VARCHAR(50) NOT NULL,
    is_verified BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- TABLE 3: ORGANIZATION_MEMBERS
CREATE TABLE IF NOT EXISTS organization_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_in_org VARCHAR(50) NOT NULL DEFAULT 'MEMBER',
    is_primary BOOLEAN NOT NULL DEFAULT TRUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_org_user UNIQUE (organization_id, user_id)
);

-- TABLE 4: KITCHENS
CREATE TABLE IF NOT EXISTS kitchens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    address TEXT NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    daily_meal_capacity INT NOT NULL DEFAULT 500 CHECK (daily_meal_capacity >= 0),
    storage_specs JSONB NOT NULL DEFAULT '{"ambient_sqm": 50, "refrigerated_liters": 2000, "frozen_liters": 1000}'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- TABLE 5: PROCESSING_UNITS
CREATE TABLE IF NOT EXISTS processing_units (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    address TEXT NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    processing_type VARCHAR(100) NOT NULL,
    daily_capacity_kg DOUBLE PRECISION NOT NULL DEFAULT 2000.0 CHECK (daily_capacity_kg >= 0),
    cold_tank_capacity_liters DOUBLE PRECISION NOT NULL DEFAULT 5000.0 CHECK (cold_tank_capacity_liters >= 0),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- TABLE 6: MENUS
CREATE TABLE IF NOT EXISTS menus (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kitchen_id UUID NOT NULL REFERENCES kitchens(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    service_date DATE NOT NULL,
    meal_service VARCHAR(50) NOT NULL CHECK (meal_service IN ('BREAKFAST', 'LUNCH', 'DINNER', 'SNACK')),
    planned_headcount INT NOT NULL CHECK (planned_headcount > 0),
    status VARCHAR(50) NOT NULL DEFAULT 'DRAFT' CHECK (status IN ('DRAFT', 'APPROVED', 'IN_PRODUCTION', 'ARCHIVED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- TABLE 7: MENU_ITEMS
CREATE TABLE IF NOT EXISTS menu_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    menu_id UUID NOT NULL REFERENCES menus(id) ON DELETE CASCADE,
    dish_name VARCHAR(255) NOT NULL,
    planned_portions INT NOT NULL CHECK (planned_portions >= 0),
    portion_weight_grams DOUBLE PRECISION NOT NULL DEFAULT 400.0 CHECK (portion_weight_grams > 0),
    dietary_category VARCHAR(50) NOT NULL DEFAULT 'STANDARD',
    allergens TEXT[] DEFAULT ARRAY[]::TEXT[],
    cost_per_portion DOUBLE PRECISION NOT NULL DEFAULT 0.0 CHECK (cost_per_portion >= 0),
    status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- TABLE 8: INGREDIENTS
CREATE TABLE IF NOT EXISTS ingredients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    unit VARCHAR(50) NOT NULL DEFAULT 'kg',
    standard_cost_per_unit DOUBLE PRECISION NOT NULL DEFAULT 0.0 CHECK (standard_cost_per_unit >= 0),
    allergen_profile TEXT[] DEFAULT ARRAY[]::TEXT[],
    storage_temp_category VARCHAR(50) NOT NULL DEFAULT 'ROOM_TEMP' CHECK (storage_temp_category IN ('ROOM_TEMP', 'REFRIGERATED', 'FROZEN')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- TABLE 9: INVENTORY
CREATE TABLE IF NOT EXISTS inventory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kitchen_id UUID REFERENCES kitchens(id) ON DELETE CASCADE,
    processing_unit_id UUID REFERENCES processing_units(id) ON DELETE CASCADE,
    ingredient_id UUID NOT NULL REFERENCES ingredients(id) ON DELETE RESTRICT,
    lot_number VARCHAR(100) NOT NULL,
    current_quantity DOUBLE PRECISION NOT NULL CHECK (current_quantity >= 0),
    reserved_quantity DOUBLE PRECISION NOT NULL DEFAULT 0.0 CHECK (reserved_quantity >= 0),
    unit VARCHAR(50) NOT NULL DEFAULT 'kg',
    reorder_level DOUBLE PRECISION NOT NULL DEFAULT 10.0 CHECK (reorder_level >= 0),
    storage_temp VARCHAR(50) NOT NULL DEFAULT 'ROOM_TEMP',
    storage_location VARCHAR(100) NOT NULL DEFAULT 'Main Cold Room',
    expiry_date TIMESTAMPTZ NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'OPTIMAL' CHECK (status IN ('OPTIMAL', 'EXPIRING_SOON', 'CRITICAL', 'DEPLETED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- TABLE 10: INVENTORY_TRANSACTIONS
CREATE TABLE IF NOT EXISTS inventory_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    inventory_id UUID NOT NULL REFERENCES inventory(id) ON DELETE CASCADE,
    transaction_type VARCHAR(50) NOT NULL CHECK (transaction_type IN ('INFLOW_PURCHASE', 'OUTFLOW_PREP', 'ADJUSTMENT', 'SURPLUS_DIVERTED', 'SPOILAGE_DISCARD')),
    quantity DOUBLE PRECISION NOT NULL,
    unit VARCHAR(50) NOT NULL,
    reference_id VARCHAR(100),
    performed_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- TABLE 11: PRODUCTION_BATCHES
CREATE TABLE IF NOT EXISTS production_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kitchen_id UUID NOT NULL REFERENCES kitchens(id) ON DELETE CASCADE,
    menu_item_id UUID REFERENCES menu_items(id) ON DELETE SET NULL,
    batch_number VARCHAR(100) UNIQUE NOT NULL,
    planned_quantity DOUBLE PRECISION NOT NULL CHECK (planned_quantity > 0),
    actual_prepared_quantity DOUBLE PRECISION NOT NULL DEFAULT 0.0 CHECK (actual_prepared_quantity >= 0),
    unit VARCHAR(50) NOT NULL DEFAULT 'portions',
    station VARCHAR(100) NOT NULL,
    target_temp_c DOUBLE PRECISION,
    current_temp_c DOUBLE PRECISION,
    haccp_compliant BOOLEAN NOT NULL DEFAULT TRUE,
    chef_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'SCHEDULED' CHECK (status IN ('SCHEDULED', 'PREPPING', 'COOKING', 'HOLDING', 'COMPLETED', 'DISCARDED')),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- TABLE 12: CONSUMPTION_RECORDS
CREATE TABLE IF NOT EXISTS consumption_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID NOT NULL REFERENCES production_batches(id) ON DELETE CASCADE,
    meal_service VARCHAR(50) NOT NULL,
    planned_headcount INT NOT NULL CHECK (planned_headcount > 0),
    actual_headcount INT NOT NULL CHECK (actual_headcount >= 0),
    variance_percentage DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    total_prepared_kg DOUBLE PRECISION NOT NULL CHECK (total_prepared_kg >= 0),
    total_consumed_kg DOUBLE PRECISION NOT NULL CHECK (total_consumed_kg >= 0),
    unconsumed_kg DOUBLE PRECISION NOT NULL CHECK (unconsumed_kg >= 0),
    diverted_to_surplus_kg DOUBLE PRECISION NOT NULL DEFAULT 0.0 CHECK (diverted_to_surplus_kg >= 0),
    recorded_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    notes TEXT,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- TABLE 13: WASTE_RECORDS
CREATE TABLE IF NOT EXISTS waste_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kitchen_id UUID NOT NULL REFERENCES kitchens(id) ON DELETE CASCADE,
    batch_id UUID REFERENCES production_batches(id) ON DELETE SET NULL,
    waste_category VARCHAR(50) NOT NULL CHECK (waste_category IN ('PREPARATION_TRIMMINGS', 'PLATE_SCRAPS', 'SPOILAGE_EXPIRY', 'OVERPRODUCTION_SURPLUS', 'EQUIPMENT_FAILURE')),
    weight_kg DOUBLE PRECISION NOT NULL CHECK (weight_kg >= 0),
    cost_loss_usd DOUBLE PRECISION NOT NULL DEFAULT 0.0 CHECK (cost_loss_usd >= 0),
    ghg_co2e_kg DOUBLE PRECISION NOT NULL DEFAULT 0.0 CHECK (ghg_co2e_kg >= 0),
    epa_hierarchy_tier VARCHAR(50) NOT NULL CHECK (epa_hierarchy_tier IN ('SOURCE_REDUCTION', 'FEED_HUNGRY_PEOPLE', 'FEED_ANIMALS', 'INDUSTRIAL_USES', 'COMPOST', 'LANDFILL')),
    department VARCHAR(100) NOT NULL,
    root_cause TEXT,
    logged_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- TABLE 14: SURPLUS_ITEMS
CREATE TABLE IF NOT EXISTS surplus_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    kitchen_id UUID REFERENCES kitchens(id) ON DELETE SET NULL,
    batch_id UUID REFERENCES production_batches(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL CHECK (category IN ('COOKED_MEALS', 'BAKERY', 'DAIRY', 'PRODUCE', 'PROTEIN', 'DRY_GOODS')),
    quantity_kg DOUBLE PRECISION NOT NULL CHECK (quantity_kg > 0),
    portions INT NOT NULL CHECK (portions > 0),
    storage_temp VARCHAR(50) NOT NULL DEFAULT 'ROOM_TEMP' CHECK (storage_temp IN ('ROOM_TEMP', 'REFRIGERATED', 'FROZEN')),
    safe_consumption_deadline TIMESTAMPTZ NOT NULL,
    blast_chilled_at TIMESTAMPTZ,
    calculated_shelf_life_hours DOUBLE PRECISION NOT NULL CHECK (calculated_shelf_life_hours >= 0),
    urgency_tier VARCHAR(50) NOT NULL DEFAULT 'STANDARD' CHECK (urgency_tier IN ('STANDARD', 'EXPEDITED', 'CRITICAL_IMMEDIATE')),
    pickup_address TEXT NOT NULL,
    pickup_lat DOUBLE PRECISION NOT NULL,
    pickup_lng DOUBLE PRECISION NOT NULL,
    dietary_tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    status VARCHAR(50) NOT NULL DEFAULT 'DECLARED' CHECK (status IN ('DECLARED', 'MATCHED', 'CLAIMED', 'IN_TRANSIT', 'DELIVERED', 'EXPIRED', 'DISCARDED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- TABLE 15: RECIPIENTS
CREATE TABLE IF NOT EXISTS recipients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    facility_type VARCHAR(50) NOT NULL CHECK (facility_type IN ('FOOD_BANK', 'SOUP_KITCHEN', 'SHELTER', 'YOUTH_REFUGE', 'COMMUNITY_PANTRY')),
    address TEXT NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    max_daily_intake_kg DOUBLE PRECISION NOT NULL DEFAULT 200.0 CHECK (max_daily_intake_kg >= 0),
    cold_storage_available BOOLEAN NOT NULL DEFAULT TRUE,
    walk_in_chiller_capacity_kg DOUBLE PRECISION NOT NULL DEFAULT 50.0 CHECK (walk_in_chiller_capacity_kg >= 0),
    verified_charity_id VARCHAR(100),
    contact_person VARCHAR(255) NOT NULL,
    contact_phone VARCHAR(50) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- TABLE 16: RECIPIENT_REQUIREMENTS
CREATE TABLE IF NOT EXISTS recipient_requirements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipient_id UUID NOT NULL REFERENCES recipients(id) ON DELETE CASCADE,
    acceptable_categories TEXT[] DEFAULT ARRAY[]::TEXT[],
    dietary_preferences TEXT[] DEFAULT ARRAY[]::TEXT[],
    required_storage_temp VARCHAR(50) DEFAULT 'ANY',
    min_portions_per_drop INT NOT NULL DEFAULT 10 CHECK (min_portions_per_drop >= 0),
    max_delivery_distance_km DOUBLE PRECISION NOT NULL DEFAULT 25.0 CHECK (max_delivery_distance_km > 0),
    operating_hours JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- TABLE 17: DONATIONS
CREATE TABLE IF NOT EXISTS donations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    donor_org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    recipient_org_id UUID REFERENCES organizations(id) ON DELETE RESTRICT,
    tracking_number VARCHAR(100) UNIQUE NOT NULL,
    total_weight_kg DOUBLE PRECISION NOT NULL CHECK (total_weight_kg > 0),
    total_portions INT NOT NULL CHECK (total_portions > 0),
    status VARCHAR(50) NOT NULL DEFAULT 'DECLARED' CHECK (status IN ('DECLARED', 'MATCHED', 'COURIER_ASSIGNED', 'IN_TRANSIT', 'DELIVERED', 'CANCELLED')),
    haccp_verified BOOLEAN NOT NULL DEFAULT TRUE,
    declaration_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    safe_handling_ack BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- TABLE 18: DONATION_ITEMS
CREATE TABLE IF NOT EXISTS donation_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    donation_id UUID NOT NULL REFERENCES donations(id) ON DELETE CASCADE,
    surplus_item_id UUID NOT NULL REFERENCES surplus_items(id) ON DELETE RESTRICT,
    allocated_quantity_kg DOUBLE PRECISION NOT NULL CHECK (allocated_quantity_kg > 0),
    allocated_portions INT NOT NULL CHECK (allocated_portions > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- TABLE 19: PICKUP_REQUESTS
CREATE TABLE IF NOT EXISTS pickup_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    donation_id UUID NOT NULL REFERENCES donations(id) ON DELETE CASCADE,
    donor_address TEXT NOT NULL,
    donor_lat DOUBLE PRECISION NOT NULL,
    donor_lng DOUBLE PRECISION NOT NULL,
    ready_time TIMESTAMPTZ NOT NULL,
    latest_pickup_time TIMESTAMPTZ NOT NULL,
    assigned_driver_id UUID REFERENCES users(id) ON DELETE SET NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'ACCEPTED', 'EN_ROUTE', 'COMPLETED', 'FAILED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- TABLE 20: DRIVERS
CREATE TABLE IF NOT EXISTS drivers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    license_number VARCHAR(100) UNIQUE NOT NULL,
    driver_status VARCHAR(50) NOT NULL DEFAULT 'AVAILABLE' CHECK (driver_status IN ('OFFLINE', 'AVAILABLE', 'EN_ROUTE_PICKUP', 'IN_TRANSIT', 'COMPLETED')),
    current_lat DOUBLE PRECISION,
    current_lng DOUBLE PRECISION,
    vehicle_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- TABLE 21: VEHICLES
CREATE TABLE IF NOT EXISTS vehicles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    license_plate VARCHAR(50) UNIQUE NOT NULL,
    vehicle_type VARCHAR(50) NOT NULL DEFAULT 'STANDARD_VAN' CHECK (vehicle_type IN ('REFRIGERATED_VAN', 'STANDARD_VAN', 'ELECTRIC_CARGO_VAN', 'HEAVY_TRUCK')),
    payload_capacity_kg DOUBLE PRECISION NOT NULL DEFAULT 400.0 CHECK (payload_capacity_kg > 0),
    active_cooling BOOLEAN NOT NULL DEFAULT FALSE,
    current_compartment_temp_c DOUBLE PRECISION,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

DO $$ BEGIN
    ALTER TABLE drivers ADD CONSTRAINT fk_drivers_vehicle FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE SET NULL;
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- TABLE 22: ROUTES
CREATE TABLE IF NOT EXISTS routes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    driver_id UUID REFERENCES drivers(id) ON DELETE SET NULL,
    vehicle_id UUID REFERENCES vehicles(id) ON DELETE SET NULL,
    route_code VARCHAR(100) UNIQUE NOT NULL,
    total_distance_km DOUBLE PRECISION NOT NULL DEFAULT 0.0 CHECK (total_distance_km >= 0),
    estimated_duration_mins DOUBLE PRECISION NOT NULL DEFAULT 0.0 CHECK (estimated_duration_mins >= 0),
    solver_status VARCHAR(50) NOT NULL DEFAULT 'OPTIMAL',
    solver_model VARCHAR(50) NOT NULL DEFAULT 'GOOGLE_OR_TOOLS_CVRPTW',
    waypoints_count INT NOT NULL DEFAULT 0 CHECK (waypoints_count >= 0),
    status VARCHAR(50) NOT NULL DEFAULT 'SCHEDULED' CHECK (status IN ('SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED')),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- TABLE 23: DELIVERIES
CREATE TABLE IF NOT EXISTS deliveries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    route_id UUID REFERENCES routes(id) ON DELETE SET NULL,
    donation_id UUID NOT NULL REFERENCES donations(id) ON DELETE CASCADE,
    pickup_request_id UUID REFERENCES pickup_requests(id) ON DELETE SET NULL,
    driver_id UUID REFERENCES drivers(id) ON DELETE SET NULL,
    stop_sequence INT NOT NULL DEFAULT 1 CHECK (stop_sequence > 0),
    status VARCHAR(50) NOT NULL DEFAULT 'ASSIGNED' CHECK (status IN ('ASSIGNED', 'ARRIVED_PICKUP', 'PICKED_UP', 'IN_TRANSIT', 'ARRIVED_DROPOFF', 'DELIVERED', 'FAILED')),
    departure_at TIMESTAMPTZ,
    arrival_at TIMESTAMPTZ,
    actual_temp_at_delivery_c DOUBLE PRECISION,
    distance_km DOUBLE PRECISION NOT NULL DEFAULT 0.0 CHECK (distance_km >= 0),
    transit_time_mins DOUBLE PRECISION NOT NULL DEFAULT 0.0 CHECK (transit_time_mins >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- TABLE 24: QR_VERIFICATIONS
CREATE TABLE IF NOT EXISTS qr_verifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    delivery_id UUID NOT NULL REFERENCES deliveries(id) ON DELETE CASCADE,
    stage VARCHAR(50) NOT NULL CHECK (stage IN ('PICKUP_HANDOVER', 'DELIVERY_RECEIPT')),
    nonce VARCHAR(64) UNIQUE NOT NULL,
    hmac_signature VARCHAR(128) NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    expires_at TIMESTAMPTZ NOT NULL,
    is_burned BOOLEAN NOT NULL DEFAULT FALSE,
    burned_at TIMESTAMPTZ,
    verified_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    verified_lat DOUBLE PRECISION,
    verified_lng DOUBLE PRECISION,
    verified_temp_c DOUBLE PRECISION,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- TABLE 25: NOTIFICATIONS
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    category VARCHAR(50) NOT NULL CHECK (category IN ('URGENT_EXPIRY', 'DISPATCH', 'PRODUCTION', 'AUDIT', 'SYSTEM')),
    priority VARCHAR(50) NOT NULL DEFAULT 'NORMAL' CHECK (priority IN ('LOW', 'NORMAL', 'HIGH', 'CRITICAL')),
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    read_at TIMESTAMPTZ,
    action_url VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- TABLE 26: MODEL_PREDICTIONS
CREATE TABLE IF NOT EXISTS model_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    kitchen_id UUID REFERENCES kitchens(id) ON DELETE SET NULL,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50) NOT NULL DEFAULT 'v1.0',
    prediction_type VARCHAR(50) NOT NULL CHECK (prediction_type IN ('DEMAND_HEADCOUNT', 'SURPLUS_QUANTITY_KG', 'SPOILAGE_RISK')),
    target_date DATE NOT NULL,
    predicted_value DOUBLE PRECISION NOT NULL,
    confidence_lower_bound DOUBLE PRECISION,
    confidence_upper_bound DOUBLE PRECISION,
    features_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    r2_score DOUBLE PRECISION DEFAULT 0.829,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- TABLE 27: AI_RECOMMENDATIONS
CREATE TABLE IF NOT EXISTS ai_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    prediction_id UUID REFERENCES model_predictions(id) ON DELETE SET NULL,
    recipe_or_item_name VARCHAR(255) NOT NULL,
    recommendation_type VARCHAR(50) NOT NULL CHECK (recommendation_type IN ('BATCH_SIZE_ADJUSTMENT', 'SURPLUS_DIVERSION', 'EXPIRATION_PRIORITY')),
    recommended_action TEXT NOT NULL,
    rationale TEXT NOT NULL,
    estimated_waste_reduction_kg DOUBLE PRECISION NOT NULL DEFAULT 0.0 CHECK (estimated_waste_reduction_kg >= 0),
    estimated_cost_savings_usd DOUBLE PRECISION NOT NULL DEFAULT 0.0 CHECK (estimated_cost_savings_usd >= 0),
    confidence_percentage INT NOT NULL CHECK (confidence_percentage BETWEEN 0 AND 100),
    is_applied BOOLEAN NOT NULL DEFAULT FALSE,
    applied_at TIMESTAMPTZ,
    applied_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- TABLE 28: IMPACT_METRICS
CREATE TABLE IF NOT EXISTS impact_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    donation_id UUID REFERENCES donations(id) ON DELETE SET NULL,
    waste_record_id UUID REFERENCES waste_records(id) ON DELETE SET NULL,
    food_diverted_kg DOUBLE PRECISION NOT NULL CHECK (food_diverted_kg >= 0),
    meals_provided INT NOT NULL CHECK (meals_provided >= 0),
    co2e_avoided_kg DOUBLE PRECISION NOT NULL CHECK (co2e_avoided_kg >= 0),
    water_saved_liters DOUBLE PRECISION NOT NULL CHECK (water_saved_liters >= 0),
    financial_value_usd DOUBLE PRECISION NOT NULL CHECK (financial_value_usd >= 0),
    calculation_methodology VARCHAR(100) NOT NULL DEFAULT 'EPA_WARM_V15',
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- TABLE 29: DOCUMENTS (Vector RAG)
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL CHECK (category IN ('FDA_FOOD_CODE', 'GOOD_SAMARITAN_ACT', 'HACCP_SOP', 'COLD_CHAIN_STANDARD', 'MUNICIPAL_BYLAW')),
    content TEXT NOT NULL,
    regulatory_source VARCHAR(255),
    document_version VARCHAR(50) DEFAULT '2024.1',
    embedding_vector JSONB,
    is_public BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- TABLE 30: AUDIT_LOGS
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    module VARCHAR(100) NOT NULL,
    action VARCHAR(100) NOT NULL,
    entity_name VARCHAR(100) NOT NULL,
    entity_id VARCHAR(100) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    client_ip VARCHAR(50),
    user_agent TEXT,
    sha256_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. PERFORMANCE & LOOKUP INDEXES
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_org_members_user ON organization_members(user_id);
CREATE INDEX IF NOT EXISTS idx_org_members_org ON organization_members(organization_id);
CREATE INDEX IF NOT EXISTS idx_kitchens_org ON kitchens(organization_id);
CREATE INDEX IF NOT EXISTS idx_inventory_expiry ON inventory(expiry_date);
CREATE INDEX IF NOT EXISTS idx_inventory_status ON inventory(status);
CREATE INDEX IF NOT EXISTS idx_batches_kitchen ON production_batches(kitchen_id);
CREATE INDEX IF NOT EXISTS idx_batches_status ON production_batches(status);
CREATE INDEX IF NOT EXISTS idx_waste_kitchen ON waste_records(kitchen_id);
CREATE INDEX IF NOT EXISTS idx_waste_recorded_at ON waste_records(recorded_at);
CREATE INDEX IF NOT EXISTS idx_surplus_status ON surplus_items(status);
CREATE INDEX IF NOT EXISTS idx_surplus_deadline ON surplus_items(safe_consumption_deadline);
CREATE INDEX IF NOT EXISTS idx_donations_status ON donations(status);
CREATE INDEX IF NOT EXISTS idx_donations_tracking ON donations(tracking_number);
CREATE INDEX IF NOT EXISTS idx_deliveries_route ON deliveries(route_id);
CREATE INDEX IF NOT EXISTS idx_deliveries_status ON deliveries(status);
CREATE INDEX IF NOT EXISTS idx_qr_nonce_unburned ON qr_verifications(nonce) WHERE is_burned = FALSE;
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at);

-- 5. ROW LEVEL SECURITY (RLS) POLICIES
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE organization_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE kitchens ENABLE ROW LEVEL SECURITY;
ALTER TABLE processing_units ENABLE ROW LEVEL SECURITY;
ALTER TABLE menus ENABLE ROW LEVEL SECURITY;
ALTER TABLE menu_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE ingredients ENABLE ROW LEVEL SECURITY;
ALTER TABLE inventory ENABLE ROW LEVEL SECURITY;
ALTER TABLE inventory_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE production_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE consumption_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE waste_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE surplus_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE recipients ENABLE ROW LEVEL SECURITY;
ALTER TABLE recipient_requirements ENABLE ROW LEVEL SECURITY;
ALTER TABLE donations ENABLE ROW LEVEL SECURITY;
ALTER TABLE donation_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE pickup_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE drivers ENABLE ROW LEVEL SECURITY;
ALTER TABLE vehicles ENABLE ROW LEVEL SECURITY;
ALTER TABLE routes ENABLE ROW LEVEL SECURITY;
ALTER TABLE deliveries ENABLE ROW LEVEL SECURITY;
ALTER TABLE qr_verifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE impact_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Helper function to extract user organization_id from Supabase JWT
CREATE OR REPLACE FUNCTION auth_user_org_id()
RETURNS TEXT AS $$
BEGIN
    RETURN COALESCE(
        NULLIF(current_setting('request.jwt.claims', true), '')::jsonb -> 'app_metadata' ->> 'organization_id',
        '00000000-0000-0000-0000-000000000000'
    );
END;
$$ LANGUAGE plpgsql STABLE;

-- Helper function to check if current user is ADMIN or AUDITOR
CREATE OR REPLACE FUNCTION auth_user_role()
RETURNS VARCHAR AS $$
BEGIN
    RETURN COALESCE(
        NULLIF(current_setting('request.jwt.claims', true), '')::jsonb -> 'app_metadata' ->> 'role',
        'GUEST'
    );
END;
$$ LANGUAGE plpgsql STABLE;

-- RLS POLICY: Organizations Isolation
DO $$ BEGIN
    CREATE POLICY org_tenant_isolation ON organizations
        FOR ALL USING (
            auth_user_role() = 'ADMIN' OR
            id::text = auth_user_org_id()::text OR
            auth_user_role() = 'AUDITOR'
        );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- RLS POLICY: Surplus Items (Public Read for NGOs, Scoped Write for Donors)
DO $$ BEGIN
    CREATE POLICY surplus_marketplace_read ON surplus_items
        FOR SELECT USING (
            status IN ('DECLARED', 'MATCHED') OR
            organization_id::text = auth_user_org_id()::text OR
            auth_user_role() IN ('ADMIN', 'AUDITOR')
        );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE POLICY surplus_tenant_mutate ON surplus_items
        FOR ALL USING (
            organization_id::text = auth_user_org_id()::text OR
            auth_user_role() = 'ADMIN'
        );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- RLS POLICY: Inventory Tenant Isolation
DO $$ BEGIN
    CREATE POLICY inventory_tenant_isolation ON inventory
        FOR ALL USING (
            EXISTS (
                SELECT 1 FROM kitchens k
                WHERE k.id = inventory.kitchen_id AND (k.organization_id::text = auth_user_org_id()::text OR auth_user_role() IN ('ADMIN', 'AUDITOR'))
            ) OR
            EXISTS (
                SELECT 1 FROM processing_units pu
                WHERE pu.id = inventory.processing_unit_id AND (pu.organization_id::text = auth_user_org_id()::text OR auth_user_role() IN ('ADMIN', 'AUDITOR'))
            ) OR
            auth_user_role() = 'ADMIN'
        );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
