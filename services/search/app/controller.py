"""
Flask Controller for Production Search Service

Wires ProductionSearchService to HTTP endpoints with:
- Request validation
- Error handling
- Rate limiting
- CORS
- Health checks
"""

from flask import Flask, request, jsonify, g
from flask_cors import CORS
from functools import wraps
import time
import logging
from typing import Dict, Any

from services.search.app.production_service import (
    ProductionSearchService,
    SearchRequest,
    ServiceError,
    ErrorCode
)

logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global service instance (initialized in main)
search_service: ProductionSearchService = None


# ============================================================================
# MIDDLEWARE
# ============================================================================

def rate_limit(max_requests: int = 100, window_seconds: int = 60):
    """Rate limiting decorator"""
    # Simple in-memory rate limiter (use Redis in production)
    request_counts = {}

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            tenant_id = request.json.get('tenant_id') if request.json else None
            if not tenant_id:
                return jsonify({'error': 'Missing tenant_id'}), 400

            now = time.time()
            # Clean old entries
            request_counts[tenant_id] = [
                t for t in request_counts.get(tenant_id, [])
                if now - t < window_seconds
            ]

            if len(request_counts.get(tenant_id, [])) >= max_requests:
                return jsonify(ServiceError(
                    code=ErrorCode.RATE_LIMIT_EXCEEDED,
                    message=f"Rate limit exceeded: {max_requests} requests per {window_seconds}s",
                    retry_after=window_seconds
                ).to_dict()), 429

            # Record this request
            if tenant_id not in request_counts:
                request_counts[tenant_id] = []
            request_counts[tenant_id].append(now)

            return f(*args, **kwargs)
        return wrapper
    return decorator


def request_id_middleware():
    """Add request ID for tracing"""
    @app.before_request
    def before_request():
        import uuid
        g.request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        g.start_time = time.time()

    @app.after_request
    def after_request(response):
        if hasattr(g, 'request_id'):
            response.headers['X-Request-ID'] = g.request_id
        if hasattr(g, 'start_time'):
            duration_ms = (time.time() - g.start_time) * 1000
            response.headers['X-Response-Time'] = f"{duration_ms:.2f}ms"
        return response


# ============================================================================
# ROUTES
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'production-search',
        'version': '1.0.0'
    })


@app.route('/ready', methods=['GET'])
def readiness_check():
    """Readiness check (checks dependencies)"""
    # TODO: Check Redis, vector DB, etc.
    return jsonify({
        'status': 'ready',
        'checks': {
            'redis': 'ok',
            'vector_db': 'ok',
            'llm': 'ok'
        }
    })


@app.route('/api/search', methods=['POST'])
@rate_limit(max_requests=100, window_seconds=60)
def search():
    """
    Main search endpoint

    Request:
    {
      "tenant_id": "acme",
      "user_id": "u123",
      "query": "How do I rotate access keys?",
      "top_k": 20,
      "retrieval_plan_id": "hybrid_v3",
      "template_id": "qa_standard_v2",
      "authz_context": {"roles": ["support"], "doc_policies": ["public", "acme-confidential"]},
      "enable_cache": true,
      "enable_fallback": true
    }

    Response:
    {
      "answer": "...",
      "confidence": "MEDIUM",
      "citations": [...],
      "telemetry": {...},
      "refusal": null
    }
    """
    try:
        # Validate request
        if not request.json:
            return jsonify(ServiceError(
                code=ErrorCode.INVALID_REQUEST,
                message="Request body must be JSON"
            ).to_dict()), 400

        # Required fields
        required = ['tenant_id', 'user_id', 'query']
        missing = [f for f in required if f not in request.json]
        if missing:
            return jsonify(ServiceError(
                code=ErrorCode.INVALID_REQUEST,
                message=f"Missing required fields: {missing}"
            ).to_dict()), 400

        # Parse request
        search_req = SearchRequest.from_dict(request.json)

        # Log request
        logger.info(
            f"Search request: tenant={search_req.tenant_id}, "
            f"user={search_req.user_id}, query={search_req.query[:50]}, "
            f"plan={search_req.retrieval_plan_id}, request_id={g.request_id}"
        )

        # Execute search
        response = search_service.search(search_req)

        # Log response
        logger.info(
            f"Search response: tenant={search_req.tenant_id}, "
            f"confidence={response.confidence}, "
            f"citations={len(response.citations)}, "
            f"cache={response.telemetry.cache_hit}, "
            f"latency={response.telemetry.total_ms:.2f}ms, "
            f"request_id={g.request_id}"
        )

        return jsonify(response.to_dict()), 200

    except ServiceError as e:
        logger.warning(f"Service error: {e.code.value} - {e.message}, request_id={g.request_id}")
        return jsonify(e.to_dict()), 400 if e.code == ErrorCode.INVALID_REQUEST else 500

    except Exception as e:
        logger.error(f"Unexpected error: {e}, request_id={g.request_id}", exc_info=True)
        return jsonify(ServiceError(
            code=ErrorCode.INTERNAL_ERROR,
            message="Internal server error"
        ).to_dict()), 500


@app.route('/api/cache/invalidate', methods=['POST'])
def invalidate_cache():
    """
    Cache invalidation endpoint

    Request:
    {
      "tenant_id": "acme",
      "plan_id": "hybrid_v3"  // optional
    }
    """
    try:
        if not request.json or 'tenant_id' not in request.json:
            return jsonify(ServiceError(
                code=ErrorCode.INVALID_REQUEST,
                message="Missing tenant_id"
            ).to_dict()), 400

        tenant_id = request.json['tenant_id']
        plan_id = request.json.get('plan_id')

        search_service.cache.invalidate_tenant(tenant_id, plan_id)

        return jsonify({
            'status': 'invalidated',
            'tenant_id': tenant_id,
            'plan_id': plan_id
        }), 200

    except Exception as e:
        logger.error(f"Cache invalidation error: {e}", exc_info=True)
        return jsonify(ServiceError(
            code=ErrorCode.INTERNAL_ERROR,
            message="Cache invalidation failed"
        ).to_dict()), 500


@app.route('/api/plans', methods=['GET'])
def list_plans():
    """List available retrieval plans"""
    # TODO: Load from config/database
    plans = [
        {
            'id': 'vector_v1',
            'name': 'Vector Only',
            'description': 'Fast vector search only',
            'latency_p95': '200ms',
            'cost': 'low'
        },
        {
            'id': 'hybrid_v3',
            'name': 'Hybrid Search',
            'description': 'Vector + BM25 with RRF reranking',
            'latency_p95': '500ms',
            'cost': 'medium'
        },
        {
            'id': 'full_v2',
            'name': 'Full Search',
            'description': 'Hybrid + Knowledge Graph + Web',
            'latency_p95': '1200ms',
            'cost': 'high'
        }
    ]
    return jsonify({'plans': plans})


@app.route('/api/templates', methods=['GET'])
def list_templates():
    """List available prompt templates"""
    templates = [
        {
            'id': 'qa_standard_v2',
            'name': 'QA Standard',
            'description': 'Concise Q&A with citations',
            'max_tokens': 4096
        },
        {
            'id': 'qa_detailed_v2',
            'name': 'QA Detailed',
            'description': 'Comprehensive answers with reasoning',
            'max_tokens': 8192
        },
        {
            'id': 'research_v1',
            'name': 'Research',
            'description': 'Multi-source synthesis',
            'max_tokens': 8192
        }
    ]
    return jsonify({'templates': templates})


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}", exc_info=True)
    return jsonify(ServiceError(
        code=ErrorCode.INTERNAL_ERROR,
        message="Internal server error"
    ).to_dict()), 500


# ============================================================================
# INITIALIZATION
# ============================================================================

def init_service(
    orchestrator,
    prompt_assembler,
    cache,
    authz_filter,
    failure_policy,
    llm_generate_fn
):
    """Initialize search service"""
    global search_service
    search_service = ProductionSearchService(
        orchestrator=orchestrator,
        prompt_assembler=prompt_assembler,
        cache=cache,
        authz_filter=authz_filter,
        failure_policy=failure_policy,
        llm_generate_fn=llm_generate_fn
    )
    request_id_middleware()


if __name__ == '__main__':
    # For local testing only
    app.run(host='0.0.0.0', port=8000, debug=True)

