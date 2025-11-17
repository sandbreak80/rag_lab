"""
A/B Testing API Routes
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Optional
import logging
import asyncio
import json
from uuid import uuid4

from ..models import RagQuery, RagResponse
from ..routes.rag import rag_query
from ..pipeline.auto_grader import grade_ab_responses

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/ab-testing", tags=["ab-testing"])


# ============================================================================
# Prompt Library Models
# ============================================================================
class PromptLibraryItem(BaseModel):
    """Prompt library item"""
    id: str
    category: str
    title: str
    prompt: str
    complexity: str
    expectedLength: str
    tags: list[str]
    difficulty: str
    expectedSources: int
    expectedLatency: str
    description: Optional[str] = None


# Load prompt library from frontend data file
# In production, this could be stored in a database
PROMPT_LIBRARY = [
    {
        "id": "factual-1",
        "category": "factual",
        "title": "What is RAG?",
        "prompt": "What is Retrieval-Augmented Generation (RAG)? Explain the core concept and how it works.",
        "complexity": "simple",
        "expectedLength": "short",
        "tags": ["RAG", "basics", "concepts"],
        "difficulty": "beginner",
        "expectedSources": 3,
        "expectedLatency": "50-100ms",
        "description": "Simple factual question requiring basic RAG knowledge"
    },
    {
        "id": "factual-2",
        "category": "factual",
        "title": "Vector Search vs Keyword Search",
        "prompt": "What is the difference between vector search and keyword search? When would you use each?",
        "complexity": "simple",
        "expectedLength": "medium",
        "tags": ["search", "vector", "keyword", "comparison"],
        "difficulty": "beginner",
        "expectedSources": 4,
        "expectedLatency": "100-150ms",
        "description": "Comparison question requiring understanding of search methods"
    },
    {
        "id": "analytical-1",
        "category": "analytical",
        "title": "RAG Architecture Comparison",
        "prompt": "Compare and contrast naive RAG, advanced RAG with reranking, and agentic RAG systems. Analyze the trade-offs between retrieval precision, computational cost, and response quality. Include specific examples of when each architecture would be most appropriate.",
        "complexity": "complex",
        "expectedLength": "long",
        "tags": ["RAG", "architecture", "comparison", "trade-offs"],
        "difficulty": "advanced",
        "expectedSources": 8,
        "expectedLatency": "500-1000ms",
        "description": "Complex analytical question requiring deep understanding and comparison"
    },
    # Add more prompts as needed - full list in frontend/src/data/promptLibrary.ts
]


# ============================================================================
# A/B Test Request/Response Models
# ============================================================================
class ABTestRequest(BaseModel):
    """Request for A/B test execution"""
    prompt: str = Field(..., description="Test prompt")
    config_a: dict[str, Any] = Field(..., description="Configuration A (RAGConfig)")
    config_b: dict[str, Any] = Field(..., description="Configuration B (RAGConfig)")
    run_parallel: bool = Field(True, description="Run queries in parallel")
    auto_grade: bool = Field(True, description="Automatically grade responses")
    user_id: str = Field("ab_test_user", description="User ID for queries")
    groups: list[str] = Field(default_factory=list, description="User groups")


class ABTestResult(BaseModel):
    """Result from A/B test execution"""
    test_id: str
    prompt: str
    result_a: RagResponse
    result_b: RagResponse
    metrics_a: dict[str, Any]
    metrics_b: dict[str, Any]
    grader_result: Optional[dict[str, Any]] = None
    winner: Optional[str] = None  # "A", "B", or "tie"


class GradeRequest(BaseModel):
    """Request for auto-grading"""
    prompt: str
    response_a: str
    response_b: str
    sources_a: list[dict[str, Any]]
    sources_b: list[dict[str, Any]]
    config_a: dict[str, Any]
    config_b: dict[str, Any]


# ============================================================================
# API Endpoints
# ============================================================================
@router.get("/prompts", response_model=list[PromptLibraryItem])
async def get_prompts(
    category: Optional[str] = None,
    complexity: Optional[str] = None,
    difficulty: Optional[str] = None
):
    """Get all prompts from the library with optional filtering"""
    prompts = [PromptLibraryItem(**p) for p in PROMPT_LIBRARY]

    if category:
        prompts = [p for p in prompts if p.category == category]
    if complexity:
        prompts = [p for p in prompts if p.complexity == complexity]
    if difficulty:
        prompts = [p for p in prompts if p.difficulty == difficulty]

    return prompts


@router.get("/prompts/{prompt_id}", response_model=PromptLibraryItem)
async def get_prompt(prompt_id: str):
    """Get a specific prompt by ID"""
    for prompt in PROMPT_LIBRARY:
        if prompt["id"] == prompt_id:
            return PromptLibraryItem(**prompt)
    raise HTTPException(status_code=404, detail=f"Prompt {prompt_id} not found")


@router.post("/run", response_model=ABTestResult)
async def run_ab_test(req: ABTestRequest):
    """
    Run an A/B test with two configurations.

    Executes the same prompt with two different configurations and returns
    both results for comparison.
    """
    test_id = uuid4().hex
    logger.info(f"A/B test started: test_id={test_id}, parallel={req.run_parallel}")

    # Convert configs to RagQuery objects
    def config_to_rag_query(config: dict[str, Any], request_id: str) -> RagQuery:
        return RagQuery(
            query=req.prompt,
            user_id=req.user_id,
            groups=req.groups,
            request_id=request_id,
            top_k=config.get("top_k", 8),
            web_search_enabled=config.get("web_search_enabled", True),
            web_search_docs=config.get("web_search_docs", 20),
            use_graph=config.get("use_graph", False),
            enable_research=config.get("enable_research", False),
        )

    request_id_a = f"{test_id}_a"
    request_id_b = f"{test_id}_b"

    query_a = config_to_rag_query(req.config_a, request_id_a)
    query_b = config_to_rag_query(req.config_b, request_id_b)

    try:
        if req.run_parallel:
            # Run both queries in parallel
            result_a, result_b = await asyncio.gather(
                rag_query(query_a),
                rag_query(query_b),
                return_exceptions=True
            )
        else:
            # Run sequentially
            result_a = await rag_query(query_a)
            result_b = await rag_query(query_b)

        # Handle errors
        if isinstance(result_a, Exception):
            logger.error(f"Query A failed: {result_a}")
            raise HTTPException(status_code=500, detail=f"Query A failed: {str(result_a)}")
        if isinstance(result_b, Exception):
            logger.error(f"Query B failed: {result_b}")
            raise HTTPException(status_code=500, detail=f"Query B failed: {str(result_b)}")

        # Extract metrics
        metrics_a = result_a.metrics if hasattr(result_a, 'metrics') else {}
        metrics_b = result_b.metrics if hasattr(result_b, 'metrics') else {}

        # Auto-grade if requested
        grader_result = None
        winner = None

        if req.auto_grade:
            try:
                grader_result = await grade_ab_responses(
                    prompt=req.prompt,
                    response_a=result_a.answer,
                    response_b=result_b.answer,
                    sources_a=result_a.sources or [],
                    sources_b=result_b.sources or [],
                    config_a=req.config_a,
                    config_b=req.config_b
                )

                # Determine winner
                if grader_result:
                    score_a = grader_result.get("response_a", {}).get("overall_score", 0)
                    score_b = grader_result.get("response_b", {}).get("overall_score", 0)
                    if abs(score_a - score_b) < 0.05:  # Within 5% = tie
                        winner = "tie"
                    elif score_a > score_b:
                        winner = "A"
                    else:
                        winner = "B"
            except Exception as e:
                logger.warning(f"Auto-grading failed: {e}", exc_info=True)
                # Continue without grading

        return ABTestResult(
            test_id=test_id,
            prompt=req.prompt,
            result_a=result_a,
            result_b=result_b,
            metrics_a=metrics_a,
            metrics_b=metrics_b,
            grader_result=grader_result,
            winner=winner
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"A/B test failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"A/B test failed: {str(e)}")


@router.post("/grade")
async def grade_responses(req: GradeRequest):
    """
    Grade two responses using LLM-based evaluation.

    Returns detailed scores across multiple dimensions.
    """
    try:
        result = await grade_ab_responses(
            prompt=req.prompt,
            response_a=req.response_a,
            response_b=req.response_b,
            sources_a=req.sources_a,
            sources_b=req.sources_b,
            config_a=req.config_a,
            config_b=req.config_b
        )
        return result
    except Exception as e:
        logger.error(f"Grading failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Grading failed: {str(e)}")

