"""
A/B Testing API Routes
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Any, Optional
import logging
import asyncio
import json
import os
import time
from uuid import uuid4
import redis

from ..models import RagQuery, RagResponse
from ..routes.rag import rag_query, get_redis_client
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
    run_parallel: bool = Field(False, description="Run queries in parallel (default: False to avoid VRAM issues)")
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


# Redis configuration for A/B test results
AB_TEST_CACHE_TTL = 30 * 60  # 30 minutes

async def _run_ab_test_async(test_id: str, req: ABTestRequest):
    """Background task to run A/B test and store results in Redis"""
    try:
        logger.info(f"A/B test background task started: test_id={test_id}, parallel={req.run_parallel}")

        # Convert configs to RagQuery objects
        def config_to_rag_query(config: dict[str, Any], request_id: str) -> RagQuery:
            # Log config keys and critical values for debugging
            logger.info(f"🔍 config_to_rag_query: request_id={request_id}, config_keys={list(config.keys())}")
            logger.info(f"🔍 config values: model={config.get('model')}, temperature={config.get('temperature')}, maxTokens={config.get('maxTokens')}, contextWindow={config.get('contextWindow')}")
            
            model = config.get("model")
            temperature = config.get("temperature")
            max_tokens = config.get("maxTokens") or config.get("max_tokens", 512)
            context_window = config.get("contextWindow") or config.get("context_window", 4096)
            
            logger.info(f"🔍 Final values for {request_id}: model={model}, temperature={temperature}, max_tokens={max_tokens}, context_window={context_window}")
            
            return RagQuery(
                query=req.prompt,
                user_id=req.user_id,
                groups=req.groups,
                request_id=request_id,
                top_k=config.get("topK") or config.get("top_k", 10),
                web_search_enabled=config.get("useWebSearch") if "useWebSearch" in config else config.get("web_search_enabled", True),
                web_search_docs=config.get("webSearchDocs") or config.get("web_search_docs", 20),
                use_graph=config.get("useGraph") if "useGraph" in config else config.get("use_graph", False),
                enable_research=config.get("useResearchAgent") if "useResearchAgent" in config else config.get("enable_research", False),
                use_query_expansion=config.get("useQueryExpansion") if "useQueryExpansion" in config else config.get("use_query_expansion", False),
                use_bm25=config.get("useBM25") if "useBM25" in config else config.get("use_bm25", False),
                use_hybrid=config.get("useHybrid") if "useHybrid" in config else config.get("use_hybrid", False),
                max_tokens=max_tokens,  # Pass max_tokens from config
                context_window=context_window,  # Pass context_window from config
                model=model,  # CRITICAL: Pass model from config (e.g., 'llama3.2:1b' vs 'gemma2:9b')
                temperature=temperature,  # CRITICAL: Pass temperature from config (e.g., 0.3 vs 0.3)
            )

        request_id_a = f"{test_id}_a"
        request_id_b = f"{test_id}_b"

        query_a = config_to_rag_query(req.config_a, request_id_a)
        query_b = config_to_rag_query(req.config_b, request_id_b)

        # Run queries
        if req.run_parallel:
            result_a, result_b = await asyncio.gather(
                rag_query(query_a),
                rag_query(query_b),
                return_exceptions=True
            )
        else:
            try:
                logger.info(f"Executing query A: request_id={request_id_a}, top_k={query_a.top_k}")
                result_a = await rag_query(query_a)
                logger.info(f"Query A completed: answer_len={len(result_a.answer) if hasattr(result_a, 'answer') else 0}")
            except Exception as e:
                logger.error(f"Query A exception: {e}", exc_info=True)
                result_a = e
            try:
                logger.info(f"Executing query B: request_id={request_id_b}, top_k={query_b.top_k}")
                result_b = await rag_query(query_b)
                logger.info(f"Query B completed: answer_len={len(result_b.answer) if hasattr(result_b, 'answer') else 0}")
            except Exception as e:
                logger.error(f"Query B exception: {e}", exc_info=True)
                result_b = e

        # Handle errors
        if isinstance(result_a, Exception):
            raise HTTPException(status_code=500, detail=f"Query A failed: {str(result_a)}")
        if isinstance(result_b, Exception):
            raise HTTPException(status_code=500, detail=f"Query B failed: {str(result_b)}")

        # Extract metrics
        metrics_a = result_a.metrics if hasattr(result_a, 'metrics') else {}
        metrics_b = result_b.metrics if hasattr(result_b, 'metrics') else {}

        # Auto-grade if requested
        grader_result = None
        winner = None

        if req.auto_grade:
            logger.info(f"Starting LLM auto-grading for test_id={test_id}")
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
                if abs(score_a - score_b) < 0.05:
                    winner = "tie"
                elif score_a > score_b:
                    winner = "A"
                else:
                    winner = "B"
            logger.info(f"LLM auto-grading completed: winner={winner}")

        # Build result
        result = ABTestResult(
            test_id=test_id,
            prompt=req.prompt,
            result_a=result_a,
            result_b=result_b,
            metrics_a=metrics_a,
            metrics_b=metrics_b,
            grader_result=grader_result,
            winner=winner
        )

        # Store in Redis
        redis_client = get_redis_client()
        if redis_client:
            result_dict = result.model_dump(mode='json')
            result_json = json.dumps(result_dict)
            redis_client.setex(
                f"ab_test:result:{test_id}",
                AB_TEST_CACHE_TTL,
                result_json
            )
            logger.info(f"✅ Stored A/B test result in Redis: test_id={test_id}, TTL={AB_TEST_CACHE_TTL}s")
        else:
            logger.warning(f"⚠️  Redis unavailable, cannot store A/B test result: test_id={test_id}")

    except Exception as e:
        logger.error(f"A/B test background task failed: {e}", exc_info=True)
        # Store error in Redis
        redis_client = get_redis_client()
        if redis_client:
            error_result = {
                "test_id": test_id,
                "error": str(e),
                "status": "error"
            }
            redis_client.setex(
                f"ab_test:result:{test_id}",
                AB_TEST_CACHE_TTL,
                json.dumps(error_result)
            )


@router.post("/run")
async def run_ab_test(req: ABTestRequest, background_tasks: BackgroundTasks):
    """
    Start an A/B test asynchronously.

    Returns immediately with test_id. Frontend should poll /result/{test_id} for results.
    Tests can take 5+ minutes, so we use async execution with Redis storage.
    """
    test_id = uuid4().hex
    logger.info(f"A/B test initiated: test_id={test_id}, parallel={req.run_parallel}, auto_grade={req.auto_grade}")

    # Start background task
    background_tasks.add_task(_run_ab_test_async, test_id, req)

    # Return immediately with test_id
    return {
        "test_id": test_id,
        "status": "running",
        "message": "A/B test started. Poll /result/{test_id} for results."
    }


@router.get("/result/{test_id}")
async def get_ab_test_result(test_id: str):
    """
    Get A/B test result by test_id.

    Returns the result if available, or {"status": "running"} if still processing.
    """
    redis_client = get_redis_client()
    if redis_client:
        try:
            result_json = redis_client.get(f"ab_test:result:{test_id}")
            if result_json:
                result_dict = json.loads(result_json)
                if "error" in result_dict:
                    # Return error in response instead of raising exception
                    # This allows frontend to display the error properly
                    return {
                        "test_id": test_id,
                        "status": "error",
                        "error": result_dict["error"],
                        "message": f"Test failed: {result_dict['error']}"
                    }
                return result_dict
        except Exception as e:
            error_msg = str(e) if e else "Unknown error"
            logger.error(f"Error retrieving A/B test result: {error_msg}", exc_info=True)

    # Not found in Redis - still running or expired
    return {
        "test_id": test_id,
        "status": "running",
        "message": "Test is still running or result expired. Please wait."
    }


@router.post("/run-sync", response_model=ABTestResult)
async def run_ab_test_sync(req: ABTestRequest):
    """
    Run an A/B test synchronously (for backwards compatibility).

    WARNING: This will block for 5+ minutes. Use /run endpoint instead.
    """
    test_id = uuid4().hex
    logger.info(f"A/B test started (sync): test_id={test_id}, parallel={req.run_parallel}")

    # Convert configs to RagQuery objects
    def config_to_rag_query(config: dict[str, Any], request_id: str) -> RagQuery:
        # Map frontend config keys to backend RagQuery fields
        # Frontend uses camelCase, backend uses snake_case
        return RagQuery(
            query=req.prompt,
            user_id=req.user_id,
            groups=req.groups,
            request_id=request_id,
            top_k=config.get("topK") or config.get("top_k", 10),
            web_search_enabled=config.get("useWebSearch") if "useWebSearch" in config else config.get("web_search_enabled", True),
            web_search_docs=config.get("webSearchDocs") or config.get("web_search_docs", 20),
            use_graph=config.get("useGraph") if "useGraph" in config else config.get("use_graph", False),
            enable_research=config.get("useResearchAgent") if "useResearchAgent" in config else config.get("enable_research", False),
            use_query_expansion=config.get("useQueryExpansion") if "useQueryExpansion" in config else config.get("use_query_expansion", False),
            use_bm25=config.get("useBM25") if "useBM25" in config else config.get("use_bm25", False),
            use_hybrid=config.get("useHybrid") if "useHybrid" in config else config.get("use_hybrid", False),
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
            try:
                logger.info(f"Executing query A: request_id={request_id_a}, top_k={query_a.top_k}")
                result_a = await rag_query(query_a)
                logger.info(f"Query A completed: answer_len={len(result_a.answer) if hasattr(result_a, 'answer') else 0}")
            except Exception as e:
                logger.error(f"Query A exception: {e}", exc_info=True)
                result_a = e
            try:
                logger.info(f"Executing query B: request_id={request_id_b}, top_k={query_b.top_k}")
                result_b = await rag_query(query_b)
                logger.info(f"Query B completed: answer_len={len(result_b.answer) if hasattr(result_b, 'answer') else 0}")
            except Exception as e:
                logger.error(f"Query B exception: {e}", exc_info=True)
                result_b = e

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
            logger.info(f"Starting LLM auto-grading for test_id={test_id} (sync)")
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
            logger.info(f"LLM auto-grading completed: winner={winner}")

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

