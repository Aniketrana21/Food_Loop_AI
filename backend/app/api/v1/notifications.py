"""
FoodLoop AI - Notifications & Alerts API Router
Handles dispatch notifications, temperature excursion alerts, and audit alerts.
"""
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import Notification
from app.schemas.enterprise_schemas import NotificationCreate, NotificationOut
from app.utils.pagination import PaginationParams, paginate_query
from app.utils.exceptions import NotFoundError

router = APIRouter(prefix="/notifications", tags=["20. Real-Time Notifications"])


@router.get("", response_model=dict)
def list_notifications(
    unread_only: bool = Query(False),
    params: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Lists notifications for the authenticated user."""
    query = db.query(Notification).filter(Notification.user_id == user["id"])
    if unread_only:
        query = query.filter(Notification.is_read == False)

    return paginate_query(query, params, model_class=Notification)


@router.patch("/{notification_id}/read", response_model=NotificationOut)
def mark_notification_read(
    notification_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Marks a notification as read."""
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user["id"]
    ).first()
    if not notif:
        raise NotFoundError(f"Notification with ID '{notification_id}' not found", code="NOTIFICATION_NOT_FOUND")

    notif.is_read = True
    notif.read_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(notif)
    return notif


@router.get("/unread-count")
def get_unread_count(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Returns count of unread notifications."""
    count = db.query(Notification).filter(
        Notification.user_id == user["id"],
        Notification.is_read == False
    ).count()
    return {"unread_count": count}
