"""
FoodLoop AI - Phase 9 AI Recipient Matching Engine
Matches available surplus food with feasible recipients using 7 deterministic factors:
1. Food compatibility (category & dietary requirements)
2. Capacity (surplus volume vs recipient intake capacity and active demand)
3. Distance (Haversine km & transit estimation)
4. Urgency (surplus remaining safe window vs transit time & intake readiness)
5. Pickup availability (recipient self-pickup fleet vs courier dependency)
6. Storage compatibility (storage type vs recipient cold/hot/dry capability)
7. Operational reliability (historical show rate, verification, punctuality)

Zero black-box scores: every match returns transparent factor breakdowns and
human-readable bulleted explanations.
"""

import math
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, asdict


@dataclass
class MatchingFactorBreakdown:
    food_compatibility: float       # 0 - 100
    capacity: float                 # 0 - 100
    distance: float                 # 0 - 100
    urgency: float                  # 0 - 100
    pickup_availability: float      # 0 - 100
    storage_compatibility: float    # 0 - 100
    operational_reliability: float  # 0 - 100


@dataclass
class RecipientMatchResult:
    recipient_id: str
    organization_name: str
    facility_type: str
    address: str
    contact_person: str
    contact_phone: str
    distance_km: float
    estimated_transit_minutes: int
    overall_match_score: float
    factors: MatchingFactorBreakdown
    explanation_bullets: List[str]
    recommendation_summary: str
    is_feasible: bool
    can_intake_immediately: bool
    requires_delivery: bool
    operating_hours: str
    verification_status: str

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["factors"] = asdict(self.factors)
        return d


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Computes great-circle distance between two GPS coordinates."""
    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


def estimate_transit_time_minutes(distance_km: float) -> int:
    """Estimates urban driving time in minutes (25 km/h average + 5 min loading)."""
    travel_min = (distance_km / 25.0) * 60.0
    return max(5, int(round(travel_min + 5)))


class RecipientMatchingEngine:
    """
    Multi-attribute transparent recipient matching engine.
    Weights each of the 7 candidate factors to produce an interpretable match.
    """

    # Configurable Factor Weights (Sum = 1.0)
    WEIGHTS = {
        "food_compatibility": 0.22,
        "capacity": 0.18,
        "distance": 0.18,
        "urgency": 0.14,
        "storage_compatibility": 0.12,
        "pickup_availability": 0.08,
        "operational_reliability": 0.08,
    }

    @classmethod
    def evaluate_match(
        cls,
        surplus: Any,
        recipient: Any,
        recipient_requirement: Optional[Any] = None
    ) -> RecipientMatchResult:
        """
        Evaluates a single recipient against a surplus lot across all 7 factors.
        Generates structured scores and transparent bulleted explanations.
        """
        bullets: List[str] = []
        is_feasible = True

        # Extract Surplus Attributes
        surplus_food = surplus.food or surplus.title or "Surplus Food"
        surplus_category = (surplus.category or "COOKED_MEALS").upper()
        surplus_kg = float(surplus.quantity or surplus.quantity_kg or 15.0)
        surplus_portions = int(surplus.portions or (surplus_kg / 0.35))
        surplus_storage = (surplus.storage_type or surplus.storage_temp or "ROOM_TEMP").upper()
        surplus_lat = float(surplus.pickup_lat or 37.7749)
        surplus_lng = float(surplus.pickup_lng or -122.4194)
        safe_window_min = float(surplus.remaining_safe_window_minutes or 240.0)

        # Extract Recipient Attributes
        rec_lat = float(recipient.latitude)
        rec_lng = float(recipient.longitude)
        rec_name = recipient.name
        rec_type = recipient.facility_type or "COMMUNITY_ORGANIZATION"
        max_intake_kg = float(recipient.max_daily_intake_kg or 150.0)
        demand_portions = int(getattr(recipient, "current_demand_portions", 100) or 100)
        pickup_avail = bool(getattr(recipient, "pickup_available", True))
        storage_caps = getattr(recipient, "storage_capabilities", None) or ["COLD_HOLD", "DRY", "HOT_HOLD"]
        verification = getattr(recipient, "verification_status", "VERIFIED") or "VERIFIED"
        reliability = float(getattr(recipient, "reliability_score", 0.95) or 0.95)
        op_hours = getattr(recipient, "operating_hours_description", "08:00 - 20:00 Daily") or "08:00 - 20:00 Daily"

        # Requirements profile if available
        accepted_cats = []
        dietary_prefs = []
        if recipient_requirement:
            accepted_cats = [c.upper() for c in (recipient_requirement.acceptable_categories or [])]
            dietary_prefs = [d.upper() for d in (recipient_requirement.dietary_preferences or [])]
        if not accepted_cats:
            accepted_cats = ["COOKED_MEALS", "GRAINS", "VEGETABLES", "PROTEIN", "BAKERY", "SOUP", "DAIRY"]

        # -------------------------------------------------------------
        # 1. DISTANCE (Haversine)
        # -------------------------------------------------------------
        dist_km = haversine_distance_km(surplus_lat, surplus_lng, rec_lat, rec_lng)
        transit_min = estimate_transit_time_minutes(dist_km)

        if dist_km <= 2.0:
            dist_score = 100.0
        elif dist_km <= 5.0:
            dist_score = 90.0 - (dist_km - 2.0) * 3.3
        elif dist_km <= 15.0:
            dist_score = 80.0 - (dist_km - 5.0) * 3.0
        elif dist_km <= 25.0:
            dist_score = 50.0 - (dist_km - 15.0) * 3.0
        else:
            dist_score = max(10.0, 20.0 - (dist_km - 25.0))
            is_feasible = False

        bullets.append(f"{dist_km} km away (~{transit_min} min estimated transit)")

        # -------------------------------------------------------------
        # 2. FOOD COMPATIBILITY
        # -------------------------------------------------------------
        food_compat_score = 100.0
        category_match = surplus_category in accepted_cats or "ALL" in accepted_cats or len(accepted_cats) == 0

        # Check keyword dietary alignments (e.g. rice, chicken, vegetables, halal)
        food_lower = surplus_food.lower()
        dietary_hits = []
        if "rice" in food_lower or "pilaf" in food_lower or "biryani" in food_lower:
            dietary_hits.append("rice-based meals")
        if "chicken" in food_lower or "fish" in food_lower or "salmon" in food_lower or "beef" in food_lower:
            dietary_hits.append("high-protein hot entrees")
        if "vegetable" in food_lower or "salad" in food_lower or "greens" in food_lower:
            dietary_hits.append("fresh plant-based dishes")
        if "soup" in food_lower or "bisque" in food_lower:
            dietary_hits.append("nutritious warm soups")
        if "bread" in food_lower or "baguette" in food_lower or "roll" in food_lower:
            dietary_hits.append("artisan bakery goods")

        if category_match:
            if dietary_hits:
                bullets.append(f"accepts {', '.join(dietary_hits[:2])}")
            else:
                bullets.append(f"accepts {surplus_category.replace('_', ' ').lower()} lots")
        else:
            food_compat_score = 30.0
            bullets.append(f"does not typically stock {surplus_category.replace('_', ' ').lower()}")
            is_feasible = False

        # -------------------------------------------------------------
        # 3. CAPACITY
        # -------------------------------------------------------------
        capacity_ratio = surplus_kg / max(1.0, max_intake_kg)
        if capacity_ratio <= 0.8:
            capacity_score = 100.0
            bullets.append(f"capacity {demand_portions} meals (can easily intake all {surplus_portions} portions / {surplus_kg:.1f} kg)")
        elif capacity_ratio <= 1.0:
            capacity_score = 85.0
            bullets.append(f"capacity {demand_portions} meals (near daily intake ceiling of {max_intake_kg} kg)")
        else:
            capacity_score = max(15.0, 100.0 - (capacity_ratio - 1.0) * 100.0)
            bullets.append(f"intake capacity constrained ({surplus_kg:.1f} kg exceeds {max_intake_kg} kg ceiling)")
            is_feasible = False

        # -------------------------------------------------------------
        # 4. URGENCY ALIGNMENT
        # -------------------------------------------------------------
        # Safe window vs transit time
        time_margin_min = safe_window_min - transit_min
        if time_margin_min > 120:
            urgency_score = 100.0
            bullets.append(f"ample safe window ({int(safe_window_min)} min remaining vs {transit_min} min transit)")
        elif time_margin_min > 45:
            urgency_score = 90.0
            bullets.append(f"comfortable dispatch margin ({int(safe_window_min)} min remaining window)")
        elif time_margin_min > 15:
            urgency_score = 75.0
            bullets.append(f"tight dispatch window: {int(safe_window_min)} min remaining, priority delivery needed")
        else:
            urgency_score = 25.0
            bullets.append(f"urgent delivery risk: only {int(safe_window_min)} min remaining window")
            if safe_window_min <= 0:
                is_feasible = False

        # -------------------------------------------------------------
        # 5. PICKUP AVAILABILITY
        # -------------------------------------------------------------
        if pickup_avail:
            pickup_score = 100.0
            bullets.append("pickup available (recipient can dispatch own vehicle immediately)")
        else:
            pickup_score = 65.0
            bullets.append("pickup requires courier dispatch (no internal transport)")

        # -------------------------------------------------------------
        # 6. STORAGE COMPATIBILITY
        # -------------------------------------------------------------
        # Check storage match
        has_cold = recipient.cold_storage_available or "COLD_HOLD" in storage_caps or "REFRIGERATED" in storage_caps
        has_hot = "HOT_HOLD" in storage_caps
        has_frozen = "FROZEN" in storage_caps

        if surplus_storage in ["COLD_HOLD", "REFRIGERATED"]:
            if has_cold:
                storage_score = 100.0
                bullets.append(f"chilled storage compatible (walk-in chiller capacity {recipient.walk_in_chiller_capacity_kg or 50:.0f} kg)")
            else:
                storage_score = 20.0
                bullets.append("lacks certified refrigerated storage for cold food")
                is_feasible = False
        elif surplus_storage in ["HOT_HOLD"]:
            if has_hot or has_cold:
                storage_score = 100.0
                bullets.append("hot-holding or rapid chill-down equipment verified")
            else:
                storage_score = 40.0
                bullets.append("immediate service only (no hot-holding equipment)")
        elif surplus_storage in ["FROZEN"]:
            if has_frozen:
                storage_score = 100.0
                bullets.append("commercial deep freezer capacity confirmed")
            else:
                storage_score = 15.0
                bullets.append("lacks commercial freezer equipment")
                is_feasible = False
        else:  # ROOM_TEMP / DRY
            storage_score = 100.0
            bullets.append("ambient dry shelving available")

        # -------------------------------------------------------------
        # 7. OPERATIONAL RELIABILITY & VERIFICATION
        # -------------------------------------------------------------
        reliability_score = reliability * 100.0
        if verification.upper() == "VERIFIED":
            reliability_score = min(100.0, reliability_score + 5.0)
            bullets.append(f"verified organization ({int(reliability * 100)}% historical receipt reliability)")
        else:
            reliability_score = max(40.0, reliability_score - 20.0)
            bullets.append("pending municipal non-profit audit review")

        # -------------------------------------------------------------
        # WEIGHTED OVERALL COMPATIBILITY SCORE
        # -------------------------------------------------------------
        breakdown = MatchingFactorBreakdown(
            food_compatibility=round(food_compat_score, 1),
            capacity=round(capacity_score, 1),
            distance=round(dist_score, 1),
            urgency=round(urgency_score, 1),
            pickup_availability=round(pickup_score, 1),
            storage_compatibility=round(storage_score, 1),
            operational_reliability=round(reliability_score, 1)
        )

        overall_score = (
            cls.WEIGHTS["food_compatibility"] * breakdown.food_compatibility +
            cls.WEIGHTS["capacity"] * breakdown.capacity +
            cls.WEIGHTS["distance"] * breakdown.distance +
            cls.WEIGHTS["urgency"] * breakdown.urgency +
            cls.WEIGHTS["pickup_availability"] * breakdown.pickup_availability +
            cls.WEIGHTS["storage_compatibility"] * breakdown.storage_compatibility +
            cls.WEIGHTS["operational_reliability"] * breakdown.operational_reliability
        )
        overall_score = round(max(0.0, min(100.0, overall_score)), 1)

        # Recommendation Summary
        pickup_str = "has pickup transport available" if pickup_avail else "requires courier delivery"
        rec_summary = (
            f"{rec_name} is {dist_km} km away, accepts {surplus_category.lower().replace('_', ' ')}, "
            f"has capacity for {surplus_portions} portions, {pickup_str}, and is a verified {rec_type.replace('_', ' ').lower()}."
        )

        return RecipientMatchResult(
            recipient_id=str(recipient.id),
            organization_name=rec_name,
            facility_type=rec_type,
            address=recipient.address,
            contact_person=recipient.contact_person,
            contact_phone=recipient.contact_phone,
            distance_km=dist_km,
            estimated_transit_minutes=transit_min,
            overall_match_score=overall_score,
            factors=breakdown,
            explanation_bullets=bullets,
            recommendation_summary=rec_summary,
            is_feasible=is_feasible,
            can_intake_immediately=pickup_avail and dist_km < 10.0,
            requires_delivery=not pickup_avail,
            operating_hours=op_hours,
            verification_status=verification
        )

    @classmethod
    def rank_recipients_for_surplus(
        cls,
        surplus: Any,
        recipients: List[Any],
        limit: int = 5
    ) -> List[RecipientMatchResult]:
        """
        Ranks all active candidate recipients against a given surplus lot.
        Returns the top matches sorted by overall_match_score descending.
        """
        results: List[RecipientMatchResult] = []
        for rec in recipients:
            if not rec.is_active:
                continue
            req = getattr(rec, "requirements", None)
            res = cls.evaluate_match(surplus, rec, req)
            results.append(res)

        # Sort descending by overall match score
        results.sort(key=lambda r: (r.is_feasible, r.overall_match_score), reverse=True)
        return results[:limit]


recipient_matching_engine = RecipientMatchingEngine()
