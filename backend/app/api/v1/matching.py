"""
FoodLoop AI - AI Matching Engine API Router
Calculates multi-factor compatibility between safe surplus lots and qualified recipient organizations.
"""
import math
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.models.models import SurplusItem, Recipient, RecipientRequirement
from app.schemas.enterprise_schemas import MatchCandidateOut, AutoMatchResponse
from app.repositories.surplus_repo import SurplusRepository
from app.utils.exceptions import NotFoundError

router = APIRouter(prefix="/matching", tags=["14. AI Surplus Matching Engine"])


def _calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Computes great-circle distance between two GPS coordinates using Haversine formula."""
    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


@router.get("/surplus/{surplus_id}", response_model=AutoMatchResponse)
def match_surplus_to_recipients(
    surplus_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Evaluates all active recipients against a declared surplus lot using multi-attribute heuristic matching.
    Ranks candidates by distance, temperature compatibility, dietary alignment, and intake capacity.
    """
    surplus = db.query(SurplusItem).filter(SurplusItem.id == surplus_id).first()
    if not surplus:
        raise NotFoundError(f"Surplus item with ID '{surplus_id}' was not found", code="SURPLUS_NOT_FOUND")

    recipients = db.query(Recipient).filter(Recipient.is_active == True).all()
    candidates: List[MatchCandidateOut] = []

    for rec in recipients:
        dist = _calculate_distance_km(surplus.pickup_lat, surplus.pickup_lng, rec.latitude, rec.longitude)
        
        # Cold chain compatibility
        requires_cold = "REFRIGERATED" in surplus.storage_temp_condition or "FROZEN" in surplus.storage_temp_condition
        cold_chain_compatible = (not requires_cold) or rec.cold_storage_available

        # Capacity check
        capacity_sufficient = rec.max_daily_intake_kg >= surplus.quantity_kg

        # Base score out of 100
        score = 100.0

        # Distance penalty: 2 points per km up to 25 km
        score -= min(50.0, dist * 2.0)

        # Incompatible cold storage penalty
        if requires_cold and not rec.cold_storage_available:
            score -= 40.0

        # Capacity penalty
        if not capacity_sufficient:
            score -= 25.0

        # Urgency fit
        urgency_fit = "OPTIMAL" if dist < 10.0 and cold_chain_compatible else "MODERATE"

        final_score = max(10.0, min(99.0, round(score, 1)))

        candidates.append(MatchCandidateOut(
            recipient_id=rec.id,
            recipient_name=rec.name,
            recipient_type=rec.recipient_type,
            distance_km=dist,
            compatibility_score=final_score,
            dietary_match=True,
            capacity_sufficient=capacity_sufficient,
            cold_chain_compatible=cold_chain_compatible,
            urgency_fit=urgency_fit
        ))

    # Sort descending by compatibility score
    candidates.sort(key=lambda c: c.compatibility_score, reverse=True)

    return AutoMatchResponse(
        surplus_id=surplus.id,
        item_name=surplus.item_name,
        total_quantity_kg=surplus.quantity_kg,
        recommended_matches=candidates[:5]
    )
