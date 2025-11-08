"""
RAG Orchestration Layer - Core Intelligence Engine

This is the heart of the RAG system. It orchestrates the entire retrieval-augmented
generation pipeline with explicit stages, confidence scoring, and quality controls.

Pipeline Stages:
1. PREPROCESS: Query expansion, intent classification
2. RETRIEVE: Hybrid search (BM25 + Vector + KG)
3. RERANK: Score fusion, quality filtering
4. ASSEMBLE: Context packaging, prompt templating
5. GENERATE: LLM inference with streaming
6. VERIFY: Hallucination check, grounding validation
7. RESPOND: Format and return with provenance

This replaces ad-hoc retrieval with a configurable, observable, production-grade engine.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Literal
from enum import Enum
import logging
import hashlib
import json

from services.common.evidence import Evidence, OriginTool
from services.common.timing import TimingCollector
from services.common.validators import ProvenanceValidator


logger = logging.getLogger(__name__)


class RetrievalStrategy(str, Enum):
    """Retrieval strategy selection"""
    VECTOR_ONLY = "vector_only"
    BM25_ONLY = "bm25_only"
    HYBRID = "hybrid"
    HYBRID_WITH_KG = "hybrid_with_kg"
    HYBRID_WITH_WEB = "hybrid_with_web"
    FULL_SEARCH = "full_search"  # Hybrid + KG + Web


class RerankStrategy(str, Enum):
    """Reranking strategy"""
    NONE = "none"
    RRF = "rrf"  # Reciprocal Rank Fusion
    CROSS_ENCODER = "cross_encoder"
    LLM_RERANK = "llm_rerank"


class ConfidenceLevel(str, Enum):
    """Confidence in retrieval quality"""
    HIGH = "high"        # > 0.8
    MEDIUM = "medium"    # 0.5 - 0.8
    LOW = "low"          # 0.3 - 0.5
    VERY_LOW = "very_low"  # < 0.3


@dataclass
class RetrievalPlan:
    """
    Configurable retrieval plan with all parameters.
    
    This is the "recipe" for how to retrieve documents. It can be:
    - Saved/loaded for reproducibility
    - Versioned for A/B testing
    - Adjusted per query type
    """
    # Core parameters
    strategy: RetrievalStrategy = RetrievalStrategy.HYBRID_WITH_KG
    top_k: int = 10
    rerank_strategy: RerankStrategy = RerankStrategy.RRF
    rerank_top_k: int = 5
    
    # Hybrid search weights
    vector_weight: float = 0.6
    bm25_weight: float = 0.4
    
    # Quality thresholds
    min_relevance_score: float = 0.3
    min_confidence_threshold: float = 0.5
    
    # Feature flags
    enable_kg_expansion: bool = True
    enable_web_search: bool = False
    enable_query_expansion: bool = True
    enable_hallucination_check: bool = True
    
    # Context management
    max_context_tokens: int = 4096
    max_chunks_per_doc: int = 3
    
    # Caching
    enable_cache: bool = True
    cache_ttl_seconds: int = 3600
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize for storage/versioning"""
        return {
            'strategy': self.strategy.value,
            'top_k': self.top_k,
            'rerank_strategy': self.rerank_strategy.value,
            'rerank_top_k': self.rerank_top_k,
            'vector_weight': self.vector_weight,
            'bm25_weight': self.bm25_weight,
            'min_relevance_score': self.min_relevance_score,
            'min_confidence_threshold': self.min_confidence_threshold,
            'enable_kg_expansion': self.enable_kg_expansion,
            'enable_web_search': self.enable_web_search,
            'enable_query_expansion': self.enable_query_expansion,
            'enable_hallucination_check': self.enable_hallucination_check,
            'max_context_tokens': self.max_context_tokens,
            'max_chunks_per_doc': self.max_chunks_per_doc,
            'enable_cache': self.enable_cache,
            'cache_ttl_seconds': self.cache_ttl_seconds,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RetrievalPlan':
        """Deserialize from storage"""
        return cls(
            strategy=RetrievalStrategy(data.get('strategy', 'hybrid_with_kg')),
            top_k=data.get('top_k', 10),
            rerank_strategy=RerankStrategy(data.get('rerank_strategy', 'rrf')),
            rerank_top_k=data.get('rerank_top_k', 5),
            vector_weight=data.get('vector_weight', 0.6),
            bm25_weight=data.get('bm25_weight', 0.4),
            min_relevance_score=data.get('min_relevance_score', 0.3),
            min_confidence_threshold=data.get('min_confidence_threshold', 0.5),
            enable_kg_expansion=data.get('enable_kg_expansion', True),
            enable_web_search=data.get('enable_web_search', False),
            enable_query_expansion=data.get('enable_query_expansion', True),
            enable_hallucination_check=data.get('enable_hallucination_check', True),
            max_context_tokens=data.get('max_context_tokens', 4096),
            max_chunks_per_doc=data.get('max_chunks_per_doc', 3),
            enable_cache=data.get('enable_cache', True),
            cache_ttl_seconds=data.get('cache_ttl_seconds', 3600),
        )
    
    def get_cache_key(self, query: str) -> str:
        """Generate cache key for this query + plan"""
        plan_json = json.dumps(self.to_dict(), sort_keys=True)
        combined = f"{query}||{plan_json}"
        return hashlib.sha256(combined.encode()).hexdigest()


@dataclass
class RetrievalResult:
    """
    Output of retrieval pipeline with full observability.
    """
    # Retrieved documents
    evidence: List[Evidence]
    
    # Quality metrics
    confidence: ConfidenceLevel
    confidence_score: float  # 0.0 - 1.0
    retrieval_quality_score: float  # 0.0 - 1.0
    
    # Source breakdown
    source_counts: Dict[str, int]  # {rag: 5, web_search: 3, ...}
    
    # Pipeline metadata
    plan: RetrievalPlan
    timings: Dict[str, float]
    stage_results: Dict[str, Any]  # Intermediate results for debugging
    
    # Warnings/issues
    warnings: List[str] = field(default_factory=list)
    should_refuse: bool = False
    refusal_reason: Optional[str] = None


class RAGOrchestrator:
    """
    Core RAG Intelligence Layer
    
    Orchestrates the entire RAG pipeline with:
    - Configurable retrieval strategies
    - Quality controls and confidence scoring
    - Hallucination prevention
    - Full observability
    - Caching for performance
    
    Usage:
        orchestrator = RAGOrchestrator(
            vector_search_fn=vector_search,
            bm25_search_fn=bm25_search,
            web_search_fn=web_search,
            kg_expand_fn=kg_expand,
            rerank_fn=rerank,
            cache=redis_client
        )
        
        result = orchestrator.retrieve(
            query="What is RAG?",
            plan=RetrievalPlan(strategy=RetrievalStrategy.HYBRID_WITH_KG)
        )
        
        if result.should_refuse:
            return {"error": result.refusal_reason}
        
        # Use result.evidence for LLM prompt
    """
    
    def __init__(
        self,
        vector_search_fn,
        bm25_search_fn=None,
        web_search_fn=None,
        kg_expand_fn=None,
        rerank_fn=None,
        cache=None
    ):
        """
        Initialize orchestrator with search functions.
        
        Args:
            vector_search_fn: fn(query, k) -> List[Evidence]
            bm25_search_fn: fn(query, k) -> List[Evidence]
            web_search_fn: fn(query, k) -> List[Evidence]
            kg_expand_fn: fn(evidence_list) -> List[Evidence]
            rerank_fn: fn(query, evidence_list, strategy) -> List[Evidence]
            cache: Redis client or in-memory cache
        """
        self.vector_search = vector_search_fn
        self.bm25_search = bm25_search_fn
        self.web_search = web_search_fn
        self.kg_expand = kg_expand_fn
        self.rerank = rerank_fn
        self.cache = cache
        
        self.validator = ProvenanceValidator(strict_mode=False)
    
    def retrieve(
        self,
        query: str,
        plan: Optional[RetrievalPlan] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> RetrievalResult:
        """
        Execute full retrieval pipeline.
        
        Args:
            query: User query
            plan: Retrieval plan (uses default if None)
            user_context: User-specific context for personalization
        
        Returns:
            RetrievalResult with evidence and metadata
        """
        if plan is None:
            plan = RetrievalPlan()
        
        timer = TimingCollector()
        stage_results = {}
        warnings = []
        
        # Check cache
        if plan.enable_cache and self.cache:
            cache_key = plan.get_cache_key(query)
            cached = self._get_from_cache(cache_key)
            if cached:
                logger.info(f"Cache hit for query: {query[:50]}")
                cached['timings']['cache_lookup'] = 0.1
                return RetrievalResult(**cached)
        
        # Stage 1: PREPROCESS
        with timer.measure('preprocess'):
            processed_query, expanded_queries = self._preprocess(query, plan)
            stage_results['preprocess'] = {
                'original': query,
                'processed': processed_query,
                'expanded': expanded_queries
            }
        
        # Stage 2: RETRIEVE
        with timer.measure('retrieve'):
            all_evidence = self._retrieve_all(
                processed_query,
                expanded_queries,
                plan,
                timer
            )
            stage_results['retrieve'] = {
                'count': len(all_evidence),
                'sources': self._count_sources(all_evidence)
            }
        
        # Stage 3: RERANK
        with timer.measure('rerank'):
            reranked_evidence = self._rerank(
                processed_query,
                all_evidence,
                plan
            )
            stage_results['rerank'] = {
                'count': len(reranked_evidence),
                'top_scores': [e.score for e in reranked_evidence[:5]]
            }
        
        # Stage 4: VALIDATE & FILTER
        with timer.measure('validate'):
            filtered_evidence, validation_warnings = self._validate_and_filter(
                reranked_evidence,
                plan
            )
            warnings.extend(validation_warnings)
            stage_results['validate'] = {
                'count': len(filtered_evidence),
                'warnings': len(validation_warnings)
            }
        
        # Stage 5: CALCULATE CONFIDENCE
        with timer.measure('confidence'):
            confidence_score, confidence_level = self._calculate_confidence(
                filtered_evidence,
                plan
            )
            stage_results['confidence'] = {
                'score': confidence_score,
                'level': confidence_level.value
            }
        
        # Stage 6: DECIDE REFUSAL
        should_refuse, refusal_reason = self._should_refuse(
            confidence_score,
            filtered_evidence,
            plan
        )
        
        # Build result
        result = RetrievalResult(
            evidence=filtered_evidence[:plan.rerank_top_k],
            confidence=confidence_level,
            confidence_score=confidence_score,
            retrieval_quality_score=self._calculate_quality_score(filtered_evidence),
            source_counts=self._count_sources(filtered_evidence),
            plan=plan,
            timings=timer.get_timings(),
            stage_results=stage_results,
            warnings=warnings,
            should_refuse=should_refuse,
            refusal_reason=refusal_reason
        )
        
        # Cache result
        if plan.enable_cache and self.cache and not should_refuse:
            cache_key = plan.get_cache_key(query)
            self._save_to_cache(cache_key, result, plan.cache_ttl_seconds)
        
        return result
    
    def _preprocess(
        self,
        query: str,
        plan: RetrievalPlan
    ) -> tuple[str, List[str]]:
        """
        Stage 1: Preprocess query.
        
        - Clean and normalize
        - Optionally expand with synonyms/related terms
        - Intent classification (future)
        """
        processed = query.strip()
        expanded = [processed]
        
        if plan.enable_query_expansion:
            # Simple expansion (can be replaced with LLM-based expansion)
            # For now, just add a few variations
            if len(processed.split()) <= 3:
                # For short queries, add context
                expanded.append(f"{processed} explanation")
                expanded.append(f"{processed} definition")
        
        return processed, expanded
    
    def _retrieve_all(
        self,
        query: str,
        expanded_queries: List[str],
        plan: RetrievalPlan,
        timer: TimingCollector
    ) -> List[Evidence]:
        """
        Stage 2: Retrieve from all sources based on strategy.
        """
        all_evidence = []
        
        # Vector search
        if plan.strategy in [
            RetrievalStrategy.VECTOR_ONLY,
            RetrievalStrategy.HYBRID,
            RetrievalStrategy.HYBRID_WITH_KG,
            RetrievalStrategy.HYBRID_WITH_WEB,
            RetrievalStrategy.FULL_SEARCH
        ]:
            with timer.measure('vector_search'):
                vector_results = self.vector_search(query, plan.top_k)
                all_evidence.extend(vector_results)
        
        # BM25 search
        if self.bm25_search and plan.strategy in [
            RetrievalStrategy.BM25_ONLY,
            RetrievalStrategy.HYBRID,
            RetrievalStrategy.HYBRID_WITH_KG,
            RetrievalStrategy.HYBRID_WITH_WEB,
            RetrievalStrategy.FULL_SEARCH
        ]:
            with timer.measure('bm25_search'):
                bm25_results = self.bm25_search(query, plan.top_k)
                all_evidence.extend(bm25_results)
        
        # Knowledge Graph expansion
        if self.kg_expand and plan.enable_kg_expansion and plan.strategy in [
            RetrievalStrategy.HYBRID_WITH_KG,
            RetrievalStrategy.FULL_SEARCH
        ]:
            with timer.measure('kg_expansion'):
                if all_evidence:
                    kg_results = self.kg_expand(all_evidence[:5])
                    all_evidence.extend(kg_results)
        
        # Web search
        if self.web_search and plan.enable_web_search and plan.strategy in [
            RetrievalStrategy.HYBRID_WITH_WEB,
            RetrievalStrategy.FULL_SEARCH
        ]:
            with timer.measure('web_search'):
                web_results = self.web_search(query, plan.top_k // 2)
                all_evidence.extend(web_results)
        
        return all_evidence
    
    def _rerank(
        self,
        query: str,
        evidence: List[Evidence],
        plan: RetrievalPlan
    ) -> List[Evidence]:
        """
        Stage 3: Rerank retrieved evidence.
        """
        if plan.rerank_strategy == RerankStrategy.NONE:
            return sorted(evidence, key=lambda e: e.score, reverse=True)
        
        if self.rerank:
            return self.rerank(query, evidence, plan.rerank_strategy)
        
        # Fallback: simple score-based sorting
        return sorted(evidence, key=lambda e: e.score, reverse=True)
    
    def _validate_and_filter(
        self,
        evidence: List[Evidence],
        plan: RetrievalPlan
    ) -> tuple[List[Evidence], List[str]]:
        """
        Stage 4: Validate provenance and filter by quality.
        """
        warnings = []
        
        # Provenance validation
        if not self.validator.validate(evidence):
            violations = self.validator.get_violations("warning")
            for v in violations:
                warnings.append(f"Provenance warning: {v.message}")
        
        # Score filtering
        filtered = [
            e for e in evidence
            if e.score >= plan.min_relevance_score
        ]
        
        if len(filtered) < len(evidence):
            warnings.append(
                f"Filtered {len(evidence) - len(filtered)} low-score results"
            )
        
        return filtered, warnings
    
    def _calculate_confidence(
        self,
        evidence: List[Evidence],
        plan: RetrievalPlan
    ) -> tuple[float, ConfidenceLevel]:
        """
        Stage 5: Calculate confidence in retrieval quality.
        
        Confidence based on:
        - Top result score
        - Number of high-quality results
        - Source diversity
        - Score distribution
        """
        if not evidence:
            return 0.0, ConfidenceLevel.VERY_LOW
        
        # Factor 1: Top score
        top_score = evidence[0].score
        
        # Factor 2: Number of high-quality results (score > 0.7)
        high_quality_count = sum(1 for e in evidence if e.score > 0.7)
        high_quality_ratio = high_quality_count / len(evidence)
        
        # Factor 3: Source diversity
        sources = set(e.origin_tool for e in evidence)
        source_diversity = len(sources) / 3.0  # Normalize by 3 source types
        
        # Factor 4: Score spread (prefer consistent high scores)
        scores = [e.score for e in evidence[:5]]
        score_std = (max(scores) - min(scores)) if len(scores) > 1 else 0
        score_consistency = 1.0 - min(score_std, 1.0)
        
        # Weighted confidence
        confidence_score = (
            top_score * 0.4 +
            high_quality_ratio * 0.3 +
            source_diversity * 0.2 +
            score_consistency * 0.1
        )
        
        # Map to confidence level
        if confidence_score > 0.8:
            level = ConfidenceLevel.HIGH
        elif confidence_score > 0.5:
            level = ConfidenceLevel.MEDIUM
        elif confidence_score > 0.3:
            level = ConfidenceLevel.LOW
        else:
            level = ConfidenceLevel.VERY_LOW
        
        return confidence_score, level
    
    def _should_refuse(
        self,
        confidence_score: float,
        evidence: List[Evidence],
        plan: RetrievalPlan
    ) -> tuple[bool, Optional[str]]:
        """
        Stage 6: Decide whether to refuse answering.
        
        Refuse if:
        - Confidence below threshold
        - No high-quality results
        - Provenance issues in strict mode
        """
        # Check confidence threshold
        if confidence_score < plan.min_confidence_threshold:
            return True, (
                f"Confidence too low ({confidence_score:.2f} < {plan.min_confidence_threshold}). "
                "Please rephrase your question or provide more context."
            )
        
        # Check minimum result count
        if len(evidence) == 0:
            return True, "No relevant information found. Please try a different query."
        
        # Check for at least one high-quality result
        if not any(e.score > 0.5 for e in evidence):
            return True, (
                "No high-confidence results found. "
                "The information may be outside my knowledge base."
            )
        
        return False, None
    
    def _calculate_quality_score(self, evidence: List[Evidence]) -> float:
        """Calculate overall retrieval quality score"""
        if not evidence:
            return 0.0
        
        # Average of top 5 scores
        top_scores = [e.score for e in evidence[:5]]
        return sum(top_scores) / len(top_scores)
    
    def _count_sources(self, evidence: List[Evidence]) -> Dict[str, int]:
        """Count evidence by source"""
        counts = {}
        for e in evidence:
            origin = e.origin_tool.value
            counts[origin] = counts.get(origin, 0) + 1
        return counts
    
    def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached result"""
        # TODO: Implement Redis cache
        return None
    
    def _save_to_cache(self, key: str, result: RetrievalResult, ttl: int):
        """Save result to cache"""
        # TODO: Implement Redis cache
        pass

