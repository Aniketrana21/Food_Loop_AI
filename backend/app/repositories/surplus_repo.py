"""
FoodLoop AI - Surplus Item Repository
Manages surplus item lifecycles, shelf-life urgencies, and availability queries.
"""
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.models.models import SurplusItem


class SurplusRepository(BaseRepository[SurplusItem]):
    def __init__(self, db: Session):
        super().__init__(SurplusItem, db)

    def get_available_lots(self, org_id: Optional[str] = None) -> List[SurplusItem]:
        now = datetime.now(timezone.utc)
        query = self.db.query(SurplusItem).filter(
            SurplusItem.deleted_at.is_(None),
            SurplusItem.status == "AVAILABLE",
            SurplusItem.consumption_safe_until > now
        )
        if org_id:
            query = query.filter(SurplusItem.organization_id == org_id)
        return query.order_by(SurplusItem.consumption_safe_until.asc()).all()

    def update_status(self, surplus_id: str, new_status: str) -> SurplusItem:
        item = self.get_or_404(surplus_id, "SurplusItem")
        item.status = new_status
        item.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(item)
        return item
