"""
Shared configuration for all microservices
"""
import os
from pathlib import Path

# Service URLs (internal Docker network)
API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://api-gateway:8000")
INGEST_SERVICE_URL = os.getenv("INGEST_SERVICE_URL", "http://ingest-service:8001")
SEARCH_SERVICE_URL = os.getenv("SEARCH_SERVICE_URL", "http://search-service:8002")
CHAT_SERVICE_URL = os.getenv("CHAT_SERVICE_URL", "http://chat-service:8003")
DOCLING_SERVICE_URL = os.getenv("DOCLING_SERVICE_URL", "http://docling-service:8004")
VECTOR_DB_URL = os.getenv("VECTOR_DB_URL", "http://vector-db:8005")
EMBEDDING_SERVICE_URL = os.getenv("EMBEDDING_SERVICE_URL", "http://embedding-service:8006")
GRAPH_SERVICE_URL = os.getenv("GRAPH_SERVICE_URL", "http://graph-service:8007")
LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://llm-service:11434")

# Ollama Configuration (for services that need it directly)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
CHAT_MODEL = os.getenv("CHAT_MODEL", "llama3.2:3b")

# RAG Configuration
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
DEFAULT_SEARCH_LIMIT = int(os.getenv("DEFAULT_SEARCH_LIMIT", "10"))
MAX_CONTEXT_LENGTH = int(os.getenv("MAX_CONTEXT_LENGTH", "8000"))

# BM25 Index Path
BM25_INDEX_PATH = os.getenv("BM25_INDEX_PATH", "/indices/bm25_index.pkl")

# Agentic Chunking Configuration
AGENTIC_CHUNKING_ENABLED = os.getenv("AGENTIC_CHUNKING", "true").lower() == "true"
AGENTIC_TARGET_CHUNK_SIZE = int(os.getenv("AGENTIC_CHUNK_SIZE", str(CHUNK_SIZE)))
AGENTIC_MAX_CHUNK_SIZE = int(os.getenv("AGENTIC_MAX_CHUNK_SIZE", str(int(CHUNK_SIZE * 1.5))))

# ChromaDB Configuration
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "markdown_vault")
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "/chroma/chroma")

# File Upload Configuration
SUPPORTED_EXTENSIONS = [
    ".pdf",           # PDF documents
    ".doc", ".docx",  # Microsoft Word
    ".xls", ".xlsx",  # Microsoft Excel
    ".ppt", ".pptx",  # Microsoft PowerPoint
    ".txt",           # Plain text
    ".md", ".markdown", # Markdown
    ".rtf"            # Rich Text Format
]
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", str(100 * 1024 * 1024)))  # 100MB (increased for large PDFs)
UPLOAD_FOLDER = Path(os.getenv("UPLOAD_FOLDER", "/uploads"))

# Service Configuration
SERVICE_NAME = os.getenv("SERVICE_NAME", "unknown-service")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8000"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Monitoring Configuration
ENABLE_METRICS = os.getenv("ENABLE_METRICS", "true").lower() == "true"
METRICS_PORT = int(os.getenv("METRICS_PORT", "9090"))

print(f"🔧 Service: {SERVICE_NAME}")
print(f"🌐 Port: {SERVICE_PORT}")
print(f"📊 Metrics enabled: {ENABLE_METRICS}")

