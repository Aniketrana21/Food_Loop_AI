from fastapi import APIRouter
from app.schemas.schemas import (
    RAGQueryRequest, RAGQueryResponse,
    RecipeGenerationRequest, RecipeGenerationResponse
)
from app.services.rag_service import rag_service
from app.services.llm_service import llm_service

router = APIRouter(prefix="/rag", tags=["RAG & LLM Assistant"])


@router.post("/ask", response_model=RAGQueryResponse)
def query_foodloop_knowledge(payload: RAGQueryRequest):
    """
    Retrieval-Augmented Generation (RAG) over food safety regulations,
    Bill Emerson Good Samaritan Act, cold-chain logistics, and tax incentives.
    """
    res = rag_service.search_knowledge(
        query=payload.query,
        category_filter=payload.category_filter
    )
    return res


@router.post("/generate-recipe", response_model=RecipeGenerationResponse)
def generate_surplus_recipe(payload: RecipeGenerationRequest):
    """
    Provider-agnostic LLM commercial rescue recipe generator.
    Transforms surplus ingredients into scalable, safe community meals.
    """
    res = llm_service.generate_rescue_recipe(
        ingredients=payload.ingredients,
        dietary_preference=payload.dietary_preference or "any",
        servings=payload.servings or 50
    )
    return res
