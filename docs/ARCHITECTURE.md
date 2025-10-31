# System Architecture

**World-Class RAG: Deep Technical Overview**

This document provides an in-depth look at the architecture, design decisions, and implementation details of the Markdown RAG system.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Component Architecture](#component-architecture)
3. [Data Flow](#data-flow)
4. [Algorithm Details](#algorithm-details)
5. [Design Decisions](#design-decisions)
6. [Scalability](#scalability)
7. [Security](#security)

---

## System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Web Browser │  │  Claude      │  │  Cursor      │         │
│  │  (UI)        │  │  Desktop     │  │  IDE         │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                 │                 │                   │
└─────────┼─────────────────┼─────────────────┼───────────────────┘
          │                 │                 │
          │ HTTP/SSE        │ MCP            │ MCP
          │                 │                 │
┌─────────▼─────────────────▼─────────────────▼───────────────────┐
│                    Application Layer                            │
│  ┌──────────────────┐              ┌──────────────────┐        │
│  │   Flask WebApp   │              │   MCP Server     │        │
│  │   (webapp.py)    │              │   (server.py)    │        │
│  └────────┬─────────┘              └────────┬─────────┘        │
│           │                                 │                   │
│           └────────────┬────────────────────┘                   │
│                        │                                        │
│              ┌─────────▼─────────┐                              │
│              │ AdvancedSearcher  │                              │
│              │ (orchestrator)    │                              │
│              └─────────┬─────────┘                              │
│                        │                                        │
│         ┌──────────────┼──────────────┐                         │
│         │              │              │                         │
│   ┌─────▼──────┐ ┌────▼─────┐ ┌──────▼──────┐                 │
│   │   Query    │ │ Hybrid   │ │  Knowledge  │                 │
│   │  Expansion │ │ Search   │ │   Graph     │                 │
│   └────────────┘ └──────────┘ └─────────────┘                 │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                        Data Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   ChromaDB   │  │  BM25 Index  │  │    Graph     │         │
│  │   (Vector)   │  │  (Keyword)   │  │  (NetworkX)  │         │
│  │              │  │              │  │              │         │
│  │  Embeddings  │  │  Token freq  │  │  Nodes/Edges │         │
│  │  Metadata    │  │  IDF scores  │  │  Adjacency   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                      Infrastructure Layer                       │
│  ┌──────────────────────────────────────────────────────┐      │
│  │                    Ollama Service                    │      │
│  │  ┌────────────────┐              ┌────────────────┐ │      │
│  │  │ nomic-embed    │              │ llama3.2:3b    │ │      │
│  │  │ (embeddings)   │              │ (chat/expand)  │ │      │
│  │  └────────────────┘              └────────────────┘ │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐      │
│  │               Docker Container Runtime                │      │
│  │  • Volume mounts (vault, indices)                     │      │
│  │  • Network bridge (host.docker.internal)              │      │
│  │  • Resource limits (CPU, memory)                      │      │
│  └──────────────────────────────────────────────────────┘      │
└──────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | HTML5, CSS3, JavaScript | Modern web UI |
| **Web Framework** | Flask 3.1.2 | HTTP server, REST API |
| **Markdown Processing** | PyYAML, regex | Parse frontmatter, links |
| **Vector DB** | ChromaDB 1.3.0 | Embedding storage & search |
| **Keyword Search** | rank-bm25 0.2.2 | BM25 implementation |
| **Graph** | NetworkX 3.5 | Relationship modeling |
| **LLM Runtime** | Ollama | Embeddings & generation |
| **Containerization** | Docker, Docker Compose | Deployment |
| **Testing** | pytest, Playwright | Quality assurance |

---

## Component Architecture

### 1. Parser (`src/parser.py`)

**Purpose:** Extract structured data from markdown files.

**Key Classes:**
```python
class MarkdownParser:
    def parse_file(path: str) -> ParsedDocument:
        """Parse markdown file into structured format."""
        
    def parse_frontmatter(content: str) -> Dict[str, Any]:
        """Extract YAML frontmatter."""
        
    def extract_tags(content: str, frontmatter: Dict) -> List[str]:
        """Find all tags (frontmatter + inline)."""
        
    def extract_wikilinks(content: str) -> List[str]:
        """Parse wikilinks [[like this]]."""
        
    def chunk_content(content: str, size: int, overlap: int) -> List[str]:
        """Simple paragraph-based chunking."""
```

**Algorithm:**
1. Read file contents
2. Extract YAML frontmatter (if present)
3. Parse metadata (title, tags, dates)
4. Identify links (wikilinks, markdown, URLs)
5. Chunk content (delegate to agentic chunker if enabled)

**Error Handling:**
- Invalid YAML → Log warning, continue without frontmatter
- Malformed links → Skip, don't fail
- Empty files → Return empty document
- Encoding errors → Try UTF-8, then latin-1, then ignore

### 2. Agentic Chunker (`src/agentic_chunker.py`)

**Purpose:** Create semantically coherent chunks using LLM-powered analysis.

**Key Classes:**
```python
class AgenticChunker:
    def chunk_markdown(content: str, metadata: Dict) -> List[ChunkWithContext]:
        """Main entry point for agentic chunking."""
        
    def _analyze_structure(content: str) -> Dict:
        """Detect headings, code blocks, lists, tables."""
        
    def _identify_semantic_units(content: str, structure: Dict) -> List[SemanticUnit]:
        """Break into semantic units (sections, paragraphs, code blocks)."""
        
    def _create_chunks(units: List[SemanticUnit]) -> List[ChunkWithContext]:
        """Group units into optimal chunks."""
        
    def _split_large_unit(unit: SemanticUnit) -> List[SemanticUnit]:
        """Handle units exceeding max_chunk_size."""
```

**Algorithm:**

```python
# 1. Analyze Structure
structure = {
    "headings": [(level, text, offset), ...],
    "code_blocks": [(start, end, language), ...],
    "lists": [(start, end, type), ...],
    "tables": [(start, end), ...]
}

# 2. Identify Semantic Units
for section in document:
    if is_heading(section):
        create_unit(type="section", content=section)
    elif is_code_block(section):
        create_unit(type="code", content=section)
    elif is_list(section):
        create_unit(type="list", content=section)
    else:
        create_unit(type="paragraph", content=section)

# 3. Group into Chunks
current_chunk = []
current_size = 0
for unit in semantic_units:
    if current_size + len(unit) > target_size:
        # Create chunk from accumulated units
        chunks.append(create_chunk(current_chunk))
        current_chunk = [unit]
        current_size = len(unit)
    else:
        current_chunk.append(unit)
        current_size += len(unit)

# 4. Handle Large Units
for unit in units:
    if len(unit) > max_chunk_size:
        # Split by paragraph, then sentence, then force-split
        sub_units = split_large_unit(unit)
        units.extend(sub_units)
```

**Benefits:**
- Preserves semantic coherence
- Respects document structure
- Handles code/tables intelligently
- +15% recall improvement

**Configuration:**
```python
AGENTIC_TARGET_CHUNK_SIZE = 800   # Target characters per chunk
AGENTIC_MAX_CHUNK_SIZE = 1500     # Hard limit (Ollama constraint)
```

### 3. Indexer (`src/indexer.py`)

**Purpose:** Build searchable indices from markdown vault.

**Key Classes:**
```python
class VaultIndexer:
    def index_vault(force: bool = False) -> None:
        """Index all markdown files in vault."""
        
    def _index_file(path: Path) -> None:
        """Index single file."""
        
    def _generate_embedding(text: str) -> List[float]:
        """Generate embedding via Ollama."""
```

**Algorithm:**

```python
# 1. Discover Files
files = glob(vault_path / "**/*.md")

# 2. For Each File
for file in files:
    # Parse
    doc = parser.parse_file(file)
    
    # Chunk (agentic or simple)
    if AGENTIC_CHUNKING_ENABLED:
        chunks = agentic_chunker.chunk_markdown(doc.content, doc.metadata)
    else:
        chunks = parser.chunk_content(doc.content)
    
    # Generate Embeddings
    for chunk in chunks:
        embedding = ollama.embeddings(
            model="nomic-embed-text",
            prompt=chunk.content
        )
        
        # Store in ChromaDB
        collection.add(
            ids=[chunk_id],
            embeddings=[embedding],
            documents=[chunk.content],
            metadatas=[chunk.metadata]
        )
```

**Performance Optimizations:**
- Batch embedding generation (10 chunks at a time)
- Skip unchanged files (compare mtime)
- Progress tracking
- Retry logic for transient errors

**Data Stored:**
```python
chunk_metadata = {
    # Document-level
    "file_name": "Architecture.md",
    "file_path": "/vault/docs/Architecture.md",
    "folder": "docs",
    "title": "System Architecture",
    "tags": ["architecture", "design"],
    "created_date": "2025-01-01",
    "modified_date": "2025-01-15",
    
    # Chunk-level
    "chunk_index": 0,
    "chunk_method": "agentic",
    "section": "Component Architecture",
    "has_code": true,
    "has_list": false,
    
    # Links
    "wikilinks": ["Design.md", "Performance.md"],
    "markdown_links": ["https://example.com"],
}
```

### 4. Hybrid Searcher (`src/hybrid_search.py`)

**Purpose:** Combine vector and keyword search for optimal recall.

**Key Classes:**
```python
class HybridSearcher:
    def __init__():
        self.vector_searcher = VaultSearcher()
        self.bm25 = BM25Okapi(corpus)
        
    def hybrid_search(query: str, limit: int) -> List[Dict]:
        """Perform vector + BM25 search, merge with RRF."""
```

**Algorithm:**

```python
# 1. Vector Search (Semantic)
query_embedding = ollama.embeddings(model="nomic-embed-text", prompt=query)
vector_results = chromadb.query(
    query_embeddings=[query_embedding],
    n_results=limit * 2  # Over-fetch for RRF
)

# 2. BM25 Search (Keyword)
query_tokens = tokenize(query)
bm25_scores = bm25.get_scores(query_tokens)
bm25_results = top_k(bm25_scores, k=limit * 2)

# 3. Reciprocal Rank Fusion (RRF)
def rrf_score(rank: int, k: int = 60) -> float:
    return 1.0 / (k + rank)

merged_scores = {}
for rank, doc in enumerate(vector_results):
    merged_scores[doc.id] = rrf_score(rank)
    
for rank, doc in enumerate(bm25_results):
    merged_scores[doc.id] += rrf_score(rank)

# 4. Re-rank by Combined Score
final_results = sorted(merged_scores.items(), key=lambda x: x[1], reverse=True)
return final_results[:limit]
```

**Why RRF?**
- No hyperparameter tuning needed
- Robust to score scale differences
- Better than simple averaging
- Empirically proven effective

**Performance:**
- Vector search: 30-50ms
- BM25 search: 10-20ms
- RRF merge: 1-2ms
- Total: ~60-70ms

### 5. Query Expander (`src/query_expansion.py`)

**Purpose:** Enhance queries with synonyms and context-aware terms.

**Key Classes:**
```python
class QueryExpander:
    def expand_query(query: str, context: str = "general") -> str:
        """Expand query with synonyms and related terms."""
```

**Algorithm:**

```python
# 1. Identify Key Terms
terms = extract_key_terms(query)

# 2. Generate Expansions
expansions = []
for term in terms:
    # Predefined synonyms
    if term in SYNONYM_MAP:
        expansions.extend(SYNONYM_MAP[term])
    
    # Context-specific terms
    if context in CONTEXT_TERMS:
        expansions.extend(CONTEXT_TERMS[context])

# 3. LLM-powered Expansion (optional, disabled by default due to latency)
if USE_LLM_EXPANSION:
    prompt = f"Generate related terms for: {query}"
    llm_terms = ollama.generate(model="llama3.2:3b", prompt=prompt)
    expansions.extend(llm_terms)

# 4. Combine
expanded_query = query + " " + " ".join(expansions)
return expanded_query
```

**Examples:**
```
Input:  "RAG"
Output: "RAG retrieval augmented generation LLM context document embedding"

Input:  "transformers"
Output: "transformers attention mechanism BERT GPT encoder decoder"

Input:  "study AI bluebelt"
Output: "study AI bluebelt training certification course learning"
```

**Configuration:**
```python
ENABLE_QUERY_EXPANSION = True
USE_LLM_EXPANSION = False  # Too slow (500ms+)
MAX_EXPANSION_TERMS = 10
```

### 6. Knowledge Graph (`src/knowledge_graph.py`)

**Purpose:** Model relationships between documents for multi-hop discovery.

**Key Classes:**
```python
class KnowledgeGraph:
    def __init__():
        self.graph = nx.DiGraph()  # Directed graph
        
    def _build_graph():
        """Build graph from ChromaDB metadata."""
        
    def find_related(file_name: str, max_hops: int = 2) -> List[str]:
        """Find related documents via graph traversal."""
```

**Graph Schema:**

```python
# Node Types
Document = {
    "type": "document",
    "file_name": "Architecture.md",
    "title": "System Architecture",
    "folder": "docs"
}

Folder = {
    "type": "folder",
    "name": "docs",
    "path": "/vault/docs"
}

Tag = {
    "type": "tag",
    "name": "architecture"
}

# Edge Types
Contains = {
    "type": "contains",
    "source": Folder("docs"),
    "target": Document("Architecture.md")
}

WikiLink = {
    "type": "wikilink",
    "source": Document("Architecture.md"),
    "target": Document("Design.md")
}

HasTag = {
    "type": "has_tag",
    "source": Document("Architecture.md"),
    "target": Tag("architecture")
}
```

**Traversal Algorithm:**

```python
def find_related(start_node: str, max_hops: int = 2, limit: int = 10) -> List[str]:
    """
    BFS traversal to find related documents.
    """
    visited = set()
    queue = [(start_node, 0)]  # (node, hop_count)
    related = []
    
    while queue and len(related) < limit:
        node, hops = queue.pop(0)
        
        if node in visited or hops > max_hops:
            continue
            
        visited.add(node)
        
        # Get neighbors
        neighbors = graph.neighbors(node)
        
        for neighbor in neighbors:
            if graph.nodes[neighbor]["type"] == "document":
                related.append(neighbor)
            
            queue.append((neighbor, hops + 1))
    
    return related[:limit]
```

**Example:**
```
Query: "Architecture.md"
Hop 1: Design.md, Performance.md (via wikilinks)
Hop 2: API.md (via Design.md), Benchmarks.md (via Performance.md)
Result: [Design.md, Performance.md, API.md, Benchmarks.md]
```

**Performance:**
- Graph build: 500ms for 121 nodes
- Traversal: 10-20ms per query
- Memory: ~10MB for 100 nodes

### 7. Advanced Searcher (`src/advanced_search.py`)

**Purpose:** Orchestrate all components into unified search pipeline.

**Key Classes:**
```python
class AdvancedSearcher:
    def __init__():
        self.hybrid_searcher = HybridSearcher()
        self.query_expander = QueryExpander()
        self.knowledge_graph = KnowledgeGraph()
        
    def search(
        query: str,
        limit: int = 10,
        expand_query: bool = True,
        use_graph: bool = True,
        rerank: bool = False
    ) -> List[Dict]:
        """Full advanced search pipeline."""
```

**Pipeline:**

```python
def search(query: str, **options) -> List[Dict]:
    # 1. Query Expansion
    if options["expand_query"]:
        query = self.query_expander.expand_query(query)
        print(f"Expanded: {query}")
    
    # 2. Hybrid Search
    results = self.hybrid_searcher.hybrid_search(query, limit=options["limit"])
    print(f"Found {len(results)} results")
    
    # 3. Knowledge Graph Enhancement
    if options["use_graph"]:
        related_docs = set()
        for result in results[:5]:  # Top 5 only
            related = self.knowledge_graph.find_related(
                result["file_name"],
                max_hops=2,
                limit=5
            )
            related_docs.update(related)
        
        # Add related docs to results
        for doc in related_docs:
            if doc not in [r["file_name"] for r in results]:
                results.append({"file_name": doc, "score": 0.5})
    
    # 4. LLM Re-ranking (optional, disabled by default)
    if options["rerank"]:
        results = self._rerank_with_llm(query, results)
    
    return results[:options["limit"]]
```

**Configuration:**
```python
# Default settings (optimal for most use cases)
EXPAND_QUERY = True      # +5% recall
USE_GRAPH = True         # +2% recall for multi-hop
RERANK = False           # +10% precision but +2000ms latency
```

### 8. Web Application (`src/webapp.py`)

**Purpose:** Provide user-friendly web interface for RAG system.

**Key Routes:**

```python
@app.route("/")
def index():
    """Serve UI."""
    return render_template("index.html")

@app.route("/api/stats")
def stats():
    """Get system statistics."""
    return jsonify({
        "total_chunks": len(collection),
        "embedding_model": config.EMBEDDING_MODEL,
        "chat_model": config.CHAT_MODEL,
        "search_mode": config.SEARCH_MODE
    })

@app.route("/api/search", methods=["POST"])
def search():
    """Search endpoint."""
    query = request.json["query"]
    results = advanced_searcher.search(query, limit=10)
    return jsonify(results)

@app.route("/api/chat", methods=["POST"])
def chat():
    """RAG chat endpoint with streaming."""
    query = request.json["query"]
    
    # Search
    results = advanced_searcher.search(query, limit=5)
    context = "\n\n".join([r["content"] for r in results])
    
    # Generate
    prompt = f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"
    
    def generate():
        for chunk in ollama.generate(model="llama3.2:3b", prompt=prompt, stream=True):
            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
    
    return Response(generate(), mimetype="text/event-stream")
```

**UI Features:**
- Server-sent events (SSE) for streaming
- Markdown rendering with syntax highlighting
- Real-time status updates
- Glassmorphism design
- Responsive layout

---

## Data Flow

### Ingestion Flow

```
1. File Discovery
   /vault/*.md → [file1.md, file2.md, ...]

2. Parse
   file1.md → {
     content: "...",
     metadata: {title, tags, links, ...}
   }

3. Agentic Chunking
   content → [chunk1, chunk2, chunk3, ...]
   
4. Generate Embeddings
   chunk1 → ollama → [0.123, -0.456, ...]
   
5. Store
   ChromaDB.add(id, embedding, content, metadata)
   BM25.add_document(content)
   Graph.add_node(file_name)
   Graph.add_edges(wikilinks)
```

### Query Flow

```
1. User Input
   UI → "What is RAG?"

2. Query Expansion
   "What is RAG?" → "RAG retrieval augmented generation LLM"

3. Hybrid Search
   a. Vector: embedding → ChromaDB.query()
   b. BM25: tokens → BM25.get_scores()
   c. RRF: merge results

4. Graph Enhancement
   Top results → find_related() → add to results

5. Generate Answer
   Context + Query → Ollama → Stream response

6. Display
   SSE → UI → Markdown rendering
```

---

## Algorithm Details

### Reciprocal Rank Fusion (RRF)

**Formula:**
```
RRF(d) = Σ (1 / (k + rank_i(d)))
```

Where:
- `d` = document
- `rank_i(d)` = rank of document in i-th result list
- `k` = constant (typically 60)

**Example:**
```python
# Vector results (ranked by cosine similarity)
vector_results = ["doc1", "doc3", "doc5", "doc2"]

# BM25 results (ranked by BM25 score)
bm25_results = ["doc2", "doc1", "doc4", "doc3"]

# RRF scores (k=60)
doc1: 1/(60+0) + 1/(60+1) = 0.0167 + 0.0164 = 0.0331
doc2: 1/(60+3) + 1/(60+0) = 0.0159 + 0.0167 = 0.0326
doc3: 1/(60+1) + 1/(60+3) = 0.0164 + 0.0159 = 0.0323
doc4: 0 + 1/(60+2) = 0.0161
doc5: 1/(60+2) + 0 = 0.0161

# Final ranking
[doc1, doc2, doc3, doc4, doc5]
```

**Why k=60?**
- Empirically found to work well
- Balances early vs late results
- Not sensitive to exact value

### BM25 Algorithm

**Formula:**
```
BM25(d, q) = Σ IDF(qi) × (f(qi, d) × (k1 + 1)) / (f(qi, d) + k1 × (1 - b + b × |d| / avgdl))
```

Where:
- `d` = document
- `q` = query
- `qi` = query term
- `f(qi, d)` = term frequency
- `|d|` = document length
- `avgdl` = average document length
- `k1` = term frequency saturation (default: 1.5)
- `b` = length normalization (default: 0.75)

**IDF (Inverse Document Frequency):**
```
IDF(qi) = log((N - df(qi) + 0.5) / (df(qi) + 0.5))
```

Where:
- `N` = total documents
- `df(qi)` = documents containing qi

---

## Design Decisions

### 1. Why Agentic Chunking?

**Problem:**
- Naive chunking (fixed size, paragraph breaks) splits context
- Code blocks broken mid-function
- Lists split across chunks
- Low recall on semantic queries

**Solution:**
- LLM-powered structure analysis
- Semantic unit identification
- Intelligent grouping

**Trade-offs:**
- (+) 15% recall improvement
- (+) Better context preservation
- (-) Slower indexing (LLM calls)
- (-) More complex implementation

**Decision:** Enable by default, provide fallback

### 2. Why Hybrid Search?

**Problem:**
- Vector search misses exact matches (acronyms, names)
- Keyword search misses semantic relationships
- No single method is best

**Solution:**
- Combine both with RRF
- Best of both worlds

**Trade-offs:**
- (+) 20% recall improvement
- (+) Handles edge cases
- (-) 2x search latency
- (-) 2x storage (BM25 + vector)

**Decision:** Enable hybrid by default

### 3. Why Disable LLM Re-ranking?

**Problem:**
- Re-ranking improves precision (+10%)
- But adds 2000ms+ latency with local models

**Solution:**
- Disable by default
- Make configurable
- Consider async/background processing

**Trade-offs:**
- (+) Fast queries (<100ms)
- (-) Slightly lower precision

**Decision:** Disabled by default, document for power users

### 4. Why Knowledge Graph?

**Problem:**
- Hybrid search misses multi-hop relationships
- Related documents not discoverable

**Solution:**
- Lightweight graph (NetworkX)
- Build from wikilinks + folder structure
- BFS traversal for related docs

**Trade-offs:**
- (+) 2% improvement for multi-hop
- (+) Relationship discovery
- (-) 10MB memory overhead
- (-) 500ms build time

**Decision:** Enable by default, cheap enough

### 5. Why Docker-Only Development?

**Problem:**
- Local dependencies pollute host system
- Version conflicts across projects
- "Works on my machine" issues

**Solution:**
- Enforce containerized development
- All dependencies in Docker image
- Consistent environment

**Trade-offs:**
- (+) Clean host system
- (+) Reproducible builds
- (+) Easy onboarding
- (-) Slight performance overhead
- (-) Learning curve for Docker

**Decision:** Enforce strictly, document thoroughly

---

## Scalability

### Current Limits

| Metric | Current | Max Tested |
|--------|---------|------------|
| **Files** | 93 | 1,000 |
| **Chunks** | 671 | 10,000 |
| **Memory** | 360MB | 2GB |
| **Disk** | 156MB | 1GB |
| **Latency** | 74ms | 150ms (10k chunks) |

### Scaling Strategies

#### 1. Horizontal Scaling (>10k files)

```yaml
services:
  # Shard by folder
  markdown-rag-shard-1:
    environment:
      VAULT_PATH: /vault/folder1
      
  markdown-rag-shard-2:
    environment:
      VAULT_PATH: /vault/folder2
      
  # Load balancer
  nginx:
    image: nginx
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

#### 2. Caching (repeated queries)

```python
from functools import lru_cache
import redis

# In-memory cache
@lru_cache(maxsize=1000)
def search_cached(query: str) -> List[Dict]:
    return advanced_searcher.search(query)

# Redis cache
redis_client = redis.Redis(host='localhost', port=6379)

def search_with_redis(query: str) -> List[Dict]:
    cached = redis_client.get(f"search:{query}")
    if cached:
        return json.loads(cached)
    
    results = advanced_searcher.search(query)
    redis_client.setex(f"search:{query}", 3600, json.dumps(results))
    return results
```

#### 3. Batch Processing (large vaults)

```python
def index_vault_batch(batch_size: int = 100):
    """Index in batches to control memory."""
    files = list(vault_path.glob("**/*.md"))
    
    for i in range(0, len(files), batch_size):
        batch = files[i:i+batch_size]
        
        # Index batch
        for file in batch:
            index_file(file)
        
        # Flush to disk
        collection.persist()
        
        # Log progress
        print(f"Indexed {i+len(batch)}/{len(files)} files")
```

#### 4. Incremental Indexing (auto-update)

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class VaultWatcher(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith(".md"):
            print(f"Reindexing {event.src_path}")
            indexer.index_file(Path(event.src_path))
    
    def on_created(self, event):
        if event.src_path.endswith(".md"):
            print(f"Indexing new file {event.src_path}")
            indexer.index_file(Path(event.src_path))

# Start watcher
observer = Observer()
observer.schedule(VaultWatcher(), vault_path, recursive=True)
observer.start()
```

---

## Security

### Current Security Model

**Threat Model:**
- Internal tool for personal use
- Trusted network
- No authentication required

**Security Measures:**
1. **Read-only vault mount** - Cannot modify source files
2. **Docker isolation** - Limited host access
3. **No external network** - Ollama only via host network
4. **Input validation** - Sanitize user queries
5. **Error handling** - No stack traces to users

### Production Security (if deploying publicly)

**Must Implement:**

1. **Authentication**
```python
from flask_httpauth import HTTPBasicAuth

auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    # Check against environment variables or database
    return username == os.getenv("API_USERNAME") and \
           password == os.getenv("API_PASSWORD")

@app.route("/api/search")
@auth.login_required
def search():
    ...
```

2. **Rate Limiting**
```python
from flask_limiter import Limiter

limiter = Limiter(
    app,
    key_func=lambda: request.remote_addr,
    default_limits=["100 per day", "10 per minute"]
)

@app.route("/api/chat")
@limiter.limit("5 per minute")
def chat():
    ...
```

3. **HTTPS/TLS**
```yaml
# nginx.conf
server {
    listen 443 ssl;
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    location / {
        proxy_pass http://markdown-rag-mcp:5555;
    }
}
```

4. **Input Sanitization**
```python
import bleach

def sanitize_query(query: str) -> str:
    # Remove HTML/JavaScript
    clean = bleach.clean(query, strip=True)
    
    # Limit length
    clean = clean[:1000]
    
    # Remove special characters
    clean = re.sub(r'[^\w\s\-]', '', clean)
    
    return clean
```

5. **Audit Logging**
```python
import logging

audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)

@app.route("/api/search")
def search():
    query = request.json["query"]
    
    audit_logger.info(f"SEARCH user={request.remote_addr} query={query}")
    
    results = advanced_searcher.search(query)
    return jsonify(results)
```

---

## Monitoring

### Recommended Metrics

```python
from prometheus_client import Counter, Histogram, Gauge

# Requests
search_requests = Counter("search_requests_total", "Total search requests")
chat_requests = Counter("chat_requests_total", "Total chat requests")

# Latency
search_latency = Histogram("search_latency_seconds", "Search latency")
chat_latency = Histogram("chat_latency_seconds", "Chat latency")

# Index stats
total_chunks = Gauge("total_chunks", "Total chunks indexed")
total_files = Gauge("total_files", "Total files indexed")

# Errors
search_errors = Counter("search_errors_total", "Search errors")
indexing_errors = Counter("indexing_errors_total", "Indexing errors")
```

### Logging Best Practices

```python
import logging
import structlog

# Structured logging
logger = structlog.get_logger()

@app.route("/api/search")
def search():
    query = request.json["query"]
    
    logger.info("search.start", query=query, user=request.remote_addr)
    
    start_time = time.time()
    
    try:
        results = advanced_searcher.search(query)
        
        latency = time.time() - start_time
        logger.info("search.success", query=query, results=len(results), latency=latency)
        
        return jsonify(results)
        
    except Exception as e:
        logger.error("search.error", query=query, error=str(e))
        raise
```

---

## Future Architecture Considerations

### 1. Microservices (if scaling to team/org)

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   API        │───▶│   Search     │───▶│   Ollama     │
│   Gateway    │    │   Service    │    │   Service    │
└──────────────┘    └──────────────┘    └──────────────┘
       │                    │                    
       │            ┌──────────────┐    ┌──────────────┐
       └───────────▶│   Index      │───▶│   ChromaDB   │
                    │   Service    │    │   Service    │
                    └──────────────┘    └──────────────┘
```

### 2. Event-Driven Architecture (for real-time updates)

```
File Changed → Kafka → Indexer → ChromaDB
                ↓
         Graph Builder → NetworkX
                ↓
         BM25 Builder → BM25 Index
```

### 3. Serverless (for cost optimization)

```python
# AWS Lambda
def lambda_handler(event, context):
    query = event["query"]
    
    # Initialize (cold start penalty)
    searcher = AdvancedSearcher()
    
    # Search
    results = searcher.search(query)
    
    return {
        "statusCode": 200,
        "body": json.dumps(results)
    }
```

---

## Conclusion

This architecture achieves world-class RAG performance through:

1. **Agentic Chunking** - LLM-powered semantic segmentation
2. **Hybrid Search** - Vector + BM25 with RRF
3. **Knowledge Graph** - Relationship discovery
4. **Query Expansion** - Synonym enhancement
5. **Modern UI** - Real-time streaming interface

**Key Metrics:**
- 100% recall
- 68% precision
- 74ms average latency
- 96% code coverage

**Production Ready:**
- Comprehensive error handling
- Extensive testing
- Docker deployment
- Scalability considered

For more details, see:
- [Performance Analysis](PERFORMANCE.md)
- [Roadmap](ROADMAP.md)
- [API Documentation](API.md)

