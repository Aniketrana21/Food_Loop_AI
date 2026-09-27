"""
FoodLoop AI - Production Optimization Engine (Google OR-Tools)
Solves multi-criteria stochastic production planning minimizing:
    Total Expected Cost = Production Cost + Expected Food Waste Penalty + Expected Shortage Risk Penalty
Subject to:
    - Kitchen equipment & station capacity limits
    - Ingredient availability limits
    - Minimum contractual / service requirements
    - Inventory holding limits & HACCP food safety constraints
    - Strict integer portion quantities
Gracefully diagnoses and handles infeasible constraints without silent invalid outputs.
"""

from typing import Dict, Any, List, Optional, Tuple
import math
from ortools.linear_solver import pywraplp


class ProductionOptimizer:
    """
    Mixed-Integer Linear Programming (MILP) Production Optimizer using Google OR-Tools.
    Optimizes prep quantities under demand uncertainty, capacity bounds, and food safety rules.
    """

    def __init__(self, solver_name: str = "SCIP"):
        self.solver_name = solver_name

    def optimize(
        self,
        demand_forecast: float,
        confidence_interval: Optional[Dict[str, float]] = None,
        inventory: float = 0.0,
        ingredient_availability: float = 300.0,
        kitchen_capacity: float = 300.0,
        historical_waste: float = 0.12,
        food_cost: float = 3.50,
        minimum_required_demand: float = 0.0,
        maximum_production_capacity: float = 350.0,
        holding_time_limit_hours: float = 4.0,
        inventory_age_hours: float = 0.0,
        dish_name: str = "Standard Dish",
        menu: str = "Classic Service",
        portion_weight_kg: float = 0.32,
        food_category: str = "GENERAL",
        unit_waste_cost: Optional[float] = None,
        unit_shortage_cost: Optional[float] = None,
        batch_granularity: int = 1,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Executes Google OR-Tools optimization.
        Returns recommended production, expected surplus, shortage risk, costs, and reasoning.
        Gracefully handles and diagnoses infeasible scenarios.
        """
        # 1. Food Safety & Usable Inventory Check
        safety_alert = None
        usable_inventory = float(inventory)

        if inventory > 0 and inventory_age_hours > holding_time_limit_hours:
            usable_inventory = 0.0
            safety_alert = (
                f"HACCP Food Safety Violation: On-hand inventory of {int(inventory)} portions has reached "
                f"{inventory_age_hours}h (exceeds {holding_time_limit_hours}h statutory discard limit under FDA Code § 3-501.19). "
                f"Inventory cannot be served and must be safely composted."
            )

        # 2. Demand Scenarios from Confidence Interval
        if confidence_interval and "lower" in confidence_interval and "upper" in confidence_interval:
            d_low = max(0.0, float(confidence_interval["lower"]))
            d_high = max(d_low, float(confidence_interval["upper"]))
        else:
            # Synthetic 90% confidence spread based on historical waste & variance
            spread = max(15.0, demand_forecast * 0.15)
            d_low = max(0.0, demand_forecast - spread)
            d_high = demand_forecast + spread

        d_mid = float(demand_forecast)
        d_low = min(d_low, d_mid)
        d_high = max(d_high, d_mid)

        # 5 Discretized Demand Scenarios with Probabilities
        scenarios = [
            {"demand": round(d_low), "prob": 0.20, "label": "Low Turnout"},
            {"demand": round(d_mid - 0.5 * (d_mid - d_low)), "prob": 0.20, "label": "Moderate Low"},
            {"demand": round(d_mid), "prob": 0.35, "label": "Expected Demand"},
            {"demand": round(d_mid + 0.5 * (d_high - d_mid)), "prob": 0.15, "label": "Moderate High"},
            {"demand": round(d_high), "prob": 0.10, "label": "Peak Demand"}
        ]

        # 3. Unit Costs & Penalties
        c_prod = float(food_cost)
        # Waste penalty incorporates ingredient loss plus disposal / emissions footprint
        c_waste = float(unit_waste_cost) if unit_waste_cost is not None else round(c_prod * 1.25, 2)
        # Shortage penalty reflects diner dissatisfaction, breach of service, and emergency substitution
        c_shortage = float(unit_shortage_cost) if unit_shortage_cost is not None else round(c_prod * 3.20, 2)

        # 4. Strict Infeasibility Pre-check
        # Physical maximum production ceiling
        max_possible_production = min(
            float(kitchen_capacity),
            float(ingredient_availability),
            float(maximum_production_capacity)
        )
        required_from_cooking = max(0.0, float(minimum_required_demand) - usable_inventory)

        if required_from_cooking > max_possible_production:
            return self._handle_infeasible_problem(
                dish_name=dish_name,
                minimum_required_demand=minimum_required_demand,
                usable_inventory=usable_inventory,
                required_from_cooking=required_from_cooking,
                kitchen_capacity=kitchen_capacity,
                ingredient_availability=ingredient_availability,
                maximum_production_capacity=maximum_production_capacity,
                demand_forecast=d_mid,
                food_cost=c_prod,
                portion_weight_kg=portion_weight_kg,
                safety_alert=safety_alert
            )

        # 5. Build and Solve Google OR-Tools MILP Model
        solver = pywraplp.Solver.CreateSolver(self.solver_name)
        if not solver:
            solver = pywraplp.Solver.CreateSolver("CBC")
        if not solver:
            raise RuntimeError(f"Unable to instantiate Google OR-Tools solver ({self.solver_name}).")

        # Decision Variable: Production quantity (integer portions)
        P = solver.IntVar(0.0, max_possible_production, "P_portions")

        # Auxiliary variables for piecewise linear surplus & shortage per scenario
        surplus_vars = []
        shortage_vars = []

        for idx, sc in enumerate(scenarios):
            d_val = float(sc["demand"])
            # W_s >= 0 (surplus portions in scenario s)
            W_s = solver.NumVar(0.0, solver.infinity(), f"W_{idx}")
            # U_s >= 0 (shortage portions in scenario s)
            U_s = solver.NumVar(0.0, solver.infinity(), f"U_{idx}")

            # Surplus constraint: W_s >= (P + usable_inventory) - d_val
            # Rewritten: W_s - P >= usable_inventory - d_val
            solver.Add(W_s - P >= usable_inventory - d_val)

            # Shortage constraint: U_s >= d_val - (P + usable_inventory)
            # Rewritten: U_s + P >= d_val - usable_inventory
            solver.Add(U_s + P >= d_val - usable_inventory)

            surplus_vars.append(W_s)
            shortage_vars.append(U_s)

        # Minimum Required Demand Constraint: P + usable_inventory >= minimum_required_demand
        solver.Add(P >= required_from_cooking)

        # Objective Function:
        # Min c_prod * P + sum_s [ p_s * (c_waste * W_s + c_shortage * U_s) ]
        objective = solver.Objective()
        objective.SetCoefficient(P, c_prod)

        for idx, sc in enumerate(scenarios):
            p_s = sc["prob"]
            objective.SetCoefficient(surplus_vars[idx], p_s * c_waste)
            objective.SetCoefficient(shortage_vars[idx], p_s * c_shortage)

        objective.SetMinimization()

        # Solve Model
        status = solver.Solve()

        if status not in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
            return self._handle_infeasible_problem(
                dish_name=dish_name,
                minimum_required_demand=minimum_required_demand,
                usable_inventory=usable_inventory,
                required_from_cooking=required_from_cooking,
                kitchen_capacity=kitchen_capacity,
                ingredient_availability=ingredient_availability,
                maximum_production_capacity=maximum_production_capacity,
                demand_forecast=d_mid,
                food_cost=c_prod,
                portion_weight_kg=portion_weight_kg,
                safety_alert=safety_alert
            )

        # 6. Extract Optimal Solution
        optimal_p = int(round(P.solution_value()))
        total_available = int(optimal_p + usable_inventory)

        # Evaluate expected metrics across scenarios
        exp_surplus_portions = sum(sc["prob"] * max(0.0, total_available - sc["demand"]) for sc in scenarios)
        exp_shortage_portions = sum(sc["prob"] * max(0.0, sc["demand"] - total_available) for sc in scenarios)

        # Shortage risk: probability that demand exceeds available portions
        shortage_risk_prob = sum(sc["prob"] for sc in scenarios if sc["demand"] > total_available)
        shortage_risk_pct = round(shortage_risk_prob * 100.0, 1)

        estimated_waste_kg = round(exp_surplus_portions * portion_weight_kg, 1)

        # Detailed financial breakdown
        production_cost_usd = round(optimal_p * c_prod, 2)
        waste_cost_usd = round(exp_surplus_portions * c_waste, 2)
        shortage_penalty_usd = round(exp_shortage_portions * c_shortage, 2)
        total_cost_usd = round(production_cost_usd + waste_cost_usd + shortage_penalty_usd, 2)

        # 7. Synthesize Grounded Operational Reasoning
        reasoning = []
        if usable_inventory > 0:
            reasoning.append(
                f"Existing usable inventory of {int(usable_inventory)} portions is incorporated, reducing fresh cooking burden."
            )

        if optimal_p + usable_inventory > d_mid:
            buffer = int(optimal_p + usable_inventory - d_mid)
            reasoning.append(
                f"Recommended production provides a +{buffer} portion buffer ({optimal_p} to cook + {int(usable_inventory)} on-hand) "
                f"to hedge against high-attendance scenarios while keeping waste probability under {round((1 - shortage_risk_prob) * 100)}%."
            )
        else:
            reasoning.append(
                f"Recommended production tightly tracks expected demand ({int(d_mid)} portions) to minimize surplus disposal."
            )

        if optimal_p == int(kitchen_capacity):
            reasoning.append(
                f"Production is capped at maximum kitchen equipment capacity ({int(kitchen_capacity)} portions)."
            )
        elif optimal_p == int(ingredient_availability):
            reasoning.append(
                f"Production is constrained by current raw ingredient availability ({int(ingredient_availability)} portions)."
            )

        reasoning.append(
            f"Asymmetric Cost Equilibrium: Solved via Google OR-Tools balancing food cost (${c_prod}/portion), "
            f"waste penalty (${c_waste}/portion), and shortage penalty (${c_shortage}/portion)."
        )

        if safety_alert:
            reasoning.insert(0, safety_alert)

        # Return standardized Phase 7 schema
        return {
            "feasible": True,
            "status": "OPTIMAL",
            "recommended_production": optimal_p,
            "total_available_portions": total_available,
            "expected_demand": int(round(d_mid)),
            "expected_surplus": round(exp_surplus_portions, 1),
            "expected_shortage_risk": shortage_risk_pct,
            "estimated_waste": round(exp_surplus_portions, 1),
            "estimated_waste_kg": estimated_waste_kg,
            "estimated_cost": {
                "production_cost_usd": production_cost_usd,
                "expected_waste_cost_usd": waste_cost_usd,
                "expected_shortage_cost_usd": shortage_penalty_usd,
                "total_expected_cost_usd": total_cost_usd
            },
            "reasoning": reasoning,
            "constraints_summary": {
                "kitchen_capacity": int(kitchen_capacity),
                "ingredient_availability": int(ingredient_availability),
                "minimum_required_demand": int(minimum_required_demand),
                "usable_inventory": int(usable_inventory),
                "maximum_production_capacity": int(maximum_production_capacity),
                "is_capacity_binding": (optimal_p == int(kitchen_capacity)),
                "is_ingredient_binding": (optimal_p == int(ingredient_availability)),
                "is_minimum_service_binding": (total_available == int(minimum_required_demand))
            },
            "infeasibility_details": None,
            "scenarios_evaluated": scenarios,
            "solver": "Google OR-Tools MILP (SCIP)"
        }

    def _handle_infeasible_problem(
        self,
        dish_name: str,
        minimum_required_demand: float,
        usable_inventory: float,
        required_from_cooking: float,
        kitchen_capacity: float,
        ingredient_availability: float,
        maximum_production_capacity: float,
        demand_forecast: float,
        food_cost: float,
        portion_weight_kg: float,
        safety_alert: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Gracefully handles infeasible problem without producing silent invalid results.
        Diagnoses conflicting constraints and provides actionable bottleneck resolutions.
        """
        conflicts = []
        bottlenecks = []

        if required_from_cooking > kitchen_capacity:
            shortfall = int(required_from_cooking - kitchen_capacity)
            conflicts.append(
                f"Kitchen Station Capacity Bottleneck: Cooking station capacity is {int(kitchen_capacity)} portions, "
                f"which cannot fulfill net minimum service requirement of {int(required_from_cooking)} portions "
                f"({int(minimum_required_demand)} min demand - {int(usable_inventory)} inventory). Shortfall: {shortfall} portions."
            )
            bottlenecks.append(f"Deploy auxiliary prep station or stagger cooking across 2 shifts to gain +{shortfall} portions capacity.")

        if required_from_cooking > ingredient_availability:
            shortfall = int(required_from_cooking - ingredient_availability)
            conflicts.append(
                f"Ingredient Supply Shortfall: On-hand raw ingredients can only yield {int(ingredient_availability)} portions, "
                f"failing net minimum service requirement of {int(required_from_cooking)} portions. Shortfall: {shortfall} portions."
            )
            bottlenecks.append(f"Initiate expedited procurement order for +{shortfall} portions of raw ingredients.")

        if required_from_cooking > maximum_production_capacity:
            shortfall = int(required_from_cooking - maximum_production_capacity)
            conflicts.append(
                f"Maximum Production Policy Limit: Facility batch policy caps production at {int(maximum_production_capacity)} portions."
            )
            bottlenecks.append("Request management authorization to override batch ceiling.")

        # Best effort constrained allocation
        best_effort_p = int(max(0.0, min(kitchen_capacity, ingredient_availability, maximum_production_capacity)))
        total_available = int(best_effort_p + usable_inventory)
        unmet_minimum = int(max(0.0, minimum_required_demand - total_available))

        reasoning = [
            "CRITICAL: Optimization problem is INFEASIBLE under strict business constraints.",
            *conflicts,
            f"Best-effort physical ceiling is capped at {best_effort_p} portions, leaving a service deficit of {unmet_minimum} portions."
        ]
        if safety_alert:
            reasoning.insert(0, safety_alert)

        return {
            "feasible": False,
            "status": "INFEASIBLE_CONSTRAINED",
            "recommended_production": best_effort_p,
            "total_available_portions": total_available,
            "expected_demand": int(demand_forecast),
            "expected_surplus": 0.0,
            "expected_shortage_risk": 100.0,
            "estimated_waste": 0.0,
            "estimated_waste_kg": 0.0,
            "estimated_cost": {
                "production_cost_usd": round(best_effort_p * food_cost, 2),
                "expected_waste_cost_usd": 0.0,
                "expected_shortage_cost_usd": round(unmet_minimum * food_cost * 3.2, 2),
                "total_expected_cost_usd": round((best_effort_p * food_cost) + (unmet_minimum * food_cost * 3.2), 2)
            },
            "reasoning": reasoning,
            "constraints_summary": {
                "kitchen_capacity": int(kitchen_capacity),
                "ingredient_availability": int(ingredient_availability),
                "minimum_required_demand": int(minimum_required_demand),
                "usable_inventory": int(usable_inventory),
                "maximum_production_capacity": int(maximum_production_capacity),
                "unmet_service_portions": unmet_minimum
            },
            "infeasibility_details": {
                "is_infeasible": True,
                "root_cause_conflicts": conflicts,
                "actionable_bottleneck_resolutions": bottlenecks,
                "warning_message": (
                    "NEVER SILENTLY OVERRIDE: The requested service level cannot be fulfilled with current physical inventory "
                    "and equipment. Executive kitchen intervention required."
                )
            },
            "scenarios_evaluated": [],
            "solver": "Google OR-Tools MILP (SCIP - Infeasibility Diagnosis)"
        }


# Singleton instance
production_optimizer = ProductionOptimizer()
