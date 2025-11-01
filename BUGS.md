# Open Bugs & Missing Features

**Date Created:** November 1, 2025
**System:** RAG Lab - Microservices Architecture
**Status:** 3 HIGH PRIORITY issues identified

---

## 🐛 BUG #1: LLM Re-ranking Not Integrated into Microservices

### Priority: HIGH
### Component: `search-service`
### Status: ❌ NOT WORKING

### Description
LLM re-ranking exists in the monolithic codebase (`src/advanced_search.py`) but is **NOT integrated** into the microservices architecture.

### Current Behavior
- ✅ Code exists in `src/advanced_search.py` with `_rerank_with_llm()` function
- ✅ Uses Ollama to score relevance (0.0 to 1.0)
- ✅ Combines hybrid score (60%) + LLM score (40%)
- ❌ NOT exposed via `search-service` API endpoint
- ❌ NOT available in UI or API calls
- ❌ `rerank` parameter not accepted by `/search` endpoint

### Expected Behavior
- `/search` endpoint should accept `use_reranking: bool` parameter
- When enabled, search results should be re-scored by LLM
- Should return results with `llm_relevance` and `final_score` fields

### Impact
- **Precision:** Missing +5-10% precision improvement
- **Relevance:** Search results not optimized for user query intent
- **Feature Gap:** Documented feature not available

### Code Location
- **Existing code:** `/workspace/src/advanced_search.py` (lines 146-224)
- **Needs integration:** `/workspace/services/search/app/service.py`

### Proposed Solution

**Option 1: Add to search-service (RECOMMENDED)**
```python
# services/search/app/service.py

@app.route('/search', methods=['POST'])
def search():
    data = request.json
    query = data.get('query', '')
    limit = data.get('limit', 10)
    expand = data.get('expand_query', True)
    use_reranking = data.get('use_reranking', False)  # NEW

    # ... existing hybrid search logic ...

    # NEW: Re-ranking
    if use_reranking and results:
        results = rerank_with_llm(query, results, limit)
        method = f"{method}_with_reranking"

    return jsonify({
        'results': results,
        'method': method,
        'reranked': use_reranking
    })

def rerank_with_llm(query: str, results: List[Dict], limit: int):
    """Re-rank using LLM relevance scoring"""
    # Port code from src/advanced_search.py lines 146-224
    pass
```

**Option 2: Create dedicated reranker-service**
```yaml
# docker-compose.test.yml
reranker-service:
  build: ./services/reranker
  ports:
    - "8007:8007"
  environment:
    - OLLAMA_BASE_URL=http://ollama:11434
```

### Performance Impact
- ⚠️ **Latency:** Adds 500-2000ms per search (LLM scoring per result)
- ⚠️ **Cost:** Multiple LLM calls per search
- **Recommendation:** Make it **opt-in only** for high-precision use cases

### Acceptance Criteria
- [ ] `/search` endpoint accepts `use_reranking` parameter
- [ ] LLM re-ranking function integrated
- [ ] Results include `llm_relevance` score
- [ ] Results include `final_score` (hybrid + LLM)
- [ ] Performance acceptable (<2s total for 10 results)
- [ ] Unit tests added
- [ ] Documentation updated

---

## 🐛 BUG #2: Knowledge Graph Missing Entity/Concept Extraction

### Priority: HIGH
### Component: `knowledge-graph` / `ingest-service`
### Status: ❌ PARTIALLY WORKING

### Description
Knowledge graph currently only connects documents via **explicit relationships** (wikilinks, tags, folders) but is **missing entity/concept extraction** for implicit relationships.

### Current Behavior
✅ **Working:**
- Wikilinks: `[[Document Name]]` creates edges
- Tags: Documents with same tags connected
- Folders: Hierarchy relationships tracked

❌ **Missing:**
- Entity extraction from content (people, places, technologies)
- Concept extraction (key topics, subjects)
- Co-occurrence relationships (docs mentioning same entities)
- Subject-based search ("all docs about embeddings")

### Expected Behavior
```python
# Document 1: "OpenAI's GPT-4 uses RAG with vector embeddings"
# Document 2: "Vector embeddings enable semantic search in RAG systems"

# Should extract:
entities = {
    'organizations': ['OpenAI'],
    'products': ['GPT-4'],
    'concepts': ['RAG', 'vector embeddings', 'semantic search']
}

# Should create edges:
doc1 → concept:RAG → doc2
doc1 → concept:vector_embeddings → doc2
doc1 → product:GPT-4
```

### Impact
- **Discovery:** Cannot find related documents by implicit relationships
- **Concepts:** No way to query "all docs about RAG" or "all docs mentioning embeddings"
- **Multi-hop:** Limited relationship traversal capabilities
- **Recall:** Missing ~2% recall improvement from graph enhancement

### Code Location
- **Existing graph:** `/workspace/src/knowledge_graph.py`
- **NEW extractor:** `/workspace/src/entity_extractor.py` (created but not integrated)
- **Needs integration:** `/workspace/services/ingest/app/service.py`

### Proposed Solution

**Step 1: Extract entities during ingestion**
```python
# services/ingest/app/service.py

from entity_extractor import EntityExtractor

entity_extractor = EntityExtractor(use_llm=False)  # Fast regex-based

def process_document(content, metadata):
    # ... existing parsing ...

    # NEW: Extract entities
    entities = entity_extractor.extract_entities(content, metadata['title'])
    metadata['entities'] = entities

    # Store entities with metadata
    # ...
```

**Step 2: Build entity graph**
```python
# src/knowledge_graph.py

def build_graph(self):
    # ... existing wikilink/tag logic ...

    # NEW: Add entity/concept nodes
    entity_groups = defaultdict(list)
    for metadata in all_docs['metadatas']:
        entities = metadata.get('entities', {})
        for entity_type, entity_list in entities.items():
            for entity in entity_list:
                entity_node = f"entity:{entity}"
                entity_groups[entity_node].append(file_name)

    # Connect documents via shared entities
    for entity_node, files in entity_groups.items():
        if len(files) > 1:
            self.graph.add_node(entity_node, type='entity')
            for file in files:
                self.graph.add_edge(file, entity_node, relation='mentions')
```

**Step 3: Add entity-based search**
```python
def find_by_entity(self, entity: str) -> List[str]:
    """Find all documents mentioning an entity"""
    entity_node = f"entity:{entity}"
    if entity_node not in self.graph:
        return []

    documents = []
    for node in self.graph.nodes():
        if self.graph.has_edge(node, entity_node):
            if self.graph.nodes[node].get('type') == 'document':
                documents.append(node)
    return documents
```

### Acceptance Criteria
- [ ] `EntityExtractor` integrated into ingest pipeline
- [ ] Entities stored in document metadata
- [ ] Knowledge graph includes entity nodes
- [ ] Documents connected via shared entities
- [ ] `find_by_entity()` method implemented
- [ ] Search service can query by entity/concept
- [ ] Graph visualization shows entity relationships
- [ ] Performance acceptable (<100ms overhead per document)

---

## 🐛 BUG #3: Knowledge Graph Not Exposed as Microservice

### Priority: MEDIUM
### Component: NEW `knowledge-graph-service`
### Status: ❌ NOT WORKING

### Description
Knowledge graph exists in monolithic codebase but is **not exposed** as a microservice with REST API endpoints.

### Current Behavior
- ✅ Code exists in `src/knowledge_graph.py`
- ✅ Graph built from ChromaDB data
- ✅ Relationship traversal functions available
- ❌ NOT running as independent service
- ❌ NOT accessible via HTTP API
- ❌ NOT integrated with search-service

### Expected Behavior
- Independent `knowledge-graph-service` container
- REST API endpoints for graph operations
- Integration with search-service for relationship expansion

### Impact
- **Isolation:** Cannot scale graph operations independently
- **API:** No programmatic access to graph relationships
- **Integration:** Cannot use graph in microservices search flow
- **Monitoring:** No separate health checks or metrics

### Proposed Solution

**Create knowledge-graph-service:**

```python
# services/knowledge-graph/app/service.py

from flask import Flask, request, jsonify
import sys
sys.path.insert(0, '/workspace/src')
from knowledge_graph import KnowledgeGraph

app = Flask(__name__)
kg = KnowledgeGraph()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'nodes': kg.graph.number_of_nodes(),
        'edges': kg.graph.number_of_edges()
    })

@app.route('/build', methods=['POST'])
def build_graph():
    """Rebuild knowledge graph from vector DB"""
    kg.build_graph()
    return jsonify({'success': True})

@app.route('/related', methods=['POST'])
def find_related():
    """Find related documents"""
    data = request.json
    file_name = data.get('file_name')
    max_hops = data.get('max_hops', 2)
    limit = data.get('limit', 10)

    related = kg.find_related(file_name, max_hops, limit)
    return jsonify({'related': related})

@app.route('/by_tag', methods=['POST'])
def find_by_tag():
    """Find documents by tag"""
    tag = request.json.get('tag')
    docs = kg.find_by_tag(tag)
    return jsonify({'documents': docs})

@app.route('/by_folder', methods=['POST'])
def find_by_folder():
    """Find documents in folder"""
    folder = request.json.get('folder')
    docs = kg.find_by_folder(folder)
    return jsonify({'documents': docs})

@app.route('/context', methods=['POST'])
def get_context():
    """Get full context for a document"""
    file_name = request.json.get('file_name')
    context = kg.get_document_context(file_name)
    return jsonify(context)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8007, debug=False)
```

**Docker configuration:**
```dockerfile
# services/knowledge-graph/Dockerfile
FROM python:3.11-slim

WORKDIR /workspace

COPY services/common/requirements.txt /workspace/
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install networkx

COPY services/knowledge-graph/app /workspace/app
COPY src/ /workspace/src/

CMD ["python", "app/service.py"]
```

**Docker Compose:**
```yaml
# docker-compose.test.yml
knowledge-graph-service:
  build:
    context: .
    dockerfile: services/knowledge-graph/Dockerfile
  ports:
    - "8007:8007"
  environment:
    - SERVICE_NAME=knowledge-graph-service
    - SERVICE_PORT=8007
  volumes:
    - ./indices:/workspace/indices:rw
  networks:
    - rag-network
  depends_on:
    - vector-db
```

### Acceptance Criteria
- [ ] `knowledge-graph-service` created
- [ ] Dockerfile and dependencies configured
- [ ] REST API endpoints implemented
- [ ] Integration with search-service added
- [ ] Health checks and metrics exposed
- [ ] Documentation updated
- [ ] Tests added

---

## Summary

| Bug # | Description | Priority | Status | Estimated Effort |
|-------|-------------|----------|--------|------------------|
| #1 | LLM Re-ranking not integrated | HIGH | ❌ Not Working | 4-6 hours |
| #2 | Entity/concept extraction missing | HIGH | ⚠️ Partial | 8-12 hours |
| #3 | Knowledge graph not exposed as service | MEDIUM | ❌ Not Working | 4-6 hours |

**Total Estimated Effort:** 16-24 hours

---

## Priority Recommendations

1. **BUG #1 (LLM Re-ranking)** - Quick win, code exists, just needs integration
2. **BUG #2 (Entity Extraction)** - High value, enables semantic graph connections
3. **BUG #3 (Graph Service)** - Nice to have for proper microservices architecture

---

## Notes

### Why These Features Were Disabled
- **LLM Re-ranking:** Too slow (500-2000ms), disabled by default in monolithic version
- **Entity Extraction:** Complex feature, not implemented in initial version
- **Graph Service:** Working in monolithic mode, microservices split didn't include it

### Performance Considerations
- LLM re-ranking should be **opt-in only** (adds significant latency)
- Entity extraction should use **fast regex-based** approach (not LLM) for real-time ingestion
- Knowledge graph should be **built async** (not blocking document uploads)

---

**Created:** November 1, 2025
**Last Updated:** November 1, 2025
**Validation Report:** See `COMPREHENSIVE_RAG_VALIDATION.md`

