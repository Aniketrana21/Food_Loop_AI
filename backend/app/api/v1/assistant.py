"""
FoodLoop AI - AI Copilot & Production RAG Assistant API Router (Phase 12)
Provides multi-tenant vector retrieval, operational database context retrieval,
strict anti-hallucination verification, source citations, and chat session management.
"""
from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.enterprise_schemas import (
    AssistantQueryRequest,
    AssistantQueryResponse,
    RecipeGenRequest,
    RecipeGenResponse
)
from app.schemas.rag_schemas import (
    RAGQueryRequest,
    RAGQueryResponse,
    ChatMessageOut,
    ChatSessionOut,
    SuggestedPromptsResponse
)
from app.services.rag_service import rag_service
from app.ai.engine import ai_engine
from app.middleware.rate_limit import RateLimiter

router = APIRouter(prefix="/assistant", tags=["22. AI Safety Assistant & RAG Copilot"])


@router.post("/chat", response_model=RAGQueryResponse, dependencies=[Depends(RateLimiter(times=40, seconds=60))])
def chat_with_rag_assistant(
    req: RAGQueryRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Production-grade RAG conversation endpoint.
    - Answers using authorized organizational operational data (waste, production, surplus, impact)
    - Retrieves verified uploaded documents & compliance policies with strict multi-tenant access control
    - Cites exact source references (Title, Document Type, Version, Date, Source, Relevance)
    - If evidence is insufficient, returns: "I don't have enough verified information to answer that."
    - Automatically persists conversation history.
    """
    return rag_service.answer_query(
        db=db,
        query=req.query,
        user=user,
        session_id=req.session_id,
        category_filter=req.category_filter,
        top_k=req.top_k
    )


@router.get("/suggested-prompts", response_model=SuggestedPromptsResponse)
def get_suggested_prompts(
    user: dict = Depends(get_current_user)
):
    """Returns curated suggested operational prompts for kitchen managers and dispatch coordinators."""
    prompts = rag_service.get_suggested_prompts()
    return SuggestedPromptsResponse(prompts=prompts)


@router.get("/history/{session_id}", response_model=ChatSessionOut)
def get_chat_session_history(
    session_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Retrieves chronological chat history for a session."""
    messages = rag_service.get_chat_history(db, session_id)
    return ChatSessionOut(
        session_id=session_id,
        total_messages=len(messages),
        messages=messages
    )


@router.delete("/history/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def clear_chat_session(
    session_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Clears history for a specific chat session."""
    rag_service.clear_chat_history(db, session_id)
    return None


# -------------------------------------------------------------
# Legacy and Specialized Endpoints
# -------------------------------------------------------------
@router.post("/query", response_model=AssistantQueryResponse, dependencies=[Depends(RateLimiter(times=30, seconds=60))])
def query_food_safety_copilot(
    req: AssistantQueryRequest,
    user: dict = Depends(get_current_user)
):
    """Legacy RAG semantic search over regulatory standards."""
    result = ai_engine.ask_safety_copilot(req.query, category_filter=req.category_filter)
    return AssistantQueryResponse(
        query=req.query,
        answer=result["answer"],
        sources=result["sources"],
        confidence_score=result["confidence_score"]
    )


@router.post("/generate-recipe", response_model=RecipeGenResponse, dependencies=[Depends(RateLimiter(times=20, seconds=60))])
def generate_upcycling_recipe(
    req: RecipeGenRequest,
    user: dict = Depends(get_current_user)
):
    """Generates institutional kitchen leftover repurposing recipes adhering to dietary tags."""
    result = ai_engine.generate_surplus_recipe(
        ingredients=req.ingredients,
        servings=req.servings,
        dietary_pref=req.dietary_preference
    )
    return RecipeGenResponse(**result)
