"""
FoodLoop AI - Donation Repository
Manages atomic creation of donation dispatches and nested donation item manifests.
"""
import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.models.models import Donation, DonationItem, SurplusItem


class DonationRepository(BaseRepository[Donation]):
    def __init__(self, db: Session):
        super().__init__(Donation, db)

    def create_donation_manifest(
        self,
        donor_org_id: str,
        recipient_org_id: Optional[str] = None,
        items_payload: List[Dict[str, Any]] = None,
        haccp_verified: bool = True,
        initial_status: str = "DONATION_CREATED",
        user_id: Optional[str] = None,
        role: str = "KITCHEN_MANAGER"
    ) -> Donation:
        from datetime import datetime, timezone
        import hashlib
        from app.models.models import DonationCustodyEvent

        items_payload = items_payload or []
        tracking_no = f"TRK-{uuid.uuid4().hex[:8].upper()}"
        immutable_id = f"DON-{uuid.uuid4().hex[:8].upper()}"

        total_weight = sum(item.get("quantity_kg", item.get("allocated_quantity_kg", 0.0)) for item in items_payload)
        total_portions = sum(item.get("portions", item.get("allocated_portions", 0)) for item in items_payload)

        status_val = initial_status if initial_status in ["DONATION_CREATED", "ACCEPTED"] else "DONATION_CREATED"

        donation = Donation(
            donor_org_id=donor_org_id,
            recipient_org_id=recipient_org_id,
            immutable_donation_id=immutable_id,
            tracking_number=tracking_no,
            total_weight_kg=total_weight,
            total_portions=total_portions,
            status=status_val,
            haccp_verified=haccp_verified
        )
        self.db.add(donation)
        self.db.flush()

        for item_data in items_payload:
            d_item = DonationItem(
                donation_id=donation.id,
                surplus_item_id=item_data["surplus_item_id"],
                allocated_quantity_kg=item_data.get("quantity_kg", item_data.get("allocated_quantity_kg", 0.0)),
                allocated_portions=item_data.get("portions", item_data.get("allocated_portions", 0))
            )
            self.db.add(d_item)

            # Mark surplus item as reserved
            s_item = self.db.query(SurplusItem).filter(SurplusItem.id == item_data["surplus_item_id"]).first()
            if s_item:
                s_item.status = "RESERVED"

        # Genesis custody event
        now = datetime.now(timezone.utc)
        prev_hash = "0" * 64
        genesis_raw = f"{prev_hash}|{now.isoformat()}|{user_id}|{role}|{donation.id}|DONATION_CREATED|weight={total_weight}kg"
        integrity_hash = hashlib.sha256(genesis_raw.encode("utf-8")).hexdigest()

        genesis_event = DonationCustodyEvent(
            donation_id=donation.id,
            event="DONATION_CREATED",
            from_status="NONE",
            to_status=status_val,
            user_id=user_id,
            role=role,
            timestamp=now.replace(tzinfo=None),
            notes=f"Manifest created with {len(items_payload)} surplus allocations ({total_weight} kg).",
            previous_hash=prev_hash,
            integrity_hash=integrity_hash
        )
        self.db.add(genesis_event)

        self.db.commit()
        self.db.refresh(donation)
        return donation
