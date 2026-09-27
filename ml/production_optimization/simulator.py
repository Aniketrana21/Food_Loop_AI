"""
FoodLoop AI - Production What-If Simulator
Provides real-time sensitivity analysis and interactive scenario evaluation.
Allows culinary operators to dynamically modify attendance, menu, planned production, and inventory,
and instantly observe the impact on demand, OR-Tools recommended production, predicted waste, and costs.
"""

from typing import Dict, Any, List, Optional
from .engine import production_optimizer


MENU_POPULARITY_MAP = {
    "Classic American Comfort": 0.22,
    "Mediterranean Harvest": 0.20,
    "Asian Wok & Noodle Bar": 0.26,
    "Chef's Daily Carvery Special": 0.28,
    "Global Plant-Forward Fusion": 0.18
}

CATEGORY_WEIGHT_MAP = {
    "VEGETABLES": 0.30,
    "MEAT_SEAFOOD": 0.35,
    "GRAINS_PASTA": 0.32,
    "PREPARED_SOUP": 0.40,
    "BAKERY": 0.15,
    "DAIRY": 0.20
}


def simulate_production_scenario(
    attendance: int = 1850,
    menu: str = "Classic American Comfort",
    production: int = 240,
    inventory: int = 20,
    dish_name: str = "Steamed Seasonal Market Vegetables",
    food_category: str = "VEGETABLES",
    food_cost: float = 3.50,
    kitchen_capacity: float = 300.0,
    ingredient_availability: float = 320.0,
    minimum_required_demand: Optional[float] = None,
    maximum_production_capacity: float = 350.0,
    holding_time_limit_hours: float = 4.0,
    inventory_age_hours: float = 1.0
) -> Dict[str, Any]:
    """
    Executes real-time What-If scenario simulation:
    1. Computes expected demand from attendance headcount and menu popularity.
    2. Runs Google OR-Tools optimization to determine optimal production.
    3. Compares the operator's planned batch vs OR-Tools recommendation.
    4. Generates a multi-point sensitivity curve across attendance shifts (-20% to +20%).
    """
    # 1. Demand Modeling
    pop_rate = MENU_POPULARITY_MAP.get(menu, 0.22)
    expected_demand = max(20, int(round(attendance * pop_rate)))
    portion_weight = CATEGORY_WEIGHT_MAP.get(food_category.upper(), 0.32)

    # Confidence Interval spread (±14%)
    d_low = max(10, int(round(expected_demand * 0.86)))
    d_high = int(round(expected_demand * 1.14))

    min_demand = float(minimum_required_demand) if minimum_required_demand is not None else round(expected_demand * 0.75)

    # 2. Run Google OR-Tools Optimizer
    opt_res = production_optimizer.optimize(
        demand_forecast=float(expected_demand),
        confidence_interval={"lower": float(d_low), "upper": float(d_high)},
        inventory=float(inventory),
        ingredient_availability=float(ingredient_availability),
        kitchen_capacity=float(kitchen_capacity),
        historical_waste=0.12,
        food_cost=float(food_cost),
        minimum_required_demand=float(min_demand),
        maximum_production_capacity=float(maximum_production_capacity),
        holding_time_limit_hours=float(holding_time_limit_hours),
        inventory_age_hours=float(inventory_age_hours),
        dish_name=dish_name,
        menu=menu,
        portion_weight_kg=portion_weight
    )

    # 3. User's Planned Production Scenario Assessment
    usable_inv = inventory if inventory_age_hours <= holding_time_limit_hours else 0
    total_planned_available = production + usable_inv
    planned_surplus_portions = max(0, total_planned_available - expected_demand)
    planned_waste_kg = round(planned_surplus_portions * portion_weight, 1)

    c_waste = round(food_cost * 1.25, 2)
    c_shortage = round(food_cost * 3.20, 2)
    planned_shortage = max(0, expected_demand - total_planned_available)

    planned_cost_usd = round(
        (production * food_cost) +
        (planned_surplus_portions * c_waste) +
        (planned_shortage * c_shortage),
        2
    )

    # Compare Savings
    opt_cost_usd = opt_res["estimated_cost"]["total_expected_cost_usd"]
    opt_waste_kg = opt_res["estimated_waste_kg"]

    waste_saved_kg = round(max(0.0, planned_waste_kg - opt_waste_kg), 1)
    cost_saved_usd = round(max(0.0, planned_cost_usd - opt_cost_usd), 2)

    # 4. Generate Sensitivity Curve (-20% to +20% Attendance Shifts)
    shifts = [-0.20, -0.10, 0.0, 0.10, 0.20]
    sensitivity_curve = []

    for s in shifts:
        s_att = int(round(attendance * (1.0 + s)))
        s_dem = max(20, int(round(s_att * pop_rate)))
        s_d_low = max(10, int(round(s_dem * 0.86)))
        s_d_high = int(round(s_dem * 1.14))

        s_opt = production_optimizer.optimize(
            demand_forecast=float(s_dem),
            confidence_interval={"lower": float(s_d_low), "upper": float(s_d_high)},
            inventory=float(inventory),
            ingredient_availability=float(ingredient_availability),
            kitchen_capacity=float(kitchen_capacity),
            food_cost=float(food_cost),
            minimum_required_demand=round(s_dem * 0.75),
            maximum_production_capacity=float(maximum_production_capacity),
            holding_time_limit_hours=float(holding_time_limit_hours),
            inventory_age_hours=float(inventory_age_hours),
            dish_name=dish_name,
            menu=menu,
            portion_weight_kg=portion_weight
        )

        scenario_label = f"{int(s * 100):+d}% Turnout" if s != 0 else "Baseline Turnout"
        sensitivity_curve.append({
            "scenario": scenario_label,
            "shift_percentage": int(s * 100),
            "attendance": s_att,
            "expected_demand": s_dem,
            "demand": s_dem,
            "recommended_production": s_opt["recommended_production"],
            "waste_portions": s_opt["expected_surplus"],
            "predicted_waste_kg": s_opt["estimated_waste_kg"],
            "total_cost_usd": s_opt["estimated_cost"]["total_expected_cost_usd"],
            "feasible": s_opt["feasible"]
        })

    return {
        "simulation_inputs": {
            "attendance": attendance,
            "menu": menu,
            "planned_production": production,
            "inventory": inventory,
            "dish_name": dish_name,
            "food_category": food_category,
            "food_cost": food_cost
        },
        "expected_demand": expected_demand,
        "recommended_production": opt_res["recommended_production"],
        "predicted_waste_portions": opt_res["expected_surplus"],
        "predicted_waste_kg": opt_res["estimated_waste_kg"],
        "estimated_cost": opt_res["estimated_cost"],
        "shortage_risk_pct": opt_res["expected_shortage_risk"],
        "comparison_vs_planned": {
            "planned_production": production,
            "planned_available_portions": total_planned_available,
            "planned_waste_kg": planned_waste_kg,
            "planned_cost_usd": planned_cost_usd,
            "waste_saved_kg": waste_saved_kg,
            "cost_saved_usd": cost_saved_usd,
            "is_optimizer_better": (waste_saved_kg > 0 or cost_saved_usd > 0)
        },
        "optimization_result": opt_res,
        "sensitivity_curve": sensitivity_curve
    }
