"""
RAG Lab API v1 - FastAPI application with complete observability
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import REGISTRY
import logging
import time
import os

from .config import CONTRACT_VERSION, ENABLE_OBS, OTEL_COLLECTOR_URL
from .routes.rag import router as rag_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# OpenTelemetry Setup
# ============================================================================
if ENABLE_OBS:
    resource = Resource.create({"service.name": "rag-api", "service.version": CONTRACT_VERSION})
    tracer_provider = TracerProvider(resource=resource)

    # OTLP exporter to collector
    otlp_exporter = OTLPSpanExporter(endpoint=OTEL_COLLECTOR_URL, insecure=True)
    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(span_processor)

    trace.set_tracer_provider(tracer_provider)
    logger.info(f"✅ OpenTelemetry configured: exporter={OTEL_COLLECTOR_URL}")
else:
    logger.info("⚠️  OpenTelemetry DISABLED (RAG_ENABLE_OBS=0)")

# ============================================================================
# Prometheus Metrics
# ============================================================================
# Request metrics
REQUEST_COUNT = Counter(
    'rag_requests_total',
    'Total RAG requests',
    ['endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'rag_request_duration_seconds',
    'RAG request latency',
    ['endpoint'],
    buckets=[0.1, 0.5, 1.0, 2.0, 3.5, 5.0, 10.0]
)

# Quality metrics
CITATION_RATE = Histogram(
    'rag_citation_rate',
    'Citations per response',
    buckets=[0, 1, 2, 3, 5, 10]
)

FRESHNESS_VIOLATIONS = Counter(
    'rag_freshness_violations_total',
    'Recency gate failures'
)

PROVENANCE_MISSING = Counter(
    'rag_provenance_missing_total',
    'Responses with missing origin_tool'
)

# ============================================================================
# FastAPI Application
# ============================================================================
app = FastAPI(
    title="RAG Lab API v1",
    description="Production RAG API with complete observability contract",
    version=CONTRACT_VERSION,
    docs_url="/docs" if os.getenv("ENABLE_DOCS", "1") == "1" else None
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instrument FastAPI with OTel
if ENABLE_OBS:
    FastAPIInstrumentor.instrument_app(app)

# Include routers
app.include_router(rag_router)
app.include_router(health.router, tags=["health"])

# ============================================================================
# Middleware - Request Logging & Metrics
# ============================================================================
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log requests and emit metrics (NO PAYLOAD LOGGING)"""
    start_time = time.time()

    try:
        response = await call_next(request)
        latency = time.time() - start_time

        # Emit Prometheus metrics
        REQUEST_COUNT.labels(
            endpoint=request.url.path,
            status=response.status_code
        ).inc()

        REQUEST_LATENCY.labels(
            endpoint=request.url.path
        ).observe(latency)

        # Log (no payloads)
        logger.info(
            f"{request.method} {request.url.path} - "
            f"status={response.status_code} latency={latency:.3f}s"
        )

        return response

    except Exception as e:
        latency = time.time() - start_time
        REQUEST_COUNT.labels(endpoint=request.url.path, status=500).inc()
        logger.error(f"{request.method} {request.url.path} - ERROR: {e}")
        raise

# ============================================================================
# Health Endpoints
# ============================================================================
@app.get("/live", tags=["health"])
async def liveness():
    """
    Liveness probe - returns 200 if process is running.
    No dependency checks.
    """
    return {"status": "alive", "service": "rag-api", "version": CONTRACT_VERSION}


@app.get("/ready", tags=["health"])
async def readiness():
    """
    Readiness probe - checks dependencies and startup grace period.
    Returns 200 only if service is ready to accept traffic.
    """
    import aiohttp

    # Check OTel collector (if observability enabled)
    otel_ready = True
    if ENABLE_OBS:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://otel-collector:13133/", timeout=aiohttp.ClientTimeout(total=2)) as resp:
                    otel_ready = resp.status == 200
        except:
            otel_ready = False

    # Check vector DB (if not using mocks)
    from config import USE_MOCK_VECTOR, VECTOR_DB_URL
    vector_ready = True
    if not USE_MOCK_VECTOR:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{VECTOR_DB_URL}/health", timeout=aiohttp.ClientTimeout(total=2)) as resp:
                    vector_ready = resp.status == 200
        except:
            vector_ready = False

    all_ready = otel_ready and vector_ready

    if not all_ready:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "checks": {
                    "otel_collector": "ok" if otel_ready else "failed",
                    "vector_db": "ok" if vector_ready else "failed (mocked)" if USE_MOCK_VECTOR else "failed"
                }
            }
        )

    return {
        "status": "ready",
        "service": "rag-api",
        "version": CONTRACT_VERSION,
        "observability_enabled": ENABLE_OBS
    }


@app.get("/health", tags=["health"])
async def health():
    """
    Legacy health endpoint (combines liveness + readiness).
    For backwards compatibility.
    """
    liveness_result = await liveness()

    try:
        readiness_result = await readiness()
        is_ready = readiness_result.get("status") == "ready" if isinstance(readiness_result, dict) else False
    except:
        is_ready = False

    return {
        "status": "healthy" if is_ready else "degraded",
        "live": True,
        "ready": is_ready,
        "service": "rag-api",
        "version": CONTRACT_VERSION
    }


@app.get("/metrics", tags=["observability"])
async def metrics():
    """Prometheus metrics endpoint"""
    from fastapi.responses import Response
    return Response(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)


@app.get("/", tags=["info"])
async def root():
    """API info endpoint"""
    return {
        "service": "RAG Lab API v1",
        "version": CONTRACT_VERSION,
        "contract_version": CONTRACT_VERSION,
        "observability_enabled": ENABLE_OBS,
        "endpoints": {
            "rag_query": "/v1/rag/query",
            "health": "/health",
            "liveness": "/live",
            "readiness": "/ready",
            "metrics": "/metrics",
            "docs": "/docs"
        },
        "feature_flags": {
            "enable_obs": ENABLE_OBS,
            "use_mock_llm": os.getenv("RAG_USE_MOCK_LLM", "1"),
            "use_mock_vector": os.getenv("RAG_USE_MOCK_VECTOR", "1"),
            "use_mock_web": os.getenv("RAG_USE_MOCK_WEB", "1")
        }
    }


# ============================================================================
# Startup Event
# ============================================================================
@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    logger.info("=" * 60)
    logger.info("🚀 RAG Lab API v1 Starting")
    logger.info("=" * 60)
    logger.info(f"   Contract Version: {CONTRACT_VERSION}")
    logger.info(f"   Observability: {'ENABLED' if ENABLE_OBS else 'DISABLED'}")
    logger.info(f"   Mock LLM: {os.getenv('RAG_USE_MOCK_LLM', '1')}")
    logger.info(f"   Mock Vector: {os.getenv('RAG_USE_MOCK_VECTOR', '1')}")
    logger.info(f"   Mock Web: {os.getenv('RAG_USE_MOCK_WEB', '1')}")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 RAG Lab API v1 Shutting Down")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8080,
        log_level="info",
        access_log=True
    )
