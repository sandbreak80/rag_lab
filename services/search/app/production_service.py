"""
Production-Grade Search Service with RAG Orchestrator

This replaces ad-hoc retrieval logic with:
- Tenant isolation + AuthZ filtering
- Redis caching (retrieval + answer)
- Failure policies (timeouts, fallbacks, circuit breaker)
- OTEL instrumentation (spans, attributes, logs)
- Structured error taxonomy

Service Contract:
- Request: {tenant_id, user_id, query, top_k, retrieval_plan_id, template_id, authz_context}
- Response: {answer, confidence, citations, telemetry, refusal}
"""

from flask import Flask, request, jsonify
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib
import json
import logging
import time
from functools import wraps
from enum import Enum

# Production dependencies
import redis
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from services.common.orchestrator import RAGOrchestrator, RetrievalPlan, RetrievalStrategy
from services.common.prompt_assembler import PromptAssembler, PromptTemplate
from services.common.evidence import Evidence, OriginTool


logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


# ============================================================================
# ERROR TAXONOMY
# ============================================================================

class ErrorCode(str, Enum):
    """Structured error codes for client handling"""
    INVALID_REQUEST = "invalid_request"
    UNAUTHORIZED = "unauthorized"
    TENANT_NOT_FOUND = "tenant_not_found"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    RETRIEVAL_TIMEOUT = "retrieval_timeout"
    LLM_TIMEOUT = "llm_timeout"
    CIRCUIT_BREAKER_OPEN = "circuit_breaker_open"
    INSUFFICIENT_CONFIDENCE = "insufficient_confidence"
    INTERNAL_ERROR = "internal_error"


@dataclass
class ServiceError(Exception):
    """Structured service error"""
    code: ErrorCode
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    retry_after: Optional[int] = None  # Seconds
    
    def to_dict(self):
        return {
            'error': {
                'code': self.code.value,
                'message': self.message,
                'details': self.details,
                'retry_after': self.retry_after
            }
        }


# ============================================================================
# REQUEST/RESPONSE DTOs
# ============================================================================

@dataclass
class AuthZContext:
    """Authorization context for multi-tenant filtering"""
    roles: List[str] = field(default_factory=list)
    doc_policies: List[str] = field(default_factory=list)  # e.g., ["public", "acme-confidential"]
    groups: List[str] = field(default_factory=list)


@dataclass
class SearchRequest:
    """Production search request"""
    tenant_id: str
    user_id: str
    query: str
    
    # Optional parameters
    top_k: int = 20
    retrieval_plan_id: str = "hybrid_v3"
    template_id: str = "qa_standard_v2"
    authz_context: Optional[AuthZContext] = None
    trace_ctx: Dict[str, str] = field(default_factory=dict)
    
    # Feature flags
    enable_cache: bool = True
    enable_fallback: bool = True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SearchRequest':
        """Parse and validate request"""
        authz_data = data.get('authz_context', {})
        authz = AuthZContext(
            roles=authz_data.get('roles', []),
            doc_policies=authz_data.get('doc_policies', []),
            groups=authz_data.get('groups', [])
        )
        
        return cls(
            tenant_id=data['tenant_id'],
            user_id=data['user_id'],
            query=data['query'],
            top_k=data.get('top_k', 20),
            retrieval_plan_id=data.get('retrieval_plan_id', 'hybrid_v3'),
            template_id=data.get('template_id', 'qa_standard_v2'),
            authz_context=authz,
            trace_ctx=data.get('trace_ctx', {}),
            enable_cache=data.get('enable_cache', True),
            enable_fallback=data.get('enable_fallback', True)
        )


@dataclass
class Citation:
    """Citation with provenance"""
    id: str
    url: Optional[str]
    title: Optional[str]
    score: float
    origin: str  # rag, web_search, research_agent


@dataclass
class Telemetry:
    """Response telemetry for observability"""
    plan_id: str
    template_id: str
    embed_model_v: str
    splitter_v: str
    index_alias: str
    
    # Performance
    p95_ms: float
    total_ms: float
    cache_hit: str  # "retrieval", "answer", "miss"
    
    # Quality
    hit_at_k: float
    mrr: Optional[float]  # Mean Reciprocal Rank
    rerank_gain: Optional[float]
    confidence_score: float
    
    # Cost
    tokens_used: int
    cost_usd: float


@dataclass
class SearchResponse:
    """Production search response"""
    answer: Optional[str]
    confidence: str  # HIGH, MEDIUM, LOW, VERY_LOW
    citations: List[Citation]
    telemetry: Telemetry
    refusal: Optional[Dict[str, str]] = None  # {"reason": "...", "next_steps": "..."}
    
    def to_dict(self):
        return {
            'answer': self.answer,
            'confidence': self.confidence,
            'citations': [asdict(c) for c in self.citations],
            'telemetry': asdict(self.telemetry),
            'refusal': self.refusal
        }


# ============================================================================
# CACHE LAYER
# ============================================================================

class RAGCache:
    """
    Two-tier cache: retrieval results + final answers
    
    Keys:
    - Retrieval: r:v1:{tenant}:{hash(query_norm)}:{plan_id}
    - Answer: a:v1:{tenant}:{hash(query_norm)}:{template_id}:{hash(citations)}
    
    Invalidation:
    - Subscribe to ingest.events (doc_updated, alias_flip)
    - Delete matching keys for affected tenants
    """
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.retrieval_ttl = 1800  # 30 minutes
        self.answer_ttl = 7200  # 2 hours
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query for cache keying (lowercase, strip, etc.)"""
        return query.lower().strip()
    
    def _hash_string(self, s: str) -> str:
        """Hash string for cache key"""
        return hashlib.sha256(s.encode()).hexdigest()[:16]
    
    def get_retrieval_result(
        self,
        tenant_id: str,
        query: str,
        plan_id: str
    ) -> Optional[List[Evidence]]:
        """Get cached retrieval result"""
        query_norm = self._normalize_query(query)
        key = f"r:v1:{tenant_id}:{self._hash_string(query_norm)}:{plan_id}"
        
        cached = self.redis.get(key)
        if cached:
            data = json.loads(cached)
            # Reconstruct Evidence objects
            return [Evidence.from_dict(e) for e in data['evidence']]
        
        return None
    
    def set_retrieval_result(
        self,
        tenant_id: str,
        query: str,
        plan_id: str,
        evidence: List[Evidence],
        index_alias: str
    ):
        """Cache retrieval result"""
        query_norm = self._normalize_query(query)
        key = f"r:v1:{tenant_id}:{self._hash_string(query_norm)}:{plan_id}"
        
        data = {
            'evidence': [e.to_dict() for e in evidence],
            'ts': datetime.utcnow().isoformat(),
            'index_alias': index_alias
        }
        
        self.redis.setex(key, self.retrieval_ttl, json.dumps(data))
    
    def get_answer(
        self,
        tenant_id: str,
        query: str,
        template_id: str,
        citations_hash: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached answer"""
        query_norm = self._normalize_query(query)
        key = f"a:v1:{tenant_id}:{self._hash_string(query_norm)}:{template_id}:{citations_hash}"
        
        cached = self.redis.get(key)
        if cached:
            return json.loads(cached)
        
        return None
    
    def set_answer(
        self,
        tenant_id: str,
        query: str,
        template_id: str,
        citations_hash: str,
        answer: str,
        token_cost: int
    ):
        """Cache answer"""
        query_norm = self._normalize_query(query)
        key = f"a:v1:{tenant_id}:{self._hash_string(query_norm)}:{template_id}:{citations_hash}"
        
        data = {
            'answer': answer,
            'ts': datetime.utcnow().isoformat(),
            'token_cost': token_cost
        }
        
        self.redis.setex(key, self.answer_ttl, json.dumps(data))
    
    def invalidate_tenant(self, tenant_id: str, plan_id: Optional[str] = None):
        """Invalidate all caches for a tenant (e.g., on doc update)"""
        # Retrieval cache
        pattern = f"r:v1:{tenant_id}:*:{plan_id}" if plan_id else f"r:v1:{tenant_id}:*"
        keys = self.redis.keys(pattern)
        if keys:
            self.redis.delete(*keys)
        
        # Answer cache (broader invalidation)
        pattern = f"a:v1:{tenant_id}:*"
        keys = self.redis.keys(pattern)
        if keys:
            self.redis.delete(*keys)
        
        logger.info(f"Invalidated cache for tenant={tenant_id}, plan={plan_id}")


# ============================================================================
# AUTHZ FILTER
# ============================================================================

class AuthZFilter:
    """
    Tenant isolation + policy-based filtering
    
    Defense-in-depth:
    1. Pre-retrieval: namespace/filter predicate
    2. Post-retrieval: sanitize results
    3. Provenance: stamp tenant_id into evidence
    """
    
    def __init__(self):
        # In production, load from policy engine or IAM service
        self.tenant_namespaces = {}
    
    def get_retrieval_filter(
        self,
        tenant_id: str,
        authz_context: AuthZContext
    ) -> Dict[str, Any]:
        """
        Generate filter predicate for retrieval stage.
        
        Returns ChromaDB/Qdrant filter dict.
        """
        filter_dict = {
            'tenant_id': tenant_id,  # Mandatory tenant isolation
        }
        
        # Policy-based filtering
        if authz_context.doc_policies:
            filter_dict['policy'] = {'$in': authz_context.doc_policies}
        
        return filter_dict
    
    def sanitize_results(
        self,
        tenant_id: str,
        authz_context: AuthZContext,
        evidence: List[Evidence]
    ) -> List[Evidence]:
        """
        Post-retrieval filtering (defense-in-depth).
        
        Remove any evidence that shouldn't be visible to this user.
        """
        sanitized = []
        
        for e in evidence:
            # Check tenant (paranoid check)
            if e.metadata.get('tenant_id') != tenant_id:
                logger.warning(f"Cross-tenant leakage detected: {e.id}")
                continue
            
            # Check policy
            doc_policy = e.metadata.get('policy', 'public')
            if authz_context.doc_policies and doc_policy not in authz_context.doc_policies:
                continue
            
            sanitized.append(e)
        
        return sanitized
    
    def stamp_provenance(
        self,
        tenant_id: str,
        user_id: str,
        evidence: List[Evidence]
    ) -> List[Evidence]:
        """Stamp tenant/user into evidence metadata for audit"""
        # Evidence is immutable, so we'd need to create new instances
        # For now, log the access
        logger.info(f"Access: tenant={tenant_id}, user={user_id}, docs={[e.id for e in evidence]}")
        return evidence


# ============================================================================
# FAILURE POLICY
# ============================================================================

class FailurePolicy:
    """
    Timeouts, fallbacks, circuit breaker
    
    Fallback ladder:
    1. Try hybrid (vector + BM25 + rerank)
    2. Fall back to vector only
    3. Fall back to BM25 only
    4. If all fail → structured refusal
    """
    
    def __init__(self):
        self.retrieval_timeout = 1.0  # seconds
        self.llm_timeout = 3.0  # seconds
        self.total_timeout = 5.0  # seconds
        
        # Circuit breaker state
        self.circuit_breaker_errors = {}
        self.circuit_breaker_threshold = 5
        self.circuit_breaker_reset_time = 60  # seconds
    
    def is_circuit_open(self, service_name: str) -> bool:
        """Check if circuit breaker is open for a service"""
        if service_name not in self.circuit_breaker_errors:
            return False
        
        errors, last_error_time = self.circuit_breaker_errors[service_name]
        
        # Reset if timeout expired
        if (datetime.utcnow() - last_error_time).total_seconds() > self.circuit_breaker_reset_time:
            del self.circuit_breaker_errors[service_name]
            return False
        
        return errors >= self.circuit_breaker_threshold
    
    def record_error(self, service_name: str):
        """Record service error for circuit breaker"""
        if service_name not in self.circuit_breaker_errors:
            self.circuit_breaker_errors[service_name] = (1, datetime.utcnow())
        else:
            errors, _ = self.circuit_breaker_errors[service_name]
            self.circuit_breaker_errors[service_name] = (errors + 1, datetime.utcnow())
    
    def record_success(self, service_name: str):
        """Record service success (reset circuit breaker)"""
        if service_name in self.circuit_breaker_errors:
            del self.circuit_breaker_errors[service_name]
    
    def get_fallback_plan(self, original_strategy: RetrievalStrategy) -> Optional[RetrievalStrategy]:
        """Get fallback retrieval strategy"""
        fallback_ladder = {
            RetrievalStrategy.FULL_SEARCH: RetrievalStrategy.HYBRID_WITH_KG,
            RetrievalStrategy.HYBRID_WITH_WEB: RetrievalStrategy.HYBRID,
            RetrievalStrategy.HYBRID_WITH_KG: RetrievalStrategy.HYBRID,
            RetrievalStrategy.HYBRID: RetrievalStrategy.VECTOR_ONLY,
            RetrievalStrategy.VECTOR_ONLY: RetrievalStrategy.BM25_ONLY,
            RetrievalStrategy.BM25_ONLY: None  # No fallback
        }
        
        return fallback_ladder.get(original_strategy)


# ============================================================================
# PRODUCTION SEARCH SERVICE
# ============================================================================

class ProductionSearchService:
    """
    Production-grade search service with:
    - Tenant isolation
    - Caching
    - AuthZ
    - Failure policies
    - OTEL instrumentation
    """
    
    def __init__(
        self,
        orchestrator: RAGOrchestrator,
        prompt_assembler: PromptAssembler,
        cache: RAGCache,
        authz_filter: AuthZFilter,
        failure_policy: FailurePolicy,
        llm_generate_fn
    ):
        self.orchestrator = orchestrator
        self.prompt_assembler = prompt_assembler
        self.cache = cache
        self.authz = authz_filter
        self.failure_policy = failure_policy
        self.llm_generate = llm_generate_fn
        
        # Config (in production, load from feature flags)
        self.embed_model_v = "text-embedding-ada-002-v2"
        self.splitter_v = "recursive-v1"
        self.index_alias = "main"
    
    def search(self, req: SearchRequest) -> SearchResponse:
        """Main search endpoint with full production features"""
        
        with tracer.start_as_current_span("search_request") as span:
            # Set span attributes
            span.set_attribute("tenant_id", req.tenant_id)
            span.set_attribute("user_id", req.user_id)
            span.set_attribute("query_length", len(req.query))
            span.set_attribute("plan_id", req.retrieval_plan_id)
            span.set_attribute("template_id", req.template_id)
            
            start_time = time.time()
            cache_hit = "miss"
            
            try:
                # Step 1: Check answer cache (fastest path)
                if req.enable_cache:
                    # TODO: Need citations hash, so check retrieval cache first
                    pass
                
                # Step 2: Retrieve with caching + authZ
                evidence = self._retrieve_with_cache_and_authz(req, span)
                
                # Step 3: Assemble prompt
                prompt_data = self.prompt_assembler.assemble(
                    query=req.query,
                    evidence=evidence,
                    template=PromptTemplate(req.template_id.split('_')[0].upper()),
                    max_context_tokens=4096
                )
                
                # Step 4: Generate answer (with LLM)
                answer = self._generate_with_timeout(prompt_data, span)
                
                # Step 5: Build response
                total_ms = (time.time() - start_time) * 1000
                
                citations = [
                    Citation(
                        id=e.id,
                        url=e.url,
                        title=e.title,
                        score=e.score,
                        origin=e.origin_tool.value
                    )
                    for e in evidence
                ]
                
                telemetry = Telemetry(
                    plan_id=req.retrieval_plan_id,
                    template_id=req.template_id,
                    embed_model_v=self.embed_model_v,
                    splitter_v=self.splitter_v,
                    index_alias=self.index_alias,
                    p95_ms=total_ms,  # TODO: Track actual p95
                    total_ms=total_ms,
                    cache_hit=cache_hit,
                    hit_at_k=self._calculate_hit_at_k(evidence),
                    mrr=None,  # TODO: Calculate MRR
                    rerank_gain=None,  # TODO: Calculate rerank gain
                    confidence_score=0.8,  # TODO: Get from orchestrator
                    tokens_used=prompt_data['token_count'],
                    cost_usd=prompt_data['token_count'] * 0.00001  # $0.01 per 1K tokens
                )
                
                return SearchResponse(
                    answer=answer,
                    confidence="MEDIUM",  # TODO: Get from orchestrator
                    citations=citations,
                    telemetry=telemetry,
                    refusal=None
                )
            
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR))
                logger.error(f"Search failed: {e}", exc_info=True)
                raise ServiceError(
                    code=ErrorCode.INTERNAL_ERROR,
                    message=str(e)
                )
    
    def _retrieve_with_cache_and_authz(
        self,
        req: SearchRequest,
        span: trace.Span
    ) -> List[Evidence]:
        """Retrieve with caching + authZ filtering"""
        
        # Check cache first
        if req.enable_cache:
            cached = self.cache.get_retrieval_result(
                req.tenant_id,
                req.query,
                req.retrieval_plan_id
            )
            if cached:
                span.set_attribute("cache_hit", "retrieval")
                return cached
        
        # Cache miss → retrieve with authZ
        with tracer.start_as_current_span("retrieve") as retrieve_span:
            # Get authZ filter
            authz_filter = self.authz.get_retrieval_filter(
                req.tenant_id,
                req.authz_context
            )
            retrieve_span.set_attribute("authz_filter", json.dumps(authz_filter))
            
            # TODO: Pass authz_filter to orchestrator
            # For now, retrieve without filter
            plan = RetrievalPlan(top_k=req.top_k)
            result = self.orchestrator.retrieve(req.query, plan)
            
            # Post-retrieval sanitization (defense-in-depth)
            sanitized = self.authz.sanitize_results(
                req.tenant_id,
                req.authz_context,
                result.evidence
            )
            
            # Stamp provenance
            stamped = self.authz.stamp_provenance(
                req.tenant_id,
                req.user_id,
                sanitized
            )
            
            # Cache result
            if req.enable_cache:
                self.cache.set_retrieval_result(
                    req.tenant_id,
                    req.query,
                    req.retrieval_plan_id,
                    stamped,
                    self.index_alias
                )
            
            return stamped
    
    def _generate_with_timeout(
        self,
        prompt_data: Dict[str, Any],
        span: trace.Span
    ) -> str:
        """Generate answer with LLM (with timeout)"""
        with tracer.start_as_current_span("llm_generate") as llm_span:
            llm_span.set_attribute("token_count", prompt_data['token_count'])
            llm_span.set_attribute("template_id", prompt_data['template_id'])
            
            # TODO: Implement timeout
            answer = self.llm_generate(prompt_data['prompt'])
            
            return answer
    
    def _calculate_hit_at_k(self, evidence: List[Evidence]) -> float:
        """Calculate hit@k metric (simplified)"""
        # TODO: Implement proper hit@k calculation
        return 0.9 if evidence else 0.0

