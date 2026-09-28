"""
FoodLoop AI - Notifications & Centralized Multi-Channel Alert Router (Phase 17)
Handles in-app notification feeds, user preferences, canonical event templates,
event outbox dispatching with deduplication, quiet hours, and retry mechanics.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import (
    Notification,
    NotificationPreference,
    NotificationTemplate,
    NotificationEvent
)
from app.schemas.enterprise_schemas import NotificationCreate, NotificationOut
from app.schemas.notification_schemas import (
    NotificationPreferenceUpdate,
    NotificationPreferenceOut,
    NotificationTemplateCreate,
    NotificationTemplateUpdate,
    NotificationTemplateOut,
    TemplateTestRenderRequest,
    TemplateTestRenderResponse,
    NotificationEventDispatch,
    NotificationEventOut,
    NotificationEventRetryResponse,
    BatchRetryResponse,
    NotificationDeliveryStatsOut
)
from app.services.notification_service import notification_service
from app.utils.pagination import PaginationParams, paginate_query
from app.utils.exceptions import NotFoundError, ValidationError

router = APIRouter(prefix="/notifications", tags=["20. Real-Time Notifications & Multi-Channel Service"])


# =====================================================================
# 1. IN-APP NOTIFICATIONS FEED
# =====================================================================
@router.get("", response_model=dict)
def list_notifications(
    unread_only: bool = Query(False),
    category: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    params: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Lists in-app notifications for the authenticated user."""
    query = db.query(Notification).filter(Notification.user_id == user["id"])
    if unread_only:
        query = query.filter(Notification.is_read == False)
    if category:
        query = query.filter(Notification.category == category)
    if priority:
        query = query.filter(Notification.priority == priority)

    query = query.order_by(desc(Notification.created_at))
    return paginate_query(query, params, model_class=Notification)


@router.patch("/{notification_id}/read", response_model=NotificationOut)
def mark_notification_read(
    notification_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Marks a single in-app notification as read."""
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


@router.patch("/read-all", response_model=Dict[str, Any])
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Marks all unread in-app notifications as read for current user."""
    now = datetime.now(timezone.utc)
    unread_items = db.query(Notification).filter(
        Notification.user_id == user["id"],
        Notification.is_read == False
    ).all()

    for item in unread_items:
        item.is_read = True
        item.read_at = now

    db.commit()
    return {
        "status": "SUCCESS",
        "marked_read_count": len(unread_items),
        "timestamp": now.isoformat()
    }


@router.get("/unread-count")
def get_unread_count(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Returns count of unread notifications for current user."""
    count = db.query(Notification).filter(
        Notification.user_id == user["id"],
        Notification.is_read == False
    ).count()
    return {"unread_count": count}


# =====================================================================
# 2. NOTIFICATION PREFERENCES
# =====================================================================
@router.get("/preferences", response_model=NotificationPreferenceOut)
def get_user_preferences(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Retrieves notification preferences for the authenticated user (creates defaults if missing)."""
    pref = notification_service.get_or_create_preference(db, user["id"])
    return pref


@router.put("/preferences", response_model=NotificationPreferenceOut)
def update_user_preferences(
    update_data: NotificationPreferenceUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Updates channels, email address, push token, quiet hours, and per-event overrides."""
    pref = notification_service.get_or_create_preference(db, user["id"])

    if update_data.in_app_enabled is not None:
        pref.in_app_enabled = update_data.in_app_enabled
    if update_data.email_enabled is not None:
        pref.email_enabled = update_data.email_enabled
    if update_data.push_enabled is not None:
        pref.push_enabled = update_data.push_enabled
    if update_data.email_address is not None:
        pref.email_address = update_data.email_address
    if update_data.push_token is not None:
        pref.push_token = update_data.push_token
    if update_data.quiet_hours_enabled is not None:
        pref.quiet_hours_enabled = update_data.quiet_hours_enabled
    if update_data.quiet_hours_start is not None:
        pref.quiet_hours_start = update_data.quiet_hours_start
    if update_data.quiet_hours_end is not None:
        pref.quiet_hours_end = update_data.quiet_hours_end
    if update_data.event_overrides is not None:
        pref.event_overrides = update_data.event_overrides

    pref.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(pref)
    return pref


# =====================================================================
# 3. NOTIFICATION TEMPLATES
# =====================================================================
@router.get("/templates", response_model=List[NotificationTemplateOut])
def list_notification_templates(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Lists all configured notification templates (auto-seeds defaults if empty)."""
    notification_service.seed_default_templates(db)
    templates = db.query(NotificationTemplate).order_by(NotificationTemplate.event_type.asc()).all()
    return templates


@router.get("/templates/{event_type}", response_model=NotificationTemplateOut)
def get_notification_template(
    event_type: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Retrieves a specific event template by its canonical event identifier."""
    notification_service.seed_default_templates(db)
    tmpl = db.query(NotificationTemplate).filter(
        NotificationTemplate.event_type == event_type
    ).first()
    if not tmpl:
        raise NotFoundError(f"Template for event '{event_type}' not found", code="TEMPLATE_NOT_FOUND")
    return tmpl


@router.put("/templates/{event_type}", response_model=NotificationTemplateOut)
def update_notification_template(
    event_type: str,
    update_data: NotificationTemplateUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Updates title, in-app, email, or push templates for an event (Super Admin / Admin)."""
    notification_service.seed_default_templates(db)
    tmpl = db.query(NotificationTemplate).filter(
        NotificationTemplate.event_type == event_type
    ).first()
    if not tmpl:
        raise NotFoundError(f"Template for event '{event_type}' not found", code="TEMPLATE_NOT_FOUND")

    if update_data.name is not None:
        tmpl.name = update_data.name
    if update_data.description is not None:
        tmpl.description = update_data.description
    if update_data.title_template is not None:
        tmpl.title_template = update_data.title_template
    if update_data.in_app_template is not None:
        tmpl.in_app_template = update_data.in_app_template
    if update_data.email_subject_template is not None:
        tmpl.email_subject_template = update_data.email_subject_template
    if update_data.email_body_template is not None:
        tmpl.email_body_template = update_data.email_body_template
    if update_data.push_title_template is not None:
        tmpl.push_title_template = update_data.push_title_template
    if update_data.push_body_template is not None:
        tmpl.push_body_template = update_data.push_body_template
    if update_data.default_priority is not None:
        tmpl.default_priority = update_data.default_priority
    if update_data.is_active is not None:
        tmpl.is_active = update_data.is_active

    tmpl.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(tmpl)
    return tmpl


@router.post("/templates/test-render", response_model=TemplateTestRenderResponse)
def test_render_template(
    req: TemplateTestRenderRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Test-renders template placeholders with provided sample payload variables."""
    notification_service.seed_default_templates(db)
    tmpl = db.query(NotificationTemplate).filter(
        NotificationTemplate.event_type == req.event_type
    ).first()

    if not tmpl:
        # Render with ad-hoc placeholders
        rendered_title = notification_service.render_template_string("Event: {event_type}", req.payload)
        rendered_in_app = notification_service.render_template_string("Notification payload: {payload}", req.payload)
        return TemplateTestRenderResponse(
            event_type=req.event_type,
            rendered_title=rendered_title,
            rendered_in_app=rendered_in_app
        )

    return TemplateTestRenderResponse(
        event_type=req.event_type,
        rendered_title=notification_service.render_template_string(tmpl.title_template, req.payload),
        rendered_in_app=notification_service.render_template_string(tmpl.in_app_template, req.payload),
        rendered_email_subject=notification_service.render_template_string(tmpl.email_subject_template, req.payload),
        rendered_email_body=notification_service.render_template_string(tmpl.email_body_template, req.payload),
        rendered_push_title=notification_service.render_template_string(tmpl.push_title_template, req.payload),
        rendered_push_body=notification_service.render_template_string(tmpl.push_body_template, req.payload)
    )


# =====================================================================
# 4. EVENT DISPATCH, OUTBOX & RETRY MECHANICS
# =====================================================================
@router.post("/events/dispatch", response_model=NotificationEventOut, status_code=status.HTTP_201_CREATED)
def dispatch_notification_event(
    dispatch_req: NotificationEventDispatch,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Dispatches a canonical notification event across in-app, email, and push channels.
    Includes automated deduplication, quiet hours filtering, and retry scheduling on delivery failure.
    """
    # Default target user if not specified
    if not dispatch_req.user_id and not dispatch_req.organization_id:
        dispatch_req.user_id = user["id"]

    event = notification_service.dispatch_event(db, dispatch_req)
    return event


@router.get("/events", response_model=List[NotificationEventOut])
def list_notification_events(
    event_type: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    user_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Queries the notification events outbox with filtering and delivery diagnostics."""
    query = db.query(NotificationEvent)
    if event_type:
        query = query.filter(NotificationEvent.event_type == event_type)
    if status_filter:
        query = query.filter(NotificationEvent.status == status_filter)
    if user_id:
        query = query.filter(NotificationEvent.user_id == user_id)

    events = query.order_by(desc(NotificationEvent.created_at)).offset(offset).limit(limit).all()
    return events


@router.get("/events/{event_id}", response_model=NotificationEventOut)
def get_notification_event(
    event_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Retrieves full dispatch metadata and channel delivery telemetry for a specific event."""
    event = db.query(NotificationEvent).filter(NotificationEvent.id == event_id).first()
    if not event:
        raise NotFoundError(f"Notification event '{event_id}' not found", code="EVENT_NOT_FOUND")
    return event


@router.post("/events/{event_id}/retry", response_model=NotificationEventRetryResponse)
def retry_single_notification_event(
    event_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Triggers an immediate retry attempt for a failed or retrying event."""
    try:
        result = notification_service.retry_event(db, event_id)
        return result
    except ValueError as e:
        raise NotFoundError(str(e), code="EVENT_NOT_FOUND")


@router.post("/events/retry-failed", response_model=BatchRetryResponse)
def retry_failed_events_batch(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Batch-retries eligible failed/retrying events across the entire outbox."""
    return notification_service.retry_batch_failed(db, limit=limit)


@router.get("/stats", response_model=NotificationDeliveryStatsOut)
def get_notification_statistics(
    organization_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Returns telemetry on delivery success rate, channel distribution, and deduplication count."""
    return notification_service.get_delivery_stats(db, organization_id=organization_id)
