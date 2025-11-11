"""
Prometheus metrics for RAG API
"""
from prometheus_client import Counter, Histogram

# Chunking metrics
CHUNKING_DOCS_TOTAL = Counter(
    "rag_chunking_docs_total",
    "Total documents processed by chunker",
    ["mode"]
)

CHUNKING_CHUNKS_TOTAL = Counter(
    "rag_chunking_chunks_total",
    "Total chunks emitted",
    ["mode"]
)

CHUNKING_TOKENS_TOTAL = Counter(
    "rag_chunking_tokens_total",
    "Total tokens across all chunks",
    ["mode"]
)

CHUNKING_AGENT_CALLS_TOTAL = Counter(
    "rag_chunking_agent_calls_total",
    "Agent calls for boundary detection",
    ["model", "status"]
)

CHUNKING_DURATION_SECONDS = Histogram(
    "rag_chunking_duration_seconds",
    "Chunking end-to-end duration (seconds)",
    ["mode"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0]
)

CHUNK_SIZE_TOKENS = Histogram(
    "rag_chunk_size_tokens",
    "Chunk size distribution (tokens)",
    buckets=[64, 128, 256, 384, 512, 640, 800, 1024, 1400, 2000]
)

# Retrieval metrics
RETRIEVAL_REQUESTS_TOTAL = Counter(
    "rag_retrieval_requests_total",
    "Total retrieval requests",
    ["source"]
)

RETRIEVAL_HITS_TOTAL = Counter(
    "rag_retrieval_hits_total",
    "Total retrieval hits",
    ["source"]
)

RETRIEVAL_DURATION_SECONDS = Histogram(
    "rag_retrieval_duration_seconds",
    "Retrieval duration (seconds)",
    ["source"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

