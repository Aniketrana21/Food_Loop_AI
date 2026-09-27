-- ====================================================================
-- FOODLOOP AI - Enterprise Production Database Seed Data (PostgreSQL 16)
-- Target Engine: Supabase Cloud PostgreSQL / SQLite Test Suite
-- Covers All 30 Core Tables with Realistic Relational Data
-- ====================================================================

-- 1. CLEAR EXISTING DATA SAFELY (CASCADE)
TRUNCATE TABLE 
    audit_logs,
    documents,
    impact_metrics,
    ai_recommendations,
    model_predictions,
    notifications,
    qr_verifications,
    deliveries,
    routes,
    drivers,
    vehicles,
    pickup_requests,
    donation_items,
    donations,
    recipient_requirements,
    recipients,
    surplus_items,
    waste_records,
    consumption_records,
    production_batches,
    inventory_transactions,
    inventory,
    ingredients,
    menu_items,
    menus,
    processing_units,
    kitchens,
    organization_members,
    organizations,
    users
CASCADE;

-- 2. USERS (6 ROLES: ADMIN, KITCHEN_MANAGER, PROCESSOR, NGO, DRIVER, AUDITOR)
-- Standard test password hash for 'DemoSafePass2026!'
INSERT INTO users (id, email, password_hash, full_name, role, phone, avatar_url, is_active, is_verified) VALUES
('11111111-1111-1111-1111-111111111111', 'admin@foodloop.ai', '$2b$12$e8w3c9X0Gk7x6uH8p9Z1eO7h4l0q1r2s3t4u5v6w7x8y9z0a1b2c3', 'Eleanor Vance', 'ADMIN', '+1-555-0100', 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150', TRUE, TRUE),
('22222222-2222-2222-2222-222222222222', 'chef.vance@hyatt-culinary.com', '$2b$12$e8w3c9X0Gk7x6uH8p9Z1eO7h4l0q1r2s3t4u5v6w7x8y9z0a1b2c3', 'Executive Chef Marcus Vance', 'KITCHEN_MANAGER', '+1-555-0101', 'https://images.unsplash.com/photo-1577219491135-ce391730fb2c?w=150', TRUE, TRUE),
('33333333-3333-3333-3333-333333333333', 'processor.chen@bayprocessing.com', '$2b$12$e8w3c9X0Gk7x6uH8p9Z1eO7h4l0q1r2s3t4u5v6w7x8y9z0a1b2c3', 'Dr. David Chen', 'PROCESSOR', '+1-555-0102', 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150', TRUE, TRUE),
('44444444-4444-4444-4444-444444444444', 'director@stjudefoodbank.org', '$2b$12$e8w3c9X0Gk7x6uH8p9Z1eO7h4l0q1r2s3t4u5v6w7x8y9z0a1b2c3', 'Maria Rodriguez', 'NGO', '+1-555-0103', 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150', TRUE, TRUE),
('55555555-5555-5555-5555-555555555555', 'alex.driver@looplogistics.com', '$2b$12$e8w3c9X0Gk7x6uH8p9Z1eO7h4l0q1r2s3t4u5v6w7x8y9z0a1b2c3', 'Alex Mercer', 'DRIVER', '+1-555-0104', 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150', TRUE, TRUE),
('66666666-6666-6666-6666-666666666666', 'auditor.helena@dph-safety.gov', '$2b$12$e8w3c9X0Gk7x6uH8p9Z1eO7h4l0q1r2s3t4u5v6w7x8y9z0a1b2c3', 'Helena Brandt', 'AUDITOR', '+1-555-0105', 'https://images.unsplash.com/photo-1580489944761-15a19d654956?w=150', TRUE, TRUE);

-- 3. ORGANIZATIONS
INSERT INTO organizations (id, name, org_type, registration_number, tax_id, license_fssai_fda, address, latitude, longitude, contact_email, contact_phone, is_verified) VALUES
('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'FoodLoop AI Global Platform HQ', 'GOVERNMENT_AUDITOR', 'REG-FL-HQ-001', 'TAX-889412-A', 'LIC-FDA-99410', '1 Market St, Suite 400, San Francisco, CA', 37.7955, -122.3937, 'governance@foodloop.ai', '+1-555-0100', TRUE),
('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'Grand Hyatt San Francisco Culinary Center', 'COMMERCIAL_KITCHEN', 'REG-HYATT-SF-04', 'TAX-441209-B', 'LIC-FSSAI-88124', '345 Stockton St, San Francisco, CA', 37.7892, -122.4064, 'kitchen@hyatt-culinary.com', '+1-415-398-1234', TRUE),
('cccccccc-cccc-cccc-cccc-cccccccccccc', 'Bay Area Canning & Puree Plant', 'FOOD_PROCESSOR', 'REG-BAY-FPU-02', 'TAX-661298-C', 'LIC-FDA-44192', '780 Industrial Pkwy, Hayward, CA', 37.6481, -122.0682, 'intake@bayprocessing.com', '+1-510-782-9900', TRUE),
('dddddddd-dddd-dddd-dddd-dddddddddddd', 'Downtown St. Jude Food Bank & Pantry', 'NGO', 'REG-STJUDE-NGO-09', 'TAX-501C3-1192', 'LIC-HEALTH-3391', '812 Mission Blvd, San Francisco, CA', 37.7818, -122.4057, 'intake@stjudefoodbank.org', '+1-415-552-4411', TRUE),
('eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee', 'FoodLoop Express Logistics Fleet', 'LOGISTICS_PROVIDER', 'REG-LOOP-FLEET-03', 'TAX-339912-E', 'LIC-DOT-77491', '100 Logistics Way, Bay 4, South San Francisco, CA', 37.6547, -122.4077, 'dispatch@looplogistics.com', '+1-650-877-3300', TRUE);

-- 4. ORGANIZATION MEMBERS
INSERT INTO organization_members (id, organization_id, user_id, role_in_org, is_primary) VALUES
('m1111111-1111-1111-1111-111111111111', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '11111111-1111-1111-1111-111111111111', 'SUPER_ADMIN', TRUE),
('m2222222-2222-2222-2222-222222222222', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', '22222222-2222-2222-2222-222222222222', 'EXECUTIVE_CHEF', TRUE),
('m3333333-3333-3333-3333-333333333333', 'cccccccc-cccc-cccc-cccc-cccccccccccc', '33333333-3333-3333-3333-333333333333', 'PLANT_DIRECTOR', TRUE),
('m4444444-4444-4444-4444-444444444444', 'dddddddd-dddd-dddd-dddd-dddddddddddd', '44444444-4444-4444-4444-444444444444', 'LOGISTICS_DIRECTOR', TRUE),
('m5555555-5555-5555-5555-555555555555', 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee', '55555555-5555-5555-5555-555555555555', 'SENIOR_COURIER', TRUE),
('m6666666-6666-6666-6666-666666666666', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '66666666-6666-6666-6666-666666666666', 'CHIEF_AUDITOR', FALSE);

-- 5. KITCHENS & PROCESSING UNITS
INSERT INTO kitchens (id, organization_id, name, address, latitude, longitude, daily_meal_capacity, storage_specs) VALUES
('k1111111-1111-1111-1111-111111111111', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'Grand Hyatt Main Banquet Kitchen #04', '345 Stockton St, San Francisco, CA', 37.7892, -122.4064, 1500, '{"ambient_sqm": 80, "refrigerated_liters": 4500, "frozen_liters": 2500}'::jsonb);

INSERT INTO processing_units (id, organization_id, name, address, latitude, longitude, processing_type, daily_capacity_kg, cold_tank_capacity_liters) VALUES
('p1111111-1111-1111-1111-111111111111', 'cccccccc-cccc-cccc-cccc-cccccccccccc', 'Bay Area Canning & Puree Plant #02', '780 Industrial Pkwy, Hayward, CA', 37.6481, -122.0682, 'Aseptic Tomato & Puree Processing', 5000.0, 10000.0);

-- 6. MENUS & MENU ITEMS
INSERT INTO menus (id, kitchen_id, name, service_date, meal_service, planned_headcount, status) VALUES
('menu1111-1111-1111-1111-111111111111', 'k1111111-1111-1111-1111-111111111111', 'Executive Conference Lunch Service', CURRENT_DATE, 'LUNCH', 480, 'IN_PRODUCTION');

INSERT INTO menu_items (id, menu_id, dish_name, planned_portions, portion_weight_grams, dietary_category, allergens, cost_per_portion) VALUES
('mi111111-1111-1111-1111-111111111111', 'menu1111-1111-1111-1111-111111111111', 'Mediterranean Lemon Herb Grilled Chicken', 350, 420.0, 'STANDARD', ARRAY['Dairy'], 4.15),
('mi222222-2222-2222-2222-222222222222', 'menu1111-1111-1111-1111-111111111111', 'Quinoa & Roasted Veggie Mezze Bowl', 130, 380.0, 'VEGAN', ARRAY['Sesame'], 2.85);

-- 7. INGREDIENTS & INVENTORY
INSERT INTO ingredients (id, organization_id, name, category, unit, standard_cost_per_unit, allergen_profile, storage_temp_category) VALUES
('ing11111-1111-1111-1111-111111111111', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'Fresh Boneless Chicken Thighs', 'Meat & Poultry', 'kg', 6.80, ARRAY[]::TEXT[], 'REFRIGERATED'),
('ing22222-2222-2222-2222-222222222222', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'Roma Cooking Tomatoes', 'Produce', 'kg', 2.10, ARRAY[]::TEXT[], 'ROOM_TEMP'),
('ing33333-3333-3333-3333-333333333333', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'Organic Heavy Cream 36%', 'Dairy', 'liters', 4.20, ARRAY['Dairy'], 'REFRIGERATED');

INSERT INTO inventory (id, kitchen_id, ingredient_id, lot_number, current_quantity, reserved_quantity, unit, reorder_level, storage_temp, storage_location, expiry_date, status) VALUES
('inv11111-1111-1111-1111-111111111111', 'k1111111-1111-1111-1111-111111111111', 'ing11111-1111-1111-1111-111111111111', 'LOT-2026-CHK-71', 82.0, 20.0, 'kg', 30.0, 'Chilled (0-4°C)', 'Walk-in Chiller Bay A', NOW() + INTERVAL '4 days', 'OPTIMAL'),
('inv22222-2222-2222-2222-222222222222', 'k1111111-1111-1111-1111-111111111111', 'ing22222-2222-2222-2222-222222222222', 'LOT-2026-TOM-44', 145.0, 30.0, 'kg', 40.0, 'Dry Ambient (15-22°C)', 'Dry Storage Room 2', NOW() + INTERVAL '3 days', 'OPTIMAL'),
('inv33333-3333-3333-3333-333333333333', 'k1111111-1111-1111-1111-111111111111', 'ing33333-3333-3333-3333-333333333333', 'LOT-2026-CRM-31', 8.0, 0.0, 'liters', 15.0, 'Chilled (0-4°C)', 'Dairy Cooler 1', NOW() + INTERVAL '22 hours', 'CRITICAL');

INSERT INTO inventory_transactions (id, inventory_id, transaction_type, quantity, unit, reference_id, performed_by_user_id, notes) VALUES
('it111111-1111-1111-1111-111111111111', 'inv11111-1111-1111-1111-111111111111', 'INFLOW_PURCHASE', 100.0, 'kg', 'PO-99412', '22222222-2222-2222-2222-222222222222', 'Delivery received from Pacific Meat Supply with cold chain certificate.');

-- 8. PRODUCTION BATCHES
INSERT INTO production_batches (id, kitchen_id, menu_item_id, batch_number, planned_quantity, actual_prepared_quantity, unit, station, target_temp_c, current_temp_c, haccp_compliant, chef_user_id, status, started_at, completed_at) VALUES
('pb111111-1111-1111-1111-111111111111', 'k1111111-1111-1111-1111-111111111111', 'mi111111-1111-1111-1111-111111111111', 'BATCH-2026-0927-A', 350.0, 345.0, 'portions', 'Hot Kitchen Range A', 74.0, 76.5, TRUE, '22222222-2222-2222-2222-222222222222', 'HOLDING', NOW() - INTERVAL '2 hours', NOW() - INTERVAL '30 minutes');

-- 9. CONSUMPTION RECORDS
INSERT INTO consumption_records (id, batch_id, meal_service, planned_headcount, actual_headcount, variance_percentage, total_prepared_kg, total_consumed_kg, unconsumed_kg, diverted_to_surplus_kg, recorded_by_user_id, notes) VALUES
('cr111111-1111-1111-1111-111111111111', 'pb111111-1111-1111-1111-111111111111', 'LUNCH', 480, 420, -12.5, 144.9, 102.4, 42.5, 42.5, '22222222-2222-2222-2222-222222222222', 'Rainy conditions reduced attendance. 42.5 kg immediately blast chilled for FoodLoop rescue.');

-- 10. WASTE RECORDS
INSERT INTO waste_records (id, kitchen_id, batch_id, waste_category, weight_kg, cost_loss_usd, ghg_co2e_kg, epa_hierarchy_tier, department, root_cause, logged_by_user_id) VALUES
('wr111111-1111-1111-1111-111111111111', 'k1111111-1111-1111-1111-111111111111', 'pb111111-1111-1111-1111-111111111111', 'PREPARATION_TRIMMINGS', 14.2, 28.40, 35.5, 'COMPOST', 'Cold Prep Line 1', 'Root vegetable peelings & broccoli stalk ends', '22222222-2222-2222-2222-222222222222'),
('wr222222-2222-2222-2222-222222222222', 'k1111111-1111-1111-1111-111111111111', NULL, 'PLATE_SCRAPS', 22.8, 68.40, 57.0, 'COMPOST', 'Buffet Stations', 'Post-consumer plate residue from self-serve banquet', '22222222-2222-2222-2222-222222222222');

-- 11. SURPLUS ITEMS
INSERT INTO surplus_items (id, organization_id, kitchen_id, batch_id, title, description, category, quantity_kg, portions, storage_temp, safe_consumption_deadline, blast_chilled_at, calculated_shelf_life_hours, urgency_tier, pickup_address, pickup_lat, pickup_lng, dietary_tags, status) VALUES
('s1111111-1111-1111-1111-111111111111', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'k1111111-1111-1111-1111-111111111111', 'pb111111-1111-1111-1111-111111111111', 'Mediterranean Lemon Herb Grilled Chicken', 'Surplus banquet entrees blast-chilled to 3.2°C. Packed in sealed aluminum catering containers.', 'COOKED_MEALS', 42.5, 85, 'REFRIGERATED', NOW() + INTERVAL '4 hours', NOW() - INTERVAL '1 hour', 4.5, 'EXPEDITED', '345 Stockton St, Loading Dock B', 37.7892, -122.4064, ARRAY['Halal', 'High Protein'], 'DECLARED');

-- 12. RECIPIENTS & REQUIREMENTS
INSERT INTO recipients (id, organization_id, name, facility_type, address, latitude, longitude, max_daily_intake_kg, cold_storage_available, walk_in_chiller_capacity_kg, verified_charity_id, contact_person, contact_phone, is_active) VALUES
('r1111111-1111-1111-1111-111111111111', 'dddddddd-dddd-dddd-dddd-dddddddddddd', 'Downtown St. Jude Food Bank', 'FOOD_BANK', '812 Mission Blvd, San Francisco, CA', 37.7818, -122.4057, 300.0, TRUE, 150.0, 'CH-501C3-9981', 'Maria Rodriguez', '+1-415-552-4411', TRUE);

INSERT INTO recipient_requirements (id, recipient_id, acceptable_categories, dietary_preferences, required_storage_temp, min_portions_per_drop, max_delivery_distance_km) VALUES
('rr111111-1111-1111-1111-111111111111', 'r1111111-1111-1111-1111-111111111111', ARRAY['COOKED_MEALS', 'BAKERY', 'DAIRY', 'PRODUCE'], ARRAY['Halal', 'Vegetarian'], 'ANY', 20, 15.0);

-- 13. DONATIONS & DONATION ITEMS
INSERT INTO donations (id, donor_org_id, recipient_org_id, tracking_number, total_weight_kg, total_portions, status, haccp_verified, safe_handling_ack) VALUES
('d1111111-1111-1111-1111-111111111111', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'dddddddd-dddd-dddd-dddd-dddddddddddd', 'TRK-FL-89412-CA', 42.5, 85, 'COURIER_ASSIGNED', TRUE, TRUE);

INSERT INTO donation_items (id, donation_id, surplus_item_id, allocated_quantity_kg, allocated_portions) VALUES
('di111111-1111-1111-1111-111111111111', 'd1111111-1111-1111-1111-111111111111', 's1111111-1111-1111-1111-111111111111', 42.5, 85);

-- 14. PICKUP REQUESTS
INSERT INTO pickup_requests (id, donation_id, donor_address, donor_lat, donor_lng, ready_time, latest_pickup_time, assigned_driver_id, status) VALUES
('pr111111-1111-1111-1111-111111111111', 'd1111111-1111-1111-1111-111111111111', '345 Stockton St, Loading Dock B', 37.7892, -122.4064, NOW(), NOW() + INTERVAL '2 hours', '55555555-5555-5555-5555-555555555555', 'ACCEPTED');

-- 15. VEHICLES & DRIVERS
INSERT INTO vehicles (id, organization_id, license_plate, vehicle_type, payload_capacity_kg, active_cooling, current_compartment_temp_c, is_active) VALUES
('v1111111-1111-1111-1111-111111111111', 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee', '7XFL492', 'REFRIGERATED_VAN', 500.0, TRUE, 3.4, TRUE);

INSERT INTO drivers (id, user_id, organization_id, license_number, driver_status, current_lat, current_lng, vehicle_id) VALUES
('drv11111-1111-1111-1111-111111111111', '55555555-5555-5555-5555-555555555555', 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee', 'CA-DL-994821', 'EN_ROUTE_PICKUP', 37.7880, -122.4100, 'v1111111-1111-1111-1111-111111111111');

-- 16. ROUTES & DELIVERIES
INSERT INTO routes (id, driver_id, vehicle_id, route_code, total_distance_km, estimated_duration_mins, solver_status, solver_model, waypoints_count, status) VALUES
('rt111111-1111-1111-1111-111111111111', 'drv11111-1111-1111-1111-111111111111', 'v1111111-1111-1111-1111-111111111111', 'ROUTE-SF-402', 8.4, 28.0, 'OPTIMAL', 'GOOGLE_OR_TOOLS_CVRPTW', 3, 'IN_PROGRESS');

INSERT INTO deliveries (id, route_id, donation_id, pickup_request_id, driver_id, stop_sequence, status, actual_temp_at_delivery_c, distance_km, transit_time_mins) VALUES
('del11111-1111-1111-1111-111111111111', 'rt111111-1111-1111-1111-111111111111', 'd1111111-1111-1111-1111-111111111111', 'pr111111-1111-1111-1111-111111111111', 'drv11111-1111-1111-1111-111111111111', 1, 'IN_TRANSIT', 3.4, 3.8, 14.0);

-- 17. QR VERIFICATIONS
INSERT INTO qr_verifications (id, delivery_id, stage, nonce, hmac_signature, payload, expires_at, is_burned, verified_by_user_id, verified_lat, verified_lng, verified_temp_c) VALUES
('qr111111-1111-1111-1111-111111111111', 'del11111-1111-1111-1111-111111111111', 'PICKUP_HANDOVER', 'nonce-9941a8e2b8344e7c', 'a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e', '{"batch_id": "pb111111", "kg": 42.5, "temp": 3.2}'::jsonb, NOW() + INTERVAL '30 minutes', TRUE, '55555555-5555-5555-5555-555555555555', 37.7892, -122.4064, 3.2);

-- 18. NOTIFICATIONS
INSERT INTO notifications (id, user_id, organization_id, title, message, category, priority) VALUES
('notif111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'Courier Arriving at Dock B', 'Courier Alex Mercer (EV Van #3) is 0.8 km away for surplus pickup.', 'DISPATCH', 'HIGH');

-- 19. MODEL PREDICTIONS & RECOMMENDATIONS
INSERT INTO model_predictions (id, organization_id, kitchen_id, model_name, model_version, prediction_type, target_date, predicted_value, confidence_lower_bound, confidence_upper_bound, r2_score) VALUES
('pred1111-1111-1111-1111-111111111111', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'k1111111-1111-1111-1111-111111111111', 'XGBoost_Surplus_Regressor', 'v2.1', 'DEMAND_HEADCOUNT', CURRENT_DATE + 1, 425.0, 395.0, 455.0, 0.829);

INSERT INTO ai_recommendations (id, organization_id, prediction_id, recipe_or_item_name, recommendation_type, recommended_action, rationale, estimated_waste_reduction_kg, estimated_cost_savings_usd, confidence_percentage) VALUES
('rec11111-1111-1111-1111-111111111111', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'pred1111-1111-1111-1111-111111111111', 'Mediterranean Lemon Herb Grilled Chicken', 'BATCH_SIZE_ADJUSTMENT', 'Reduce batch prep target from 480 to 425 portions.', 'Historical drop in Monday lunch headcount post-holiday weekend.', 28.5, 232.0, 94);

-- 20. IMPACT METRICS
INSERT INTO impact_metrics (id, organization_id, donation_id, food_diverted_kg, meals_provided, co2e_avoided_kg, water_saved_liters, financial_value_usd, calculation_methodology) VALUES
('imp11111-1111-1111-1111-111111111111', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'd1111111-1111-1111-1111-111111111111', 42.5, 85, 106.25, 2450.0, 348.50, 'EPA_WARM_V15');

-- 21. DOCUMENTS (Vector RAG)
INSERT INTO documents (id, title, category, content, regulatory_source, document_version, is_public) VALUES
('doc11111-1111-1111-1111-111111111111', 'FDA Food Code Section 3-501.19 (Time Control & 4-Hour Rule)', 'FDA_FOOD_CODE', 'Ready-to-eat TCS food held without temperature control must be discarded or consumed within 4 hours if removed from cold storage at or below 41°F (5°C).', 'US FDA Food Code 2022', '2022.3', TRUE),
('doc22222-2222-2222-2222-222222222222', 'Bill Emerson Good Samaritan Food Donation Act (42 U.S. Code § 1791)', 'GOOD_SAMARITAN_ACT', 'Shields institutional donors and food recovery non-profits from civil and criminal liability arising from the nature, age, or packaging of apparently wholesome food.', 'Federal Food Donation Act of 1996 / Reauthorized 2023', '42-USC-1791', TRUE);

-- 22. AUDIT LOGS
INSERT INTO audit_logs (id, organization_id, user_id, module, action, entity_name, entity_id, client_ip, sha256_hash) VALUES
('aud11111-1111-1111-1111-111111111111', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', '22222222-2222-2222-2222-222222222222', 'SURPLUS_DISPATCH', 'DECLARE_SURPLUS_ITEM', 'surplus_items', 's1111111-1111-1111-1111-111111111111', '192.168.1.104', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855');
