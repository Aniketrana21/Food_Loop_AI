"""
FoodLoop AI - Deterministic Configurable Food Safety Rules Engine
PHASE 8 CRITICAL ARCHITECTURAL DIRECTIVE:
    "Do not allow an LLM to independently determine food safety.
     Use deterministic configurable rules and authorized human approval."

Calculates:
- remaining_safe_window (minutes & hours)
- urgency (CRITICAL, HIGH, MEDIUM, LOW, EXPIRED)
- eligibility (ELIGIBLE_FOR_DONATION, NEEDS_HUMAN_INSPECTION, INELIGIBLE_EXPIRED, INELIGIBLE_TEMPERATURE_ABUSE, INELIGIBLE_HOLDING_TIME_EXCEEDED)
- required_action (clear operational instruction)
- suggested_waste_workflow (if ineligible: INDUSTRIAL_COMPOSTING, ANAEROBIC_DIGESTION, ANIMAL_FEED_VALORIZATION)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class FoodSafetyConfig(BaseModel):
    """
    Configurable institutional food safety rules.
    Compliant with FDA Food Code § 3-501.16 & § 3-501.19.
    Can be adjusted per institution (university, hospital, corporate cafeteria).
    """
    # Hot holding: Min 135°F (57.2°C), max 4 hours without temperature control
    hot_hold_min_temp_c: float = 57.0
    hot_hold_max_hours: float = 4.0

    # Cold holding: Max 41°F (5.0°C), max 7 days (168h) for TCS cooked foods
    cold_hold_max_temp_c: float = 5.0
    cold_hold_cooked_max_hours: float = 72.0  # 3 days institutional buffer
    cold_hold_dairy_produce_max_hours: float = 120.0  # 5 days

    # Frozen holding: Max 0°F (-17.8°C), up to 90 days
    frozen_max_temp_c: float = -18.0
    frozen_max_hours: float = 2160.0  # 90 days

    # Room temperature / Ambient holding
    room_temp_max_hours: float = 2.0  # Strict 2h for ambient TCS items
    bakery_dry_room_temp_max_hours: float = 48.0  # Non-TCS bread/pastries

    # Transit buffer: minimum safe minutes remaining to permit dispatch
    minimum_dispatch_window_minutes: float = 30.0

    # Human sign-off threshold: if remaining window is between 30m and 60m, manager signoff is required
    manager_approval_threshold_minutes: float = 60.0

    # Institutional waste diversion hierarchy when food is ineligible for human consumption
    waste_hierarchy_mapping: Dict[str, str] = {
        "VEGETABLES": "INDUSTRIAL_COMPOSTING",
        "PRODUCE": "INDUSTRIAL_COMPOSTING",
        "GRAINS": "INDUSTRIAL_COMPOSTING",
        "GRAINS_PASTA": "INDUSTRIAL_COMPOSTING",
        "BAKERY": "ANIMAL_FEED_VALORIZATION",
        "DRY_GOODS": "ANIMAL_FEED_VALORIZATION",
        "COOKED_MEALS": "ANAEROBIC_DIGESTION",
        "PROTEIN": "ANAEROBIC_DIGESTION",
        "MEAT_POULTRY": "ANAEROBIC_DIGESTION",
        "SEAFOOD": "ANAEROBIC_DIGESTION",
        "DAIRY": "ANAEROBIC_DIGESTION",
        "SOUP": "ANAEROBIC_DIGESTION",
        "PREPARED_SOUP": "ANAEROBIC_DIGESTION",
        "DEFAULT": "INDUSTRIAL_COMPOSTING",
    }


# Singleton default config instance
DEFAULT_FOOD_SAFETY_CONFIG = FoodSafetyConfig()


class FoodSafetyEvaluationResult(BaseModel):
    remaining_safe_window_minutes: float
    remaining_safe_window_formatted: str
    urgency: str  # CRITICAL, HIGH, MEDIUM, LOW, EXPIRED
    eligibility: str  # ELIGIBLE_FOR_DONATION, NEEDS_HUMAN_INSPECTION, INELIGIBLE_EXPIRED, INELIGIBLE_TEMPERATURE_ABUSE, INELIGIBLE_HOLDING_TIME_EXCEEDED
    required_action: str
    suggested_waste_workflow: Optional[str] = None
    human_approval_required: bool = False
    temperature_verified: bool = False
    safety_rule_applied: str
    reasons: List[str]


def evaluate_food_safety(
    food: str,
    category: str = "COOKED_MEALS",
    storage_type: str = "REFRIGERATED",
    temperature: Optional[float] = None,
    prepared_at: Optional[datetime] = None,
    best_use_before: Optional[datetime] = None,
    current_time: Optional[datetime] = None,
    config: Optional[FoodSafetyConfig] = None
) -> FoodSafetyEvaluationResult:
    """
    Deterministic food safety rules engine.
    Strictly rule-based: zero non-deterministic or LLM-based decisions.
    """
    cfg = config or DEFAULT_FOOD_SAFETY_CONFIG
    now = current_time or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    # Normalize category & storage type
    norm_cat = (category or "COOKED_MEALS").upper().strip()
    norm_storage = (storage_type or "REFRIGERATED").upper().strip()
    if norm_storage in ["HOT", "WARMER", "HOT_HOLDING"]:
        norm_storage = "HOT_HOLD"
    elif norm_storage in ["COLD", "CHILLED", "COOLER", "WALK_IN", "REFRIGERATOR"]:
        norm_storage = "REFRIGERATED"
    elif norm_storage in ["FREEZE", "DEEP_FREEZE"]:
        norm_storage = "FROZEN"
    elif norm_storage in ["ROOM", "AMBIENT", "COUNTER"]:
        norm_storage = "ROOM_TEMP"

    reasons: List[str] = []

    # 1. Determine baseline safe holding hours from storage type and food category
    if norm_storage == "HOT_HOLD":
        max_safe_hours = cfg.hot_hold_max_hours
        rule_desc = f"FDA § 3-501.19 Hot-Hold 4h Time Limit (Min {cfg.hot_hold_min_temp_c}°C)"
    elif norm_storage == "REFRIGERATED":
        if norm_cat in ["DAIRY", "PRODUCE", "VEGETABLES"]:
            max_safe_hours = cfg.cold_hold_dairy_produce_max_hours
            rule_desc = f"Cold Chain Hold: {int(max_safe_hours)}h (Max {cfg.cold_hold_max_temp_c}°C)"
        else:
            max_safe_hours = cfg.cold_hold_cooked_max_hours
            rule_desc = f"Cooked Food Cold Chain: {int(max_safe_hours)}h (Max {cfg.cold_hold_max_temp_c}°C)"
    elif norm_storage == "FROZEN":
        max_safe_hours = cfg.frozen_max_hours
        rule_desc = f"Deep Freeze Safe Storage: {int(max_safe_hours)}h (Max {cfg.frozen_max_temp_c}°C)"
    elif norm_storage == "ROOM_TEMP":
        if norm_cat in ["BAKERY", "DRY_GOODS"]:
            max_safe_hours = cfg.bakery_dry_room_temp_max_hours
            rule_desc = f"Dry Ambient Holding: {int(max_safe_hours)}h"
        else:
            max_safe_hours = cfg.room_temp_max_hours
            rule_desc = f"Ambient TCS 2h Danger Zone Discard Rule"
    else:
        max_safe_hours = 4.0
        rule_desc = "Default TCS Holding Limit: 4.0h"

    # 2. Check Temperature Abuse (if temperature probe reading is provided)
    temp_violation = False
    temp_verified = False

    if temperature is not None:
        temp_verified = True
        temp_val = float(temperature)

        if norm_storage == "HOT_HOLD":
            if temp_val < cfg.hot_hold_min_temp_c:
                temp_violation = True
                reasons.append(
                    f"CRITICAL TEMPERATURE ABUSE: Hot hold temperature of {temp_val:.1f}°C is below required minimum {cfg.hot_hold_min_temp_c}°C (135°F)."
                )
        elif norm_storage == "REFRIGERATED":
            if temp_val > cfg.cold_hold_max_temp_c:
                temp_violation = True
                reasons.append(
                    f"CRITICAL TEMPERATURE ABUSE: Chilled temperature of {temp_val:.1f}°C exceeds safe maximum {cfg.cold_hold_max_temp_c}°C (41°F)."
                )
        elif norm_storage == "FROZEN":
            if temp_val > cfg.frozen_max_temp_c:
                reasons.append(
                    f"WARNING: Freezer temperature of {temp_val:.1f}°C is warmer than {cfg.frozen_max_temp_c}°C target."
                )

    # 3. Calculate Age & Remaining Time Window
    if prepared_at:
        prep_dt = prepared_at.replace(tzinfo=timezone.utc) if prepared_at.tzinfo is None else prepared_at
        age_seconds = (now - prep_dt).total_seconds()
        age_hours = max(0.0, age_seconds / 3600.0)
    else:
        # Default assumption: prepared 1 hour ago if timestamp missing
        age_hours = 1.0

    remaining_hours = max_safe_hours - age_hours

    # 4. Factor in best_use_before if explicitly set
    if best_use_before:
        bub_dt = best_use_before.replace(tzinfo=timezone.utc) if best_use_before.tzinfo is None else best_use_before
        bub_remaining_hours = (bub_dt - now).total_seconds() / 3600.0
        if bub_remaining_hours < remaining_hours:
            remaining_hours = bub_remaining_hours
            reasons.append(f"Safe consumption bound constrained by explicit Best-Use-Before date ({bub_dt.strftime('%Y-%m-%d %H:%M UTC')}).")

    remaining_minutes = max(0.0, round(remaining_hours * 60.0, 1))

    # Format human-friendly remaining window string
    if remaining_minutes <= 0.0:
        formatted_window = "0 min (EXPIRED)"
    elif remaining_minutes < 60.0:
        formatted_window = f"{int(remaining_minutes)}m remaining"
    else:
        h = int(remaining_minutes // 60)
        m = int(remaining_minutes % 60)
        formatted_window = f"{h}h {m:02d}m remaining"

    # Determine institutional alternative waste workflow
    suggested_workflow = cfg.waste_hierarchy_mapping.get(norm_cat, cfg.waste_hierarchy_mapping["DEFAULT"])

    # 5. Evaluate Eligibility, Urgency, and Required Action
    if temp_violation:
        eligibility = "INELIGIBLE_TEMPERATURE_ABUSE"
        urgency = "EXPIRED"
        remaining_minutes = 0.0
        formatted_window = "0 min (TEMPERATURE ABUSE)"
        required_action = (
            f"MANDATORY DISCARD: Temperature abuse breached HACCP limits. "
            f"Divert lot to {suggested_workflow.replace('_', ' ').title()}."
        )
        human_approval_required = False

    elif remaining_minutes <= 0.0:
        eligibility = "INELIGIBLE_EXPIRED"
        urgency = "EXPIRED"
        reasons.append(
            f"Maximum safe holding duration ({max_safe_hours:.1f}h) has elapsed since preparation ({age_hours:.1f}h ago)."
        )
        required_action = (
            f"MANDATORY FOOD WASTE DIVERSION: Safe window expired. "
            f"Divert lot to {suggested_workflow.replace('_', ' ').title()} per institutional policy."
        )
        human_approval_required = False

    elif remaining_minutes < cfg.minimum_dispatch_window_minutes:
        eligibility = "INELIGIBLE_HOLDING_TIME_EXCEEDED"
        urgency = "CRITICAL"
        reasons.append(
            f"Insufficient transit window: only {int(remaining_minutes)} minutes remaining. Courier transit requires at least {int(cfg.minimum_dispatch_window_minutes)} minutes."
        )
        required_action = (
            f"IMMEDIATE LOCAL ACTION: Cannot safely dispatch via courier. "
            f"Option A: On-site staff immediate consumption. "
            f"Option B: Immediate diversion to {suggested_workflow.replace('_', ' ').title()}."
        )
        human_approval_required = True

    elif remaining_minutes <= cfg.manager_approval_threshold_minutes:
        eligibility = "NEEDS_HUMAN_INSPECTION"
        urgency = "CRITICAL"
        reasons.append(
            f"Approaching critical threshold: {int(remaining_minutes)} minutes remaining. Requires Kitchen Manager physical sign-off."
        )
        required_action = (
            "AUTHORIZED HUMAN APPROVAL REQUIRED: Kitchen Manager must physically verify temperature probe & sensory quality before dispatch approval."
        )
        human_approval_required = True

    elif remaining_minutes <= 180.0:  # 3 hours
        eligibility = "ELIGIBLE_FOR_DONATION"
        urgency = "HIGH"
        required_action = f"Schedule expedited courier pickup within {int(remaining_minutes)} minutes."
        human_approval_required = False

    elif remaining_minutes <= 360.0:  # 6 hours
        eligibility = "ELIGIBLE_FOR_DONATION"
        urgency = "MEDIUM"
        required_action = f"Broadcast to regional food rescue partners for day-of distribution."
        human_approval_required = False

    else:
        eligibility = "ELIGIBLE_FOR_DONATION"
        urgency = "LOW"
        required_action = "Surplus lot is safely stabilized in cold/frozen chain. Available for scheduled pickup."
        human_approval_required = False

    return FoodSafetyEvaluationResult(
        remaining_safe_window_minutes=remaining_minutes,
        remaining_safe_window_formatted=formatted_window,
        urgency=urgency,
        eligibility=eligibility,
        required_action=required_action,
        suggested_waste_workflow=suggested_workflow if eligibility != "ELIGIBLE_FOR_DONATION" else None,
        human_approval_required=human_approval_required,
        temperature_verified=temp_verified,
        safety_rule_applied=rule_desc,
        reasons=reasons
    )
