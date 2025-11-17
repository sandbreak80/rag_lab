"""
Pydantic models for RAG API v1
"""
from pydantic import BaseModel, Field
from typing import Any, Literal
from uuid import uuid4


class RagQuery(BaseModel):
    """Request model for /v1/rag/query"""
    query: str = Field(..., description="User's natural language query")
    user_id: str = Field(..., description="User identifier for AuthZ")
    groups: list[str] = Field(default_factory=list, description="User's group memberships")
    dept: str | None = Field(None, description="User's department")
    filters: dict[str, Any] = Field(default_factory=dict, description="Additional query filters")
    top_k: int = Field(8, ge=1, le=50, description="Number of results to return")
    ab_bucket: Literal["A", "B"] | None = Field(None, description="A/B test bucket assignment")
    request_id: str | None = Field(None, description="Client-provided request ID for correlation")
    trace_id: str | None = Field(None, description="Distributed trace ID")
    contract_version: str | None = Field(None, description="Expected contract version")
    enable_research: bool = Field(False, description="Enable research agent sources (UI-004)")
    web_search_enabled: bool = Field(True, description="Enable web search (Issue #4)")
    web_search_docs: int = Field(20, ge=1, le=50, description="Number of web search results to retrieve")
    use_graph: bool = Field(False, description="Enable knowledge graph search")
    use_query_expansion: bool = Field(False, description="Enable query expansion")
    use_bm25: bool = Field(False, description="Enable BM25 keyword search")
    use_hybrid: bool = Field(False, description="Enable hybrid search (vector + BM25 fusion)")

    class Config:
        schema_extra = {
            "example": {
                "query": "What is the refund policy for enterprise customers?",
                "user_id": "user_123",
                "groups": ["sales", "tier2_support"],
                "dept": "customer_success",
                "top_k": 8
            }
        }


class RagResponse(BaseModel):
    """Response model for /v1/rag/query"""
    answer: str = Field(..., description="Generated answer text")
    citations: list[dict[str, Any]] = Field(
        ...,
        description="Sentence-level citations with (doc_id, version, chunk_id, char_range, source_uri)"
    )
    sources: list[dict[str, Any]] | None = Field(
        None,
        description="Simplified source list for E2E test compatibility (doc_id, score, origin_tool)"
    )
    artifacts: dict[str, Any] = Field(
        ...,
        description="Schemas A-G serialized (A=planner, B=retrieval_log, C=evidence_map, etc.)"
    )
    metrics: dict[str, Any] = Field(
        ...,
        description="Pipeline metrics (latency_ms, tokens_in, tokens_out, model, cost_usd)"
    )
    security_status: Literal["ok", "degraded", "blocked"] = Field(
        ...,
        description="Security/guardrail status"
    )
    request_id: str = Field(..., description="Request correlation ID")
    trace_id: str = Field(..., description="Distributed trace ID")
    contract_version: str = Field(..., description="API contract version")

    class Config:
        schema_extra = {
            "example": {
                "answer": "Our enterprise refund policy allows...",
                "citations": [
                    {
                        "doc_id": "policy_v2.3",
                        "version": "2.3",
                        "chunk_id": "chunk_42",
                        "char_range": [120, 456],
                        "source_uri": "https://docs.example.com/policies/refunds"
                    }
                ],
                "artifacts": {
                    "planner": {"route": "hybrid", "budgets_applied": {}},
                    "retrieval_log": {"total_retrieved": 15, "acl_filtered_count": 3},
                    "evidence_map": {"citations_count": 1}
                },
                "metrics": {
                    "latency_ms": 1234.5,
                    "tokens_in": 256,
                    "tokens_out": 128,
                    "model": "llama3.1:8b",
                    "cost_usd": 0.0001
                },
                "security_status": "ok",
                "request_id": "req_abc123",
                "trace_id": "trace_xyz789",
                "contract_version": "1.0.0"
            }
        }

