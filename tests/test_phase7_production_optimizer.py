"""
FoodLoop AI - Phase 7 Production Optimizer & What-If Simulator Test Suite
Validates:
1. Google OR-Tools SCIP MILP Solver optimization model minimizing:
   food waste + shortage risk + production cost
2. All 9 required operational inputs:
   demand forecast, confidence interval, inventory, ingredient availability,
   kitchen capacity, historical waste, food cost, minimum required demand, maximum production capacity
3. Physical and business constraints:
   - production cannot exceed kitchen capacity
   - ingredient availability
   - minimum service requirement
   - inventory limits
   - food safety holding constraints (FDA Food Code § 3-501.19 4-hour rule)
   - integer quantities strictly enforced
4. Comprehensive outputs:
   recommended production, expected surplus, expected shortage risk,
   estimated cost, estimated waste, reasoning
5. Graceful infeasibility handling:
   never silently produce an invalid recommendation, diagnose bottlenecks, provide actionable resolutions
6. What-If Simulator engine:
   attendance, menu, production, inventory changes with immediate demand, recommended production,
   predicted waste, and estimated cost
7. FastAPI endpoints:
   - POST /api/v1/production/optimize
   - POST /api/v1/production/simulate
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.security import create_access_token
from ml.production_optimization.engine import (
    ProductionOptimizer,
    production_optimizer,
)
from ml.production_optimization.simulator import (
    simulate_production_scenario,
)

client = TestClient(app)


@pytest.fixture
def auth_headers():
    token = create_access_token(
        data={"sub": "chef.marcus@foodloop.org", "id": "test-chef-001", "role": "KITCHEN_MANAGER"}
    )
    return {"Authorization": f"Bearer {token}"}


# =====================================================================
# 1. OR-TOOLS ENGINE UNIT TESTS (OPTIMAL MILP FORMULATION)
# =====================================================================

def test_production_optimizer_all_9_inputs_optimal():
    """
    Verify OR-Tools SCIP model optimizes batch with all 9 required inputs:
    1. demand forecast
    2. confidence interval
    3. inventory
    4. ingredient availability
    5. kitchen capacity
    6. historical waste
    7. food cost
    8. minimum required demand
    9. maximum production capacity
    """
    optimizer = ProductionOptimizer()

    result = optimizer.optimize(
        dish_name="Roasted Mediterranean Vegetables",
        demand_forecast=220.0,
        confidence_interval={"lower": 190.0, "upper": 260.0},
        inventory=30.0,
        inventory_age_hours=1.5,
        ingredient_availability=300.0,
        kitchen_capacity=260.0,
        historical_waste=8.5,
        food_cost=3.50,
        minimum_required_demand=150.0,
        maximum_production_capacity=350.0,
    )

    # 1. Status and feasibility
    assert result["feasible"] is True
    assert result["status"] in ["OPTIMAL", "FEASIBLE"]
    assert "Google OR-Tools" in result["solver"]

    # 2. Strict Integer Production
    assert isinstance(result["recommended_production"], int)
    assert result["recommended_production"] >= 0

    # 3. Kitchen capacity and ingredient limits respected
    assert result["recommended_production"] <= 260
    assert result["recommended_production"] <= 300
    assert result["recommended_production"] <= 350

    # 4. Service requirement respected (Production + Inventory >= Minimum Demand)
    effective_inv = result["constraints_summary"]["usable_inventory"]
    assert result["recommended_production"] + effective_inv >= 150

    # 5. Core required output fields
    assert result["expected_demand"] == pytest.approx(220, abs=2)
    assert result["expected_surplus"] >= 0.0
    assert result["expected_shortage_risk"] >= 0.0 and result["expected_shortage_risk"] <= 100.0
    assert result["estimated_waste"] >= 0.0
    assert result["estimated_waste_kg"] >= 0.0

    # 6. Cost breakdown
    cost = result["estimated_cost"]
    assert cost["production_cost_usd"] > 0.0
    assert cost["total_expected_cost_usd"] >= cost["production_cost_usd"]

    # 7. Model reasoning
    assert len(result["reasoning"]) >= 2
    assert any("portions" in r for r in result["reasoning"])


def test_production_optimizer_respects_ingredient_and_capacity_ceilings():
    """
    Ensure the production batch never exceeds the minimum of kitchen capacity
    and ingredient availability, even when demand forecast is very high.
    """
    optimizer = ProductionOptimizer()

    result = optimizer.optimize(
        demand_forecast=500.0,
        confidence_interval={"lower": 450.0, "upper": 550.0},
        inventory=20.0,
        ingredient_availability=140.0,  # Tight ingredient bottleneck!
        kitchen_capacity=250.0,
        minimum_required_demand=100.0,
    )

    assert result["feasible"] is True
    # Production cannot exceed ingredient limit of 140
    assert result["recommended_production"] <= 140


def test_production_optimizer_haccp_food_safety_discard_rule():
    """
    Under FDA Food Code § 3-501.19, ready-to-eat TCS food held without temperature control
    must be discarded after 4 hours. Inventory older than 4 hours cannot offset demand.
    """
    optimizer = ProductionOptimizer()

    # Case A: Fresh inventory (< 3 hours old)
    res_fresh = optimizer.optimize(
        demand_forecast=200.0,
        inventory=40.0,
        inventory_age_hours=2.0,
        ingredient_availability=300.0,
        kitchen_capacity=300.0,
        minimum_required_demand=100.0,
    )
    assert res_fresh["constraints_summary"]["usable_inventory"] == 40

    # Case B: Expired inventory (> 4.0 hours old)
    res_expired = optimizer.optimize(
        demand_forecast=200.0,
        inventory=40.0,
        inventory_age_hours=4.5,  # Exceeds FDA 4h threshold!
        ingredient_availability=300.0,
        kitchen_capacity=300.0,
        minimum_required_demand=100.0,
    )
    # Zero usable inventory credited due to HACCP safety breach
    assert res_expired["constraints_summary"]["usable_inventory"] == 0
    # Production must be higher to compensate for discarded inventory
    assert res_expired["recommended_production"] > res_fresh["recommended_production"]


# =====================================================================
# 2. INFEASIBILITY DIAGNOSTICS & SAFETY SAFEGUARD TESTS
# =====================================================================

def test_production_optimizer_graceful_infeasibility_handling():
    """
    Requirement: "The optimizer must gracefully handle infeasible solutions.
    Never silently produce an invalid recommendation."

    Test when minimum service requirement cannot be satisfied due to kitchen or ingredient bottleneck.
    """
    optimizer = ProductionOptimizer()

    result = optimizer.optimize(
        dish_name="Atlantic Salmon Supreme",
        demand_forecast=250.0,
        inventory=10.0,
        ingredient_availability=120.0,  # Caps at 120
        kitchen_capacity=100.0,          # Caps at 100!
        minimum_required_demand=180.0,  # Impossible: 10 inv + 100 cap = 110 < 180!
    )

    # Must NOT raise exception and must NOT mark as feasible
    assert result["feasible"] is False
    assert result["status"] == "INFEASIBLE_CONSTRAINED"

    # Production must not exceed physical ceiling
    assert result["recommended_production"] <= 100

    # Comprehensive diagnostics provided
    details = result["infeasibility_details"]
    assert details is not None
    assert details["is_infeasible"] is True
    assert len(details["root_cause_conflicts"]) > 0
    assert len(details["actionable_bottleneck_resolutions"]) > 0
    assert "NEVER SILENTLY OVERRIDE" in details["warning_message"]

    # Reasoning clearly warns user
    assert any("INFEASIBLE" in r or "Shortfall" in r for r in result["reasoning"])


# =====================================================================
# 3. WHAT-IF SIMULATOR ENGINE TESTS
# =====================================================================

def test_what_if_simulator_responsiveness_and_outputs():
    """
    Requirement:
    "User can change: attendance, menu, production, inventory
    and immediately see: expected demand, recommended production, predicted waste, estimated cost"
    """
    result = simulate_production_scenario(
        attendance=2200,
        menu="Classic American Comfort",
        dish_name="Lemon Herb Baked Chicken",
        food_category="MEAT_POULTRY",
        production=300,
        inventory=35,
        food_cost=4.50,
        kitchen_capacity=350.0,
        ingredient_availability=380.0,
        minimum_required_demand=180.0,
    )

    # 1. Inputs reflected
    assert result["simulation_inputs"]["attendance"] == 2200
    assert result["simulation_inputs"]["planned_production"] == 300
    assert result["simulation_inputs"]["inventory"] == 35

    # 2. Immediate core outputs
    assert result["expected_demand"] > 0
    assert result["recommended_production"] > 0
    assert result["predicted_waste_portions"] >= 0
    assert result["predicted_waste_kg"] >= 0.0
    assert result["estimated_cost"]["total_expected_cost_usd"] > 0.0

    # 3. Head-to-Head Comparison vs Chef's planned batch
    comp = result["comparison_vs_planned"]
    assert comp["planned_production"] == 300
    assert "waste_saved_kg" in comp
    assert "cost_saved_usd" in comp
    assert isinstance(comp["is_optimizer_better"], bool)

    # 4. Sensitivity Curve (5 scenarios: -20%, -10%, baseline, +10%, +20%)
    assert len(result["sensitivity_curve"]) == 5
    assert result["sensitivity_curve"][0]["scenario"] == "-20% Turnout"
    assert result["sensitivity_curve"][2]["scenario"] == "Baseline Turnout"
    assert result["sensitivity_curve"][4]["scenario"] == "+20% Turnout"
    for pt in result["sensitivity_curve"]:
        assert pt["demand"] > 0
        assert pt["recommended_production"] >= 0


def test_what_if_simulator_infeasible_scenario():
    """
    Verify simulator handles infeasible scenarios gracefully
    when user inputs severe bottlenecks in the simulator.
    """
    result = simulate_production_scenario(
        attendance=3000,
        production=150,
        inventory=5,
        kitchen_capacity=80.0,          # Constrained
        ingredient_availability=70.0,   # Very constrained
        minimum_required_demand=200.0,  # Exceeds max possible
    )

    assert result["optimization_result"]["feasible"] is False
    assert result["optimization_result"]["status"] == "INFEASIBLE_CONSTRAINED"
    assert result["optimization_result"]["infeasibility_details"] is not None


# =====================================================================
# 4. FASTAPI ENDPOINT TESTS
# =====================================================================

def test_api_optimize_production_success(auth_headers):
    """
    Test POST /api/v1/production/optimize endpoint with full payload.
    """
    payload = {
        "dish_name": "Quinoa Garden Bowl",
        "food_category": "GRAINS",
        "demand_forecast": 180,
        "confidence_interval": {
            "lower": 160,
            "upper": 210,
            "confidence_level": 0.95
        },
        "inventory": 20,
        "inventory_age_hours": 1.0,
        "ingredient_availability": 250,
        "kitchen_capacity": 220,
        "maximum_production_capacity": 300,
        "historical_waste": 7.0,
        "food_cost": 2.80,
        "minimum_required_demand": 120
    }

    res = client.post("/api/v1/production/optimize", json=payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["feasible"] is True
    assert data["status"] in ["OPTIMAL", "FEASIBLE"]
    assert isinstance(data["recommended_production"], int)
    assert data["recommended_production"] <= 220
    assert data["expected_demand"] == 180
    assert data["expected_surplus"] >= 0
    assert data["expected_shortage_risk"] >= 0
    assert "estimated_cost" in data
    assert len(data["reasoning"]) > 0


def test_api_optimize_production_infeasible_diagnostics(auth_headers):
    """
    Test POST /api/v1/production/optimize returns 200 with feasible=False
    and comprehensive diagnostics when physical constraints conflict.
    """
    payload = {
        "dish_name": "Herb Crusted Salmon",
        "demand_forecast": 250,
        "inventory": 10,
        "ingredient_availability": 80,
        "kitchen_capacity": 90,
        "minimum_required_demand": 150,  # 80 ingredients < 150 - 10 = 140 needed!
    }

    res = client.post("/api/v1/production/optimize", json=payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["feasible"] is False
    assert data["status"] == "INFEASIBLE_CONSTRAINED"
    assert data["infeasibility_details"] is not None
    assert data["infeasibility_details"]["is_infeasible"] is True
    assert len(data["infeasibility_details"]["root_cause_conflicts"]) > 0
    assert len(data["infeasibility_details"]["actionable_bottleneck_resolutions"]) > 0


def test_api_simulate_what_if_endpoint(auth_headers):
    """
    Test POST /api/v1/production/simulate endpoint.
    """
    payload = {
        "attendance": 1900,
        "menu": "VEGETARIAN",
        "dish_name": "Steamed Seasonal Vegetables",
        "food_category": "VEGETABLES",
        "production": 250,
        "inventory": 20,
        "food_cost": 3.00,
        "kitchen_capacity": 300,
        "ingredient_availability": 320,
        "minimum_required_demand": 150
    }

    res = client.post("/api/v1/production/simulate", json=payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["expected_demand"] > 0
    assert data["recommended_production"] > 0
    assert "comparison_vs_planned" in data
    assert "sensitivity_curve" in data
    assert len(data["sensitivity_curve"]) == 5
