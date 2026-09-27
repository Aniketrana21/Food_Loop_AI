"""
FoodLoop AI - RAG Assistant Schemas (Phase 12)
Defines request/response data contracts for document ingestion, multi-tenant vector retrieval,
operational context citations, and chat history.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from pydantic import BaseModel, Field


class DocumentIngestRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=255, description="Document title")
    content: str = Field(..., min_length=20, description="Full text content of document")
    category: str = Field("HACCP_SOP", description="Category: FDA_FOOD_CODE, GOOD_SAMARITAN_ACT, HACCP_SOP, COLD_CHAIN_STANDARD, MUNICIPAL_BYLAW, etc.")
    document_type: str = Field(
        "HACCP_SOP",
        description="Type: HACCP_SOP, INSTITUTIONAL_POLICY, WASTE_MANAGEMENT_POLICY, DONATION_PROCEDURE, GOVERNMENT_GUIDELINE, OPERATIONAL_MANUAL"
    )
    version: str = Field("2024.1", description="Document version code")
    doc_date: Optional[date] = Field(default_factory=date.today, description="Publication or effective date")
    access_level: str = Field(
        "ORGANIZATION_INTERNAL",
        description="Access Level: PUBLIC, ORGANIZATION_INTERNAL, CONFIDENTIAL, ADMIN_ONLY"
    )
    source: str = Field("Internal Kitchen Policy", description="Authoritative regulatory or organizational source")
    organization_id: Optional[str] = Field(None, description="Owning organization ID (null for universal public docs)")


class DocumentChunkOut(BaseModel):
    id: str
    document_id: str
    chunk_index: int
    content: str
    token_count: int
    chunk_metadata: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentIngestResponse(BaseModel):
    document_id: str
    title: str
    document_type: str
    version: str
    access_level: str
    source: str
    organization_id: Optional[str]
    total_chunks: int
    created_at: datetime
    message: str


class SourceReferenceOut(BaseModel):
    document_id: str
    chunk_id: Optional[str] = None
    title: str
    document_type: str
    version: str
    date: Optional[str] = None
    access_level: str
    source: str
    organization_id: Optional[str] = None
    relevance_score: float
    snippet: str


class OperationalContextOut(BaseModel):
    query_type: str  # waste_increase, food_waste_causes, production_tomorrow, urgent_surplus, month_impact, generic_operational
    is_live_data: bool = True
    metric_count: int = 0
    summary: str
    key_metrics: Dict[str, Any] = Field(default_factory=dict)
    records: List[Dict[str, Any]] = Field(default_factory=list)


class RAGQueryRequest(BaseModel):
    query: str = Field(..., min_length=2, description="User question or prompt")
    session_id: Optional[str] = Field(None, description="Chat session ID for ongoing conversation")
    category_filter: Optional[str] = Field(None, description="Optional document category filter")
    top_k: int = Field(4, ge=1, le=10, description="Max verified chunks to retrieve")


class RAGQueryResponse(BaseModel):
    query: str
    session_id: str
    answer: str
    grounded: bool
    is_insufficient_evidence: bool = False
    sources: List[SourceReferenceOut] = Field(default_factory=list)
    operational_context: Optional[OperationalContextOut] = None
    suggested_prompts: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ChatMessageOut(BaseModel):
    id: str
    session_id: str
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    role: str
    content: str
    sources: List[SourceReferenceOut] = Field(default_factory=list)
    data_context: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSessionOut(BaseModel):
    session_id: str
    total_messages: int
    messages: List[ChatMessageOut]


class SuggestedPromptOut(BaseModel):
    prompt: str
    category: str
    description: str


class SuggestedPromptsResponse(BaseModel):
    prompts: List[SuggestedPromptOut]
