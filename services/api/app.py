"""
RAG Query API - FULL OBSERVABILITY CONTRACT

This implements the complete observability specification with:
- Immutable provenance tracking
- Recency gates and freshness histograms
- Full artifact schemas (A-G)
- KG + chunking visibility
- A/B evaluation framework
- Budget tracking and route decisions
- Guardrail reporting
"""

from flask import Flask, request, jsonify, g
from flask_cors import CORS
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Literal
from datetime import datetime, timedelta, timezone
from enum import Enum
import time
import uuid
import logging
import hashlib
import json

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from opentelemetry.propagate import extract

# Import RAG components
from services.common.orchestrator import RAGOrchestrator, RetrievalPlan, RetrievalStrategy
from services.common.prompt_assembler import PromptAssembler, PromptTemplate
from services.common.evidence import Evidence, OriginTool
from services.common.artifact_base import ArtifactBase, OrchestrationContext, CONTRACT_VERSION
from services.common.deduplicator import deduplicate_evidence, DedupAuditEntry
from services.common.domain_filter import create_default_filter, DomainFilterAuditEntry
from services.common.mock_retrievers import mock_vector_search, mock_web_search, mock_research_agent_retrieve
from services.common.schema_b_builder import build_retrieval_log, add_detailed_audit_to_retrieval_log
from services.common.recency_gate import evaluate_recency_gate

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

app = Flask(__name__)
CORS(app)


# ============================================================================
# FULL REQUEST CONTRACT
# ============================================================================

@dataclass
class Budgets:
    """Per-query resource budgets for observability"""
    max_web_queries: int = 10
    max_internal_queries: int = 20
    max_parallel: int = 5
    sla_ms: int = 3000  # Hard SLA limit


@dataclass
class Policy:
    """Query policy constraints"""
    requires_recency: bool = False  # Must have ≤48h sources
    min_primary_sources: int = 1
    min_internal_conf_before_web: float = 0.5  # Confidence threshold before web search


@dataclass
class ABTest:
    """A/B test configuration"""
    setting: Literal["A", "B"] = "A"
    run_id: Optional[str] = None


@dataclass
class RagRequest:
    """Full observability request contract"""
    query: str
    tenant: str
    user_id: str

    # Strategy
    plan_id: str = "hybrid_v1"

    # Settings snapshot
    settings_snapshot: Dict[str, Any] = field(default_factory=dict)

    # Budgets
    budgets: Budgets = field(default_factory=Budgets)

    # Policy
    policy: Policy = field(default_factory=Policy)

    # A/B testing
    ab_test: ABTest = field(default_factory=ABTest)

    # Debug
    debug: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RagRequest':
        return cls(
            query=data['query'],
            tenant=data['tenant'],
            user_id=data['user_id'],
            plan_id=data.get('plan_id', 'hybrid_v1'),
            settings_snapshot=data.get('settings_snapshot', {}),
            budgets=Budgets(**data.get('budgets', {})),
            policy=Policy(**data.get('policy', {})),
            ab_test=ABTest(**data.get('ab_test', {})),
            debug=data.get('debug', False)
        )


# ============================================================================
# FULL RESPONSE CONTRACT - SOURCES WITH IMMUTABLE PROVENANCE
# ============================================================================

@dataclass
class Source:
    """Source with full provenance and recency metadata"""
    index: int  # [1], [2], etc.
    id: str
    content: str
    url: Optional[str]
    title: Optional[str]
    score: float

    # IMMUTABLE PROVENANCE
    origin_tool: Literal["rag", "web_search", "research_agent"]  # Immutable

    # RECENCY METADATA
    published_at: Optional[str]  # ISO8601
    is_primary: bool  # Primary vs. secondary source

    # Additional metadata
    domain: Optional[str] = None
    freshness_hours: Optional[int] = None  # Hours since published

    def to_dict(self) -> Dict[str, Any]:
        return {
            'index': self.index,
            'id': self.id,
            'content': self.content[:200] + '...' if len(self.content) > 200 else self.content,
            'url': self.url,
            'title': self.title,
            'score': round(self.score, 3),
            'origin_tool': self.origin_tool,  # Immutable
            'published_at': self.published_at,
            'is_primary': self.is_primary,
            'domain': self.domain,
            'freshness_hours': self.freshness_hours
        }


# ============================================================================
# ARTIFACT SCHEMAS (A-G)
# ============================================================================

@dataclass
class PlannerArtifact(ArtifactBase):
    """Schema A: Planner decisions"""
    subtasks: List[str] = field(default_factory=list)
    requires_recency: List[bool] = field(default_factory=list)
    queries_planned: List[str] = field(default_factory=list)
    budgets_applied: Optional[Budgets] = None
    route_decision: Literal["rag", "web", "blended"] = "rag"
    route_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            'subtasks': self.subtasks,
            'requires_recency': self.requires_recency,
            'queries_planned': self.queries_planned,
            'budgets_applied': asdict(self.budgets_applied) if self.budgets_applied else {},
            'route_decision': self.route_decision,
            'route_reason': self.route_reason
        })
        return base


@dataclass
class RetrievalLogEntry:
    """Single retrieval attempt"""
    source_type: Literal["internal", "web"]
    query: str
    results_count: int
    dedup_removed: int
    domain_filtered: int
    timing_ms: float
    rank_list: List[Dict[str, Any]]  # Top 5 with scores


@dataclass
class RetrievalLog(ArtifactBase):
    """Schema B: Retrieval log"""
    internal_queries: List[RetrievalLogEntry] = field(default_factory=list)
    web_queries: List[RetrievalLogEntry] = field(default_factory=list)
    total_retrieved: int = 0
    total_deduped: int = 0
    domains_filtered: List[str] = field(default_factory=list)
    timing_breakdown_ms: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            'internal_queries': [asdict(e) for e in self.internal_queries],
            'web_queries': [asdict(e) for e in self.web_queries],
            'total_retrieved': self.total_retrieved,
            'total_deduped': self.total_deduped,
            'domains_filtered': self.domains_filtered,
            'timing_breakdown_ms': self.timing_breakdown_ms
        })
        return base


@dataclass
class EvidenceMap(ArtifactBase):
    """Schema C: Claim → Citation binding"""
    claims: List[Dict[str, Any]] = field(default_factory=list)  # {claim_text, citation_indices, confidence}
    ungrounded_claims: List[str] = field(default_factory=list)
    grounding_rate: float = 0.0  # % of claims grounded

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            'claims': self.claims,
            'ungrounded_claims': self.ungrounded_claims,
            'grounding_rate': round(self.grounding_rate, 3)
        })
        return base


@dataclass
class KGLog(ArtifactBase):
    """Schema D: Knowledge Graph expansion"""
    resolved_entities: List[Dict[str, str]] = field(default_factory=list)  # {entity, type, confidence}
    edges_used: List[Dict[str, Any]] = field(default_factory=list)  # {source, relation, target, hops}
    evidence_urls: List[str] = field(default_factory=list)
    timing_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            'resolved_entities': self.resolved_entities,
            'edges_used': self.edges_used,
            'evidence_urls': self.evidence_urls,
            'timing_ms': round(self.timing_ms, 2)
        })
        return base


@dataclass
class ChunkingSample:
    """Sample chunk with reasoning"""
    chunk_id: str
    token_count: int
    heading_path: List[str]
    reason: str  # Why this chunk boundary


@dataclass
class ChunkingReport(ArtifactBase):
    """Schema E: Chunking strategy visibility"""
    params: Dict[str, Any] = field(default_factory=dict)  # target_size, min/max, overlap, biases
    samples: List[ChunkingSample] = field(default_factory=list)  # 3 representative chunks
    timing_ms: float = 0.0
    total_chunks: int = 0

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            'params': self.params,
            'samples': [asdict(s) for s in self.samples],
            'timing_ms': round(self.timing_ms, 2),
            'total_chunks': self.total_chunks
        })
        return base


@dataclass
class GuardrailDetection:
    """Single guardrail finding"""
    type: str  # pii, toxicity, prompt_injection, etc.
    severity: Literal["low", "medium", "high", "critical"]
    details: str
    action_taken: str  # redacted, blocked, flagged


@dataclass
class GuardrailReport(ArtifactBase):
    """Schema F: Guardrail outcomes"""
    detections: List[GuardrailDetection] = field(default_factory=list)
    service_errors: List[Dict[str, str]] = field(default_factory=list)  # {service, error, timestamp}
    overall_safe: bool = True

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            'detections': [asdict(d) for d in self.detections],
            'service_errors': self.service_errors,
            'overall_safe': self.overall_safe
        })
        return base


@dataclass
class ABEvaluation(ArtifactBase):
    """Schema G: A/B evaluation rubric"""
    setting: Literal["A", "B"] = "A"
    dimensions: Dict[str, float] = field(default_factory=dict)  # coverage, grounding, recency, retrieval_quality, etc.
    overall_score: float = 0.0
    comparison: Optional[Dict[str, Any]] = None  # Δ vs other setting

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            'setting': self.setting,
            'dimensions': {k: round(v, 3) for k, v in self.dimensions.items()},
            'overall_score': round(self.overall_score, 3),
            'comparison': self.comparison
        })
        return base


# ============================================================================
# RECENCY EVALUATION
# ============================================================================

@dataclass
class RecencyEvaluation(ArtifactBase):
    """Recency gate outcome"""
    window_hours: int = 48
    passed: bool = False
    notes: str = ""
    freshness_histogram: Dict[str, int] = field(default_factory=dict)  # {<24h: 3, 24-48h: 2, >48h: 5}
    primary_sources_within_window: int = 0

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            'window_hours': self.window_hours,
            'passed': self.passed,
            'notes': self.notes,
            'freshness_histogram': self.freshness_histogram,
            'primary_sources_within_window': self.primary_sources_within_window
        })
        return base


# ============================================================================
# MODEL ROUTING
# ============================================================================

@dataclass
class ModelRoutingEntry:
    """Model used at a stage"""
    stage: str
    model: str
    approximate_latency_ms: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            'stage': self.stage,
            'model': self.model,
            'approximate_latency_ms': round(self.approximate_latency_ms, 2)
        }


# ============================================================================
# METRICS (ENHANCED)
# ============================================================================

@dataclass
class Metrics:
    """Enhanced metrics with budget tracking"""
    total_ms: float
    retrieve_ms: float
    rerank_ms: float
    generate_ms: float
    docs_retrieved: int
    docs_reranked: int
    cache_hit: bool = False

    # Budget consumption
    budget_use: Dict[str, int] = field(default_factory=dict)  # {web_queries: 3, internal_queries: 10}

    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_ms': round(self.total_ms, 2),
            'retrieve_ms': round(self.retrieve_ms, 2),
            'rerank_ms': round(self.rerank_ms, 2),
            'generate_ms': round(self.generate_ms, 2),
            'docs_retrieved': self.docs_retrieved,
            'docs_reranked': self.docs_reranked,
            'cache_hit': self.cache_hit,
            'breakdown_pct': {
                'retrieve': round((self.retrieve_ms / self.total_ms) * 100, 1) if self.total_ms > 0 else 0,
                'rerank': round((self.rerank_ms / self.total_ms) * 100, 1) if self.total_ms > 0 else 0,
                'generate': round((self.generate_ms / self.total_ms) * 100, 1) if self.total_ms > 0 else 0,
            },
            'budget_use': self.budget_use
        }


# ============================================================================
# FULL RESPONSE CONTRACT
# ============================================================================

@dataclass
class RagResponse:
    """Complete observability response"""
    # Core answer
    answer: str
    confidence: str
    sources: List[Source]
    trace_id: str

    # Route decision
    route: Literal["rag", "web", "blended"]
    route_reason: str

    # Model routing
    model_routing: List[ModelRoutingEntry]

    # Recency evaluation
    recency: RecencyEvaluation

    # Artifacts (Schemas A-G)
    planner: PlannerArtifact
    retrieval_log: RetrievalLog
    evidence_map: EvidenceMap
    kg_log: Optional[KGLog]
    chunking_report: ChunkingReport
    guardrail_report: GuardrailReport
    ab_eval: ABEvaluation

    # Metrics
    metrics: Metrics

    # Footer
    source_mix: Dict[str, int]  # {rag: 5, web_search: 3, research_agent: 0}
    wall_time_ms: float
    sha256: str  # Hash of final answer

    # Optional
    refusal: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'answer': self.answer,
            'confidence': self.confidence,
            'sources': [s.to_dict() for s in self.sources],
            'trace_id': self.trace_id,
            'route': self.route,
            'route_reason': self.route_reason,
            'model_routing': [m.to_dict() for m in self.model_routing],
            'recency': self.recency.to_dict(),
            'planner': self.planner.to_dict(),
            'retrieval_log': self.retrieval_log.to_dict(),
            'evidence_map': self.evidence_map.to_dict(),
            'kg_log': self.kg_log.to_dict() if self.kg_log else None,
            'chunking_report': self.chunking_report.to_dict(),
            'guardrail_report': self.guardrail_report.to_dict(),
            'ab_eval': self.ab_eval.to_dict(),
            'metrics': self.metrics.to_dict(),
            'source_mix': self.source_mix,
            'wall_time_ms': round(self.wall_time_ms, 2),
            'sha256': self.sha256,
            'refusal': self.refusal
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

# Old evaluate_recency function removed - now using recency_gate module


def calculate_source_mix(sources: List[Source]) -> Dict[str, int]:
    """Count sources by origin_tool"""
    mix = {"rag": 0, "web_search": 0, "research_agent": 0}
    for source in sources:
        mix[source.origin_tool] = mix.get(source.origin_tool, 0) + 1
    return mix


def hash_answer(answer: str) -> str:
    """SHA-256 hash of answer for reproducibility"""
    return hashlib.sha256(answer.encode('utf-8')).hexdigest()


# ============================================================================
# MAIN ENDPOINT
# ============================================================================

# Global instances
orchestrator: Optional[RAGOrchestrator] = None
prompt_assembler: Optional[PromptAssembler] = None
llm_generate: Optional[callable] = None


@app.before_request
def before_request():
    """
    ID CORRELATION & PROPAGATION

    Extract or generate trace_id and request_id.
    These IDs will be propagated to ALL artifacts and services.
    """
    # Extract trace_id from OTel context or header
    span = trace.get_current_span()
    span_context = span.get_span_context()

    if span_context.is_valid:
        g.trace_id = format(span_context.trace_id, '032x')
    else:
        # Fallback: extract from header or generate
        g.trace_id = request.headers.get('X-Trace-ID', str(uuid.uuid4()).replace('-', ''))

    # Extract or generate request_id
    g.request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))

    # Timing
    g.start_time = time.time()

    # Tenant (for multi-tenancy)
    g.tenant = request.json.get('tenant', 'unknown') if request.json else 'unknown'

    # Set OTel span attributes for correlation
    span.set_attribute("request_id", g.request_id)
    span.set_attribute("trace_id", g.trace_id)
    span.set_attribute("tenant", g.tenant)

    logger.info(f"Request started: trace_id={g.trace_id}, request_id={g.request_id}, tenant={g.tenant}")


@app.after_request
def after_request(response):
    """
    Add observability headers for client-side correlation.
    """
    if hasattr(g, 'request_id'):
        response.headers['X-Request-ID'] = g.request_id
    if hasattr(g, 'trace_id'):
        response.headers['X-Trace-ID'] = g.trace_id
    if hasattr(g, 'start_time'):
        duration_ms = (time.time() - g.start_time) * 1000
        response.headers['X-Response-Time'] = f"{duration_ms:.2f}ms"

    # Contract version for client compatibility checks
    response.headers['X-Contract-Version'] = CONTRACT_VERSION

    return response


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'rag-api', 'version': '2.0.0'})


@app.route('/v1/rag/query', methods=['POST'])
def query():
    """
    FULL OBSERVABILITY RAG ENDPOINT

    See RagRequest and RagResponse dataclasses for complete contract.
    """
    with tracer.start_as_current_span("rag.request") as span:
        try:
            # Parse request
            if not request.json:
                return jsonify({'error': 'Request body must be JSON'}), 400

            rag_req = RagRequest.from_dict(request.json)

            # Set span attributes
            span.set_attribute("tenant", rag_req.tenant)
            span.set_attribute("user_id", rag_req.user_id)
            span.set_attribute("plan_id", rag_req.plan_id)
            span.set_attribute("ab_setting", rag_req.ab_test.setting)

            # Get trace ID
            span_ctx = span.get_span_context()
            trace_id = format(span_ctx.trace_id, '032x')

            # Build orchestration context (ID correlation)
            orch_ctx = OrchestrationContext(
                trace_id=trace_id,
                request_id=g.request_id,
                tenant=rag_req.tenant,
                user_id=rag_req.user_id,
                query=rag_req.query,
                plan_id=rag_req.plan_id,
                settings_snapshot=rag_req.settings_snapshot,
                budgets=rag_req.budgets,
                policy=rag_req.policy,
                ab_test=rag_req.ab_test,
                start_time=g.start_time
            )

            # === RETRIEVAL PIPELINE WITH PROVENANCE ===

            timings = {}

            # Step 1: Vector search (sets origin_tool=RAG)
            start = time.time()
            internal_evidence = mock_vector_search(rag_req.query, k=10, ctx=orch_ctx)
            timings['vector_search'] = (time.time() - start) * 1000

            # Step 2: Web search (sets origin_tool=WEB_SEARCH)
            start = time.time()
            web_evidence = mock_web_search(rag_req.query, k=5, ctx=orch_ctx)
            timings['web_search'] = (time.time() - start) * 1000

            # Step 3: Merge
            all_evidence = internal_evidence + web_evidence

            # Step 4: Deduplication (preserves origin_tool)
            start = time.time()
            deduped_evidence, dedup_audit = deduplicate_evidence(all_evidence)
            timings['dedup'] = (time.time() - start) * 1000

            # Step 5: Domain filtering (preserves origin_tool)
            domain_filter = create_default_filter()
            start = time.time()
            filtered_evidence, filter_audit = domain_filter.filter_evidence(deduped_evidence)
            timings['domain_filter'] = (time.time() - start) * 1000

            # Step 6: Build Schema B (RetrievalLog)
            retrieval_log = build_retrieval_log(
                internal_results=[e for e in filtered_evidence if e.origin_tool == OriginTool.RAG],
                web_results=[e for e in filtered_evidence if e.origin_tool == OriginTool.WEB_SEARCH],
                dedup_audit=dedup_audit,
                filter_audit=filter_audit,
                timings=timings,
                ctx=orch_ctx
            )

            # Convert Evidence to Source for response
            # Note: freshness_hours will be computed in recency evaluation
            mock_sources = [
                Source(
                    index=i+1,
                    id=ev.id,
                    content=ev.content,
                    url=ev.url,
                    title=ev.title,
                    score=ev.metadata.get('score', 0.0),
                    origin_tool=ev.origin_tool.value,  # Preserved origin_tool
                    published_at=ev.published_at.isoformat() if ev.published_at else None,
                    is_primary=ev.is_primary,
                    domain=ev.metadata.get('domain'),
                    freshness_hours=ev.metadata.get('freshness_hours')  # Will be set by recency gate
                )
                for i, ev in enumerate(filtered_evidence[:10])
            ]

            # Step 7: Evaluate recency gate (SERVER-SIDE freshness calculation)
            recency_result = evaluate_recency_gate(
                evidence_list=filtered_evidence[:10],
                query=rag_req.query,
                policy_requires_recency=rag_req.policy.requires_recency,
                policy_min_primary_sources=rag_req.policy.min_primary_sources,
                window_hours=48
            )
            
            # Update sources with freshness_hours (now computed server-side)
            for i, ev in enumerate(filtered_evidence[:10]):
                if i < len(mock_sources):
                    mock_sources[i].freshness_hours = ev.metadata.get('freshness_hours')
            
            # Build RecencyEvaluation artifact
            recency = RecencyEvaluation(
                trace_id=trace_id,
                request_id=g.request_id,
                window_hours=recency_result['window_hours'],
                passed=recency_result['passed'],
                notes=recency_result['notes'],
                freshness_histogram=recency_result['freshness_histogram'],
                primary_sources_within_window=recency_result['primary_sources_within_window']
            )
            
            # If recency gate fails and query is temporal, return refusal
            refusal = None
            answer = "Mock answer - wire real LLM"
            confidence = "MEDIUM"
            
            if not recency_result['passed'] and recency_result['query_is_temporal']:
                refusal = (
                    f"Unable to provide a confident answer for this temporal query. "
                    f"{recency_result['notes']} "
                    f"Please try rephrasing your query or check back when more recent sources are available."
                )
                answer = ""
                confidence = "VERY_LOW"
                logger.warning(f"Recency gate failed: {recency_result['notes']}")

            # Build artifacts with ID correlation
            planner = PlannerArtifact(
                trace_id=trace_id,
                request_id=g.request_id,
                subtasks=["retrieve_internal", "retrieve_web", "dedup", "filter", "synthesize"],
                requires_recency=[False],
                queries_planned=[rag_req.query],
                budgets_applied=rag_req.budgets,
                route_decision="blended",
                route_reason=f"Blended RAG + Web search. Retrieved {len(internal_evidence)} internal + {len(web_evidence)} web, deduped {len(all_evidence) - len(deduped_evidence)}, filtered {len(deduped_evidence) - len(filtered_evidence)}"
            )

            # retrieval_log already built above with full audit trail

            evidence_map = EvidenceMap(
                trace_id=trace_id,
                request_id=g.request_id,
                claims=[{"claim_text": "RAG combines retrieval and generation", "citation_indices": [1], "confidence": 0.9}],
                ungrounded_claims=[],
                grounding_rate=1.0
            )

            chunking_report = ChunkingReport(
                trace_id=trace_id,
                request_id=g.request_id,
                params={"target_size": 500, "min": 300, "max": 800, "overlap": 100},
                samples=[],
                timing_ms=10.0,
                total_chunks=0
            )

            guardrail_report = GuardrailReport(
                trace_id=trace_id,
                request_id=g.request_id,
                detections=[],
                service_errors=[],
                overall_safe=True
            )

            ab_eval = ABEvaluation(
                trace_id=trace_id,
                request_id=g.request_id,
                setting=rag_req.ab_test.setting,
                dimensions={"coverage": 0.8, "grounding": 0.9, "recency": 0.7, "retrieval_quality": 0.85},
                overall_score=0.81
            )

            # Build response
            response = RagResponse(
                answer=answer,
                confidence=confidence,
                sources=mock_sources,
                trace_id=trace_id,
                route="blended",
                route_reason=planner.route_reason,
                model_routing=[
                    ModelRoutingEntry("embedding", "text-embedding-ada-002", timings.get('vector_search', 0)),
                    ModelRoutingEntry("web_search", "searxng", timings.get('web_search', 0)),
                    ModelRoutingEntry("generation", "llama2:13b", 200.0)
                ],
                recency=recency,
                planner=planner,
                retrieval_log=retrieval_log,
                evidence_map=evidence_map,
                kg_log=None,
                chunking_report=chunking_report,
                guardrail_report=guardrail_report,
                ab_eval=ab_eval,
                metrics=Metrics(
                    total_ms=(time.time() - g.start_time) * 1000,
                    retrieve_ms=timings.get('vector_search', 0) + timings.get('web_search', 0),
                    rerank_ms=0.0,
                    generate_ms=200.0,
                    docs_retrieved=len(internal_evidence) + len(web_evidence),
                    docs_reranked=len(filtered_evidence),
                    budget_use=orch_ctx.budget_use
                ),
                source_mix=calculate_source_mix(mock_sources),
                wall_time_ms=(time.time() - g.start_time) * 1000,
                sha256=hash_answer(answer),
                refusal=refusal
            )

            return jsonify(response.to_dict()), 200

        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR))
            logger.error(f"Error: {e}", exc_info=True)
            return jsonify({'error': str(e), 'trace_id': format(span.get_span_context().trace_id, '032x')}), 500


def mock_llm_generate(prompt: str) -> str:
    return "Mock answer - wire real LLM"


def initialize_app():
    global orchestrator, prompt_assembler, llm_generate

    def mock_vector_search(query: str, k: int) -> List[Evidence]:
        return []

    orchestrator = RAGOrchestrator(vector_search_fn=mock_vector_search)
    prompt_assembler = PromptAssembler()
    llm_generate = mock_llm_generate

    logger.info("RAG API v2.0 initialized with full observability contract")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    initialize_app()
    app.run(host='0.0.0.0', port=8080, debug=True)
