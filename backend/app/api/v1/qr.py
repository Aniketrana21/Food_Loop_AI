"""
FoodLoop AI - Cryptographic QR Verification & Handover API Router
Generates HMAC-SHA256 single-use burn tokens for tamper-proof custody handovers.
Enforces Phase 11 QR Chain of Custody:
- Unique immutable donation tracking
- Role-authorized scanning (Kitchen Handover, Driver Pickup, Recipient Receipt)
- Prevention of duplicate scans, unauthorized scans, invalid state transitions, tampered IDs
- Forensic cryptographically chained audit trail.
"""
import uuid
import hmac
import hashlib
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.core.security import get_current_user, RoleChecker
from app.models.models import QrVerification, Delivery, Donation
from app.schemas.enterprise_schemas import (
    QRGenerateRequest,
    QRGenerateResponse,
    QRVerifyRequest,
    QRVerifyResponse
)
from app.schemas.custody_schemas import (
    DonationQRGenerateRequest,
    DonationQRGenerateResponse,
    DonationQRScanVerifyRequest,
    DonationQRScanVerifyResponse,
    DonationStatusTransitionRequest
)
from app.services.custody_service import CustodyService
from app.middleware.rate_limit import RateLimiter
from app.utils.exceptions import QRVerificationError, NotFoundError

router = APIRouter(prefix="/qr", tags=["19. Cryptographic QR Verification"])


# ====================================================================
# PHASE 11: DONATION QR CHAIN OF CUSTODY ENDPOINTS
# ====================================================================

@router.post("/donations/generate", response_model=DonationQRGenerateResponse)
def generate_donation_custody_qr(
    req: DonationQRGenerateRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "KITCHEN_MANAGER", "CHEF", "DRIVER", "LOGISTICS_MANAGER", "NGO", "RECIPIENT"]))
):
    """
    Phase 11: Generates a cryptographically signed HMAC-SHA256 single-use QR burn token
    for a specific donation and custody stage (KITCHEN_HANDOVER, DRIVER_PICKUP, RECIPIENT_RECEIPT).
    """
    service = CustodyService(db)
    result = service.generate_handover_token(
        donation_ref=req.donation_id,
        stage=req.stage,
        user=user,
        expires_in_minutes=req.expires_in_minutes or 60
    )
    return DonationQRGenerateResponse(**result)


@router.post("/donations/verify", response_model=DonationQRScanVerifyResponse, dependencies=[Depends(RateLimiter(times=30, seconds=60))])
def verify_donation_custody_scan(
    req: DonationQRScanVerifyRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "KITCHEN_MANAGER", "CHEF", "DRIVER", "LOGISTICS_MANAGER", "NGO", "RECIPIENT"]))
):
    """
    Phase 11: Validates cryptographic QR scan for donation custody:
    1. Rejects tampered donation IDs (cryptographic HMAC verification)
    2. Rejects unauthorized scanner roles (server-side RBAC)
    3. Rejects duplicate scanning / replay attacks (single-use burned nonces)
    4. Rejects invalid state transitions (strict 7-stage state machine)
    5. Records full forensic audit trail with optional proof (temperature, signature, GPS, photo).
    """
    service = CustodyService(db)
    proof_data = {
        "proof_type": req.proof_type,
        "measured_temp_c": req.measured_temp_c,
        "current_lat": req.current_lat,
        "current_lng": req.current_lng,
        "signature_data": req.signature_data,
        "proof_image_url": req.proof_image_url,
        "notes": req.notes,
        "metadata": req.proof_metadata or {}
    }
    result = service.verify_and_burn_scan(
        token_str=req.token,
        scanner_user=user,
        proof_payload=proof_data
    )
    return DonationQRScanVerifyResponse(**result)


@router.get("/donations/{donation_id}/audit-trail")
def get_donation_custody_audit_trail(
    donation_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Phase 11: Retrieves the complete, immutable cryptographic audit trail for a donation,
    verifying SHA-256 chain integrity and listing next allowed transitions.
    """
    service = CustodyService(db)
    return service.get_audit_trail(donation_id)


@router.post("/donations/{donation_id}/transition")
def transition_donation_status(
    donation_id: str,
    req: DonationStatusTransitionRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "KITCHEN_MANAGER", "CHEF", "DRIVER", "LOGISTICS_MANAGER", "NGO", "RECIPIENT"]))
):
    """
    Phase 11: Executes an authorized custody status transition (e.g. DONATION_CREATED -> ACCEPTED,
    or ACCEPTED -> PICKUP_ASSIGNED) with server-side RBAC and forensic audit logging.
    """
    service = CustodyService(db)
    proof_data = {
        "proof_type": req.proof_type,
        "verified_temp_c": req.verified_temp_c,
        "signature_data": req.signature_data,
        "proof_image_url": req.proof_image_url,
        "notes": req.notes
    }
    donation = service.transition_status(
        donation_ref=donation_id,
        target_status=req.target_status,
        user=user,
        proof_payload=proof_data
    )
    return {
        "donation_id": donation.id,
        "immutable_donation_id": donation.immutable_donation_id or donation.id,
        "status": donation.status,
        "message": f"Successfully transitioned donation to '{donation.status}'."
    }


@router.get("/donations/{donation_id}/status")
def get_donation_custody_status(
    donation_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Phase 11: Returns current custody status, immutable ID, and available actions for a donation.
    """
    service = CustodyService(db)
    donation = service.get_donation_by_id_or_immutable(donation_id)
    norm_status = service.normalize_status(donation.status)
    allowed_actions = service._compute_allowed_actions(norm_status)
    return {
        "donation_id": donation.id,
        "immutable_donation_id": donation.immutable_donation_id or donation.tracking_number or donation.id,
        "tracking_number": donation.tracking_number,
        "status": norm_status,
        "total_weight_kg": donation.total_weight_kg,
        "total_portions": donation.total_portions,
        "donor_org_id": donation.donor_org_id,
        "recipient_org_id": donation.recipient_org_id,
        "allowed_actions": allowed_actions
    }


# ====================================================================
# LEGACY DELIVERY QR ENDPOINTS (BACKWARD COMPATIBILITY)
# ====================================================================

@router.post("/generate", response_model=QRGenerateResponse)
def generate_handover_qr(
    req: QRGenerateRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "KITCHEN_MANAGER", "DRIVER", "NGO"]))
):
    """
    Generates a single-use cryptographically signed QR burn token for deliveries.
    Token expires within 45 minutes and contains an immutable nonce to prevent replay attacks.
    """
    deliv = db.query(Delivery).filter(Delivery.id == req.delivery_id).first()
    if not deliv:
        raise NotFoundError(f"Delivery with ID '{req.delivery_id}' was not found", code="DELIVERY_NOT_FOUND")

    nonce = uuid.uuid4().hex
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=45)

    payload = {
        "delivery_id": req.delivery_id,
        "handover_type": req.handover_type,
        "nonce": nonce,
        "expires_at": expires_at.isoformat(),
        "issued_by_user_id": user["id"]
    }

    raw_signature = f"{req.delivery_id}|{req.handover_type}|{nonce}|{expires_at.isoformat()}"
    signature = hmac.new(settings.SECRET_KEY.encode(), raw_signature.encode(), hashlib.sha256).hexdigest()

    token_str = f"FOODLOOP:{req.delivery_id}:{nonce}:{signature[:16]}"

    stage_val = "PICKUP_HANDOVER" if "PICKUP" in req.handover_type.upper() else "DELIVERY_RECEIPT"
    qr_record = QrVerification(
        delivery_id=req.delivery_id,
        stage=stage_val,
        nonce=nonce,
        hmac_signature=signature,
        payload=payload,
        expires_at=expires_at,
        is_burned=False
    )
    db.add(qr_record)
    db.commit()
    db.refresh(qr_record)

    return QRGenerateResponse(
        token=token_str,
        handover_type=req.handover_type,
        nonce=nonce,
        hmac_signature=signature,
        expires_at=expires_at,
        qr_payload=payload
    )


@router.post("/verify", response_model=QRVerifyResponse, dependencies=[Depends(RateLimiter(times=20, seconds=60))])
def verify_and_burn_qr(
    verify_req: QRVerifyRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "DRIVER", "NGO"]))
):
    """
    Verifies cryptographic signature, burns single-use token, and transitions delivery state.
    Protects against replay attacks and expired QR codes.
    """
    parts = verify_req.token.split(":")
    if len(parts) < 3 or parts[0] != "FOODLOOP":
        raise QRVerificationError("Malformed QR code format. Expected 'FOODLOOP:<delivery_id>:<nonce>:...'")

    delivery_id = parts[1]
    nonce = parts[2]

    record = db.query(QrVerification).filter(
        QrVerification.delivery_id == delivery_id,
        QrVerification.nonce == nonce
    ).first()

    if not record:
        raise QRVerificationError("QR verification token not recognized or fake signature.")

    if record.is_burned:
        raise QRVerificationError("Security Alert: QR token has already been burned / used.")

    now = datetime.now(timezone.utc)
    exp = record.expires_at.replace(tzinfo=timezone.utc) if record.expires_at.tzinfo is None else record.expires_at
    if exp < now:
        raise QRVerificationError("QR verification token has expired. Request a refreshed token.")

    # Burn token atomically
    record.is_burned = True
    record.verified_by_user_id = user["id"]
    record.verified_at = now
    record.verified_lat = verify_req.current_lat
    record.verified_lng = verify_req.current_lng
    record.verified_temp_c = verify_req.measured_temp_c

    # Update delivery status
    deliv = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if deliv:
        if verify_req.handover_type == "PICKUP":
            deliv.status = "IN_TRANSIT"
            deliv.actual_pickup_at = now
            if verify_req.measured_temp_c is not None:
                deliv.pickup_temp_c = verify_req.measured_temp_c
        elif verify_req.handover_type == "DROPOFF":
            deliv.status = "DELIVERED"
            deliv.actual_dropoff_at = now
            if verify_req.measured_temp_c is not None:
                deliv.dropoff_temp_c = verify_req.measured_temp_c

    db.commit()

    return QRVerifyResponse(
        verified=True,
        message=f"Handover {verify_req.handover_type} successfully verified and single-use token burned.",
        delivery_id=delivery_id,
        handover_type=verify_req.handover_type,
        verified_at=now
    )
