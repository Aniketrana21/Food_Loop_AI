"""
FoodLoop AI - Audit Repository
Creates immutable forensic audit log records with SHA-256 integrity hashing.
"""
import hashlib
import json
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.models import AuditLog


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def log_action(
        self,
        module: str,
        action: str,
        entity_name: str,
        entity_id: str,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        raw_signature = f"{module}|{action}|{entity_name}|{entity_id}|{user_id}|{organization_id}|{json.dumps(new_values, default=str)}"
        sha_hash = hashlib.sha256(raw_signature.encode("utf-8")).hexdigest()

        entry = AuditLog(
            organization_id=organization_id,
            user_id=user_id,
            module=module,
            action=action,
            entity_name=entity_name,
            entity_id=entity_id,
            old_values=old_values,
            new_values=new_values,
            client_ip=client_ip,
            user_agent=user_agent,
            sha256_hash=sha_hash
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry
