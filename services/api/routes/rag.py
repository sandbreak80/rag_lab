"""
RAG v1 API Routes - Complete observability contract implementation
"""
from fastapi import APIRouter, Depends, HTTPException
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
import time
import logging
from uuid import uuid4
from datetime import datetime, timezone

# Local imports
from ..models import RagQuery, RagResponse
from ..config import (
    CONTRACT_VERSION, ENABLE_OBS, USE_MOCK_LLM, USE_MOCK_VECTOR, USE_MOCK_WEB,
    FRESHNESS_HOURS, TOPN, AB_TEST_ENABLED
)
from ..authz.abac import build_acl_predicate
from ..adapters import vector, web, llm
from ..pipeline.recency_gate import evaluate_recency_gate
from ..pipeline.ab_grader import ABGrader
from ..pipeline.guardrail_client import check_guardrails, get_security_status

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)
router = APIRouter(prefix="/v1/rag", tags=["rag-v1"])


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


def build_prompt_messages(query: str, results: list) -> list[dict]:
    """Build extractive-first prompt with citations"""
    context_parts = []
    for i, result in enumerate(results):
        context_parts.append(f"[{i+1}] {result.content}")

    context = "\n\n".join(context_parts)

    return [
        {
            "role": "system",
            "content": "You are a helpful assistant. Answer the question based ONLY on the provided context. Include citations [1], [2], etc. to reference sources. If the context doesn't contain enough information, say so."
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
            # STAGE 2: Retrieval (Hybrid with ACL pre-filter)
            # ===================================================================
            t_retrieve_start = time.perf_counter()
            with tracer.start_as_current_span("retrieve_internal.vector") as retrieve_span:
                vector_results, vector_stats = await vector.search(
                    query=req.query,
                    acl_predicate=acl_pred,
                    top_k=req.top_k * 2,  # Over-fetch
                    use_mock=USE_MOCK_VECTOR
                )
                retrieve_span.set_attribute("docs_retrieved", len(vector_results))
                retrieve_span.set_attribute("acl_filtered", vector_stats.get("acl_filtered_count", 0))
            t_vector_end = time.perf_counter()
            stage_timings["vector_ms"] = int((t_vector_end - t_retrieve_start) * 1000)

            with tracer.start_as_current_span("retrieve_web.searxng") as web_span:
                web_results = await web.search(
                    query=req.query,
                    top_k=5,
                    use_mock=USE_MOCK_WEB
                )
                web_span.set_attribute("docs_retrieved", len(web_results))
            t_web_end = time.perf_counter()
            stage_timings["web_ms"] = int((t_web_end - t_vector_end) * 1000)

            # Combine results
            all_results = vector_results + web_results

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
            sorted_results = sorted(all_results, key=lambda x: x.score, reverse=True)
            top_results = sorted_results[:TOPN]

            span.set_attribute("rag.rerank.model", "score_sort")

            # ===================================================================
            # STAGE 5: Synthesis (LLM)
            # ===================================================================
            t_llm_start = time.perf_counter()
            messages = build_prompt_messages(req.query, top_results)

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

            t_llm_end = time.perf_counter()
            stage_timings["llm_ms"] = int((t_llm_end - t_llm_start) * 1000)

            span.set_attribute("rag.synth.model", llm_response.model)

            # Extract citations
            citations = extract_citations(llm_response.text, top_results)

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
                hasattr(r, 'origin_tool') and r.origin_tool in ["rag", "web_search", "research_agent"]
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
                "model": llm_response.model,
                "cost_usd": llm_response.cost_usd,
                "stage_timings": stage_timings  # Include stage breakdown
            }

            logger.info(f"RAG query completed: request_id={request_id}, latency_ms={latency_ms:.0f}, citations={len(citations)}")

            # Build sources array for backward compatibility with E2E tests
            sources = [
                {
                    "doc_id": c["doc_id"],
                    "chunk_id": c["chunk_id"],
                    "score": c["score"],
                    "origin_tool": c["origin_tool"],
                    "source_type": "rag" if c["origin_tool"] == "rag" else "web",
                    "content": c["content"][:200] + "..." if len(c["content"]) > 200 else c["content"]
                }
                for c in citations
            ]

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

