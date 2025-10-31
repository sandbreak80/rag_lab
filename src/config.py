"""
Configuration for Markdown RAG MCP Server
"""
import os
from pathlib import Path

# Vault Configuration
# Set VAULT_PATH environment variable or update docker-compose.override.yml
VAULT_PATH = Path(os.getenv("VAULT_PATH", "/vault"))
INDICES_PATH = Path(__file__).parent.parent / "indices"

# Ollama Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
CHAT_MODEL = os.getenv("CHAT_MODEL", "llama3.2:3b")  # Lighter/faster for performance

# Indexing Configuration
CHUNK_SIZE = 1000  # Characters per chunk
CHUNK_OVERLAP = 200  # Overlap between chunks
BATCH_SIZE = 10  # Number of documents to embed at once

# Search Configuration
DEFAULT_SEARCH_LIMIT = 10
MAX_CONTEXT_LENGTH = 8000  # Characters for RAG context

# ChromaDB Configuration
COLLECTION_NAME = "markdown_vault"
CHROMA_DB_PATH = INDICES_PATH / "chromadb"

# Supported file extensions
SUPPORTED_EXTENSIONS = [".md", ".markdown"]

# Ensure indices directory exists
INDICES_PATH.mkdir(parents=True, exist_ok=True)
CHROMA_DB_PATH.mkdir(parents=True, exist_ok=True)

print(f"📁 Vault path: {VAULT_PATH}")
print(f"💾 Indices path: {INDICES_PATH}")
print(f"🤖 Ollama URL: {OLLAMA_BASE_URL}")
print(f"🧠 Embedding model: {EMBEDDING_MODEL}")
print(f"💬 Chat model: {CHAT_MODEL}")



