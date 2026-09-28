"""
FoodLoop AI - Phase 15: Impact Analytics Engine Test Suite
Tests for:
1. Documented configurable emission factors (EPA WARM v15 / FAO)
2. All 11 core impact & operational metrics
3. Mandatory labeling of environmental metrics as estimates with audit disclaimer
4. Daily, Weekly, Monthly, Yearly granularity time views
5. All 8 required charts generation
6. Strict multi-tenant security scoping ("Do not expose data outside authorized scope")
7. Admin filtering by organization, kitchen, date range, and food category
"""

import pytest
from datetime import datetime, timedelta, timezone

from app.main import app
from app.models.models import (
    Organization,
    Kitchen,
    User,
    WasteRecord,
    SurplusItem,
    Delivery,
    ImpactEmissionFactor
)
from app.core.security import get_current_user


# Mock Auth Dependency Fixtures
def admin_user():
    return {
        "id": "admin-user-001",
        "email": "superadmin@foodloop.ai",
        "role": "SUPER_ADMIN",
        "organization_id": "org-alpha-111",
        "organization_name": "FoodLoop Global HQ"
    }


def regular_kitchen_mgr():
    return {
        "id": "mgr-user-002",
        "email": "chef@hyatthospitality.com",
        "role": "KITCHEN_MANAGER",
        "organization_id": "org-alpha-111",
        "organization_name": "Hyatt Hospitality"
    }


def outside_tenant_user():
    return {
        "id": "mgr-user-999",
        "email": "external@competitor.com",
        "role": "KITCHEN_MANAGER",
        "organization_id": "org-beta-222",
        "organization_name": "External Restaurant Co"
    }


# ====================================================================
# TEST 1: DEFAULT DOCUMENTED EMISSION FACTORS SEEDING
# ====================================================================

def test_default_documented_emission_factors_seeding(client, db):
    """Verify standard documented lifecycle factors (EPA WARM v15 & FAO) are seeded."""
    app.dependency_overrides[get_current_user] = admin_user
    try:
        response = client.get("/api/v1/impact/emission-factors")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 8

        categories = [item["category"] for item in data]
        assert "DEFAULT" in categories
        assert "PRODUCE" in categories
        assert "DAIRY" in categories
        assert "MEAT_POULTRY" in categories
        assert "BAKERY" in categories
        assert "PREPARED_MEALS" in categories

        # Verify documentation citation
        default_factor = next(d for d in data if d["category"] == "DEFAULT")
        assert "EPA WARM" in default_factor["documentation_source"]
        assert default_factor["co2e_kg_per_kg_food"] == 2.5
        assert default_factor["water_liters_per_kg_food"] == 1850.0
        assert default_factor["is_estimate"] is True
    finally:
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]


# ====================================================================
# TEST 2: CUSTOM EMISSION FACTOR CONFIGURATION
# ====================================================================

def test_custom_emission_factor_configuration(client, db):
    """Verify administrator can configure emission factors with custom documentation."""
    app.dependency_overrides[get_current_user] = admin_user
    try:
        payload = {
            "organization_id": "org-alpha-111",
            "category": "DAIRY",
            "co2e_kg_per_kg_food": 5.2,
            "water_liters_per_kg_food": 1150.0,
            "landfill_diversion_m3_per_kg": 0.0012,
            "meal_equivalent_kg": 0.40,
            "people_served_per_meal": 1.0,
            "economic_value_usd_per_kg": 6.50,
            "production_cost_factor_per_kg": 4.10,
            "documentation_source": "ISO 14044 Certified Dairy Lifecycle Assessment 2026",
            "notes": "Custom high-protein yogurt batch lifecycle"
        }
        response = client.post("/api/v1/impact/emission-factors", json=payload)
        assert response.status_code == 200
        factor = response.json()
        assert factor["category"] == "DAIRY"
        assert factor["co2e_kg_per_kg_food"] == 5.2
        assert factor["water_liters_per_kg_food"] == 1150.0
        assert "ISO 14044" in factor["documentation_source"]
        assert factor["is_estimate"] is True
    finally:
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]


# ====================================================================
# TEST 3: CORE METRICS CALCULATION (11 METRICS)
# ====================================================================

def test_calculate_impact_analytics_core_metrics(client, db):
    """Verify all 11 core metrics are accurately computed from operational records."""
    # Seed test org and kitchen
    org = Organization(
        id="org-alpha-111",
        name="Hyatt Hospitality Group",
        registration_number="REG-HYATT-1001",
        address="123 Hotel Way, San Francisco, CA",
        latitude=37.7749,
        longitude=-122.4194,
        contact_email="admin@hyatt.com",
        contact_phone="+1-415-555-0199"
    )
    db.add(org)
    kitchen = Kitchen(
        id="kitchen-k1",
        organization_id=org.id,
        name="Grand Ballroom Kitchen",
        address="123 Hotel Way, San Francisco, CA",
        latitude=37.7749,
        longitude=-122.4194
    )
    db.add(kitchen)
    db.commit()

    now = datetime.now(timezone.utc)
    # Add waste records
    w1 = WasteRecord(
        kitchen_id=kitchen.id,
        organization_id=org.id,
        food_item="Trimmings",
        waste_category="PREPARATION_WASTE",
        weight_kg=40.0,
        cost_loss_usd=130.0,
        recorded_at=now - timedelta(days=2)
    )
    w2 = WasteRecord(
        kitchen_id=kitchen.id,
        organization_id=org.id,
        food_item="Leftover rice",
        waste_category="OVERPRODUCTION",
        weight_kg=25.0,
        cost_loss_usd=75.0,
        recorded_at=now - timedelta(days=1)
    )
    db.add_all([w1, w2])

    # Add surplus items
    s1 = SurplusItem(
        id="surplus-s1",
        kitchen_id=kitchen.id,
        organization_id=org.id,
        title="Prepared Entree Pans",
        category="PREPARED_MEALS",
        quantity_kg=120.0,
        portions=250,
        status="DELIVERED",
        pickup_address="123 Hotel Way",
        pickup_lat=37.77,
        pickup_lng=-122.41,
        created_at=now - timedelta(days=2)
    )
    s2 = SurplusItem(
        id="surplus-s2",
        kitchen_id=kitchen.id,
        organization_id=org.id,
        title="Artisan Breads",
        category="BAKERY",
        quantity_kg=60.0,
        portions=100,
        status="CLAIMED",
        pickup_address="123 Hotel Way",
        pickup_lat=37.77,
        pickup_lng=-122.41,
        created_at=now - timedelta(days=1)
    )
    db.add_all([s1, s2])

    # Add deliveries
    d1 = Delivery(
        id="delivery-d1",
        surplus_item_id="surplus-s1",
        cargo_weight_kg=120.0,
        status="DELIVERED",
        transit_time_mins=22.0,
        created_at=now - timedelta(days=2)
    )
    d2 = Delivery(
        id="delivery-d2",
        surplus_item_id="surplus-s2",
        cargo_weight_kg=60.0,
        status="FAILED",
        transit_time_mins=35.0,
        created_at=now - timedelta(days=1)
    )
    db.add_all([d1, d2])
    db.commit()

    app.dependency_overrides[get_current_user] = admin_user
    try:
        response = client.get("/api/v1/impact/analytics?organization_id=org-alpha-111&time_granularity=monthly")
        assert response.status_code == 200
        data = response.json()
        kpis = data["kpis"]

        # Check all 11 core metrics
        # 1. Food rescued
        assert kpis["food_rescued_kg"] == 180.0
        # 2. Food waste
        assert kpis["food_waste_kg"] == 65.0
        # 3. Waste reduction percentage (180 / 245 = ~73.5%)
        assert 70.0 <= kpis["waste_reduction_percentage"] <= 75.0
        # 4. Meals equivalent (180 / 0.42 = ~428)
        assert kpis["meals_equivalent"] >= 400
        # 5. People served
        assert kpis["people_served"] >= 400
        # 6. Estimated value preserved
        assert kpis["estimated_value_preserved_usd"] > 0
        # 7. Production cost saved
        assert kpis["production_cost_saved_usd"] > 0
        # 8. Redistribution count
        assert kpis["redistribution_count"] == 2
        # 9. Successful deliveries
        assert kpis["successful_deliveries"] == 1
        # 10. Failed deliveries
        assert kpis["failed_deliveries"] == 1
        # 11. Average pickup time
        assert 20.0 <= kpis["average_pickup_time_minutes"] <= 30.0

    finally:
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]


# ====================================================================
# TEST 4: ENVIRONMENTAL ESTIMATES MANDATORY LABELING
# ====================================================================

def test_environmental_metrics_estimate_labeling(client, db):
    """Verify environmental metrics are explicitly labeled as estimates with disclaimer."""
    app.dependency_overrides[get_current_user] = admin_user
    try:
        response = client.get("/api/v1/impact/analytics")
        assert response.status_code == 200
        data = response.json()
        kpis = data["kpis"]

        assert kpis["is_environmental_estimate"] is True
        assert "ESTIMATE NOTICE" in kpis["environmental_estimate_disclaimer"]
        assert "EPA WARM" in kpis["environmental_estimate_disclaimer"]
        assert "operational estimates" in kpis["environmental_estimate_disclaimer"]

        # Verify environmental quantities
        assert kpis["co2e_avoided_kg"] > 0
        assert kpis["water_saved_liters"] > 0
        assert kpis["landfill_diverted_m3"] > 0
    finally:
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]


# ====================================================================
# TEST 5: TIME VIEWS (DAILY, WEEKLY, MONTHLY, YEARLY)
# ====================================================================

def test_multi_granularity_time_views(client, db):
    """Verify daily, weekly, monthly, and yearly aggregation views."""
    app.dependency_overrides[get_current_user] = admin_user
    try:
        for gran in ["daily", "weekly", "monthly", "yearly"]:
            response = client.get(f"/api/v1/impact/analytics?time_granularity={gran}")
            assert response.status_code == 200
            data = response.json()
            assert data["time_granularity"] == gran
            charts = data["charts"]
            assert len(charts["waste_trend"]) > 0
            assert len(charts["food_rescued"]) > 0
    finally:
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]


# ====================================================================
# TEST 6: ALL 8 REQUIRED CHARTS PRESENT & POPULATED
# ====================================================================

def test_all_8_required_charts_populated(client, db):
    """Verify that all 8 required charts exist and have structured data points."""
    app.dependency_overrides[get_current_user] = admin_user
    try:
        response = client.get("/api/v1/impact/analytics?time_granularity=monthly")
        assert response.status_code == 200
        charts = response.json()["charts"]

        # 1. waste trend
        assert "waste_trend" in charts
        assert len(charts["waste_trend"]) > 0
        assert "waste_kg" in charts["waste_trend"][0]

        # 2. food rescued
        assert "food_rescued" in charts
        assert len(charts["food_rescued"]) > 0
        assert "rescued_kg" in charts["food_rescued"][0]

        # 3. category breakdown
        assert "category_breakdown" in charts
        assert len(charts["category_breakdown"]) > 0
        assert "percentage_of_total" in charts["category_breakdown"][0]

        # 4. kitchen comparison
        assert "kitchen_comparison" in charts
        assert len(charts["kitchen_comparison"]) > 0
        assert "waste_reduction_pct" in charts["kitchen_comparison"][0]

        # 5. redistribution trend
        assert "redistribution_trend" in charts
        assert len(charts["redistribution_trend"]) > 0
        assert "redistribution_count" in charts["redistribution_trend"][0]

        # 6. forecast vs actual
        assert "forecast_vs_actual" in charts
        assert len(charts["forecast_vs_actual"]) > 0
        assert "predicted_waste_kg" in charts["forecast_vs_actual"][0]

        # 7. cost trend
        assert "cost_trend" in charts
        assert len(charts["cost_trend"]) > 0
        assert "value_preserved_usd" in charts["cost_trend"][0]

        # 8. operational efficiency
        assert "operational_efficiency" in charts
        assert len(charts["operational_efficiency"]) > 0
        assert "delivery_success_rate_pct" in charts["operational_efficiency"][0]
    finally:
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]


# ====================================================================
# TEST 7: SECURITY SCOPING ENFORCEMENT
# ====================================================================

def test_security_scoping_enforcement(client, db):
    """
    Ensure non-admin cannot access data outside their authorized organization.
    'Do not expose data outside authorized scope.'
    """
    # 1. Non-admin requests data with their own org -> Allowed
    app.dependency_overrides[get_current_user] = regular_kitchen_mgr
    try:
        response = client.get("/api/v1/impact/analytics?organization_id=org-alpha-111")
        assert response.status_code == 200
        data = response.json()
        assert data["filters_applied"]["organization_id"] == "org-alpha-111"

        # 2. Non-admin attempts to request another organization's data -> 403 Forbidden
        response = client.get("/api/v1/impact/analytics?organization_id=org-other-999")
        assert response.status_code == 403
        assert "Security Scope Violation" in response.json()["detail"]

        # 3. Non-admin requests with no org specified -> Automatically scoped to their own org
        response = client.get("/api/v1/impact/analytics")
        assert response.status_code == 200
        assert response.json()["filters_applied"]["organization_id"] == "org-alpha-111"

    finally:
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]


# ====================================================================
# TEST 8: ADMIN DASHBOARD FILTERING
# ====================================================================

def test_admin_dashboard_filtering(client, db):
    """Verify admin filtering by organization, kitchen, date, and food category."""
    app.dependency_overrides[get_current_user] = admin_user
    try:
        start = (datetime.now(timezone.utc) - timedelta(days=60)).strftime("%Y-%m-%d")
        end = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        url = (
            f"/api/v1/impact/analytics?"
            f"organization_id=org-alpha-111&"
            f"kitchen_id=kitchen-k1&"
            f"start_date={start}&"
            f"end_date={end}&"
            f"category=PREPARED_MEALS&"
            f"time_granularity=weekly"
        )
        response = client.get(url)
        assert response.status_code == 200
        data = response.json()
        filters = data["filters_applied"]
        assert filters["organization_id"] == "org-alpha-111"
        assert filters["kitchen_id"] == "kitchen-k1"
        assert filters["category"] == "PREPARED_MEALS"
        assert filters["time_granularity"] == "weekly"
    finally:
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]


# ====================================================================
# TEST 9: FILTER OPTIONS ENDPOINT
# ====================================================================

def test_filter_options_endpoint(client, db):
    """Verify filter options returns organizations, kitchens, categories, and granularities."""
    app.dependency_overrides[get_current_user] = admin_user
    try:
        response = client.get("/api/v1/impact/filter-options")
        assert response.status_code == 200
        data = response.json()
        assert "organizations" in data
        assert "kitchens" in data
        assert "categories" in data
        assert "granularities" in data
        assert "daily" in data["granularities"]
        assert "weekly" in data["granularities"]
        assert "monthly" in data["granularities"]
        assert "yearly" in data["granularities"]
    finally:
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]


# ====================================================================
# TEST 10: BACKWARD COMPATIBLE SUMMARY ENDPOINT
# ====================================================================

def test_legacy_summary_endpoint(client, db):
    """Verify backward-compatible summary endpoint works with disclaimer."""
    app.dependency_overrides[get_current_user] = admin_user
    try:
        response = client.get("/api/v1/impact/summary")
        assert response.status_code == 200
        data = response.json()
        assert "total_food_diverted_kg" in data
        assert "total_meals_provided" in data
        assert "total_co2_avoided_kg" in data
        assert "environmental_estimate_disclaimer" in data
        assert data["is_estimate"] is True
    finally:
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]
