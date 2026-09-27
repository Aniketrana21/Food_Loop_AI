"""
FoodLoop AI - Phase 11 QR Chain of Custody Pydantic Schemas
Strict schemas for immutable donation tracking, cryptographic handover tokens,
role-based scanning, forensic audit trails, and proof-of-custody verification.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class DonationCustodyEventOut(BaseModel):
    id: str
    donation_id: str
    event: str
    from_status: str
    to_status: str
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    role: str
    timestamp: datetime
    token_nonce: Optional[str] = None
    proof_type: Optional[str] = None
    verified_temp_c: Optional[float] = None
    verified_lat: Optional[float] = None
    verified_lng: Optional[float] = None
    signature_data: Optional[str] = None
    proof_image_url: Optional[str] = None
    notes: Optional[str] = None
    proof_metadata: Optional[Dict[str, Any]] = None
    previous_hash: Optional[str] = None
    integrity_hash: str
    model_config = ConfigDict(from_attributes=True)


class DonationQRGenerateRequest(BaseModel):
    donation_id: str = Field(..., description="Donation UUID or immutable ID (DON-XXXXXXXX)")
    stage: str = Field(..., description="Custody stage: KITCHEN_HANDOVER, DRIVER_PICKUP, RECIPIENT_RECEIPT")
    expires_in_minutes: Optional[int] = Field(60, ge=5, le=1440, description="Token validity window in minutes")


class DonationQRGenerateResponse(BaseModel):
    donation_id: str
    immutable_donation_id: str
    stage: str
    token: str
    nonce: str
    hmac_signature: str
    expires_at: datetime
    current_status: str
    allowed_scanner_roles: List[str]
    instructions: str


class DonationQRScanVerifyRequest(BaseModel):
    token: str = Field(..., description="Cryptographic QR token string (FOODLOOP:DONATION:...)")
    stage: Optional[str] = Field(None, description="Optional target stage confirmation")
    proof_type: Optional[str] = Field(None, description="Proof type: SIGNATURE, TEMPERATURE, PHOTO, GPS, SEAL")
    measured_temp_c: Optional[float] = Field(None, ge=-30.0, le=100.0, description="Measured food cargo temperature in °C")
    current_lat: Optional[float] = Field(None, ge=-90.0, le=90.0, description="GPS Latitude of scanning device")
    current_lng: Optional[float] = Field(None, ge=-180.0, le=180.0, description="GPS Longitude of scanning device")
    signature_data: Optional[str] = Field(None, description="Digital signature base64/SVG or signer acknowledgement")
    proof_image_url: Optional[str] = Field(None, description="URL or dataURI of handover condition photo")
    notes: Optional[str] = Field(None, description="Custody condition notes, seal integrity, packaging remarks")
    proof_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Arbitrary proof telemetry")


class DonationQRScanVerifyResponse(BaseModel):
    verified: bool
    message: str
    donation_id: str
    immutable_donation_id: str
    previous_status: str
    current_status: str
    event: str
    scanner_role: str
    scanner_user_id: str
    scanner_user_name: Optional[str] = None
    timestamp: datetime
    integrity_hash: str
    proof_summary: Optional[Dict[str, Any]] = None


class DonationStatusTransitionRequest(BaseModel):
    target_status: str = Field(..., description="Target status: ACCEPTED, PICKUP_ASSIGNED, PICKED_UP, IN_TRANSIT, DELIVERED, RECEIVED")
    notes: Optional[str] = Field(None, description="Transition notes")
    proof_type: Optional[str] = Field(None, description="Optional proof type")
    verified_temp_c: Optional[float] = None
    signature_data: Optional[str] = None
    proof_image_url: Optional[str] = None


class DonationCreatePhase11Request(BaseModel):
    donor_org_id: str
    recipient_org_id: Optional[str] = None
    surplus_item_ids: List[str]
    notes: Optional[str] = None
    haccp_verified: bool = True
    initial_temp_c: Optional[float] = None


class DonationDetailOut(BaseModel):
    id: str
    immutable_donation_id: str
    tracking_number: str
    donor_org_id: str
    recipient_org_id: Optional[str] = None
    status: str
    total_weight_kg: float
    total_portions: int
    haccp_verified: bool
    created_at: datetime
    updated_at: datetime
    next_allowed_actions: List[Dict[str, Any]]
    custody_events: List[DonationCustodyEventOut]

    model_config = ConfigDict(from_attributes=True)

