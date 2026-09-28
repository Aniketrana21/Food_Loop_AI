"""
FoodLoop AI - Phase 17 Notification System Schemas
Contracts for notification preferences, templates, event dispatches, and delivery logs.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


# =====================================================================
# 1. NOTIFICATION PREFERENCES
# =====================================================================
class NotificationPreferenceBase(BaseModel):
    in_app_enabled: bool = True
    email_enabled: bool = True
    push_enabled: bool = True
    email_address: Optional[str] = None
    push_token: Optional[str] = None
    quiet_hours_enabled: bool = False
    quiet_hours_start: str = Field(default="22:00", description="HH:MM in 24hr format")
    quiet_hours_end: str = Field(default="07:00", description="HH:MM in 24hr format")
    event_overrides: Dict[str, Dict[str, bool]] = Field(
        default_factory=dict,
        description="Per-event channel toggles, e.g. {'surplus.urgent': {'email': True, 'push': True, 'in_app': True}}"
    )


class NotificationPreferenceUpdate(BaseModel):
    in_app_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    email_address: Optional[str] = None
    push_token: Optional[str] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    event_overrides: Optional[Dict[str, Dict[str, bool]]] = None


class NotificationPreferenceOut(NotificationPreferenceBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# =====================================================================
# 2. NOTIFICATION TEMPLATES
# =====================================================================
class NotificationTemplateBase(BaseModel):
    event_type: str = Field(..., description="Canonical event identifier, e.g. 'surplus.urgent'")
    name: str = Field(..., description="Human-readable template name")
    description: Optional[str] = None
    title_template: str = Field(..., description="Title with variable placeholders, e.g. '{quantity_kg}kg {item_name}'")
    in_app_template: str = Field(..., description="In-app notification body template")
    email_subject_template: Optional[str] = None
    email_body_template: Optional[str] = None
    push_title_template: Optional[str] = None
    push_body_template: Optional[str] = None
    default_priority: str = Field(default="NORMAL", description="LOW | NORMAL | HIGH | CRITICAL")
    is_active: bool = True


class NotificationTemplateCreate(NotificationTemplateBase):
    pass


class NotificationTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    title_template: Optional[str] = None
    in_app_template: Optional[str] = None
    email_subject_template: Optional[str] = None
    email_body_template: Optional[str] = None
    push_title_template: Optional[str] = None
    push_body_template: Optional[str] = None
    default_priority: Optional[str] = None
    is_active: Optional[bool] = None


class NotificationTemplateOut(NotificationTemplateBase):
    id: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TemplateTestRenderRequest(BaseModel):
    event_type: str
    payload: Dict[str, Any]


class TemplateTestRenderResponse(BaseModel):
    event_type: str
    rendered_title: str
    rendered_in_app: str
    rendered_email_subject: Optional[str] = None
    rendered_email_body: Optional[str] = None
    rendered_push_title: Optional[str] = None
    rendered_push_body: Optional[str] = None


# =====================================================================
# 3. NOTIFICATION EVENTS & DISPATCH
# =====================================================================
class NotificationEventDispatch(BaseModel):
    event_type: str = Field(
        ...,
        description="One of the 10 canonical events: surplus.created, surplus.urgent, recipient.accepted, "
                    "pickup.assigned, pickup.delayed, delivery.completed, expiry.approaching, "
                    "waste.high_detected, forecast.generated, ai.recommendation_generated"
    )
    payload: Dict[str, Any] = Field(..., description="Context dictionary matching template variables")
    user_id: Optional[str] = Field(None, description="Direct target recipient user ID")
    organization_id: Optional[str] = Field(None, description="Target organization ID")
    channels: Optional[List[str]] = Field(None, description="Explicit channels: in_app, email, push. Defaults to user prefs.")
    idempotency_key: Optional[str] = Field(None, description="Deduplication key to avoid repeated dispatches")
    force_dispatch: bool = Field(False, description="If True, bypasses deduplication window")
    priority_override: Optional[str] = Field(None, description="LOW | NORMAL | HIGH | CRITICAL")


class NotificationEventOut(BaseModel):
    id: str
    event_type: str
    organization_id: Optional[str] = None
    user_id: Optional[str] = None
    idempotency_key: Optional[str] = None
    payload: Dict[str, Any]
    channels: List[str]
    status: str
    attempts: int
    max_retries: int
    last_error: Optional[str] = None
    rendered_title: Optional[str] = None
    rendered_body: Optional[str] = None
    channel_delivery_results: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    sent_at: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class NotificationEventRetryResponse(BaseModel):
    event_id: str
    status: str
    attempts: int
    channel_delivery_results: Dict[str, Any]
    last_error: Optional[str] = None


class BatchRetryResponse(BaseModel):
    total_eligible: int
    retried_count: int
    succeeded_count: int
    failed_count: int
    details: List[NotificationEventRetryResponse]


# =====================================================================
# 4. NOTIFICATION OVERVIEW & STATS
# =====================================================================
class NotificationDeliveryStatsOut(BaseModel):
    total_events: int
    delivered_events: int
    failed_events: int
    retrying_events: int
    deduplicated_events: int
    suppressed_quiet_hours: int
    channel_counts: Dict[str, int]
    success_rate_pct: float
    average_attempts: float
