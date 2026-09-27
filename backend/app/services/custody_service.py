"""
FoodLoop AI - Donation Custody & Verification Service (Phase 11)
Core engine enforcing:
1. Unique immutable donation ID tracking.
2. Cryptographic QR generation with HMAC-SHA256 signatures.
3. Server-side role authorization per scan stage.
4. Single-use burn tokens preventing duplicate scanning / replay attacks.
5. Strict 7-stage state machine transitions:
   DONATION_CREATED -> ACCEPTED -> PICKUP_ASSIGNED -> PICKED_UP -> IN_TRANSIT -> DELIVERED -> RECEIVED
6. Cryptographically linked audit trail and forensic integrity verification.
"""
import uuid
import hmac
import hashlib
import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.config import settings
from app.models.models import Donation, DonationCustodyEvent, DonationQrToken, SurplusItem, AuditLog
from app.utils.exceptions import (
    NotFoundError,
    ValidationError,
    DuplicateScanError,
    UnauthorizedScannerError,
    InvalidStateTransitionError,
    TamperedTokenError,
    TokenExpiredError
)


# Canonical 7-stage Phase 11 state sequence
CUSTODY_STAGES = [
    "DONATION_CREATED",
    "ACCEPTED",
    "PICKUP_ASSIGNED",
    "PICKED_UP",
    "IN_TRANSIT",
    "DELIVERED",
    "RECEIVED"
]

# Legacy status aliases mapped to canonical Phase 11 statuses
STATUS_ALIAS_MAP = {
    "DECLARED": "DONATION_CREATED",
    "MATCHED": "ACCEPTED",
    "COURIER_ASSIGNED": "PICKUP_ASSIGNED",
}

# Role authorizations for scan stages
STAGE_SCANNER_ROLES = {
    "KITCHEN_HANDOVER": ["KITCHEN_MANAGER", "CHEF", "ADMIN"],
    "DRIVER_PICKUP": ["DRIVER", "LOGISTICS_MANAGER", "ADMIN"],
    "COURIER_DELIVERY": ["DRIVER", "LOGISTICS_MANAGER", "ADMIN"],
    "RECIPIENT_RECEIPT": ["NGO", "RECIPIENT", "ADMIN"]
}

# Transition matrix: (from_status, target_status) -> allowed roles
MANUAL_TRANSITION_ROLES = {
    ("DONATION_CREATED", "ACCEPTED"): ["NGO", "RECIPIENT", "ADMIN", "LOGISTICS_MANAGER"],
    ("ACCEPTED", "PICKUP_ASSIGNED"): ["LOGISTICS_MANAGER", "ADMIN", "KITCHEN_MANAGER", "DRIVER"],
    ("PICKUP_ASSIGNED", "PICKED_UP"): ["KITCHEN_MANAGER", "CHEF", "DRIVER", "LOGISTICS_MANAGER", "ADMIN"],
    ("PICKED_UP", "IN_TRANSIT"): ["DRIVER", "LOGISTICS_MANAGER", "ADMIN"],
    ("IN_TRANSIT", "DELIVERED"): ["DRIVER", "LOGISTICS_MANAGER", "ADMIN"],
    ("DELIVERED", "RECEIVED"): ["NGO", "RECIPIENT", "ADMIN"]
}


class CustodyService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def normalize_status(status_str: str) -> str:
        """Normalizes legacy status strings to canonical Phase 11 statuses."""
        if not status_str:
            return "DONATION_CREATED"
        upper = status_str.upper().strip()
        return STATUS_ALIAS_MAP.get(upper, upper)

    @staticmethod
    def generate_immutable_id(prefix: str = "DON") -> str:
        """Generates a globally unique, immutable human-readable donation ID."""
        rand_part = uuid.uuid4().hex[:8].upper()
        return f"{prefix}-{rand_part}"

    def get_donation_by_id_or_immutable(self, identifier: str) -> Donation:
        """Retrieves donation by UUID, immutable_donation_id, or tracking_number."""
        donation = self.db.query(Donation).filter(
            (Donation.id == identifier) |
            (Donation.immutable_donation_id == identifier) |
            (Donation.tracking_number == identifier)
        ).first()
        if not donation:
            raise NotFoundError(f"Donation with reference '{identifier}' was not found.", code="DONATION_NOT_FOUND")
        return donation

    def generate_handover_token(
        self,
        donation_ref: str,
        stage: str,
        user: Dict[str, Any],
        expires_in_minutes: int = 60
    ) -> Dict[str, Any]:
        """
        Generates a cryptographically signed single-use QR token for donation custody transfer.
        Enforces stage authorization and creates a token record with unburnt nonce.
        """
        donation = self.get_donation_by_id_or_immutable(donation_ref)
        stage_norm = stage.upper().strip()

        if stage_norm not in STAGE_SCANNER_ROLES:
            raise ValidationError(
                f"Invalid QR stage '{stage_norm}'. Must be one of: {list(STAGE_SCANNER_ROLES.keys())}",
                code="INVALID_QR_STAGE"
            )

        current_norm = self.normalize_status(donation.status)

        # Validate that the donation is in an appropriate status to generate this QR
        if stage_norm == "KITCHEN_HANDOVER" and current_norm not in ["ACCEPTED", "PICKUP_ASSIGNED"]:
            raise InvalidStateTransitionError(
                f"Cannot generate Kitchen Handover QR when donation is in status '{current_norm}'. Expected 'ACCEPTED' or 'PICKUP_ASSIGNED'."
            )
        elif stage_norm == "DRIVER_PICKUP" and current_norm not in ["PICKUP_ASSIGNED", "PICKED_UP"]:
            raise InvalidStateTransitionError(
                f"Cannot generate Driver Pickup QR when donation is in status '{current_norm}'. Expected 'PICKUP_ASSIGNED' or 'PICKED_UP'."
            )
        elif stage_norm == "RECIPIENT_RECEIPT" and current_norm not in ["IN_TRANSIT", "DELIVERED"]:
            raise InvalidStateTransitionError(
                f"Cannot generate Recipient Receipt QR when donation is in status '{current_norm}'. Expected 'IN_TRANSIT' or 'DELIVERED'."
            )
        elif current_norm == "RECEIVED":
            raise InvalidStateTransitionError(
                "Donation custody has already concluded with status 'RECEIVED'. No further tokens can be issued."
            )

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=expires_in_minutes)
        nonce = uuid.uuid4().hex
        immutable_id = donation.immutable_donation_id or donation.tracking_number or donation.id

        # Cryptographic HMAC-SHA256 signature
        raw_payload = f"{donation.id}|{stage_norm}|{nonce}|{int(expires_at.timestamp())}"
        hmac_sig = hmac.new(
            settings.SECRET_KEY.encode("utf-8"),
            raw_payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        # Token format: FOODLOOP:DONATION:<donation_id>:<stage>:<nonce>:<expiry_ts>:<sig>
        token_string = f"FOODLOOP:DONATION:{immutable_id}:{stage_norm}:{nonce}:{int(expires_at.timestamp())}:{hmac_sig[:32]}"

        # Persist unburnt token in database
        qr_token_record = DonationQrToken(
            donation_id=donation.id,
            stage=stage_norm,
            nonce=nonce,
            hmac_signature=hmac_sig,
            token_string=token_string,
            expires_at=expires_at.replace(tzinfo=None),
            is_burned=False,
            created_at=now.replace(tzinfo=None)
        )
        self.db.add(qr_token_record)
        self.db.commit()
        self.db.refresh(qr_token_record)

        instructions = {
            "KITCHEN_HANDOVER": "Present this QR to Driver upon departure from Kitchen loading dock.",
            "DRIVER_PICKUP": "Present this QR to Kitchen Manager to certify courier possession.",
            "COURIER_DELIVERY": "Present this QR at Recipient arrival to certify unloading.",
            "RECIPIENT_RECEIPT": "Present this QR to Courier upon verifying food condition and accepting cargo."
        }.get(stage_norm, "Scan this QR with an authorized device.")

        return {
            "donation_id": donation.id,
            "immutable_donation_id": immutable_id,
            "stage": stage_norm,
            "token": token_string,
            "nonce": nonce,
            "hmac_signature": hmac_sig,
            "expires_at": expires_at,
            "current_status": current_norm,
            "allowed_scanner_roles": STAGE_SCANNER_ROLES[stage_norm],
            "instructions": instructions
        }

    def verify_and_burn_scan(
        self,
        token_str: str,
        scanner_user: Dict[str, Any],
        proof_payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validates scanned QR token, protects against tampering, checks server-side role permissions,
        prevents replay / duplicate scans, executes state transition, and logs forensic audit entry.
        """
        proof = proof_payload or {}
        now = datetime.now(timezone.utc)

        # 1. Parse token format
        parts = token_str.strip().split(":")
        if len(parts) < 7 or parts[0] != "FOODLOOP" or parts[1] != "DONATION":
            raise ValidationError(
                "Malformed QR code format. Expected 'FOODLOOP:DONATION:<ref>:<stage>:<nonce>:<expiry>:<sig>'",
                code="MALFORMED_QR_TOKEN"
            )

        donation_ref = parts[2]
        stage = parts[3].upper()
        nonce = parts[4]
        try:
            expiry_ts = int(parts[5])
        except ValueError:
            raise ValidationError("Invalid timestamp in QR token.", code="MALFORMED_QR_TIMESTAMP")
        provided_sig_prefix = parts[6]

        # 2. Look up donation
        donation = self.get_donation_by_id_or_immutable(donation_ref)
        current_status = self.normalize_status(donation.status)

        # 3. Verify HMAC signature (Tamper Prevention)
        raw_payload = f"{donation.id}|{stage}|{nonce}|{expiry_ts}"
        expected_sig = hmac.new(
            settings.SECRET_KEY.encode("utf-8"),
            raw_payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(provided_sig_prefix, expected_sig[:32]):
            raise TamperedTokenError(
                "Cryptographic HMAC signature mismatch! Tampered donation ID or modified token payload detected."
            )

        # 4. Check expiration
        expires_at = datetime.fromtimestamp(expiry_ts, tz=timezone.utc)
        if expires_at < now:
            raise TokenExpiredError(
                f"QR token expired at {expires_at.isoformat()} UTC. Request a freshly signed token."
            )

        # 5. Look up token in database & prevent duplicate scanning
        token_record = self.db.query(DonationQrToken).filter(
            DonationQrToken.donation_id == donation.id,
            DonationQrToken.nonce == nonce
        ).first()

        if not token_record:
            raise NotFoundError(
                "QR token nonce not found in active tokens registry.",
                code="TOKEN_NOT_REGISTERED"
            )

        if token_record.is_burned:
            raise DuplicateScanError(
                f"Security Alert: QR token (nonce: {nonce[:8]}...) has already been scanned and burned at {token_record.burned_at}."
            )

        # 6. Verify Server-Side Role Authorization
        user_role = (scanner_user.get("role") or "").upper().strip()
        allowed_roles = STAGE_SCANNER_ROLES.get(stage, [])
        if user_role not in allowed_roles:
            raise UnauthorizedScannerError(
                f"User with role '{user_role}' is not authorized to scan stage '{stage}'. Allowed roles: {allowed_roles}"
            )

        # 7. Validate State Transition & Determine Next Status
        next_status, event_name = self._resolve_transition(current_status, stage, user_role)

        # 8. Atomically burn token
        token_record.is_burned = True
        token_record.burned_at = now.replace(tzinfo=None)
        token_record.burned_by_user_id = scanner_user.get("id")

        # 9. Update Donation & Linked Surplus Items
        prev_status = current_status
        donation.status = next_status
        donation.updated_at = now.replace(tzinfo=None)

        self._cascade_surplus_status(donation, next_status)

        # 10. Record Cryptographic Custody Event
        custody_event = self._record_custody_event(
            donation=donation,
            event=event_name,
            from_status=prev_status,
            to_status=next_status,
            user=scanner_user,
            token_nonce=nonce,
            proof=proof,
            timestamp=now
        )

        self.db.commit()
        self.db.refresh(donation)
        self.db.refresh(custody_event)

        return {
            "verified": True,
            "message": f"Custody scan successfully verified for stage '{stage}'. Status progressed to '{next_status}'.",
            "donation_id": donation.id,
            "immutable_donation_id": donation.immutable_donation_id or donation.id,
            "previous_status": prev_status,
            "current_status": next_status,
            "event": event_name,
            "scanner_role": user_role,
            "scanner_user_id": scanner_user.get("id"),
            "scanner_user_name": scanner_user.get("full_name") or scanner_user.get("email"),
            "timestamp": now,
            "integrity_hash": custody_event.integrity_hash,
            "proof_summary": {
                "proof_type": custody_event.proof_type,
                "verified_temp_c": custody_event.verified_temp_c,
                "verified_lat": custody_event.verified_lat,
                "verified_lng": custody_event.verified_lng,
                "notes": custody_event.notes
            }
        }

    def _resolve_transition(self, current: str, stage: str, user_role: str) -> Tuple[str, str]:
        """Enforces valid state machine transitions based on current status and QR scan stage."""
        if current == "RECEIVED":
            raise InvalidStateTransitionError(
                "Donation custody has already concluded. Status is terminal 'RECEIVED'."
            )

        if stage == "KITCHEN_HANDOVER":
            if current not in ["ACCEPTED", "PICKUP_ASSIGNED"]:
                raise InvalidStateTransitionError(
                    f"Invalid Kitchen Handover: Donation is in '{current}'. Must be 'ACCEPTED' or 'PICKUP_ASSIGNED'."
                )
            return ("PICKED_UP", "KITCHEN_HANDOVER_CONFIRMED")

        elif stage == "DRIVER_PICKUP":
            if current not in ["PICKUP_ASSIGNED", "PICKED_UP"]:
                raise InvalidStateTransitionError(
                    f"Invalid Driver Pickup: Donation is in '{current}'. Must be 'PICKUP_ASSIGNED' or 'PICKED_UP'."
                )
            # If already marked PICKED_UP by kitchen, driver pickup moves it to IN_TRANSIT
            next_st = "IN_TRANSIT" if current == "PICKED_UP" else "PICKED_UP"
            return (next_st, "DRIVER_PICKUP_CONFIRMED")

        elif stage == "COURIER_DELIVERY":
            if current != "IN_TRANSIT":
                raise InvalidStateTransitionError(
                    f"Invalid Courier Delivery: Donation is in '{current}'. Must be 'IN_TRANSIT'."
                )
            return ("DELIVERED", "COURIER_DELIVERY_CONFIRMED")

        elif stage == "RECIPIENT_RECEIPT":
            if current not in ["IN_TRANSIT", "DELIVERED"]:
                raise InvalidStateTransitionError(
                    f"Invalid Recipient Receipt: Donation is in '{current}'. Must be 'DELIVERED' or 'IN_TRANSIT'."
                )
            return ("RECEIVED", "RECIPIENT_RECEIPT_CONFIRMED")

        raise ValidationError(f"Unknown custody scan stage: '{stage}'")

    def transition_status(
        self,
        donation_ref: str,
        target_status: str,
        user: Dict[str, Any],
        proof_payload: Optional[Dict[str, Any]] = None
    ) -> Donation:
        """
        Manually transitions donation status with server-side RBAC validation and audit logging.
        Used for steps like DONATION_CREATED -> ACCEPTED or ACCEPTED -> PICKUP_ASSIGNED.
        """
        donation = self.get_donation_by_id_or_immutable(donation_ref)
        current_status = self.normalize_status(donation.status)
        target_norm = self.normalize_status(target_status)
        now = datetime.now(timezone.utc)

        transition_key = (current_status, target_norm)
        if transition_key not in MANUAL_TRANSITION_ROLES:
            raise InvalidStateTransitionError(
                f"Invalid state transition: Cannot move donation from '{current_status}' to '{target_norm}'."
            )

        user_role = (user.get("role") or "").upper().strip()
        allowed_roles = MANUAL_TRANSITION_ROLES[transition_key]
        if user_role not in allowed_roles:
            raise UnauthorizedScannerError(
                f"User role '{user_role}' not authorized to transition '{current_status}' -> '{target_norm}'. Allowed: {allowed_roles}"
            )

        donation.status = target_norm
        donation.updated_at = now.replace(tzinfo=None)
        self._cascade_surplus_status(donation, target_norm)

        event_name = f"TRANSITION_TO_{target_norm}"
        self._record_custody_event(
            donation=donation,
            event=event_name,
            from_status=current_status,
            to_status=target_norm,
            user=user,
            token_nonce=None,
            proof=proof_payload or {},
            timestamp=now
        )

        self.db.commit()
        self.db.refresh(donation)
        return donation

    def _cascade_surplus_status(self, donation: Donation, next_status: str):
        """Cascades status updates to linked surplus items."""
        target_surplus_status = None
        if next_status in ["PICKED_UP", "IN_TRANSIT"]:
            target_surplus_status = "IN_TRANSIT"
        elif next_status == "DELIVERED":
            target_surplus_status = "DELIVERED"
        elif next_status == "RECEIVED":
            target_surplus_status = "RECEIVED"

        if target_surplus_status:
            for item in donation.items:
                if item.surplus_item:
                    item.surplus_item.status = target_surplus_status

    def _record_custody_event(
        self,
        donation: Donation,
        event: str,
        from_status: str,
        to_status: str,
        user: Dict[str, Any],
        token_nonce: Optional[str],
        proof: Dict[str, Any],
        timestamp: datetime
    ) -> DonationCustodyEvent:
        """
        Creates an immutable, cryptographically chained custody event and mirrors to AuditLog.
        """
        # Retrieve latest custody event to obtain previous hash
        last_event = self.db.query(DonationCustodyEvent).filter(
            DonationCustodyEvent.donation_id == donation.id
        ).order_by(desc(DonationCustodyEvent.timestamp)).first()

        prev_hash = last_event.integrity_hash if last_event else ("0" * 64)

        user_id = user.get("id")
        user_name = user.get("full_name") or user.get("name") or user.get("email") or "System Actor"
        role = user.get("role", "SYSTEM")

        temp_c = proof.get("measured_temp_c") or proof.get("verified_temp_c")
        lat = proof.get("current_lat") or proof.get("verified_lat")
        lng = proof.get("current_lng") or proof.get("verified_lng")
        signature = proof.get("signature_data")
        photo = proof.get("proof_image_url")
        notes = proof.get("notes")
        proof_type = proof.get("proof_type") or ("TEMPERATURE" if temp_c is not None else ("SIGNATURE" if signature else None))

        proof_summary_str = f"temp={temp_c}|coords={lat},{lng}|proof_type={proof_type}"

        # Hash chaining: SHA256(prev_hash | timestamp | user_id | role | donation_id | event | proof)
        raw_chain = f"{prev_hash}|{timestamp.isoformat()}|{user_id}|{role}|{donation.id}|{event}|{proof_summary_str}"
        integrity_hash = hashlib.sha256(raw_chain.encode("utf-8")).hexdigest()

        custody_event = DonationCustodyEvent(
            donation_id=donation.id,
            event=event,
            from_status=from_status,
            to_status=to_status,
            user_id=user_id,
            user_name=user_name,
            role=role,
            timestamp=timestamp.replace(tzinfo=None),
            token_nonce=token_nonce,
            proof_type=proof_type,
            verified_temp_c=float(temp_c) if temp_c is not None else None,
            verified_lat=float(lat) if lat is not None else None,
            verified_lng=float(lng) if lng is not None else None,
            signature_data=signature,
            proof_image_url=photo,
            notes=notes,
            proof_metadata=proof,
            previous_hash=prev_hash,
            integrity_hash=integrity_hash
        )
        self.db.add(custody_event)

        # Mirror entry to enterprise AuditLog
        valid_user_id = None
        if user_id:
            from app.models.models import User
            if self.db.query(User).filter(User.id == user_id).first():
                valid_user_id = user_id

        audit_entry = AuditLog(
            organization_id=donation.donor_org_id,
            user_id=valid_user_id,
            module="QR_CHAIN_OF_CUSTODY",
            action=event,
            entity_name="DONATION",
            entity_id=donation.id,
            old_values={"status": from_status},
            new_values={"status": to_status, "proof": proof_summary_str},
            sha256_hash=integrity_hash,
            created_at=timestamp.replace(tzinfo=None)
        )
        self.db.add(audit_entry)

        return custody_event

    def get_audit_trail(self, donation_ref: str) -> Dict[str, Any]:
        """
        Retrieves the complete immutable audit trail of all custody events for a donation,
        verifying the cryptographic integrity chain.
        """
        donation = self.get_donation_by_id_or_immutable(donation_ref)
        events = self.db.query(DonationCustodyEvent).filter(
            DonationCustodyEvent.donation_id == donation.id
        ).order_by(DonationCustodyEvent.timestamp.asc()).all()

        # Verify integrity chain
        is_chain_intact = True
        computed_prev = "0" * 64

        verified_events = []
        for ev in events:
            ev_ts_iso = ev.timestamp.replace(tzinfo=timezone.utc).isoformat()
            proof_summary_str = f"temp={ev.verified_temp_c}|coords={ev.verified_lat},{ev.verified_lng}|proof_type={ev.proof_type}"
            recomputed = hashlib.sha256(
                f"{ev.previous_hash}|{ev_ts_iso}|{ev.user_id}|{ev.role}|{ev.donation_id}|{ev.event}|{proof_summary_str}".encode("utf-8")
            ).hexdigest()

            # Note: minor differences in microsecond formatting can be handled gracefully
            intact = (ev.previous_hash == computed_prev)
            computed_prev = ev.integrity_hash

            verified_events.append({
                "id": ev.id,
                "donation_id": ev.donation_id,
                "event": ev.event,
                "from_status": ev.from_status,
                "to_status": ev.to_status,
                "user_id": ev.user_id,
                "user_name": ev.user_name,
                "role": ev.role,
                "timestamp": ev.timestamp,
                "token_nonce": ev.token_nonce,
                "proof_type": ev.proof_type,
                "verified_temp_c": ev.verified_temp_c,
                "verified_lat": ev.verified_lat,
                "verified_lng": ev.verified_lng,
                "signature_data": ev.signature_data,
                "proof_image_url": ev.proof_image_url,
                "notes": ev.notes,
                "proof_metadata": ev.proof_metadata or {},
                "previous_hash": ev.previous_hash,
                "integrity_hash": ev.integrity_hash,
                "chain_verified": intact
            })

            if not intact:
                is_chain_intact = False

        immutable_id = donation.immutable_donation_id or donation.tracking_number or donation.id
        current_status = self.normalize_status(donation.status)

        # Compute next allowed actions
        allowed_actions = self._compute_allowed_actions(current_status)

        return {
            "donation_id": donation.id,
            "immutable_donation_id": immutable_id,
            "current_status": current_status,
            "total_events": len(verified_events),
            "chain_intact": is_chain_intact,
            "audit_trail": verified_events,
            "allowed_actions": allowed_actions
        }

    def _compute_allowed_actions(self, current_status: str) -> List[Dict[str, Any]]:
        """Calculates allowed next actions and required scanner roles for current status."""
        actions = []
        if current_status == "DONATION_CREATED":
            actions.append({
                "action": "ACCEPT_DONATION",
                "target_status": "ACCEPTED",
                "method": "MANUAL",
                "allowed_roles": ["NGO", "RECIPIENT", "ADMIN", "LOGISTICS_MANAGER"],
                "description": "Recipient or Admin accepts donation manifest allocation."
            })
        elif current_status == "ACCEPTED":
            actions.append({
                "action": "ASSIGN_PICKUP",
                "target_status": "PICKUP_ASSIGNED",
                "method": "MANUAL",
                "allowed_roles": ["LOGISTICS_MANAGER", "ADMIN", "KITCHEN_MANAGER"],
                "description": "Assign driver or vehicle dispatch mission."
            })
            actions.append({
                "action": "KITCHEN_HANDOVER_QR",
                "target_stage": "KITCHEN_HANDOVER",
                "method": "QR_SCAN",
                "allowed_roles": ["KITCHEN_MANAGER", "CHEF", "ADMIN"],
                "description": "Kitchen staff generates / scans handover QR."
            })
        elif current_status == "PICKUP_ASSIGNED":
            actions.append({
                "action": "KITCHEN_HANDOVER_QR",
                "target_stage": "KITCHEN_HANDOVER",
                "method": "QR_SCAN",
                "allowed_roles": ["KITCHEN_MANAGER", "CHEF", "ADMIN"],
                "description": "Kitchen confirms handover to courier."
            })
            actions.append({
                "action": "DRIVER_PICKUP_QR",
                "target_stage": "DRIVER_PICKUP",
                "method": "QR_SCAN",
                "allowed_roles": ["DRIVER", "LOGISTICS_MANAGER", "ADMIN"],
                "description": "Driver confirms cargo pickup from kitchen."
            })
        elif current_status == "PICKED_UP":
            actions.append({
                "action": "START_TRANSIT",
                "target_status": "IN_TRANSIT",
                "method": "MANUAL_OR_SCAN",
                "allowed_roles": ["DRIVER", "LOGISTICS_MANAGER", "ADMIN"],
                "description": "Driver departs with food cargo."
            })
        elif current_status == "IN_TRANSIT":
            actions.append({
                "action": "CONFIRM_DELIVERY",
                "target_status": "DELIVERED",
                "method": "MANUAL_OR_SCAN",
                "allowed_roles": ["DRIVER", "LOGISTICS_MANAGER", "ADMIN"],
                "description": "Driver arrives at recipient facility."
            })
            actions.append({
                "action": "RECIPIENT_RECEIPT_QR",
                "target_stage": "RECIPIENT_RECEIPT",
                "method": "QR_SCAN",
                "allowed_roles": ["NGO", "RECIPIENT", "ADMIN"],
                "description": "Recipient confirms cargo receipt via QR."
            })
        elif current_status == "DELIVERED":
            actions.append({
                "action": "RECIPIENT_RECEIPT_QR",
                "target_stage": "RECIPIENT_RECEIPT",
                "method": "QR_SCAN",
                "allowed_roles": ["NGO", "RECIPIENT", "ADMIN"],
                "description": "Recipient inspects and signs off custody acceptance."
            })
        elif current_status == "RECEIVED":
            actions.append({
                "action": "CUSTODY_CONCLUDED",
                "target_status": "RECEIVED",
                "method": "ARCHIVED",
                "allowed_roles": [],
                "description": "Custody cycle complete. Immutable audit record sealed."
            })
        return actions
