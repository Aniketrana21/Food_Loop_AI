"""
FoodLoop AI - Surplus Lifecycle, Recipient Matching & Safety Safeguard Service
Enforces:
1. Strict deterministic food safety rule checks on all status transitions.
2. PREVENTS ACCIDENTAL ALLOCATION OF EXPIRED SURPLUS.
3. Automated recipient matching for eligible lots.
4. Alternative institutional waste workflow guidance for ineligible lots.
5. Authorized human approval workflows.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import math
from sqlalchemy.orm import Session

from app.models.models import SurplusItem, Organization
from app.services.food_safety_rules import (
    evaluate_food_safety, 
    FoodSafetyConfig, 
    FoodSafetyEvaluationResult, 
    DEFAULT_FOOD_SAFETY_CONFIG
)


# Verified regional non-profit recipient partners for rescue matching
VERIFIED_RECIPIENT_NETWORK = [
    {
        "id": "rec-001",
        "name": "St. Vincent Community Kitchen & Shelter",
        "organization_type": "EMERGENCY_SHELTER",
        "address": "450 Golden Gate Ave, San Francisco, CA",
        "lat": 37.7812,
        "lng": -122.4180,
        "capacity_portions": 250,
        "accepted_categories": ["COOKED_MEALS", "PROTEIN", "VEGETABLES", "BAKERY", "SOUP"],
        "has_refrigeration": True,
        "accepts_hot_hold": True,
        "contact_person": "Sister Mary / Chef Lucas",
        "phone": "+1 (415) 555-0142",
        "urgency_readiness": "IMMEDIATE_DISPATCH"
    },
    {
        "id": "rec-002",
        "name": "Bay Area Youth Oasis Food Pantry",
        "organization_type": "YOUTH_PANTRY",
        "address": "1025 Market St, San Francisco, CA",
        "lat": 37.7801,
        "lng": -122.4105,
        "capacity_portions": 140,
        "accepted_categories": ["COOKED_MEALS", "DAIRY", "BAKERY", "PRODUCE", "GRAINS"],
        "has_refrigeration": True,
        "accepts_hot_hold": False,
        "contact_person": "David Vance",
        "phone": "+1 (415) 555-0188",
        "urgency_readiness": "DAY_OF_PICKUP"
    },
    {
        "id": "rec-003",
        "name": "Mission Senior Dining & Wellness Center",
        "organization_type": "SENIOR_CENTER",
        "address": "2580 Mission St, San Francisco, CA",
        "lat": 37.7554,
        "lng": -122.4188,
        "capacity_portions": 180,
        "accepted_categories": ["COOKED_MEALS", "SOUP", "VEGETABLES", "DAIRY"],
        "has_refrigeration": True,
        "accepts_hot_hold": True,
        "contact_person": "Carla Mendez",
        "phone": "+1 (415) 555-0199",
        "urgency_readiness": "IMMEDIATE_DISPATCH"
    },
    {
        "id": "rec-004",
        "name": "East Bay Urban Food Coalition",
        "organization_type": "REGIONAL_FOOD_BANK",
        "address": "800 14th St, Oakland, CA",
        "lat": 37.8055,
        "lng": -122.2740,
        "capacity_portions": 600,
        "accepted_categories": ["PRODUCE", "DRY_GOODS", "BAKERY", "DAIRY", "FROZEN"],
        "has_refrigeration": True,
        "accepts_hot_hold": False,
        "contact_person": "Marcus Bell",
        "phone": "+1 (510) 555-0177",
        "urgency_readiness": "SCHEDULED_ROUTE"
    },
]


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two GPS coordinates in kilometers."""
    r = 6371.0  # Earth's radius in km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(r * c, 2)


class SurplusManagementService:
    """
    Core service coordinating surplus lot evaluation, recipient matching,
    and allocation safety enforcement.
    """

    @staticmethod
    def evaluate_item(item: SurplusItem, config: Optional[FoodSafetyConfig] = None) -> FoodSafetyEvaluationResult:
        """Runs the deterministic food safety rules engine on a surplus item."""
        food_name = getattr(item, "food", None) or getattr(item, "title", "Prepared Food")
        category = getattr(item, "category", "COOKED_MEALS")
        storage_type = getattr(item, "storage_type", None) or getattr(item, "storage_temp", "REFRIGERATED")
        temperature = getattr(item, "temperature", None)
        prepared_at = getattr(item, "prepared_at", None)
        best_use_before = getattr(item, "best_use_before", None) or getattr(item, "safe_consumption_deadline", None)

        return evaluate_food_safety(
            food=food_name,
            category=category,
            storage_type=storage_type,
            temperature=temperature,
            prepared_at=prepared_at,
            best_use_before=best_use_before,
            config=config
        )

    @staticmethod
    def sync_item_safety_fields(item: SurplusItem, safety_eval: FoodSafetyEvaluationResult) -> None:
        """Syncs calculated safety evaluation into the SurplusItem record."""
        item.remaining_safe_window_minutes = safety_eval.remaining_safe_window_minutes
        item.urgency = safety_eval.urgency
        item.eligibility = safety_eval.eligibility
        item.required_action = safety_eval.required_action
        item.suggested_waste_workflow = safety_eval.suggested_waste_workflow
        item.human_approval_required = safety_eval.human_approval_required

        # If expired and was previously available, auto-transition status
        if safety_eval.eligibility in ["INELIGIBLE_EXPIRED", "INELIGIBLE_TEMPERATURE_ABUSE"]:
            if item.status in ["AVAILABLE", "RESERVED"]:
                item.status = "EXPIRED"

    @classmethod
    def find_eligible_recipients(
        cls,
        item: SurplusItem,
        max_distance_km: float = 35.0
    ) -> List[Dict[str, Any]]:
        """
        Finds matched community recipients for an eligible surplus lot.
        Matches based on category compatibility, distance, transit duration, and capacity.
        """
        safety_eval = cls.evaluate_item(item)
        if safety_eval.eligibility in ["INELIGIBLE_EXPIRED", "INELIGIBLE_TEMPERATURE_ABUSE", "INELIGIBLE_HOLDING_TIME_EXCEEDED"]:
            return []

        item_lat = float(getattr(item, "pickup_lat", 37.7749) or 37.7749)
        item_lng = float(getattr(item, "pickup_lng", -122.4194) or -122.4194)
        item_cat = (getattr(item, "category", "COOKED_MEALS") or "COOKED_MEALS").upper()
        portions = int(getattr(item, "portions", 50) or 50)
        storage_type = (getattr(item, "storage_type", None) or getattr(item, "storage_temp", "REFRIGERATED")).upper()

        matches = []
        for recipient in VERIFIED_RECIPIENT_NETWORK:
            # Category match check
            if item_cat not in recipient["accepted_categories"] and "COOKED_MEALS" not in recipient["accepted_categories"]:
                continue

            # Hot hold capability check
            if storage_type == "HOT_HOLD" and not recipient["accepts_hot_hold"]:
                continue

            # Distance & transit check
            dist_km = haversine_distance_km(item_lat, item_lng, recipient["lat"], recipient["lng"])
            if dist_km > max_distance_km:
                continue

            est_transit_minutes = round(dist_km * 2.8 + 10.0, 1)  # 2.8 min/km + 10 min loading buffer

            # Transit window safety check: must arrive well before safe consumption deadline
            if est_transit_minutes > safety_eval.remaining_safe_window_minutes - 15.0:
                continue

            # Capacity suitability score
            capacity_score = min(1.0, portions / max(1, recipient["capacity_portions"]))
            proximity_score = max(0.0, 1.0 - (dist_km / max_distance_km))
            overall_score = round((proximity_score * 0.6) + (capacity_score * 0.4), 2)

            matches.append({
                "recipient_id": recipient["id"],
                "organization_name": recipient["name"],
                "organization_type": recipient["organization_type"],
                "address": recipient["address"],
                "distance_km": dist_km,
                "estimated_transit_minutes": est_transit_minutes,
                "capacity_portions": recipient["capacity_portions"],
                "match_score": int(overall_score * 100),
                "contact_person": recipient["contact_person"],
                "phone": recipient["phone"],
                "readiness": recipient["urgency_readiness"],
                "can_receive_immediately": est_transit_minutes < safety_eval.remaining_safe_window_minutes,
                "safe_margin_minutes": round(safety_eval.remaining_safe_window_minutes - est_transit_minutes, 1)
            })

        matches.sort(key=lambda m: m["match_score"], reverse=True)
        return matches

    @classmethod
    def allocate_surplus(
        cls,
        surplus_id: str,
        recipient_id: str,
        db: Session,
        actor_name: str = "Authorized Dispatcher"
    ) -> Dict[str, Any]:
        """
        CRITICAL SAFETY ENFORCEMENT:
        Allocates surplus to a recipient.
        ABSOLUTELY PREVENTS ALLOCATING EXPIRED OR INELIGIBLE SURPLUS.
        """
        item = db.query(SurplusItem).filter(
            SurplusItem.id == surplus_id,
            SurplusItem.deleted_at.is_(None)
        ).first()

        if not item:
            raise ValueError(f"Surplus record '{surplus_id}' was not found.")

        # 1. State machine check
        if item.status in ["DELIVERED", "RECEIVED", "CANCELLED"]:
            raise ValueError(f"Cannot allocate surplus with terminal status '{item.status}'.")

        # 2. Re-evaluate real-time deterministic food safety
        safety_eval = cls.evaluate_item(item)
        cls.sync_item_safety_fields(item, safety_eval)

        # STRICT EXPIRATION GUARD
        if safety_eval.remaining_safe_window_minutes <= 0.0 or safety_eval.eligibility in ["INELIGIBLE_EXPIRED", "INELIGIBLE_TEMPERATURE_ABUSE"]:
            item.status = "EXPIRED"
            db.commit()
            raise ValueError(
                f"SAFETY LOCKOUT: Expired surplus ({safety_eval.eligibility}) CANNOT be allocated for human consumption. "
                f"Item has been automatically locked and routed to {safety_eval.suggested_waste_workflow}."
            )

        if safety_eval.eligibility == "INELIGIBLE_HOLDING_TIME_EXCEEDED":
            raise ValueError(
                f"SAFETY LOCKOUT: Remaining window ({int(safety_eval.remaining_safe_window_minutes)}m) is insufficient for safe courier transit. "
                f"Recommended action: {safety_eval.required_action}"
            )

        # 3. Manager approval gate
        if safety_eval.eligibility == "NEEDS_HUMAN_INSPECTION":
            if getattr(item, "approval_status", "") != "APPROVED":
                raise ValueError(
                    "AUTHORIZED HUMAN SIGN-OFF REQUIRED: This lot is in the critical 30-60 minute window. "
                    "A Kitchen Manager must inspect and physically approve the lot before reservation."
                )

        # 4. Find recipient info
        matched_recipient = next((r for r in VERIFIED_RECIPIENT_NETWORK if r["id"] == recipient_id), None)
        recipient_name = matched_recipient["name"] if matched_recipient else f"Partner Org ({recipient_id})"

        # 5. Successfully reserve
        item.status = "RESERVED"
        now = datetime.now(timezone.utc)
        item.updated_at = now

        db.commit()
        db.refresh(item)

        return {
            "surplus_id": item.id,
            "status": item.status,
            "recipient_id": recipient_id,
            "recipient_name": recipient_name,
            "remaining_safe_window_minutes": safety_eval.remaining_safe_window_minutes,
            "allocated_at": now.isoformat(),
            "allocated_by": actor_name,
            "message": f"Surplus lot successfully reserved for {recipient_name}. Cold chain courier dispatch initialized."
        }

    @classmethod
    def record_human_approval(
        cls,
        surplus_id: str,
        approved: bool,
        approver_name: str,
        notes: str,
        verified_temp: Optional[float],
        db: Session
    ) -> Dict[str, Any]:
        """
        Records authorized human sign-off for lots requiring physical sensory or temperature inspection.
        """
        item = db.query(SurplusItem).filter(
            SurplusItem.id == surplus_id,
            SurplusItem.deleted_at.is_(None)
        ).first()

        if not item:
            raise ValueError(f"Surplus record '{surplus_id}' was not found.")

        # Expired items can NEVER be approved
        safety_eval = cls.evaluate_item(item)
        if safety_eval.remaining_safe_window_minutes <= 0.0 or safety_eval.eligibility in ["INELIGIBLE_EXPIRED", "INELIGIBLE_TEMPERATURE_ABUSE"]:
            item.status = "EXPIRED"
            db.commit()
            raise ValueError("CANNOT APPROVE: Food safety critical threshold elapsed. Mandatory discard required.")

        item.approved_by = approver_name
        item.approval_status = "APPROVED" if approved else "REJECTED"
        item.approval_notes = notes
        if verified_temp is not None:
            item.temperature = verified_temp

        if not approved:
            # Manager rejected: route to alternative waste workflow
            item.eligibility = "INELIGIBLE_TEMPERATURE_ABUSE"
            item.status = "EXPIRED"
            item.required_action = f"Manager inspection failed: {notes}. Routed to alternative waste workflow."

        db.commit()
        db.refresh(item)

        return {
            "surplus_id": item.id,
            "approved": approved,
            "approved_by": approver_name,
            "approval_status": item.approval_status,
            "verified_temp": verified_temp,
            "notes": notes,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    @classmethod
    def transition_status(
        cls,
        surplus_id: str,
        new_status: str,
        db: Session,
        actor_name: str = "Authorized Operator"
    ) -> SurplusItem:
        """
        Transitions surplus status through the 9 required statuses:
        AVAILABLE -> RESERVED -> PICKUP_SCHEDULED -> PICKED_UP -> IN_TRANSIT -> DELIVERED -> RECEIVED
        or EXPIRED / CANCELLED.
        """
        valid_statuses = [
            "AVAILABLE", "RESERVED", "PICKUP_SCHEDULED", "PICKED_UP",
            "IN_TRANSIT", "DELIVERED", "RECEIVED", "EXPIRED", "CANCELLED"
        ]
        norm_status = new_status.upper().strip()
        if norm_status not in valid_statuses:
            raise ValueError(f"Invalid status '{new_status}'. Allowed statuses: {', '.join(valid_statuses)}")

        item = db.query(SurplusItem).filter(
            SurplusItem.id == surplus_id,
            SurplusItem.deleted_at.is_(None)
        ).first()

        if not item:
            raise ValueError(f"Surplus record '{surplus_id}' was not found.")

        # Guard: Cannot move from terminal states to active states
        if item.status in ["DELIVERED", "RECEIVED", "CANCELLED"] and norm_status not in ["CANCELLED"]:
            raise ValueError(f"Cannot transition surplus from terminal state '{item.status}' to '{norm_status}'.")

        # Guard: Expired surplus cannot transition into active delivery lifecycle
        if norm_status in ["RESERVED", "PICKUP_SCHEDULED", "PICKED_UP", "IN_TRANSIT", "DELIVERED", "RECEIVED"]:
            safety_eval = cls.evaluate_item(item)
            if safety_eval.remaining_safe_window_minutes <= 0.0 or item.status == "EXPIRED":
                item.status = "EXPIRED"
                db.commit()
                raise ValueError("FOOD SAFETY VIOLATION: Expired surplus cannot be progressed in delivery pipeline.")

        item.status = norm_status
        item.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(item)
        return item
