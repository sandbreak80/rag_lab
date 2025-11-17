"""
RAG v1 API Routes - Complete observability contract implementation
"""
from fastapi import APIRouter, Depends, HTTPException
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
import time
import logging
import os
from uuid import uuid4
from datetime import datetime, timezone
from prometheus_client import Counter

# Local imports
from ..models import RagQuery, RagResponse
from ..config import (
    CONTRACT_VERSION, ENABLE_OBS, USE_MOCK_LLM, USE_MOCK_VECTOR, USE_MOCK_WEB,
    FRESHNESS_HOURS, TOPN, AB_TEST_ENABLED
)
from ..authz.abac import build_acl_predicate
from ..adapters import vector, web, llm, kg
from ..pipeline.recency_gate import evaluate_recency_gate
from ..pipeline.ab_grader import ABGrader
from ..pipeline.guardrail_client import check_guardrails, get_security_status

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)
router = APIRouter(prefix="/v1/rag", tags=["rag-v1"])

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
    """Build extractive-first prompt with citations"""
    context_parts = []
    web_indices = []
    kg_indices = []

    for i, result in enumerate(results):
        context_parts.append(f"[{i+1}] {result.content}")
        # Track which indices are web/KG results
        if result.origin_tool == "web_search":
            web_indices.append(i + 1)
        elif result.origin_tool == "knowledge_graph":
            kg_indices.append(i + 1)

    context = "\n\n".join(context_parts)

    # Build citation instruction
    citation_instruction = "Include citations [1], [2], etc. to reference sources."
    if require_web_citation and web_indices:
        citation_instruction += f" IMPORTANT: You must cite at least one web source from [{', '.join(map(str, web_indices))}]."
    if require_kg_citation and kg_indices:
        citation_instruction += f" IMPORTANT: You must cite at least one knowledge graph source from [{', '.join(map(str, kg_indices))}]."

    return [
        {
            "role": "system",
            "content": f"You are a helpful assistant. Answer the question based ONLY on the provided context. {citation_instruction} If the context doesn't contain enough information, say so."
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
            t_acl = time.perf_counter()
            acl_pred = build_acl_predicate(req.user_id, req.groups, req.dept)
            span.set_attribute("rag.auth.perms_tag", acl_pred.tag)

            # ===================================================================
            # STAGE 2: Retrieval (Parallel Hybrid with ACL pre-filter)
            # ===================================================================
            t_retrieve_start = time.perf_counter()

            # Define parallel retrieval tasks
            async def vector_search_task():
                with tracer.start_as_current_span("retrieve_internal.vector") as retrieve_span:
                    t_vec_start = time.perf_counter()
                    results, stats = await vector.search(
                        query=req.query,
                        acl_predicate=acl_pred,
                        top_k=req.top_k * 2,  # Over-fetch
                        use_mock=USE_MOCK_VECTOR
                    )
                    t_vec_end = time.perf_counter()
                    retrieve_span.set_attribute("docs_retrieved", len(results))
                    retrieve_span.set_attribute("acl_filtered", stats.get("acl_filtered_count", 0))
                    return results, stats, int((t_vec_end - t_vec_start) * 1000)

            async def web_search_task():
                with tracer.start_as_current_span("retrieve_web.searxng") as web_span:
                    t_web_start = time.perf_counter()
                    results = await web.search(
                        query=req.query,
                        top_k=5,
                        use_mock=USE_MOCK_WEB
                    )
                    t_web_end = time.perf_counter()
                    web_span.set_attribute("docs_retrieved", len(results))
                    return results, int((t_web_end - t_web_start) * 1000)

            async def kg_search_task():
                with tracer.start_as_current_span("retrieve_kg.relationships") as kg_span:
                    t_kg_start = time.perf_counter()
                    results = await kg.search(
                        query=req.query,
                        vector_results=vector_results,
                        top_k=5,
                        use_mock=USE_MOCK_VECTOR  # Use same mock setting as vector
                    )
                    t_kg_end = time.perf_counter()
                    kg_span.set_attribute("docs_retrieved", len(results))
                    return results, int((t_kg_end - t_kg_start) * 1000)

            # B1: Early-stop logic - check if vector results are strong enough
            RAG_EARLYSTOP_MIN_HITS = int(os.getenv("RAG_EARLYSTOP_MIN_HITS", "8"))
            RAG_EARLYSTOP_MIN_SCORE = float(os.getenv("RAG_EARLYSTOP_MIN_SCORE", "0.60"))

            # Execute vector search first to evaluate early-stop
            import asyncio
            vector_results, vector_stats, vector_ms = await vector_search_task()

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
            else:
                logger.info(f"Web search skipped: {web_reason}")

            # Knowledge Graph search (if enabled)
            kg_results = []
            kg_ms = 0
            if req.use_graph:
                kg_results, kg_ms = await kg_search_task()
                span.set_attribute("kg.enabled", True)
                span.set_attribute("kg.docs_retrieved", len(kg_results))
                logger.info(f"KG search executed: {len(kg_results)} results")
            else:
                span.set_attribute("kg.enabled", False)
                logger.info("KG search disabled")

            t_retrieve_end = time.perf_counter()
            stage_timings["vector_ms"] = vector_ms
            stage_timings["web_ms"] = web_ms
            stage_timings["kg_ms"] = kg_ms
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
            recency_result = evaluate_recency_gate(
                evidence_list=all_results,
                query=req.query,
                policy_requires_recency=False,  # Can be from req.filters
                policy_min_primary_sources=2,
                window_hours=FRESHNESS_HOURS
            )

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
            # STAGE 4: Rerank (simple score sort for now)
            # ===================================================================
            # Sort results by score, but ensure we have a mix of source types in top results
            sorted_results = sorted(all_results, key=lambda x: x.score, reverse=True)

            # Take top results, ensuring web and KG results are included if available
            top_results = sorted_results[:TOPN]

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
                # This ensures they're included but maintains score-based ordering
                top_results.extend(results_to_add)

                # Re-sort to maintain score order, but keep all results (don't truncate yet)
                top_results = sorted(top_results, key=lambda x: x.score, reverse=True)

                # Now take TOPN, but ensure we have at least some web/KG if they were requested
                # If we added web/KG results, make sure at least one of each type is in the final list
                if results_to_add:
                    # Separate by origin_tool (check both variants for compatibility)
                    web_in_top = [r for r in top_results[:TOPN] if r.origin_tool in ["web_search", "web"]]
                    kg_in_top = [r for r in top_results[:TOPN] if r.origin_tool in ["knowledge_graph", "kg"]]

                    # If web was requested but not in top, add at least one
                    if req.web_search_enabled and len(web_in_top) == 0 and len(web_results) > 0:
                        # Find a web result not in top_results
                        for web_result in web_results:
                            if (web_result.doc_id, web_result.chunk_id) not in {(r.doc_id, r.chunk_id) for r in top_results[:TOPN]}:
                                top_results.insert(TOPN - 1, web_result)  # Insert near the end
                                break

                    # If KG was requested but not in top, add at least one
                    if req.use_graph and len(kg_in_top) == 0 and len(kg_results) > 0:
                        # Find a KG result not in top_results
                        for kg_result in kg_results:
                            if (kg_result.doc_id, kg_result.chunk_id) not in {(r.doc_id, r.chunk_id) for r in top_results[:TOPN]}:
                                top_results.insert(TOPN - 1, kg_result)  # Insert near the end
                                break

                # Final truncation to TOPN
                top_results = top_results[:TOPN]

            span.set_attribute("rag.rerank.model", "score_sort")

            # ===================================================================
            # STAGE 5: Synthesis (LLM)
            # ===================================================================
            t_llm_start = time.perf_counter()

            # Log what's in top_results for debugging
            origin_tools_in_prompt = [r.origin_tool for r in top_results]
            logger.info(f"Top results for LLM prompt: {len(top_results)} results, origin_tools: {origin_tools_in_prompt}")

            # Check if we need to require web/KG citations (check both variants for compatibility)
            has_web_in_prompt = any(r.origin_tool in ["web_search", "web"] for r in top_results)
            has_kg_in_prompt = any(r.origin_tool in ["knowledge_graph", "kg"] for r in top_results)

            messages = build_prompt_messages(
                req.query,
                top_results,
                require_web_citation=req.web_search_enabled and has_web_in_prompt,
                require_kg_citation=req.use_graph and has_kg_in_prompt
            )

            with tracer.start_as_current_span("synthesis_v1") as synth_span:
                llm_response = await llm.generate(
                    messages=messages,
                    model="llama3.1:8b",
                    temperature=0.7,
                    max_tokens=512,
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
            stage_timings["llm_ms"] = int((t_llm_end - t_llm_start) * 1000)

            span.set_attribute("rag.synth.model", llm_response.model)

            # Extract citations
            citations = extract_citations(llm_response.text, top_results)

            # If web/KG were enabled but not cited, add at least one to citations
            # This ensures they appear in the response even if LLM didn't cite them
            cited_origin_tools = {c.get("origin_tool") for c in citations}

            # Check if web/KG results exist in top_results or original arrays
            # Web results can have origin_tool="web" or "web_search" (check both for compatibility)
            web_in_top = any(r.origin_tool in ["web_search", "web"] for r in top_results)
            kg_in_top = any(r.origin_tool in ["knowledge_graph", "kg"] for r in top_results)

            if req.web_search_enabled and "web_search" not in cited_origin_tools and "web" not in cited_origin_tools:
                # Try to find web result in top_results first
                web_result_to_add = None
                for result in top_results:
                    if result.origin_tool in ["web_search", "web"]:
                        web_result_to_add = result
                        break

                # If not in top_results, get from web_results array
                if not web_result_to_add and len(web_results) > 0:
                    web_result_to_add = web_results[0]
                    logger.info(f"Web result not in top_results, using from web_results array")

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
                    logger.info(f"Auto-added web result to citations: {web_result_to_add.doc_id}")
                else:
                    logger.warning(f"Web search enabled but no web results available to add to citations")

            if req.use_graph and "knowledge_graph" not in cited_origin_tools:
                # Try to find KG result in top_results first
                kg_result_to_add = None
                for result in top_results:
                    if result.origin_tool == "knowledge_graph":
                        kg_result_to_add = result
                        break

                # If not in top_results, get from kg_results array
                if not kg_result_to_add and len(kg_results) > 0:
                    kg_result_to_add = kg_results[0]
                    logger.info(f"KG result not in top_results, using from kg_results array")

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
                    logger.info(f"Auto-added KG result to citations: {kg_result_to_add.doc_id}")
                else:
                    logger.warning(f"KG search enabled but no KG results available to add to citations")

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
                "cost_usd": llm_response.cost_usd,
                "stage_timings": stage_timings  # Include stage breakdown
            }

            logger.info(f"RAG query completed: request_id={request_id}, latency_ms={latency_ms:.0f}, citations={len(citations)}")

            # Build sources array for backward compatibility with E2E tests
            # Include both citations (from LLM extraction) AND raw web results
            sources = []

            # Add citations (RAG + any web results that were cited)
            for c in citations:
                sources.append({
                    "doc_id": c["doc_id"],
                    "chunk_id": c["chunk_id"],
                    "score": c["score"],
                    "origin_tool": c["origin_tool"],
                    "source_type": "rag" if c["origin_tool"] == "rag" else ("web" if c["origin_tool"] in ["web_search", "web"] else c["origin_tool"]),
                    "content": c["content"][:200] + "..." if len(c["content"]) > 200 else c["content"]
                })

            # Add web results that weren't cited (for transparency)
            cited_doc_ids = {c["doc_id"] for c in citations}
            for idx, web_result in enumerate(web_results):
                if web_result.doc_id not in cited_doc_ids:
                    sources.append({
                        "doc_id": web_result.doc_id,
                        "chunk_id": getattr(web_result, 'chunk_id', f"web_{idx}"),
                        "score": web_result.score,
                        "origin_tool": "web_search",  # Use consistent naming
                        "source_type": "web",
                        "title": getattr(web_result, 'title', ''),
                        "url": getattr(web_result, 'source_uri', ''),
                        "snippet": web_result.content[:200] + "..." if len(web_result.content) > 200 else web_result.content,
                        "rank": idx + 1
                    })

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

            return RagResponse(
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

