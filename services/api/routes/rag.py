"""
RAG v1 API Routes - Complete observability contract implementation
"""
from fastapi import APIRouter, Depends, HTTPException, status
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
import time
import logging
import os
import json
from uuid import uuid4
from datetime import datetime, timezone
from prometheus_client import Counter
import redis
from typing import Optional

# Local imports
from ..models import RagQuery, RagResponse
from ..config import (
    CONTRACT_VERSION, ENABLE_OBS, USE_MOCK_LLM, USE_MOCK_VECTOR, USE_MOCK_WEB,
    FRESHNESS_HOURS, TOPN, AB_TEST_ENABLED, SEARCH_SERVICE_URL
)
from ..authz.abac import build_acl_predicate
from ..adapters import vector, web, llm, kg
from ..pipeline.recency_gate import evaluate_recency_gate
from ..pipeline.ab_grader import ABGrader
from ..pipeline.guardrail_client import check_guardrails, get_security_status

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)
router = APIRouter(prefix="/v1/rag", tags=["rag-v1"])

# Redis client for persistent response storage
# TTL: 30 minutes (allows time for user to navigate away and come back)
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
CACHE_TTL = 30 * 60  # 30 minutes

_redis_client: Optional[redis.Redis] = None

def get_redis_client() -> Optional[redis.Redis]:
    """Get or create Redis client with connection pooling"""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(
                REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
                retry_on_timeout=True,
                health_check_interval=30
            )
            # Test connection
            _redis_client.ping()
            logger.info(f"✅ Redis connected: {REDIS_URL}")
        except Exception as e:
            logger.warning(f"⚠️  Redis unavailable: {e}. Falling back to in-memory cache.")
            _redis_client = None
    return _redis_client

# Fallback in-memory cache if Redis is unavailable
_response_cache_fallback: dict[str, tuple[RagResponse, float]] = {}

# B1: Prometheus metrics for early-stop
RAG_RETRIEVAL_WEB_SKIPPED = Counter(
    'rag_retrieval_web_skipped_total',
    'Number of queries where web search was skipped due to strong vector hits'
)

# Issue #5: Prometheus metrics for token accounting
RAG_LLM_TOKENS = Counter(
    'rag_llm_tokens_total',
    'Total LLM tokens consumed (input + output)',
    ['model', 'token_type']  # token_type: 'input' or 'output'
)


def infer_query_intent(query: str) -> str:
    """Classify query intent for observability"""
    query_lower = query.lower()

    if any(word in query_lower for word in ["what is", "define", "meaning of", "explain"]):
        return "definition"
    elif any(word in query_lower for word in ["how to", "how do i", "steps to", "procedure"]):
        return "procedural"
    elif any(word in query_lower for word in ["why", "troubleshoot", "error", "problem", "issue"]):
        return "diagnostic"
    else:
        return "general"


def build_prompt_messages(query: str, results: list, require_web_citation: bool = False, require_kg_citation: bool = False) -> list[dict]:
    """Build extractive-first prompt with citations - now uses dynamic prompts from storage"""
    # Import here to avoid circular dependency
    from .prompts import get_prompt_template

    context_parts = []
    web_indices = []
    kg_indices = []

    for i, result in enumerate(results):
        context_parts.append(f"[{i+1}] {result.content}")
        # Track which indices are web/KG results (check both variants for compatibility)
        if result.origin_tool in ["web_search", "web"]:
            web_indices.append(i + 1)
        elif result.origin_tool in ["knowledge_graph", "kg"]:
            kg_indices.append(i + 1)

    context = "\n\n".join(context_parts)

    # Build citation instruction
    citation_instruction = "Include citations [1], [2], etc. to reference sources."
    if require_web_citation and web_indices:
        citation_instruction += f" IMPORTANT: You must cite at least one web source from [{', '.join(map(str, web_indices))}]."
    if require_kg_citation and kg_indices:
        citation_instruction += f" IMPORTANT: You must cite at least one knowledge graph source from [{', '.join(map(str, kg_indices))}]."

    # Count research sources to inform the system prompt
    research_count = sum(1 for r in results if hasattr(r, 'doc_id') and r.doc_id.startswith('research_'))
    web_count = len(web_indices)

    # Build context-aware system prompt
    source_context = ""
    if research_count > 0:
        source_context = f" The context includes {research_count} research article(s) from recent AI publications and news sources."
    if web_count > 0:
        source_context += f" It also includes {web_count} live web search result(s) with current information."

    # Load system prompt template from storage (editable via API!)
    system_prompt_template = get_prompt_template("rag_synthesis")
    system_prompt = system_prompt_template.format(
        source_context=source_context,
        citation_instruction=citation_instruction
    )

    return [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer with citations:"
        }
    ]


def extract_citations(answer: str, results: list) -> list[dict]:
    """Extract sentence-level citations from answer"""
    import re

    citations = []
    # Find all citation markers like [1], [2], etc.
    citation_pattern = r'\[(\d+)\]'
    matches = re.findall(citation_pattern, answer)

    for match in set(matches):  # Remove duplicates
        idx = int(match) - 1  # Convert to 0-based
        if 0 <= idx < len(results):
            result = results[idx]
            citations.append({
                "doc_id": result.doc_id,
                "version": result.metadata.get("version", "1.0"),
                "chunk_id": result.chunk_id,
                "char_range": [0, len(result.content)],  # Full chunk for now
                "content": result.content,  # Add content field for frontend display
                "source_uri": result.metadata.get("source_uri", ""),
                "origin_tool": result.origin_tool,
                "score": getattr(result, 'score', 0.95)  # Include score if available
            })

    return citations


@router.post("/query", response_model=RagResponse)
async def rag_query(req: RagQuery):
    """
    RAG query handler with complete observability contract.

    Implements 9-stage pipeline:
    1. IDs & Context
    2. AuthZ & ACL
    3. Retrieval (Hybrid)
    4. Recency Gate
    5. Rerank
    6. Synthesis (LLM)
    7. Guardrails
    8. A/B Evaluation
    9. Artifacts & Provenance
    """
    with tracer.start_as_current_span("rag.query") as span:
        try:
            t0 = time.perf_counter()
            stage_timings = {}  # Track stage latencies

            # ===================================================================
            # STAGE 0: IDs & Context
            # ===================================================================
            request_id = req.request_id or uuid4().hex
            trace_id = span.get_span_context().trace_id if span else uuid4().hex
            query_intent = infer_query_intent(req.query)

            span.set_attribute("rag.request.contract_version", CONTRACT_VERSION)
            span.set_attribute("rag.request.freshness_hours", FRESHNESS_HOURS)
            span.set_attribute("rag.request.intent", query_intent)

            logger.info(f"RAG query started: request_id={request_id}, query_len={len(req.query)}")

            # ===================================================================
            # STAGE 1: AuthZ & ACL Claims
            # ===================================================================
            t_acl_start = time.perf_counter()
            acl_pred = build_acl_predicate(req.user_id, req.groups, req.dept)
            t_acl_end = time.perf_counter()
            stage_timings["acl_ms"] = round((t_acl_end - t_acl_start) * 1000, 2)  # Use float precision
            span.set_attribute("rag.auth.perms_tag", acl_pred.tag)

            # ===================================================================
            # STAGE 2: Retrieval (Parallel Hybrid with ACL pre-filter)
            # ===================================================================
            t_retrieve_start = time.perf_counter()

            # Initialize timings for query expansion, BM25, and hybrid fusion
            query_expansion_ms = None
            bm25_ms = None
            hybrid_fusion_ms = None
            expanded_query = req.query

            # If query expansion, BM25, or hybrid is enabled, use search-service
            if req.use_query_expansion or req.use_bm25 or req.use_hybrid:
                try:
                    import httpx
                    t_search_start = time.perf_counter()
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        search_response = await client.post(
                            f"{SEARCH_SERVICE_URL}/search_with_config",
                            json={
                                "query": req.query,
                                "config": {
                                    "use_query_expansion": req.use_query_expansion,
                                    "use_bm25": req.use_bm25,
                                    "use_hybrid": req.use_hybrid,
                                    "use_graph": False,  # We handle KG separately
                                    "use_reranking": False,  # We handle reranking separately
                                    "top_k": req.top_k * 2  # Over-fetch for reranking
                                }
                            }
                        )
                        search_response.raise_for_status()
                        search_data = search_response.json()
                        t_search_end = time.perf_counter()

                        # Extract timings from search-service response
                        # The search-service returns: {"results": [...], "metrics": {"timings": {...}, "perf_metrics": {...}}}
                        metrics_data = search_data.get("metrics", {})
                        perf_metrics = metrics_data.get("perf_metrics", {})
                        all_timings = metrics_data.get("timings", {})

                        # Fallback: also check top-level keys for backwards compatibility
                        if not all_timings:
                            all_timings = search_data.get("timings", {})
                        if not perf_metrics:
                            perf_metrics = search_data.get("perf_metrics", {})

                        # Extract timings - TimingCollector returns milliseconds already
                        # Use None if feature disabled, otherwise use actual timing (even if 0)
                        query_expansion_ms = round(all_timings.get("query_expansion", 0), 2) if req.use_query_expansion else None
                        bm25_ms = round(all_timings.get("bm25_search", 0), 2) if req.use_bm25 else None
                        hybrid_fusion_ms = round(all_timings.get("hybrid_fusion", 0), 2) if req.use_hybrid else None

                        # Log extracted timings for debugging
                        logger.info(f"Extracted timings from search-service: QE={query_expansion_ms}ms, BM25={bm25_ms}ms, Hybrid={hybrid_fusion_ms}ms")
                        logger.info(f"Raw timings dict from search-service: {all_timings}")
                        logger.info(f"Request config: use_query_expansion={req.use_query_expansion}, use_bm25={req.use_bm25}, use_hybrid={req.use_hybrid}")

                        # Get expanded query if query expansion was used
                        if req.use_query_expansion and perf_metrics.get("query_expanded"):
                            expanded_query = search_data.get("expanded_query") or req.query

                        # Convert search-service results to our format
                        search_results = search_data.get("results", [])
                        # Note: If using search-service, we'll use these results instead of direct vector search
                        # For now, we'll still do vector search but could replace it
                        logger.info(f"Search-service: QE={query_expansion_ms}ms, BM25={bm25_ms}ms, Hybrid={hybrid_fusion_ms}ms")

                except Exception as e:
                    logger.warning(f"Search-service call failed (service may be unavailable), continuing without QE/BM25/Hybrid: {e}")
                    # Continue without these features - don't fail the entire request
                    # Set timings to None to indicate they weren't executed
                    query_expansion_ms = None
                    bm25_ms = None
                    hybrid_fusion_ms = None

            # Define parallel retrieval tasks
            async def vector_search_task():
                with tracer.start_as_current_span("retrieve_internal.vector") as retrieve_span:
                    t_vec_start = time.perf_counter()
                    results, stats = await vector.search(
                        query=expanded_query,  # Use expanded query if available
                        acl_predicate=acl_pred,
                        top_k=req.top_k * 2,  # Over-fetch
                        use_mock=USE_MOCK_VECTOR
                    )
                    t_vec_end = time.perf_counter()
                    retrieve_span.set_attribute("docs_retrieved", len(results))
                    retrieve_span.set_attribute("acl_filtered", stats.get("acl_filtered_count", 0))
                    # Extract detailed timings from stats if available
                    embedding_ms = stats.get("embedding_ms", 0)
                    vector_db_ms = stats.get("vector_db_ms", 0)
                    total_ms = int((t_vec_end - t_vec_start) * 1000)
                    return results, stats, total_ms, embedding_ms, vector_db_ms

            async def web_search_task():
                with tracer.start_as_current_span("retrieve_web.searxng") as web_span:
                    t_web_start = time.perf_counter()
                    results = await web.search(
                        query=req.query,
                        top_k=req.web_search_docs,  # Use value from request (default 20)
                        use_mock=USE_MOCK_WEB
                    )
                    t_web_end = time.perf_counter()
                    web_span.set_attribute("docs_retrieved", len(results))
                    web_span.set_attribute("web.top_k_requested", req.web_search_docs)
                    return results, int((t_web_end - t_web_start) * 1000)

            async def kg_search_task():
                with tracer.start_as_current_span("retrieve_kg.relationships") as kg_span:
                    t_kg_start = time.perf_counter()
                    # Always use real KG service - no mocks
                    results = await kg.search(
                        query=req.query,
                        vector_results=vector_results,
                        top_k=5,
                        use_mock=False  # Always real - no mocks
                    )
                    t_kg_end = time.perf_counter()
                    kg_span.set_attribute("docs_retrieved", len(results))
                    # Use float precision to avoid rounding to 0 for fast searches
                    kg_timing_ms = round((t_kg_end - t_kg_start) * 1000, 2)
                    return results, kg_timing_ms

            # B1: Early-stop logic - check if vector results are strong enough
            RAG_EARLYSTOP_MIN_HITS = int(os.getenv("RAG_EARLYSTOP_MIN_HITS", "8"))
            RAG_EARLYSTOP_MIN_SCORE = float(os.getenv("RAG_EARLYSTOP_MIN_SCORE", "0.60"))

            # Execute vector search first to evaluate early-stop
            import asyncio
            vector_results, vector_stats, vector_ms, embedding_ms, vector_db_ms = await vector_search_task()

            # Determine web search behavior based on settings and early-stop logic
            web_skipped = False
            web_reason = "ok"  # Default: web search will run
            web_results = []
            web_ms = 0

            # Check if web search is disabled in settings
            if not req.web_search_enabled:
                web_skipped = True
                web_reason = "disabled"
                span.set_attribute("web.skipped", True)
                span.set_attribute("web.skip_reason", "disabled_in_settings")
                logger.info("Web search disabled in settings")
            else:
                # Evaluate early-stop: skip web if vector has strong hits
                # BUT: If web_search_enabled=True, user explicitly wants web search
                # Only apply early-stop if enabled via env var AND user hasn't explicitly enabled web search
                # Actually, if user sets web_search_enabled=True, we should respect that and NOT skip
                # Early-stop should only apply when web_search_enabled is not explicitly set to True
                # For now, we'll make early-stop optional via env var, defaulting to False when web_search_enabled=True
                RAG_EARLYSTOP_ENABLED = os.getenv("RAG_EARLYSTOP_ENABLED", "false").lower() == "true"

                # Only apply early-stop if explicitly enabled AND vector results are strong
                if RAG_EARLYSTOP_ENABLED and len(vector_results) >= RAG_EARLYSTOP_MIN_HITS:
                    # Check if median score is above threshold
                    scores = [r.score for r in vector_results if hasattr(r, 'score')]
                    if scores:
                        median_score = sorted(scores)[len(scores) // 2]
                        if median_score >= RAG_EARLYSTOP_MIN_SCORE:
                            web_skipped = True
                            web_reason = "early_stop"
                            span.set_attribute("web.skipped", True)
                            span.set_attribute("web.skip_reason", "strong_vector_hits")
                            RAG_RETRIEVAL_WEB_SKIPPED.inc()
                            logger.info(
                                f"Early-stop: Skipping web search (vector: {len(vector_results)} hits, "
                                f"median_score: {median_score:.3f} >= {RAG_EARLYSTOP_MIN_SCORE})"
                            )

            # Execute web search if not skipped
            if not web_skipped:
                web_results, web_ms = await web_search_task()
                span.set_attribute("web.skipped", False)
                web_reason = "ok"
                logger.info(f"Web search executed: {len(web_results)} results")
                if len(web_results) > 0:
                    logger.info(f"Web results origin_tools: {[r.origin_tool for r in web_results[:3]]}")
            else:
                logger.info(f"Web search skipped: {web_reason}")

            # Knowledge Graph search (if enabled)
            kg_results = []
            kg_ms = None  # Use None to indicate not enabled
            if req.use_graph:
                kg_results, kg_ms = await kg_search_task()
                # kg_ms is already rounded to 2 decimal places from kg_search_task
                # Ensure it's at least 0.01ms if the search ran (even with 0 results)
                if kg_ms == 0 and len(kg_results) == 0:
                    # Search ran but was very fast - show minimal time to indicate it executed
                    kg_ms = 0.01
                span.set_attribute("kg.enabled", True)
                span.set_attribute("kg.docs_retrieved", len(kg_results))
                logger.info(f"KG search executed: {len(kg_results)} results in {kg_ms}ms")
                if len(kg_results) > 0:
                    logger.info(f"KG results origin_tools: {[r.origin_tool for r in kg_results[:3]]}")
            else:
                span.set_attribute("kg.enabled", False)
                logger.info("KG search disabled")

            t_retrieve_end = time.perf_counter()
            # Store all retrieval timings (use float precision to avoid rounding to 0)
            stage_timings["vector_ms"] = round(vector_ms, 2) if vector_ms else 0  # Total vector search time
            stage_timings["embedding_ms"] = round(embedding_ms, 2) if embedding_ms else 0  # Embedding generation time
            stage_timings["vector_db_ms"] = round(vector_db_ms, 2) if vector_db_ms else 0  # Vector DB search time
            stage_timings["web_ms"] = round(web_ms, 2) if web_ms else (None if web_skipped else 0)
            stage_timings["kg_ms"] = kg_ms  # None if disabled, float if enabled
            stage_timings["retrieve_parallel_ms"] = int((t_retrieve_end - t_retrieve_start) * 1000)
            stage_timings["web_skipped"] = web_skipped
            stage_timings["web_reason"] = web_reason
            stage_timings["web_enabled"] = req.web_search_enabled
            stage_timings["kg_enabled"] = req.use_graph

            # Combine results
            all_results = vector_results + web_results + kg_results

            span.set_attribute("rag.retrieve.candidate_count", len(all_results))
            span.set_attribute("rag.retrieve.acl_filtered_count", vector_stats.get("acl_filtered_count", 0))

            # Build RetrievalLog (Schema B)
            retrieval_log = {
                "trace_id": str(trace_id),
                "request_id": request_id,
                "contract_version": CONTRACT_VERSION,
                "internal_queries": [{
                    "query": req.query,
                    "retriever": "vector_search",
                    "k_requested": req.top_k * 2,
                    "k_returned": len(vector_results),
                    "candidates_before_acl": vector_stats.get("candidates_before_acl", 0),
                    "candidates_after_acl": vector_stats.get("candidates_after_acl", 0)
                }],
                "web_queries": [{
                    "query": req.query,
                    "retriever": "web_search",
                    "k_returned": len(web_results)
                }],
                "kg_queries": [{
                    "query": req.query,
                    "retriever": "knowledge_graph",
                    "k_returned": len(kg_results)
                }] if req.use_graph else [],
                "total_retrieved": len(all_results)
            }

            # ===================================================================
            # STAGE 3: Recency Gate
            # ===================================================================
            t_recency_start = time.perf_counter()
            recency_result = evaluate_recency_gate(
                evidence_list=all_results,
                query=req.query,
                policy_requires_recency=False,  # Can be from req.filters - set to False to not block responses
                policy_min_primary_sources=2,
                window_hours=FRESHNESS_HOURS
            )

            # Log recency gate result for debugging
            logger.info(f"Recency gate: passed={recency_result['passed']}, "
                       f"primary_within_window={recency_result.get('primary_sources_within_window', 0)}, "
                       f"total_sources={len(all_results)}, "
                       f"query_is_temporal={recency_result.get('query_is_temporal', False)}, "
                       f"notes={recency_result.get('notes', '')}")
            t_recency_end = time.perf_counter()
            stage_timings["recency_gate_ms"] = round((t_recency_end - t_recency_start) * 1000, 2)  # Use float precision

            if not recency_result["passed"]:
                # Recency gate failure - emit Schema F and degrade
                guardrail_report = {
                    "trace_id": str(trace_id),
                    "request_id": request_id,
                    "contract_version": CONTRACT_VERSION,
                    "detections": [{
                        "severity": "high",
                        "details": recency_result["notes"],
                        "action_taken": "degraded"
                    }],
                    "service_errors": [],
                    "overall_safe": False
                }

                # Add stage timings for early exit
                stage_timings["total_ms"] = int((time.perf_counter() - t0) * 1000)

                return RagResponse(
                    answer="I apologize, but I don't have sufficiently recent information to answer this query with confidence.",
                    citations=[],
                    sources=[],  # Empty sources for E2E test compatibility
                    artifacts={
                        "retrieval_log": retrieval_log,
                        "guardrail_report": guardrail_report,
                        "recency": recency_result
                    },
                    metrics={
                        "latency_ms": (time.perf_counter() - t0) * 1000,
                        "stage_timings": stage_timings
                    },
                    security_status="degraded",
                    request_id=request_id,
                    trace_id=str(trace_id),
                    contract_version=CONTRACT_VERSION
                )

            # ===================================================================
            # STAGE 4: Rerank (weighted scoring by source type)
            # ===================================================================
            t_rerank_start = time.perf_counter()
            # Apply source-type weights to normalize scores across different retrieval methods
            # RAG/Research: 1.0x (trusted internal sources)
            # Web: 0.65x (external sources, less reliable)
            # KG: 0.9x (graph relationships, good but secondary)
            def get_weighted_score(result):
                base_score = result.score
                origin = result.origin_tool

                # Research sources (from research agent) - highest priority
                if origin == "research" or (hasattr(result, 'doc_id') and str(result.doc_id).startswith('research_')):
                    return base_score * 1.0
                # RAG sources (vector DB) - highest priority
                elif origin == "rag":
                    return base_score * 1.0
                # Knowledge Graph - high priority but secondary to RAG
                elif origin in ["knowledge_graph", "kg"]:
                    return base_score * 0.9
                # Web search - lower priority (external, less reliable)
                elif origin in ["web_search", "web"]:
                    return base_score * 0.65
                # Default - unknown sources get neutral weight
                else:
                    return base_score * 0.8

            # Sort by weighted score, then by original score as tiebreaker
            sorted_results = sorted(
                all_results,
                key=lambda x: (get_weighted_score(x), x.score),
                reverse=True
            )

            logger.info(f"Reranking: {len(all_results)} results with weighted scoring (RAG/Research: 1.0x, KG: 0.9x, Web: 0.65x)")

            # Log score distribution for debugging
            if sorted_results:
                top_5_origins = [r.origin_tool for r in sorted_results[:5]]
                top_5_scores = [f"{r.score:.3f}→{get_weighted_score(r):.3f}" for r in sorted_results[:5]]
                logger.info(f"Top 5 after weighting: {top_5_origins} | Scores: {top_5_scores}")

            # Take top results, ensuring web and KG results are included if available
            top_results = sorted_results[:req.top_k]

            # If we have web/KG results but they're not in top_results, add them
            # This ensures web/KG sources appear in citations
            # We'll prioritize them by inserting them at the beginning or ensuring they're included
            if len(web_results) > 0 or len(kg_results) > 0:
                # Get top web and KG results that aren't already in top_results
                top_result_ids = {(r.doc_id, r.chunk_id) for r in top_results}

                # Collect web and KG results to add
                results_to_add = []

                # Add top web results if not already included
                for web_result in web_results[:3]:  # Add up to 3 web results
                    if (web_result.doc_id, web_result.chunk_id) not in top_result_ids:
                        results_to_add.append(web_result)
                        top_result_ids.add((web_result.doc_id, web_result.chunk_id))

                # Add top KG results if not already included
                for kg_result in kg_results[:3]:  # Add up to 3 KG results
                    if (kg_result.doc_id, kg_result.chunk_id) not in top_result_ids:
                        results_to_add.append(kg_result)
                        top_result_ids.add((kg_result.doc_id, kg_result.chunk_id))

                # Add web/KG results to top_results, then re-sort
                # This ensures they're included but maintains weighted score-based ordering
                top_results.extend(results_to_add)

                # Re-sort using weighted scores to maintain proper ordering
                top_results = sorted(top_results, key=lambda x: (get_weighted_score(x), x.score), reverse=True)

                # Now take TOPN, but ensure we have at least some web/KG if they were requested
                # If we added web/KG results, make sure at least one of each type is in the final list
                if results_to_add:
                    logger.info(f"Added {len(results_to_add)} web/KG results to top_results before truncation")
                    # Separate by origin_tool (check both variants for compatibility)
                    web_in_top = [r for r in top_results[:req.top_k] if r.origin_tool in ["web_search", "web"]]
                    kg_in_top = [r for r in top_results[:req.top_k] if r.origin_tool in ["knowledge_graph", "kg"]]
                    logger.info(f"After re-sort, web_in_top: {len(web_in_top)}, kg_in_top: {len(kg_in_top)}")

                    # If web was requested but not in top, add at least one
                    if req.web_search_enabled and len(web_in_top) == 0 and len(web_results) > 0:
                        logger.info(f"Web requested but not in top_results[:top_k], forcing one in")
                        # Find a web result not in top_results
                        for web_result in web_results:
                            if (web_result.doc_id, web_result.chunk_id) not in {(r.doc_id, r.chunk_id) for r in top_results[:req.top_k]}:
                                top_results.insert(req.top_k - 1, web_result)  # Insert near the end
                                logger.info(f"Forced web result into top_results: {web_result.doc_id}, origin_tool={web_result.origin_tool}")
                                break

                    # If KG was requested but not in top, add at least one
                    if req.use_graph and len(kg_in_top) == 0 and len(kg_results) > 0:
                        logger.info(f"KG requested but not in top_results[:top_k], forcing one in")
                        # Find a KG result not in top_results
                        for kg_result in kg_results:
                            if (kg_result.doc_id, kg_result.chunk_id) not in {(r.doc_id, r.chunk_id) for r in top_results[:req.top_k]}:
                                top_results.insert(req.top_k - 1, kg_result)  # Insert near the end
                                logger.info(f"Forced KG result into top_results: {kg_result.doc_id}, origin_tool={kg_result.origin_tool}")
                                break

                # Final truncation to top_k
                top_results = top_results[:req.top_k]

            # Log final source type distribution
            source_counts = {}
            for r in top_results:
                origin = r.origin_tool
                if origin == "research" or (hasattr(r, 'doc_id') and str(r.doc_id).startswith('research_')):
                    source_counts['research'] = source_counts.get('research', 0) + 1
                elif origin == "rag":
                    source_counts['rag'] = source_counts.get('rag', 0) + 1
                elif origin in ["knowledge_graph", "kg"]:
                    source_counts['kg'] = source_counts.get('kg', 0) + 1
                elif origin in ["web_search", "web"]:
                    source_counts['web'] = source_counts.get('web', 0) + 1
                else:
                    source_counts['unknown'] = source_counts.get('unknown', 0) + 1

            logger.info(f"Final top_{req.top_k} source distribution: {source_counts}")

            # Log final state
            final_web = [r for r in top_results if r.origin_tool in ["web_search", "web"]]
            final_kg = [r for r in top_results if r.origin_tool in ["knowledge_graph", "kg"]]
            if req.web_search_enabled or req.use_graph:
                logger.info(f"Final top_results: {len(top_results)} results, web: {len(final_web)}, kg: {len(final_kg)}")

            t_rerank_end = time.perf_counter()
            stage_timings["rerank_ms"] = round((t_rerank_end - t_rerank_start) * 1000, 2)  # Use float precision
            span.set_attribute("rag.rerank.model", "score_sort")

            # Query expansion, BM25, and hybrid fusion timings (from search-service if enabled)
            stage_timings["query_expansion_ms"] = query_expansion_ms
            stage_timings["bm25_ms"] = bm25_ms
            stage_timings["hybrid_fusion_ms"] = hybrid_fusion_ms

            # ===================================================================
            # STAGE 5: Synthesis (LLM)
            # ===================================================================
            t_llm_start = time.perf_counter()

            # Log what's in top_results for debugging
            origin_tools_in_prompt = [r.origin_tool for r in top_results]
            logger.info(f"Top results for LLM prompt: {len(top_results)} results, origin_tools: {origin_tools_in_prompt}")
            logger.info(f"Web results available: {len(web_results)}, KG results available: {len(kg_results)}")

            # Check if we need to require web/KG citations (check both variants for compatibility)
            has_web_in_prompt = any(r.origin_tool in ["web_search", "web"] for r in top_results)
            has_kg_in_prompt = any(r.origin_tool in ["knowledge_graph", "kg"] for r in top_results)

            messages = build_prompt_messages(
                req.query,
                top_results,
                require_web_citation=req.web_search_enabled and has_web_in_prompt,
                require_kg_citation=req.use_graph and has_kg_in_prompt
            )

            # Estimate prompt token count (rough: ~4 chars per token)
            total_prompt_chars = sum(len(m.get("content", "")) for m in messages)
            estimated_prompt_tokens = total_prompt_chars // 4
            logger.info(f"Prompt size: ~{estimated_prompt_tokens} tokens (estimated from {total_prompt_chars} chars), context_window={req.context_window}, max_tokens={req.max_tokens}")
            if estimated_prompt_tokens > req.context_window * 0.8:
                logger.warning(f"⚠️  Prompt is ~{estimated_prompt_tokens} tokens, which is >80% of context_window={req.context_window}. Response may be truncated!")

            with tracer.start_as_current_span("synthesis_v1") as synth_span:
                # Use model and temperature from request if provided, otherwise use defaults
                llm_model = getattr(req, 'model', None) or "llama3.1:8b"
                llm_temperature = getattr(req, 'temperature', None) or 0.7
                
                llm_response = await llm.generate(
                    messages=messages,
                    model=llm_model,  # Use model from request (from preset config)
                    temperature=llm_temperature,  # Use temperature from request (from preset config)
                    max_tokens=req.max_tokens,  # Use max_tokens from request (from preset config)
                    context_window=req.context_window,  # Use context_window from request (from preset config)
                    use_mock=USE_MOCK_LLM
                )

                # OpenLLMetry semantic attributes
                synth_span.set_attribute("llm.model.name", llm_response.model)
                synth_span.set_attribute("llm.model.provider", llm_response.provider)
                synth_span.set_attribute("llm.temperature", llm_response.temperature)
                synth_span.set_attribute("llm.tokens.input", llm_response.tokens_in)
                synth_span.set_attribute("llm.tokens.output", llm_response.tokens_out)
                synth_span.set_attribute("llm.tokens.total", llm_response.tokens_total)
                synth_span.set_attribute("llm.cost.usd", llm_response.cost_usd)

                # Issue #5: Increment Prometheus token counters
                RAG_LLM_TOKENS.labels(model=llm_response.model, token_type='input').inc(llm_response.tokens_in)
                RAG_LLM_TOKENS.labels(model=llm_response.model, token_type='output').inc(llm_response.tokens_out)

            t_llm_end = time.perf_counter()
            stage_timings["llm_ms"] = round((t_llm_end - t_llm_start) * 1000, 2)  # Use float precision

            span.set_attribute("rag.synth.model", llm_response.model)

            # Extract citations
            citations = extract_citations(llm_response.text, top_results)

            # If web/KG were enabled but not cited, add at least one to citations
            # This ensures they appear in the response even if LLM didn't cite them
            cited_origin_tools = {c.get("origin_tool") for c in citations}
            logger.info(f"Cited origin_tools: {cited_origin_tools}")

            # Check if web/KG results exist in top_results or original arrays
            # Web results can have origin_tool="web" or "web_search" (check both for compatibility)
            web_in_top = any(r.origin_tool in ["web_search", "web"] for r in top_results)
            kg_in_top = any(r.origin_tool in ["knowledge_graph", "kg"] for r in top_results)
            logger.info(f"After LLM: web_in_top={web_in_top}, kg_in_top={kg_in_top}, web_enabled={req.web_search_enabled}, kg_enabled={req.use_graph}")

            if req.web_search_enabled and "web_search" not in cited_origin_tools and "web" not in cited_origin_tools:
                logger.info(f"Web search enabled but not cited, attempting to auto-add")
                # Try to find web result in top_results first
                web_result_to_add = None
                for result in top_results:
                    if result.origin_tool in ["web_search", "web"]:
                        web_result_to_add = result
                        break

                # If not in top_results, get from web_results array
                if not web_result_to_add and len(web_results) > 0:
                    web_result_to_add = web_results[0]
                    logger.info(f"Web result not in top_results, using from web_results array: {web_result_to_add.doc_id}, origin_tool={web_result_to_add.origin_tool}")

                if web_result_to_add:
                    citations.append({
                        "doc_id": web_result_to_add.doc_id,
                        "version": web_result_to_add.metadata.get("version", "1.0"),
                        "chunk_id": web_result_to_add.chunk_id,
                        "char_range": [0, len(web_result_to_add.content)],
                        "content": web_result_to_add.content,
                        "source_uri": web_result_to_add.metadata.get("source_uri", ""),
                        "origin_tool": web_result_to_add.origin_tool,
                        "score": getattr(web_result_to_add, 'score', 0.95),
                        "auto_added": True  # Mark as auto-added
                    })
                    logger.info(f"Auto-added web result to citations: {web_result_to_add.doc_id}, origin_tool={web_result_to_add.origin_tool}")
                else:
                    logger.warning(f"Web search enabled but no web results available to add to citations (web_results={len(web_results)}, top_results has web={web_in_top})")

            if req.use_graph and "knowledge_graph" not in cited_origin_tools and "kg" not in cited_origin_tools:
                logger.info(f"KG search enabled but not cited, attempting to auto-add")
                # Try to find KG result in top_results first
                kg_result_to_add = None
                for result in top_results:
                    if result.origin_tool in ["knowledge_graph", "kg"]:
                        kg_result_to_add = result
                        logger.info(f"Found KG result in top_results: {result.doc_id}, origin_tool={result.origin_tool}")
                        break

                # If not in top_results, get from kg_results array
                if not kg_result_to_add and len(kg_results) > 0:
                    kg_result_to_add = kg_results[0]
                    logger.info(f"KG result not in top_results, using from kg_results array: {kg_result_to_add.doc_id}, origin_tool={kg_result_to_add.origin_tool}")

                if kg_result_to_add:
                    citations.append({
                        "doc_id": kg_result_to_add.doc_id,
                        "version": kg_result_to_add.metadata.get("version", "1.0"),
                        "chunk_id": kg_result_to_add.chunk_id,
                        "char_range": [0, len(kg_result_to_add.content)],
                        "content": kg_result_to_add.content,
                        "source_uri": kg_result_to_add.metadata.get("source_uri", ""),
                        "origin_tool": kg_result_to_add.origin_tool,
                        "score": getattr(kg_result_to_add, 'score', 0.95),
                        "auto_added": True  # Mark as auto-added
                    })
                    logger.info(f"Auto-added KG result to citations: {kg_result_to_add.doc_id}, origin_tool={kg_result_to_add.origin_tool}")
                else:
                    logger.warning(f"KG search enabled but no KG results available to add to citations (kg_results={len(kg_results)}, top_results has KG={kg_in_top})")

            span.set_attribute("rag.citations.count", len(citations))
            span.set_attribute("rag.citations.unique_documents", len(set(c["doc_id"] for c in citations)))

            # Build EvidenceMap (Schema C)
            evidence_map = {
                "trace_id": str(trace_id),
                "request_id": request_id,
                "contract_version": CONTRACT_VERSION,
                "citations": citations,
                "provenance_immutable": True,  # origin_tool never modified
                "unique_docs": len(set(c["doc_id"] for c in citations))
            }

            # ===================================================================
            # STAGE 6: Guardrails
            # ===================================================================
            t_guardrails_start = time.perf_counter()
            guardrail_report = None
            security_status = "ok"

            if len(citations) == 0:
                # No citations - degraded response
                guardrail_report = {
                    "trace_id": str(trace_id),
                    "request_id": request_id,
                    "contract_version": CONTRACT_VERSION,
                    "detections": [{
                        "severity": "medium",
                        "details": "No citations found in generated answer",
                        "action_taken": "flagged"
                    }],
                    "service_errors": [],
                    "overall_safe": True  # Not unsafe, just low quality
                }
                security_status = "degraded"

            t_guardrails_end = time.perf_counter()
            stage_timings["guardrails_ms"] = round((t_guardrails_end - t_guardrails_start) * 1000, 2)  # Use float precision
            span.set_attribute("rag.guardrail.status", security_status)

            # ===================================================================
            # STAGE 7: A/B Evaluation (optional)
            # ===================================================================
            ab_eval = None
            if AB_TEST_ENABLED and req.ab_bucket:
                grader = ABGrader()
                grade_result = grader.grade(
                    query=req.query,
                    answer=llm_response.text,
                    evidence_list=top_results,
                    ungrounded_claims=[],  # Would be computed by NLI
                    recency_passed=recency_result["passed"],
                    recency_notes=recency_result["notes"],
                    total_retrieved=len(all_results),
                    total_deduped=len(all_results),  # Mock - no dedup yet
                    domains_filtered=[],
                    budget_use={},
                    budgets_applied={}
                )

                ab_eval = {
                    "trace_id": str(trace_id),
                    "request_id": request_id,
                    "contract_version": CONTRACT_VERSION,
                    "setting": req.ab_bucket,
                    "dimensions": grade_result.dimensions,
                    "overall_score": grade_result.overall_score,
                    "passed_dimensions": grade_result.passed_dimensions,
                    "failed_dimensions": grade_result.failed_dimensions
                }

                span.set_attribute("rag.abtest.bucket", req.ab_bucket)

            # ===================================================================
            # STAGE 8: Provenance Verification
            # ===================================================================
            # Verify origin_tool is present and immutable
            provenance_intact = all(
                hasattr(r, 'origin_tool') and r.origin_tool in ["rag", "web_search", "web", "research_agent"]
                for r in all_results
            )
            span.set_attribute("rag.provenance.origin_tool_immutable", provenance_intact)

            # ===================================================================
            # STAGE 9: Artifacts & Response
            # ===================================================================
            planner_artifact = {
                "trace_id": str(trace_id),
                "request_id": request_id,
                "contract_version": CONTRACT_VERSION,
                "route_decision": "hybrid",
                "route_reason": "Blended internal vector + web search",
                "budgets_applied": {
                    "max_web_queries": 1,
                    "max_internal_queries": req.top_k * 2
                }
            }

            artifacts = {
                "planner": planner_artifact,
                "retrieval_log": retrieval_log,
                "evidence_map": evidence_map,
                "recency": recency_result
            }

            if guardrail_report:
                artifacts["guardrail_report"] = guardrail_report
            if ab_eval:
                artifacts["ab_eval"] = ab_eval

            # Metrics
            latency_ms = (time.perf_counter() - t0) * 1000
            # Add total timing
            stage_timings["total_ms"] = int(latency_ms)

            metrics = {
                "latency_ms": round(latency_ms, 2),
                "tokens_in": llm_response.tokens_in,
                "tokens_out": llm_response.tokens_out,
                # Issue #5: Add frontend-compatible field names
                "prompt_tokens": llm_response.tokens_in,
                "completion_tokens": llm_response.tokens_out,
                "total_tokens": llm_response.tokens_total,
                "model": llm_response.model,
                # Ollama verbose metrics
                "ollama": {
                    "total_duration_ns": llm_response.total_duration_ns,
                    "total_duration_ms": round(llm_response.total_duration_ns / 1_000_000, 2) if llm_response.total_duration_ns else None,
                    "load_duration_ns": llm_response.load_duration_ns,
                    "load_duration_ms": round(llm_response.load_duration_ns / 1_000_000, 2) if llm_response.load_duration_ns else None,
                    "prompt_eval_count": llm_response.prompt_eval_count,
                    "prompt_eval_duration_ns": llm_response.prompt_eval_duration_ns,
                    "prompt_eval_duration_ms": round(llm_response.prompt_eval_duration_ns / 1_000_000, 2) if llm_response.prompt_eval_duration_ns else None,
                    "prompt_eval_rate": round(llm_response.prompt_eval_rate, 2) if llm_response.prompt_eval_rate else None,
                    "eval_count": llm_response.eval_count,
                    "eval_duration_ns": llm_response.eval_duration_ns,
                    "eval_duration_ms": round(llm_response.eval_duration_ns / 1_000_000, 2) if llm_response.eval_duration_ns else None,
                    "eval_rate": round(llm_response.eval_rate, 2) if llm_response.eval_rate else None,
                } if llm_response.total_duration_ns else None,
                "cost_usd": llm_response.cost_usd,
                "stage_timings": stage_timings  # Include stage breakdown
            }

            logger.info(f"RAG query completed: request_id={request_id}, latency_ms={latency_ms:.0f}, citations={len(citations)}")

            # Build sources array - Show ALL retrieved results for transparency
            # Users want to see all top_k results, not just what LLM cited
            sources = []

            # Add ALL top_results that went to the LLM (not just citations)
            cited_doc_ids = {c["doc_id"] for c in citations}
            for idx, result in enumerate(top_results):
                # Mark if this was cited by the LLM
                was_cited = result.doc_id in cited_doc_ids

                sources.append({
                    "doc_id": result.doc_id,
                    "chunk_id": getattr(result, 'chunk_id', f"{result.origin_tool}_{idx}"),
                    "score": result.score,
                    "origin_tool": result.origin_tool,
                    "source_type": "rag" if result.origin_tool == "rag" else ("web" if result.origin_tool in ["web_search", "web"] else result.origin_tool),
                    "content": result.content[:200] + "..." if len(result.content) > 200 else result.content,
                    "title": getattr(result, 'title', ''),
                    "url": getattr(result, 'source_uri', ''),
                    "cited": was_cited,  # Mark which ones LLM actually used
                    "rank": idx + 1
                })

            # Log for debugging
            logger.info(f"Built {len(sources)} sources from {len(top_results)} top_results, {len(citations)} citations")

            # Add mock research sources if enabled (for UI-004 demonstration)
            # In production, this would come from actual research agent
            if req.enable_research and len(sources) > 0:
                # Add 1-2 mock research sources for demonstration
                sources.append({
                    "doc_id": "research_demo_1",
                    "chunk_id": "research_1",
                    "score": 0.85,
                    "origin_tool": "research",
                    "source_type": "research",
                    "title": "Research Agent Finding",
                    "url": "https://example.com/research",
                    "snippet": "This is a demonstration research source that would come from the research agent when fully implemented.",
                    "rank": 1
                })

            response = RagResponse(
                answer=llm_response.text,
                citations=citations,
                sources=sources,  # Add sources field for E2E test compatibility
                artifacts=artifacts,
                metrics=metrics,
                security_status=security_status,
                request_id=request_id,
                trace_id=str(trace_id),
                contract_version=CONTRACT_VERSION
            )

            # Store response in Redis for persistent retrieval after page refresh
            # This ensures responses are available even if user navigates away
            try:
                redis_client = get_redis_client()
                if redis_client:
                    # Serialize response to JSON
                    response_dict = response.model_dump(mode='json')
                    response_json = json.dumps(response_dict)
                    # Store with TTL
                    redis_client.setex(
                        f"rag:response:{request_id}",
                        CACHE_TTL,
                        response_json
                    )
                    logger.info(f"✅ Stored response in Redis: request_id={request_id}, TTL={CACHE_TTL}s")
                else:
                    # Fallback to in-memory cache
                    _response_cache_fallback[request_id] = (response, time.time())
                    logger.info(f"⚠️  Stored response in memory (Redis unavailable): request_id={request_id}")
            except Exception as e:
                logger.error(f"Failed to store response in cache: {e}", exc_info=True)
                # Fallback to in-memory cache
                _response_cache_fallback[request_id] = (response, time.time())

            return response

        except Exception as e:
            logger.error(f"RAG query error: {e}", exc_info=True)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)

            raise HTTPException(
                status_code=500,
                detail={
                    "error": "INTERNAL_ERROR",
                    "message": "An error occurred processing your request",
                    "request_id": request_id if 'request_id' in locals() else None
                }
            )


@router.get("/response/{request_id}", response_model=RagResponse)
async def get_response(request_id: str):
    """
    Retrieve a cached response by request_id.
    Allows frontend to retrieve responses after page refresh or navigation.
    Checks Redis first, then falls back to in-memory cache.
    """
    try:
        # Try Redis first
        redis_client = get_redis_client()
        if redis_client:
            response_json = redis_client.get(f"rag:response:{request_id}")
            if response_json:
                response_dict = json.loads(response_json)
                response = RagResponse(**response_dict)
                ttl = redis_client.ttl(f"rag:response:{request_id}")
                logger.info(f"✅ Retrieved response from Redis: request_id={request_id}, TTL={ttl}s")
                return response

        # Fallback to in-memory cache
        if request_id in _response_cache_fallback:
            response, timestamp = _response_cache_fallback[request_id]
            now = time.time()
            age = now - timestamp

            # Check if expired
            if age > CACHE_TTL:
                del _response_cache_fallback[request_id]
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Response for request_id {request_id} has expired (TTL: {CACHE_TTL}s)"
                )

            logger.info(f"Retrieved response from memory: request_id={request_id}, age={age:.1f}s")
            return response

    except Exception as e:
        logger.error(f"Error retrieving response: {e}", exc_info=True)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Response for request_id {request_id} not found or expired"
    )

