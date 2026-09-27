"""
FoodLoop AI - Regulatory Documents & SOPs API Router (Phase 12)
Manages regulatory compliance standards, FDA guidelines, institutional SOPs,
and document ingestion pipeline with chunking and access control.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.models.models import Document, DocumentChunk
from app.schemas.enterprise_schemas import DocumentCreate, DocumentOut
from app.schemas.rag_schemas import (
    DocumentIngestRequest,
    DocumentIngestResponse,
    DocumentChunkOut
)
from app.services.rag_service import rag_service
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/documents", tags=["23. Regulatory Knowledge & SOPs"])


@router.get("", response_model=dict)
def list_documents(
    category: Optional[str] = Query(None, description="Filter by category or document_type"),
    document_type: Optional[str] = Query(None, description="Filter by document type (e.g. HACCP_SOP, INSTITUTIONAL_POLICY)"),
    params: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Lists compliance documentation with strict multi-tenant access control filtering.
    Users only see public guidelines and their own organization's internal policies.
    """
    user_org_id = user.get("organization_id")
    user_role = user.get("role", "KITCHEN_STAFF")

    query = db.query(Document)

    # Multi-tenant isolation filter
    if user_role != "ADMIN":
        query = query.filter(
            or_(
                Document.access_level == "PUBLIC",
                Document.is_public == True,
                Document.organization_id == None,
                and_(
                    Document.organization_id == user_org_id,
                    Document.access_level.in_(["PUBLIC", "ORGANIZATION_INTERNAL", "CONFIDENTIAL"])
                )
            )
        )

    if category:
        query = query.filter(
            or_(
                Document.category == category,
                Document.document_type == category
            )
        )
    if document_type:
        query = query.filter(Document.document_type == document_type)

    total = query.count()
    items = query.order_by(Document.created_at.desc()).offset(params.offset).limit(params.limit).all()

    items_data = [
        {
            "id": d.id,
            "title": d.title,
            "category": d.category,
            "document_type": d.document_type,
            "version": d.document_version,
            "access_level": d.access_level,
            "regulatory_source": d.regulatory_source,
            "organization_id": d.organization_id,
            "doc_date": str(d.doc_date) if d.doc_date else None,
            "is_public": d.is_public,
            "total_chunks": len(d.chunks) if d.chunks else 0,
            "created_at": d.created_at.isoformat() if d.created_at else None
        }
        for d in items
    ]

    return {
        "items": items_data,
        "total": total,
        "page": params.page,
        "size": params.limit
    }


@router.post("/ingest", response_model=DocumentIngestResponse, status_code=status.HTTP_201_CREATED)
def ingest_document(
    doc_in: DocumentIngestRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "AUDITOR", "KITCHEN_MANAGER"]))
):
    """
    Phase 12 Document Ingestion Pipeline:
    - Parses document text
    - Segments into overlapping semantic chunks
    - Calculates term embeddings
    - Attaches organization, document type, version, date, access level, and source metadata
    - Persists to vector chunks store
    """
    return rag_service.ingest_document(db, doc_in, current_user=user)


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
def create_document(
    doc_in: DocumentCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "AUDITOR"]))
):
    """Legacy document ingestion endpoint."""
    doc = Document(**doc_in.model_dump())
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Retrieves document text and verifies access authorization."""
    user_org_id = user.get("organization_id")
    user_role = user.get("role", "KITCHEN_STAFF")

    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Access control verification
    if user_role != "ADMIN":
        if doc.access_level != "PUBLIC" and not doc.is_public and doc.organization_id is not None:
            if doc.organization_id != user_org_id:
                raise HTTPException(status_code=403, detail="Access denied: Cross-organization document exposure restricted")

    return doc


@router.get("/{document_id}/chunks", response_model=List[DocumentChunkOut])
def get_document_chunks(
    document_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Retrieves all vector chunks for a specific authorized document."""
    # First verify access
    get_document(document_id, db, user)
    chunks = db.query(DocumentChunk).filter(
        DocumentChunk.document_id == document_id
    ).order_by(DocumentChunk.chunk_index.asc()).all()
    return chunks
