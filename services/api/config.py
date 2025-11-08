"""
Configuration for RAG API with feature flags
"""
import os
from typing import Literal

# Contract versioning
CONTRACT_VERSION = os.getenv("RAG_CONTRACT_VERSION", "1.0.0")

# Feature flags (default to safe: mocks ON, observability OFF)
ENABLE_OBS = int(os.getenv("RAG_ENABLE_OBS", "0")) == 1
USE_MOCK_LLM = int(os.getenv("RAG_USE_MOCK_LLM", "1")) == 1
USE_MOCK_VECTOR = int(os.getenv("RAG_USE_MOCK_VECTOR", "1")) == 1
USE_MOCK_WEB = int(os.getenv("RAG_USE_MOCK_WEB", "1")) == 1

# Pipeline parameters
FRESHNESS_HOURS = int(os.getenv("RAG_FRESHNESS_HOURS", "48"))
TOPN = int(os.getenv("RAG_TOPN", "8"))
AB_TEST_ENABLED = int(os.getenv("RAG_AB_TEST", "0")) == 1

# Service URLs
VECTOR_DB_URL = os.getenv("VECTOR_DB_URL", "http://vector-db:8001")
SEARCH_SERVICE_URL = os.getenv("SEARCH_SERVICE_URL", "http://search-service:8002")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
OTEL_COLLECTOR_URL = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")

# Prometheus metrics port
METRICS_PORT = int(os.getenv("METRICS_PORT", "9309"))

# Security
NO_PAYLOAD_LOGGING = True  # Never log payloads (PII/DLP compliance)

