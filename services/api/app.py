"""
RAG Query API - Production Endpoint with Observability

This is the main entry point for the RAG Lab system.
Students will use this API to query their RAG system and observe:
- Request/response flow
- Trace IDs for distributed tracing
- Performance metrics
- Source citations
"""

from flask import Flask, request, jsonify, g
from flask_cors import CORS
from dataclasses import asdict
from typing import Dict, Any, List, Optional
import time
import uuid
import logging

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

# Import our RAG components (already built)
from services.common.orchestrator import RAGOrchestrator, RetrievalPlan, RetrievalStrategy
from services.common.prompt_assembler import PromptAssembler, PromptTemplate
from services.common.evidence import Evidence

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

app = Flask(__name__)
CORS(app)

# Global instances (will be initialized in main)
orchestrator: Optional[RAGOrchestrator] = None
prompt_assembler: Optional[PromptAssembler] = None
llm_generate: Optional[callable] = None


# ============================================================================
# DATA MODELS
# ============================================================================

class RagRequest:
    """Student's RAG query request"""
    def __init__(self, query: str, tenant: str, user_id: str, 
                 plan_id: str = "hybrid_v1", debug: bool = False):
        self.query = query
        self.tenant = tenant
        self.user_id = user_id
        self.plan_id = plan_id
        self.debug = debug
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RagRequest':
        return cls(
            query=data['query'],
            tenant=data['tenant'],
            user_id=data['user_id'],
            plan_id=data.get('plan_id', 'hybrid_v1'),
            debug=data.get('debug', False)
        )


class Source:
    """Source citation with observability metadata"""
    def __init__(self, index: int, id: str, content: str, 
                 url: Optional[str], title: Optional[str], 
                 score: float, origin: str):
        self.index = index
        self.id = id
        self.content = content
        self.url = url
        self.title = title
        self.score = score
        self.origin = origin
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'index': self.index,
            'id': self.id,
            'content': self.content[:200] + '...' if len(self.content) > 200 else self.content,
            'url': self.url,
            'title': self.title,
            'score': round(self.score, 3),
            'origin': self.origin
        }


class Metrics:
    """Observability metrics for students to analyze"""
    def __init__(self, total_ms: float, retrieve_ms: float, 
                 rerank_ms: float, generate_ms: float,
                 docs_retrieved: int, docs_reranked: int,
                 cache_hit: bool = False):
        self.total_ms = round(total_ms, 2)
        self.retrieve_ms = round(retrieve_ms, 2)
        self.rerank_ms = round(rerank_ms, 2)
        self.generate_ms = round(generate_ms, 2)
        self.docs_retrieved = docs_retrieved
        self.docs_reranked = docs_reranked
        self.cache_hit = cache_hit
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_ms': self.total_ms,
            'retrieve_ms': self.retrieve_ms,
            'rerank_ms': self.rerank_ms,
            'generate_ms': self.generate_ms,
            'docs_retrieved': self.docs_retrieved,
            'docs_reranked': self.docs_reranked,
            'cache_hit': self.cache_hit,
            'breakdown_pct': {
                'retrieve': round((self.retrieve_ms / self.total_ms) * 100, 1) if self.total_ms > 0 else 0,
                'rerank': round((self.rerank_ms / self.total_ms) * 100, 1) if self.total_ms > 0 else 0,
                'generate': round((self.generate_ms / self.total_ms) * 100, 1) if self.total_ms > 0 else 0,
            }
        }


class RagResponse:
    """Response with full observability data for students"""
    def __init__(self, answer: str, confidence: str, 
                 sources: List[Source], trace_id: str, 
                 metrics: Metrics, refusal: Optional[str] = None):
        self.answer = answer
        self.confidence = confidence
        self.sources = sources
        self.trace_id = trace_id
        self.metrics = metrics
        self.refusal = refusal
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'answer': self.answer,
            'confidence': self.confidence,
            'sources': [s.to_dict() for s in self.sources],
            'trace_id': self.trace_id,
            'metrics': self.metrics.to_dict(),
            'refusal': self.refusal
        }


# ============================================================================
# MIDDLEWARE
# ============================================================================

@app.before_request
def before_request():
    """Add request ID and start timing"""
    g.request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
    g.start_time = time.time()
    g.tenant = request.json.get('tenant', 'unknown') if request.json else 'unknown'
    
    logger.info(f"[{g.request_id}] Request started: {request.method} {request.path}")


@app.after_request
def after_request(response):
    """Add observability headers"""
    if hasattr(g, 'request_id'):
        response.headers['X-Request-ID'] = g.request_id
    
    if hasattr(g, 'start_time'):
        duration_ms = (time.time() - g.start_time) * 1000
        response.headers['X-Response-Time'] = f"{duration_ms:.2f}ms"
        
        logger.info(
            f"[{g.request_id}] Request completed: "
            f"status={response.status_code}, "
            f"duration={duration_ms:.2f}ms, "
            f"tenant={g.tenant}"
        )
    
    return response


# ============================================================================
# ROUTES
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Health check - students can use this to verify system is up"""
    return jsonify({
        'status': 'healthy',
        'service': 'rag-api',
        'version': '1.0.0'
    })


@app.route('/v1/rag/query', methods=['POST'])
def query():
    """
    Main RAG query endpoint with full observability
    
    Request:
    {
      "query": "What is retrieval augmented generation?",
      "tenant": "student1",
      "user_id": "u123",
      "plan_id": "hybrid_v1",  // optional
      "debug": false  // optional
    }
    
    Response:
    {
      "answer": "RAG combines retrieval and generation...",
      "confidence": "HIGH",
      "sources": [
        {"index": 1, "id": "doc_123", "score": 0.95, "origin": "rag"}
      ],
      "trace_id": "0x1234567890abcdef",
      "metrics": {
        "total_ms": 450.2,
        "retrieve_ms": 120.5,
        "rerank_ms": 80.3,
        "generate_ms": 200.1,
        "docs_retrieved": 10,
        "docs_reranked": 5,
        "breakdown_pct": {"retrieve": 26.7, "rerank": 17.8, "generate": 44.4}
      }
    }
    """
    with tracer.start_as_current_span("rag.request") as span:
        try:
            # 1. Parse request
            if not request.json:
                return jsonify({'error': 'Request body must be JSON'}), 400
            
            rag_req = RagRequest.from_dict(request.json)
            
            # 2. Set span attributes for observability
            span.set_attribute("tenant", rag_req.tenant)
            span.set_attribute("user_id", rag_req.user_id)
            span.set_attribute("plan_id", rag_req.plan_id)
            span.set_attribute("query_length", len(rag_req.query))
            
            # 3. Get trace ID for response
            ctx = span.get_span_context()
            trace_id = format(ctx.trace_id, '032x')
            
            logger.info(
                f"[{g.request_id}] RAG Query: tenant={rag_req.tenant}, "
                f"query='{rag_req.query[:50]}...', trace_id={trace_id}"
            )
            
            # 4. Execute retrieval
            start_retrieve = time.time()
            plan = RetrievalPlan(
                strategy=RetrievalStrategy.HYBRID_WITH_KG,
                top_k=10,
                rerank_top_k=5
            )
            
            result = orchestrator.retrieve(rag_req.query, plan)
            retrieve_ms = (time.time() - start_retrieve) * 1000
            
            # 5. Check for refusal
            if result.should_refuse:
                span.set_attribute("refused", True)
                span.set_attribute("refusal_reason", result.refusal_reason)
                
                return jsonify(RagResponse(
                    answer="",
                    confidence=result.confidence.value,
                    sources=[],
                    trace_id=trace_id,
                    metrics=Metrics(
                        total_ms=(time.time() - g.start_time) * 1000,
                        retrieve_ms=retrieve_ms,
                        rerank_ms=0,
                        generate_ms=0,
                        docs_retrieved=len(result.evidence),
                        docs_reranked=0
                    ),
                    refusal=result.refusal_reason
                ).to_dict()), 200
            
            # 6. Assemble prompt
            prompt_data = prompt_assembler.assemble(
                query=rag_req.query,
                evidence=result.evidence,
                template=PromptTemplate.QA_STANDARD,
                max_context_tokens=4096
            )
            
            # 7. Generate answer
            start_generate = time.time()
            answer = llm_generate(prompt_data['prompt'])
            generate_ms = (time.time() - start_generate) * 1000
            
            # 8. Build sources with [1], [2] citations
            sources = [
                Source(
                    index=i+1,
                    id=e.id,
                    content=e.content,
                    url=e.url,
                    title=e.title,
                    score=e.score,
                    origin=e.origin_tool.value
                )
                for i, e in enumerate(result.evidence[:5])
            ]
            
            # 9. Calculate metrics
            rerank_ms = result.timings.get('rerank', 0)
            total_ms = (time.time() - g.start_time) * 1000
            
            metrics = Metrics(
                total_ms=total_ms,
                retrieve_ms=retrieve_ms,
                rerank_ms=rerank_ms,
                generate_ms=generate_ms,
                docs_retrieved=len(result.evidence),
                docs_reranked=len([e for e in result.evidence if e.score > 0.5]),
                cache_hit=False  # TODO: Wire cache
            )
            
            # 10. Set observability attributes
            span.set_attribute("confidence", result.confidence.value)
            span.set_attribute("confidence_score", result.confidence_score)
            span.set_attribute("docs_retrieved", metrics.docs_retrieved)
            span.set_attribute("docs_reranked", metrics.docs_reranked)
            span.set_attribute("total_ms", metrics.total_ms)
            
            # 11. Build response
            response = RagResponse(
                answer=answer,
                confidence=result.confidence.value,
                sources=sources,
                trace_id=trace_id,
                metrics=metrics
            )
            
            logger.info(
                f"[{g.request_id}] RAG Response: "
                f"confidence={response.confidence}, "
                f"sources={len(sources)}, "
                f"total_ms={metrics.total_ms:.2f}"
            )
            
            return jsonify(response.to_dict()), 200
        
        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR))
            
            logger.error(f"[{g.request_id}] Error: {e}", exc_info=True)
            
            return jsonify({
                'error': str(e),
                'trace_id': format(span.get_span_context().trace_id, '032x')
            }), 500


@app.route('/v1/rag/plans', methods=['GET'])
def list_plans():
    """List available retrieval plans for students to experiment with"""
    plans = [
        {
            'id': 'vector_only_v1',
            'name': 'Vector Only',
            'description': 'Fast vector search only - good for semantic queries',
            'avg_latency_ms': 200,
            'use_case': 'When you need speed and have good semantic embeddings'
        },
        {
            'id': 'hybrid_v1',
            'name': 'Hybrid Search',
            'description': 'Vector + BM25 with reciprocal rank fusion',
            'avg_latency_ms': 350,
            'use_case': 'Best for most queries - balances semantic and keyword matching'
        },
        {
            'id': 'hybrid_kg_v1',
            'name': 'Hybrid + Knowledge Graph',
            'description': 'Hybrid search plus knowledge graph expansion',
            'avg_latency_ms': 500,
            'use_case': 'When you need related entities and connections'
        },
        {
            'id': 'full_search_v1',
            'name': 'Full Search',
            'description': 'Hybrid + KG + Web Search (slowest, most comprehensive)',
            'avg_latency_ms': 1200,
            'use_case': 'When thoroughness matters more than speed'
        }
    ]
    return jsonify({'plans': plans})


@app.route('/v1/rag/metrics/summary', methods=['GET'])
def metrics_summary():
    """Get overall system metrics - useful for student dashboards"""
    # TODO: Implement real metrics collection
    return jsonify({
        'total_queries': 0,
        'avg_latency_ms': 0,
        'p95_latency_ms': 0,
        'cache_hit_rate': 0,
        'avg_confidence': 0,
        'error_rate': 0
    })


# ============================================================================
# INITIALIZATION
# ============================================================================

def mock_llm_generate(prompt: str) -> str:
    """Mock LLM for testing - replace with real LLM"""
    return "This is a mock answer. Wire your LLM (Ollama, vLLM, or OpenAI) here."


def initialize_app():
    """Initialize RAG components"""
    global orchestrator, prompt_assembler, llm_generate
    
    # Mock vector search for now
    def mock_vector_search(query: str, k: int) -> List[Evidence]:
        return [
            Evidence(
                id=f"doc_{i}",
                content=f"Mock content {i} for query: {query}",
                origin_tool="rag",
                score=0.9 - (i * 0.1),
                title=f"Document {i}"
            )
            for i in range(min(k, 5))
        ]
    
    orchestrator = RAGOrchestrator(
        vector_search_fn=mock_vector_search
    )
    
    prompt_assembler = PromptAssembler()
    llm_generate = mock_llm_generate
    
    logger.info("RAG API initialized successfully")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    initialize_app()
    app.run(host='0.0.0.0', port=8080, debug=True)

