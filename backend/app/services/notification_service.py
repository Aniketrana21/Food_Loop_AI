"""
FoodLoop AI - Centralized Notification Service (Phase 17)
Handles multi-channel delivery (in-app, email, push), templating for 10 canonical events,
deduplication, quiet hours filtering, exponential backoff retries, and non-crashing fault tolerance.
"""
import re
import hashlib
import logging
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta, time as dtime
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc

from app.models.models import (
    Notification,
    NotificationPreference,
    NotificationTemplate,
    NotificationEvent,
    User,
    OrganizationMember
)
from app.schemas.notification_schemas import (
    NotificationEventDispatch,
    NotificationEventOut,
    NotificationEventRetryResponse,
    BatchRetryResponse,
    NotificationDeliveryStatsOut
)

logger = logging.getLogger("foodloop.notifications")

# =====================================================================
# 10 CANONICAL EVENTS & DEFAULT SEED TEMPLATES
# =====================================================================
CANONICAL_TEMPLATES = [
    {
        "event_type": "surplus.created",
        "name": "Surplus Created",
        "description": "Triggered when a kitchen or processing unit lists a new surplus food batch.",
        "default_priority": "NORMAL",
        "title_template": "New Surplus Available: {item_name} ({quantity_kg} kg)",
        "in_app_template": "{quantity_kg} kg of {item_name} listed by {facility_name}. Available for matching until {expiry_time}.",
        "email_subject_template": "[FoodLoop] New Surplus Available: {item_name} ({quantity_kg} kg)",
        "email_body_template": (
            "Hello,\n\nA new surplus lot of {quantity_kg} kg of {item_name} has been listed at {facility_name}.\n"
            "Storage Condition: {storage_type}\n"
            "Pickup Window Ends: {expiry_time}\n\n"
            "Log in to FoodLoop to claim or coordinate redistribution.\n\n"
            "— FoodLoop AI Redistribution Engine"
        ),
        "push_title_template": "Surplus Listed: {item_name}",
        "push_body_template": "{quantity_kg} kg available from {facility_name}. Tap to inspect and claim."
    },
    {
        "event_type": "surplus.urgent",
        "name": "Surplus Urgent",
        "description": "Triggered when surplus inventory approaches critical food safety expiration thresholds.",
        "default_priority": "CRITICAL",
        "title_template": "🚨 URGENT RESCUE: {quantity_kg} kg of {item_name} expiring soon!",
        "in_app_template": "CRITICAL: {quantity_kg} kg of {item_name} at {facility_name} reaches safety limit in {hours_remaining} hours. Urgent dispatch required.",
        "email_subject_template": "[URGENT RESCUE] {quantity_kg} kg of {item_name} at {facility_name}",
        "email_body_template": (
            "URGENT ATTENTION REQUIRED:\n\n"
            "{quantity_kg} kg of {item_name} at {facility_name} has entered the emergency rescue window.\n"
            "Estimated Expiry: {expiry_time} ({hours_remaining} hours remaining).\n"
            "Immediate redistribution or recipient handoff is mandated by FEFO food safety protocols.\n\n"
            "— FoodLoop AI Automated Safety Monitor"
        ),
        "push_title_template": "🚨 Urgent Surplus: {item_name}",
        "push_body_template": "{quantity_kg} kg needs rescue within {hours_remaining}h at {facility_name}!"
    },
    {
        "event_type": "recipient.accepted",
        "name": "Recipient Accepted",
        "description": "Triggered when a charitable recipient confirms acceptance of a surplus donation.",
        "default_priority": "HIGH",
        "title_template": "Donation Claim Confirmed: {recipient_name}",
        "in_app_template": "{recipient_name} has accepted donation {donation_id} for {quantity_kg} kg of {item_name}. Preparing logistics dispatch.",
        "email_subject_template": "[FoodLoop] Donation Claim Confirmed by {recipient_name}",
        "email_body_template": (
            "Hello,\n\n"
            "Great news! {recipient_name} has accepted donation {donation_id} ({quantity_kg} kg of {item_name}).\n"
            "Logistics coordination is underway. You will be notified when a driver is assigned for pickup.\n\n"
            "— FoodLoop AI Logistics Engine"
        ),
        "push_title_template": "Donation Claimed",
        "push_body_template": "{recipient_name} confirmed {quantity_kg} kg of {item_name}."
    },
    {
        "event_type": "pickup.assigned",
        "name": "Pickup Assigned",
        "description": "Triggered when a driver or fleet courier is assigned to pick up a donation.",
        "default_priority": "NORMAL",
        "title_template": "Courier Assigned: {courier_name} (ETA: {eta_minutes}m)",
        "in_app_template": "Courier {courier_name} assigned for pickup at {facility_name}. Estimated arrival: {eta_minutes} minutes.",
        "email_subject_template": "[FoodLoop Dispatch] Courier {courier_name} Assigned for Pickup",
        "email_body_template": (
            "Logistics Dispatch Update:\n\n"
            "Courier {courier_name} ({courier_phone}) has been assigned for donation {donation_id}.\n"
            "Pickup Location: {facility_name}\n"
            "Estimated Arrival: {eta_minutes} minutes.\n\n"
            "— FoodLoop AI Fleet Dispatch"
        ),
        "push_title_template": "Courier Assigned",
        "push_body_template": "{courier_name} is en route to {facility_name} (ETA {eta_minutes}m)."
    },
    {
        "event_type": "pickup.delayed",
        "name": "Pickup Delayed",
        "description": "Triggered when active delivery encounters logistics congestion, vehicle trouble, or schedule delay.",
        "default_priority": "HIGH",
        "title_template": "⚠️ Pickup Delayed: {courier_name} (+{delay_minutes}m)",
        "in_app_template": "Logistics delay reported for donation {donation_id}. Reason: {delay_reason}. Revised ETA: {new_eta_minutes} minutes.",
        "email_subject_template": "[FoodLoop Alert] Logistics Delay for Donation {donation_id}",
        "email_body_template": (
            "Notice of Transit Delay:\n\n"
            "Courier {courier_name} has reported a delay for donation {donation_id}.\n"
            "Reason: {delay_reason}\n"
            "Revised Arrival Window: {new_eta_minutes} minutes from now.\n\n"
            "— FoodLoop AI Logistics Engine"
        ),
        "push_title_template": "⚠️ Delivery Delay",
        "push_body_template": "Donation {donation_id} delayed ({delay_reason}). New ETA: {new_eta_minutes}m."
    },
    {
        "event_type": "delivery.completed",
        "name": "Delivery Completed",
        "description": "Triggered upon verified digital handoff and recipient signature confirmation.",
        "default_priority": "NORMAL",
        "title_template": "✅ Delivery Completed: {quantity_kg} kg to {recipient_name}",
        "in_app_template": "Success! {quantity_kg} kg of {item_name} safely delivered to {recipient_name}. Verified with secure handoff signature.",
        "email_subject_template": "[FoodLoop Impact] Delivery Completed to {recipient_name}",
        "email_body_template": (
            "Handoff Confirmation:\n\n"
            "Donation {donation_id} has been successfully delivered to {recipient_name}.\n"
            "Quantity Rescued: {quantity_kg} kg of {item_name}\n"
            "Estimated CO2e Avoided: {co2e_kg} kg\n\n"
            "Thank you for powering sustainable zero-waste operations!\n\n"
            "— FoodLoop AI"
        ),
        "push_title_template": "Delivery Completed ✅",
        "push_body_template": "{quantity_kg} kg of {item_name} safely delivered to {recipient_name}."
    },
    {
        "event_type": "expiry.approaching",
        "name": "Expiry Approaching",
        "description": "Triggered by the FEFO engine when batches reach 7, 3, or 1 day thresholds.",
        "default_priority": "HIGH",
        "title_template": "⏰ Expiry Warning: {item_name} ({hours_remaining}h remaining)",
        "in_app_template": "Batch {batch_id} ({item_name}) at {facility_name} is within {hours_remaining} hours of expiry. Expedite production or schedule redistribution.",
        "email_subject_template": "[FEFO Food Safety] Expiry Approaching for Batch {batch_id}",
        "email_body_template": (
            "Attention Production & Kitchen Operations:\n\n"
            "Batch {batch_id} ({item_name}) at {facility_name} will expire in {hours_remaining} hours (Date: {expiry_date}).\n"
            "Action required: Allocate to immediate prep or mark as surplus lot for redistribution.\n\n"
            "— FoodLoop AI FEFO Quality Engine"
        ),
        "push_title_template": "Expiry Warning ⏰",
        "push_body_template": "{item_name} (Batch {batch_id}) expires in {hours_remaining} hours."
    },
    {
        "event_type": "waste.high_detected",
        "name": "High Waste Detected",
        "description": "Triggered when kitchen or FPU waste logs exceed moving-average thresholds by >30%.",
        "default_priority": "HIGH",
        "title_template": "🚨 Abnormal Waste Spike: {waste_kg} kg (+{percentage_increase}%)",
        "in_app_template": "Abnormal organic waste recorded at {kitchen_name}: {waste_kg} kg (+{percentage_increase}% vs 14-day baseline). Immediate kitchen audit recommended.",
        "email_subject_template": "[Waste Anomaly Alert] High Waste Detected at {kitchen_name}",
        "email_body_template": (
            "Attention Management:\n\n"
            "A waste log at {kitchen_name} recorded {waste_kg} kg of food waste, representing a {percentage_increase}% increase above historical baseline.\n"
            "Category Breakdown: {waste_category}\n"
            "Recommended Action: Conduct immediate station audit and review prep forecast.\n\n"
            "— FoodLoop AI Sustainability Engine"
        ),
        "push_title_template": "🚨 Abnormal Waste Spike",
        "push_body_template": "{waste_kg} kg waste recorded at {kitchen_name} (+{percentage_increase}%)."
    },
    {
        "event_type": "forecast.generated",
        "name": "Forecast Generated",
        "description": "Triggered when Bayesian demand forecast and surplus projection completes.",
        "default_priority": "LOW",
        "title_template": "📊 Demand & Surplus Forecast Ready ({target_date})",
        "in_app_template": "AI forecast completed for {facility_name} ({target_date}). Projected headcount: {projected_headcount}, estimated surplus: {estimated_surplus_kg} kg.",
        "email_subject_template": "[FoodLoop AI] Operational Forecast Ready for {target_date}",
        "email_body_template": (
            "Operational Intelligence Summary:\n\n"
            "Forecasting for {facility_name} on {target_date} is complete.\n"
            "• Projected Headcount: {projected_headcount}\n"
            "• Estimated Surplus: {estimated_surplus_kg} kg\n"
            "• Model Confidence: {confidence_score}%\n\n"
            "Access the kitchen portal to review prep recommendations.\n\n"
            "— FoodLoop AI ML Forecasting System"
        ),
        "push_title_template": "Forecast Ready 📊",
        "push_body_template": "Operational forecast ready for {target_date} at {facility_name}."
    },
    {
        "event_type": "ai.recommendation_generated",
        "name": "AI Recommendation Generated",
        "description": "Triggered when AI recipe repurposing or dynamic redistribution recommendation is generated.",
        "default_priority": "NORMAL",
        "title_template": "💡 AI Sustainability Recommendation: {recommendation_title}",
        "in_app_template": "AI Assistant generated a recipe and prep recommendation for {facility_name}: {recommendation_summary}",
        "email_subject_template": "[FoodLoop AI] New Recipe & Redistribution Recommendation",
        "email_body_template": (
            "AI Copilot Insight:\n\n"
            "A new sustainability recommendation has been synthesized for {facility_name}:\n"
            "Recommendation: {recommendation_title}\n"
            "Details: {recommendation_summary}\n"
            "Potential Waste Saved: {potential_saving_kg} kg\n\n"
            "— FoodLoop AI Assistant"
        ),
        "push_title_template": "💡 AI Recommendation",
        "push_body_template": "{recommendation_title} generated for {facility_name}."
    }
]


class NotificationService:
    """Centralized notification management and multi-channel dispatch engine."""

    def __init__(self, dedup_window_minutes: int = 10, max_retries: int = 3):
        self.dedup_window_minutes = dedup_window_minutes
        self.max_retries = max_retries

    # -----------------------------------------------------------------
    # TEMPLATE SEEDING & RENDERING
    # -----------------------------------------------------------------
    def seed_default_templates(self, db: Session) -> int:
        """Seeds canonical templates into the database if not present."""
        created_count = 0
        for item in CANONICAL_TEMPLATES:
            existing = db.query(NotificationTemplate).filter(
                NotificationTemplate.event_type == item["event_type"]
            ).first()
            if not existing:
                template = NotificationTemplate(
                    id=str(uuid.uuid4()),
                    event_type=item["event_type"],
                    name=item["name"],
                    description=item.get("description"),
                    default_priority=item.get("default_priority", "NORMAL"),
                    title_template=item["title_template"],
                    in_app_template=item["in_app_template"],
                    email_subject_template=item.get("email_subject_template"),
                    email_body_template=item.get("email_body_template"),
                    push_title_template=item.get("push_title_template"),
                    push_body_template=item.get("push_body_template"),
                    is_active=True,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                db.add(template)
                created_count += 1
        if created_count > 0:
            db.commit()
            logger.info(f"Seeded {created_count} default notification templates.")
        return created_count

    def render_template_string(self, template_str: Optional[str], payload: Dict[str, Any]) -> str:
        """Safely renders template variables with fallback placeholders for missing keys."""
        if not template_str:
            return ""

        # Support both {variable} and {{variable}} placeholders
        def replace_match(match):
            key = match.group(1).strip("{} ").strip()
            val = payload.get(key)
            if val is not None:
                return str(val)
            # Friendly fallback for missing keys
            return f"[{key}]"

        # Regex matches {{key}} or {key}
        pattern = re.compile(r"\{\{?([a-zA-Z0-9_\-\.]+)\}?\}")
        return pattern.sub(replace_match, template_str)

    # -----------------------------------------------------------------
    # USER PREFERENCES & QUIET HOURS
    # -----------------------------------------------------------------
    def get_or_create_preference(self, db: Session, user_id: str) -> NotificationPreference:
        """Retrieves or creates default notification preferences for a user."""
        pref = db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id
        ).first()

        if not pref:
            # Query user email if available
            user = db.query(User).filter(User.id == user_id).first()
            user_email = user.email if user else None

            pref = NotificationPreference(
                id=str(uuid.uuid4()),
                user_id=user_id,
                in_app_enabled=True,
                email_enabled=True,
                push_enabled=True,
                email_address=user_email,
                push_token=None,
                quiet_hours_enabled=False,
                quiet_hours_start="22:00",
                quiet_hours_end="07:00",
                event_overrides={},
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(pref)
            db.commit()
            db.refresh(pref)
        return pref

    def is_in_quiet_hours(self, pref: NotificationPreference, now: Optional[datetime] = None) -> bool:
        """Checks if current time falls within user's configured quiet hours."""
        if not pref or not pref.quiet_hours_enabled:
            return False

        current = (now or datetime.now(timezone.utc)).time()
        try:
            start_parts = [int(p) for p in pref.quiet_hours_start.split(":")]
            end_parts = [int(p) for p in pref.quiet_hours_end.split(":")]
            start_t = dtime(start_parts[0], start_parts[1])
            end_t = dtime(end_parts[0], end_parts[1])

            if start_t <= end_t:
                return start_t <= current <= end_t
            else:
                # Overnight quiet hours, e.g. 22:00 to 07:00
                return current >= start_t or current <= end_t
        except Exception as e:
            logger.warning(f"Error parsing quiet hours ({pref.quiet_hours_start} - {pref.quiet_hours_end}): {e}")
            return False

    # -----------------------------------------------------------------
    # DEDUPLICATION LOGIC
    # -----------------------------------------------------------------
    def compute_idempotency_key(self, event_type: str, user_id: Optional[str], org_id: Optional[str], payload: Dict[str, Any]) -> str:
        """Generates a deterministic deduplication key for an event."""
        # Significant identifying elements from payload (e.g., entity IDs)
        key_fields = []
        for candidate in ["donation_id", "surplus_id", "item_name", "batch_id", "kitchen_id", "delivery_id"]:
            if candidate in payload:
                key_fields.append(f"{candidate}:{payload[candidate]}")

        payload_repr = "|".join(key_fields) if key_fields else str(sorted(payload.items()))
        raw = f"{event_type}:{user_id or org_id or 'global'}:{payload_repr}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]

    def check_duplicate(self, db: Session, idempotency_key: str, window_minutes: int) -> Optional[NotificationEvent]:
        """Checks if an event with the same idempotency key was emitted within the deduplication window."""
        if not idempotency_key:
            return None

        cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
        existing = db.query(NotificationEvent).filter(
            NotificationEvent.idempotency_key == idempotency_key,
            NotificationEvent.created_at >= cutoff,
            NotificationEvent.status.in_(["DELIVERED", "PARTIALLY_DELIVERED", "PENDING", "RETRYING"])
        ).first()

        return existing

    # -----------------------------------------------------------------
    # CHANNEL DELIVERY HANDLERS
    # -----------------------------------------------------------------
    def deliver_in_app(
        self,
        db: Session,
        user_ids: List[str],
        org_id: Optional[str],
        title: str,
        message: str,
        priority: str,
        event_id: str,
        action_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Delivers in-app notification records to the database."""
        created_ids = []
        for uid in user_ids:
            # Query organization ID for user if not provided
            target_org_id = org_id
            if not target_org_id:
                member = db.query(OrganizationMember).filter(OrganizationMember.user_id == uid).first()
                if member:
                    target_org_id = member.organization_id

            if not target_org_id:
                # Fallback to user's first available org or skip
                continue

            notif = Notification(
                id=str(uuid.uuid4()),
                user_id=uid,
                organization_id=target_org_id,
                title=title,
                message=message,
                category="SYSTEM",
                priority=priority,
                is_read=False,
                action_url=action_url,
                event_id=event_id,
                created_at=datetime.now(timezone.utc)
            )
            db.add(notif)
            created_ids.append(notif.id)

        db.flush()
        return {
            "status": "DELIVERED",
            "created_notifications": len(created_ids),
            "notification_ids": created_ids,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def deliver_email(
        self,
        recipient_email: str,
        subject: str,
        body: str,
        event_id: str,
        simulate_failure: bool = False
    ) -> Dict[str, Any]:
        """Dispatches an email notification via SMTP adapter (with simulated transport)."""
        if not recipient_email or "@" not in recipient_email:
            return {
                "status": "FAILED",
                "error": f"Invalid or missing recipient email address: '{recipient_email}'",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        if simulate_failure:
            return {
                "status": "FAILED",
                "error": "Simulated SMTP connection timeout (504 Gateway Timeout)",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        # Simulated high-reliability transport log
        msg_id = f"smtp_{hashlib.sha256(f'{event_id}:{recipient_email}'.encode()).hexdigest()[:16]}"
        logger.info(f"[Email Dispatch] Sent to {recipient_email}: '{subject}' (ID: {msg_id})")

        return {
            "status": "DELIVERED",
            "provider": "smtp_mock_adapter",
            "recipient": recipient_email,
            "message_id": msg_id,
            "subject": subject,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def deliver_push(
        self,
        push_token: Optional[str],
        title: str,
        body: str,
        event_id: str,
        priority: str,
        simulate_failure: bool = False
    ) -> Dict[str, Any]:
        """Dispatches a web/mobile push notification."""
        if not push_token:
            return {
                "status": "SKIPPED",
                "reason": "No push token registered for user",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        if simulate_failure:
            return {
                "status": "FAILED",
                "error": "Simulated Push Gateway 503 Service Unavailable",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        ticket_id = f"push_{hashlib.sha256(f'{event_id}:{push_token[:10]}'.encode()).hexdigest()[:16]}"
        logger.info(f"[Push Dispatch] Sent push to token {push_token[:12]}...: '{title}' (Ticket: {ticket_id})")

        return {
            "status": "DELIVERED",
            "provider": "webpush_fcm_adapter",
            "ticket_id": ticket_id,
            "priority": priority,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    # -----------------------------------------------------------------
    # CORE DISPATCH ENGINE (FAULT TOLERANT)
    # -----------------------------------------------------------------
    def dispatch_event(
        self,
        db: Session,
        dispatch_req: NotificationEventDispatch
    ) -> NotificationEvent:
        """
        Main entry point to dispatch an event across configured channels.
        Handles template matching, deduplication, quiet hours, delivery, and retry registration.
        """
        self.seed_default_templates(db)

        # 1. Fetch template
        template = db.query(NotificationTemplate).filter(
            NotificationTemplate.event_type == dispatch_req.event_type,
            NotificationTemplate.is_active == True
        ).first()

        priority = dispatch_req.priority_override or (template.default_priority if template else "NORMAL")

        # Fallback if no template in DB
        title_tmpl = template.title_template if template else "FoodLoop Notification: {event_type}"
        in_app_tmpl = template.in_app_template if template else "{event_type} event triggered."
        email_sub_tmpl = template.email_subject_template if template else "[FoodLoop] {event_type}"
        email_body_tmpl = template.email_body_template if template else "An event has occurred: {event_type}"
        push_title_tmpl = template.push_title_template if template else "FoodLoop Update"
        push_body_tmpl = template.push_body_template if template else "{event_type}"

        # 2. Render content
        rendered_title = self.render_template_string(title_tmpl, dispatch_req.payload)
        rendered_in_app = self.render_template_string(in_app_tmpl, dispatch_req.payload)
        rendered_email_sub = self.render_template_string(email_sub_tmpl, dispatch_req.payload)
        rendered_email_body = self.render_template_string(email_body_tmpl, dispatch_req.payload)
        rendered_push_title = self.render_template_string(push_title_tmpl, dispatch_req.payload)
        rendered_push_body = self.render_template_string(push_body_tmpl, dispatch_req.payload)

        # 3. Deduplication Check
        idempotency_key = dispatch_req.idempotency_key or self.compute_idempotency_key(
            dispatch_req.event_type,
            dispatch_req.user_id,
            dispatch_req.organization_id,
            dispatch_req.payload
        )

        if not dispatch_req.force_dispatch:
            duplicate = self.check_duplicate(db, idempotency_key, self.dedup_window_minutes)
            if duplicate:
                logger.info(f"Deduplicating event '{dispatch_req.event_type}' (key: {idempotency_key}). Duplicate of {duplicate.id}.")
                event = NotificationEvent(
                    id=str(uuid.uuid4()),
                    event_type=dispatch_req.event_type,
                    organization_id=dispatch_req.organization_id,
                    user_id=dispatch_req.user_id,
                    idempotency_key=idempotency_key,
                    payload=dispatch_req.payload,
                    channels=dispatch_req.channels or ["in_app"],
                    status="DEDUPLICATED",
                    attempts=1,
                    max_retries=self.max_retries,
                    rendered_title=rendered_title,
                    rendered_body=rendered_in_app,
                    channel_delivery_results={"deduplication": {"suppressed": True, "duplicate_of_id": duplicate.id}},
                    created_at=datetime.now(timezone.utc),
                    sent_at=None
                )
                db.add(event)
                db.commit()
                db.refresh(event)
                return event

        # 4. Resolve Target Users & Preferences
        target_user_ids = []
        if dispatch_req.user_id:
            target_user_ids.append(dispatch_req.user_id)
        elif dispatch_req.organization_id:
            members = db.query(OrganizationMember).filter(
                OrganizationMember.organization_id == dispatch_req.organization_id
            ).all()
            target_user_ids = [m.user_id for m in members]

        primary_pref = None
        if dispatch_req.user_id:
            primary_pref = self.get_or_create_preference(db, dispatch_req.user_id)

        # 5. Determine Enabled Channels
        requested_channels = dispatch_req.channels
        if not requested_channels:
            # Derive from user preferences
            channels_to_use = []
            if primary_pref:
                # Check per-event overrides
                ev_override = primary_pref.event_overrides.get(dispatch_req.event_type, {})
                in_app_on = ev_override.get("in_app", primary_pref.in_app_enabled)
                email_on = ev_override.get("email", primary_pref.email_enabled)
                push_on = ev_override.get("push", primary_pref.push_enabled)

                if in_app_on:
                    channels_to_use.append("in_app")
                if email_on:
                    channels_to_use.append("email")
                if push_on:
                    channels_to_use.append("push")
            else:
                channels_to_use = ["in_app", "email", "push"]
        else:
            channels_to_use = [c.lower() for c in requested_channels]

        # 6. Quiet Hours Check (CRITICAL events bypass quiet hours!)
        is_quiet = False
        if primary_pref and priority != "CRITICAL":
            is_quiet = self.is_in_quiet_hours(primary_pref)

        # Create the Event Record
        event_id = str(uuid.uuid4())
        event = NotificationEvent(
            id=event_id,
            event_type=dispatch_req.event_type,
            organization_id=dispatch_req.organization_id,
            user_id=dispatch_req.user_id,
            idempotency_key=idempotency_key,
            payload=dispatch_req.payload,
            channels=channels_to_use,
            status="PENDING",
            attempts=1,
            max_retries=self.max_retries,
            rendered_title=rendered_title,
            rendered_body=rendered_in_app,
            channel_delivery_results={},
            created_at=datetime.now(timezone.utc)
        )
        db.add(event)
        db.flush()

        if is_quiet:
            logger.info(f"Event {event_id} suppressed by quiet hours for user {dispatch_req.user_id}.")
            event.status = "SUPPRESSED_QUIET_HOURS"
            event.channel_delivery_results = {
                "quiet_hours": {
                    "suppressed": True,
                    "reason": f"Active quiet hours ({primary_pref.quiet_hours_start} - {primary_pref.quiet_hours_end})",
                    "priority": priority
                }
            }
            db.commit()
            db.refresh(event)
            return event

        # 7. Execute Channel Deliveries
        delivery_results = {}
        has_failure = False
        has_success = False

        # Channel: IN-APP
        if "in_app" in channels_to_use and target_user_ids:
            try:
                res = self.deliver_in_app(
                    db=db,
                    user_ids=target_user_ids,
                    org_id=dispatch_req.organization_id,
                    title=rendered_title,
                    message=rendered_in_app,
                    priority=priority,
                    event_id=event_id,
                    action_url=dispatch_req.payload.get("action_url")
                )
                delivery_results["in_app"] = res
                has_success = True
            except Exception as e:
                logger.exception(f"In-app delivery failed for event {event_id}: {e}")
                delivery_results["in_app"] = {"status": "FAILED", "error": str(e)}
                has_failure = True

        # Channel: EMAIL
        if "email" in channels_to_use:
            email_addr = (
                primary_pref.email_address
                if primary_pref and primary_pref.email_address
                else dispatch_req.payload.get("recipient_email")
            )
            if not email_addr and dispatch_req.user_id:
                u = db.query(User).filter(User.id == dispatch_req.user_id).first()
                if u:
                    email_addr = u.email

            simulate_fail = dispatch_req.payload.get("_simulate_email_failure", False)
            res = self.deliver_email(
                recipient_email=email_addr,
                subject=rendered_email_sub,
                body=rendered_email_body,
                event_id=event_id,
                simulate_failure=simulate_fail
            )
            delivery_results["email"] = res
            if res.get("status") == "DELIVERED":
                has_success = True
            elif res.get("status") == "FAILED":
                has_failure = True

        # Channel: PUSH
        if "push" in channels_to_use:
            token = primary_pref.push_token if primary_pref else dispatch_req.payload.get("push_token")
            simulate_push_fail = dispatch_req.payload.get("_simulate_push_failure", False)
            res = self.deliver_push(
                push_token=token,
                title=rendered_push_title,
                body=rendered_push_body,
                event_id=event_id,
                priority=priority,
                simulate_failure=simulate_push_fail
            )
            delivery_results["push"] = res
            if res.get("status") == "DELIVERED":
                has_success = True
            elif res.get("status") == "FAILED":
                has_failure = True

        # 8. Determine Event Status & Next Retry
        event.channel_delivery_results = delivery_results

        if not has_failure:
            event.status = "DELIVERED"
            event.sent_at = datetime.now(timezone.utc)
            event.last_error = None
        else:
            # Handle retry scheduling
            if event.attempts < event.max_retries:
                event.status = "RETRYING"
                # Exponential backoff: 2^attempts * 10 seconds
                delay_sec = (2 ** event.attempts) * 10
                event.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay_sec)
                event.last_error = f"One or more channels failed on attempt {event.attempts}. Next retry in {delay_sec}s."
            else:
                event.status = "FAILED"
                event.last_error = f"Max retries ({event.max_retries}) reached without full channel success."

        db.commit()
        db.refresh(event)
        return event

    def dispatch_event_safe(
        self,
        db: Session,
        dispatch_req: NotificationEventDispatch
    ) -> Tuple[bool, Optional[NotificationEvent], Optional[str]]:
        """
        Safe non-crashing wrapper for business workflows.
        Guarantees that notification failures NEVER crash business operations.
        Returns: (success_bool, event_or_none, error_message_or_none)
        """
        try:
            event = self.dispatch_event(db, dispatch_req)
            return True, event, None
        except Exception as e:
            logger.error(f"[Fault-Tolerant Notification] Safe dispatch caught error: {e}", exc_info=True)
            return False, None, str(e)

    # -----------------------------------------------------------------
    # RETRY LOGIC FOR FAILED DELIVERIES
    # -----------------------------------------------------------------
    def retry_event(self, db: Session, event_id: str) -> NotificationEventRetryResponse:
        """Retries delivery for a specific failed or retrying event."""
        event = db.query(NotificationEvent).filter(NotificationEvent.id == event_id).first()
        if not event:
            raise ValueError(f"Notification event '{event_id}' not found.")

        event.attempts += 1
        curr_results = dict(event.channel_delivery_results or {})
        has_failure = False

        # Re-attempt failed email
        # Re-attempt failed email (on retry, transient failure is resolved unless explicitly configured)
        if "email" in event.channels and curr_results.get("email", {}).get("status") == "FAILED":
            user = db.query(User).filter(User.id == event.user_id).first() if event.user_id else None
            email_addr = (user.email if user else None) or event.payload.get("recipient_email")

            simulate_fail = event.payload.get("_simulate_email_failure_on_retry", False)
            res = self.deliver_email(
                recipient_email=email_addr,
                subject=event.rendered_title or "FoodLoop Notification",
                body=event.rendered_body or "",
                event_id=event.id,
                simulate_failure=simulate_fail
            )
            curr_results["email"] = res
            if res.get("status") == "FAILED":
                has_failure = True

        # Re-attempt failed push
        if "push" in event.channels and curr_results.get("push", {}).get("status") == "FAILED":
            pref = db.query(NotificationPreference).filter(NotificationPreference.user_id == event.user_id).first() if event.user_id else None
            token = pref.push_token if pref else event.payload.get("push_token")
            simulate_push_fail = event.payload.get("_simulate_push_failure_on_retry", False)
            res = self.deliver_push(
                push_token=token,
                title=event.rendered_title or "FoodLoop Update",
                body=event.rendered_body or "",
                event_id=event.id,
                priority="NORMAL",
                simulate_failure=simulate_push_fail
            )
            curr_results["push"] = res
            if res.get("status") == "FAILED":
                has_failure = True

        event.channel_delivery_results = curr_results

        if not has_failure:
            event.status = "DELIVERED"
            event.sent_at = datetime.now(timezone.utc)
            event.last_error = None
            event.next_retry_at = None
        else:
            if event.attempts < event.max_retries:
                event.status = "RETRYING"
                delay_sec = (2 ** event.attempts) * 15
                event.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay_sec)
                event.last_error = f"Retry attempt {event.attempts} failed. Next retry in {delay_sec}s."
            else:
                event.status = "FAILED"
                event.last_error = f"Max retries ({event.max_retries}) exceeded."
                event.next_retry_at = None

        db.commit()
        db.refresh(event)

        return NotificationEventRetryResponse(
            event_id=event.id,
            status=event.status,
            attempts=event.attempts,
            channel_delivery_results=event.channel_delivery_results,
            last_error=event.last_error
        )

    def retry_batch_failed(self, db: Session, limit: int = 50) -> BatchRetryResponse:
        """Finds eligible failed/retrying events and executes retry dispatch."""
        eligible_events = db.query(NotificationEvent).filter(
            or_(
                NotificationEvent.status == "RETRYING",
                and_(
                    NotificationEvent.status == "FAILED",
                    NotificationEvent.attempts < NotificationEvent.max_retries
                )
            )
        ).order_by(NotificationEvent.created_at.asc()).limit(limit).all()

        details = []
        succeeded = 0
        failed = 0

        for ev in eligible_events:
            try:
                res = self.retry_event(db, ev.id)
                details.append(res)
                if res.status == "DELIVERED":
                    succeeded += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"Error retrying event {ev.id}: {e}")
                failed += 1

        return BatchRetryResponse(
            total_eligible=len(eligible_events),
            retried_count=len(details),
            succeeded_count=succeeded,
            failed_count=failed,
            details=details
        )

    # -----------------------------------------------------------------
    # METRICS & STATS
    # -----------------------------------------------------------------
    def get_delivery_stats(self, db: Session, organization_id: Optional[str] = None) -> NotificationDeliveryStatsOut:
        """Calculates system-wide or organization-scoped delivery telemetry."""
        query = db.query(NotificationEvent)
        if organization_id:
            query = query.filter(NotificationEvent.organization_id == organization_id)

        all_events = query.all()
        total = len(all_events)
        delivered = sum(1 for e in all_events if e.status == "DELIVERED")
        failed = sum(1 for e in all_events if e.status == "FAILED")
        retrying = sum(1 for e in all_events if e.status == "RETRYING")
        deduplicated = sum(1 for e in all_events if e.status == "DEDUPLICATED")
        suppressed_quiet = sum(1 for e in all_events if e.status == "SUPPRESSED_QUIET_HOURS")

        channel_counts = {"in_app": 0, "email": 0, "push": 0}
        total_attempts = 0
        for e in all_events:
            total_attempts += (e.attempts or 1)
            for ch in (e.channels or []):
                if ch in channel_counts:
                    channel_counts[ch] += 1

        success_rate = (delivered / total * 100.0) if total > 0 else 100.0
        avg_attempts = (total_attempts / total) if total > 0 else 1.0

        return NotificationDeliveryStatsOut(
            total_events=total,
            delivered_events=delivered,
            failed_events=failed,
            retrying_events=retrying,
            deduplicated_events=deduplicated,
            suppressed_quiet_hours=suppressed_quiet,
            channel_counts=channel_counts,
            success_rate_pct=round(success_rate, 2),
            average_attempts=round(avg_attempts, 2)
        )


notification_service = NotificationService()
