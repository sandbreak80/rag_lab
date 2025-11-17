"""
Configuration module for RAG API
Reads environment variables with safe defaults
"""
import os

# Contract version
CONTRACT_VERSION = os.getenv("RAG_CONTRACT_VERSION", "1.0.0")

# Feature flags
ENABLE_OBS = os.getenv("RAG_ENABLE_OBS", "0") == "1"
USE_MOCK_LLM = os.getenv("RAG_USE_MOCK_LLM", "1") == "1"
USE_MOCK_VECTOR = os.getenv("RAG_USE_MOCK_VECTOR", "1") == "1"
USE_MOCK_WEB = os.getenv("RAG_USE_MOCK_WEB", "1") == "1"

# RAG pipeline configuration
FRESHNESS_HOURS = int(os.getenv("RAG_FRESHNESS_HOURS", "48"))
TOPN = int(os.getenv("RAG_TOPN", "8"))
AB_TEST_ENABLED = os.getenv("RAG_AB_TEST", "0") == "1"

# Agentic Chunking Configuration
CHUNKING_MODE = os.getenv("RAG_CHUNKING_MODE", "fixed")  # agentic | regex | fixed
CHUNK_TARGET_TOKENS = int(os.getenv("RAG_CHUNK_TARGET_TOKENS", "450"))
CHUNK_OVERLAP_TOKENS = int(os.getenv("RAG_CHUNK_OVERLAP_TOKENS", "128"))
CHUNK_AGENT_MODEL = os.getenv("RAG_CHUNK_AGENT_MODEL", "llama3.1:8b")
CHUNK_MAX_SECTIONS = int(os.getenv("RAG_CHUNK_MAX_SECTIONS", "200"))
CHUNK_AGENT_TIMEOUT_MS = int(os.getenv("RAG_CHUNK_AGENT_TIMEOUT_MS", "9000"))
CHUNK_EMIT_STAGE_TIMINGS = os.getenv("RAG_CHUNK_EMIT_STAGE_TIMINGS", "1") == "1"
CHUNK_EMIT_METADATA = os.getenv("RAG_CHUNK_EMIT_METADATA", "1") == "1"

# Service URLs
VECTOR_DB_URL = os.getenv("VECTOR_DB_URL", "http://vector-db:8005")
EMBEDDING_URL = os.getenv("EMBEDDING_URL", "http://embedding-service:8006")
EMBED_URL = os.getenv("EMBED_URL", "http://embedding-service:8006/embed")
SEARXNG_URL = os.getenv("SEARXNG_URL", "http://searxng:8080")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
SEARCH_SERVICE_URL = os.getenv("SEARCH_SERVICE_URL", "http://search-service:8002")
KNOWLEDGE_GRAPH_URL = os.getenv("KNOWLEDGE_GRAPH_URL", "http://knowledge-graph:8007")

# LLM Configuration
LLM_MODEL = os.getenv("RAG_LLM_MODEL", "llama3.2:3b")
LLM_MAX_TOKENS = int(os.getenv("RAG_LLM_MAX_TOKENS", "300"))

# OpenTelemetry
OTEL_COLLECTOR_URL = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4318")

# Temporary debug flags
DISABLE_ACL_FOR_DEBUG = os.getenv("RAG_DISABLE_ACL_FOR_DEBUG", "0") == "1"
