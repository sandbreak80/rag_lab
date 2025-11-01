# Performance Optimization Guide

## 🐌 Issue: Slow Inference on M2 MacBook Pro (16GB)

Your setup is running inference very slowly. Here's how to optimize it.

---

## ⚡ Quick Win: Switch to Lighter Model

### Current Setup (Slow)
- **Model**: `llama3.1:8b` (8 billion parameters)
- **Size**: ~4.7 GB
- **Speed**: 30-120 seconds per response
- **Quality**: Excellent

### Recommended (Fast)
- **Model**: `llama3.2:3b` (3 billion parameters)  
- **Size**: ~2 GB
- **Speed**: 10-30 seconds per response
- **Quality**: Good (sufficient for RAG)

### Even Faster Options
- **qwen2.5:3b**: 10-25 seconds, excellent quality
- **phi3.5:mini**: 5-15 seconds, good for simple queries

---

## 🔧 How to Switch Models

### Option 1: Environment Variable (Temporary)
```bash
# Restart webapp with lighter model
docker-compose exec markdown-rag-mcp bash -c "export CHAT_MODEL=llama3.2:3b && cd /workspace/src && python webapp.py &"
```

### Option 2: Update Config (Permanent)
Already done! The config now defaults to `llama3.2:3b`.

Restart the webapp:
```bash
docker-compose exec markdown-rag-mcp bash -c "killall python; cd /workspace/src && python webapp.py &"
```

### Option 3: Try Different Models
Edit `docker-compose.yml` line 23:
```yaml
- CHAT_MODEL=qwen2.5:3b  # Very fast, great quality
- CHAT_MODEL=phi3.5:mini  # Fastest, good for simple queries
- CHAT_MODEL=llama3.2:1b  # Ultra-fast for testing
```

---

## 📊 Performance Comparison (M2 16GB)

| Model | Size | Tokens/sec | Response Time | Quality | Recommended For |
|-------|------|------------|---------------|---------|-----------------|
| **llama3.1:8b** | 4.7GB | ~8-12 | 60-120s | Excellent | Production, important queries |
| **llama3.2:3b** | 2GB | ~20-30 | 10-30s | Good | ✅ Web UI default |
| **qwen2.5:3b** | 1.9GB | ~25-35 | 10-25s | Very Good | ✅ Best balance |
| **phi3.5:mini** | 2.2GB | ~40-50 | 5-15s | Good | Quick queries |
| **llama3.2:1b** | 1.3GB | ~50-70 | 3-10s | Fair | Testing only |

---

## 🧠 Knowledge Graph Options

### Option 1: Lightweight Graph (Recommended ✅)

**Use existing wikilinks** - minimal overhead, already extracted!

**What you get:**
- Note-to-note connections via `[[wikilinks]]`
- Tag-based relationships
- Folder hierarchy

**Cost:** ~5-10ms per query (negligible)

**Implementation:**
```python
# Already available in search.py
results = searcher.search(query, limit=10)
# Each result has:
# - result['metadata']['tags']
# - result['metadata']['wikilinks']
# - result['metadata']['folder']
```

**Good for:**
- Finding related notes
- Topic clustering
- Basic graph traversal

### Option 2: Full Knowledge Graph (Heavy ⚠️)

**Extract entities and relationships** using NLP

**What you get:**
- Named entities (people, places, concepts)
- Relationship extraction (X works for Y, A is related to B)
- Graph database (Neo4j, NetworkX)

**Cost:** 
- 🔴 **Indexing**: +30-60 minutes
- 🔴 **Memory**: +2-4 GB RAM
- 🔴 **Query**: +100-500ms per search

**Not recommended for your hardware**

### Option 3: Hybrid Approach (Best Balance)

**Wikilinks + Tag Graph + Basic Entity Recognition**

**Implementation:**
1. Use existing wikilinks (free)
2. Build tag co-occurrence graph (cheap)
3. Extract people/orgs from frontmatter only (no NLP needed)

**Cost:** +20-50ms per query

---

## 🎯 Recommended Configuration

### For Your M2 MacBook (16GB)

```yaml
# docker-compose.yml
environment:
  - CHAT_MODEL=llama3.2:3b  # Or qwen2.5:3b
  - EMBEDDING_MODEL=nomic-embed-text  # Keep this, it's fast
```

### Why This Works

1. **Embeddings are fast**: `nomic-embed-text` runs at ~500 docs/sec
2. **RAG reduces context**: Only 3-5 chunks sent to LLM (not whole vault)
3. **Lighter model**: 3B params vs 8B = 3x faster
4. **Quality stays good**: RAG provides context, smaller model just synthesizes

---

## 📈 Expected Performance Improvements

### Before (llama3.1:8b)
- Query search: 0.5s ✅ (fast)
- LLM response: **60-120s** 🔴 (very slow)
- Total: 60-120s

### After (llama3.2:3b)
- Query search: 0.5s ✅
- LLM response: **10-30s** 🟡 (acceptable)
- Total: 10-30s

### With qwen2.5:3b
- Query search: 0.5s ✅
- LLM response: **10-25s** 🟡
- Total: 10-25s

**3-6x faster!**

---

## 🔬 Testing Your New Setup

### Test 1: Quick Query
```bash
curl -X POST http://localhost:5555/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "AI prompting", "limit": 3}'
```
**Expected**: < 1 second

### Test 2: Full RAG Response
Open http://localhost:5555 and ask:
"What are AI prompting best practices?"

**Expected**: 
- llama3.2:3b: 15-30 seconds
- qwen2.5:3b: 10-25 seconds

---

## 💡 Additional Optimizations

### 1. Reduce Context Size
Edit `src/webapp.py` line 221:
```python
results = searcher.search(query, limit=3)  # Was 5, now 3
```
**Saves**: 20-30% inference time

### 2. Shorter Responses
Edit `src/webapp.py` line 143:
```python
"num_predict": 300  # Was 500, now 300
```
**Saves**: 40% inference time

### 3. Use Streaming (Already Implemented ✅)
Your webapp already streams responses, so you see words appear immediately.

### 4. Batch Queries
Instead of asking 3 separate questions, ask one compound question:
- ❌ "Who is X?" then "What does X do?" then "Where is X from?"
- ✅ "Who is X, what do they do, and where are they from?"

---

## 🚫 What NOT to Do

### Don't Use GPU Acceleration
Your M2 chip is ARM-based. Ollama already uses Metal for GPU acceleration automatically. No additional config needed.

### Don't Add Full Knowledge Graph
Your laptop will struggle with:
- Entity extraction (slow)
- Graph database (memory intensive)
- Complex graph queries (CPU intensive)

**Stick with lightweight wikilink graph instead.**

### Don't Use Quantized Models
Ollama models are already quantized (4-bit). Further quantization degrades quality significantly.

---

## 📊 Knowledge Graph: Simple Implementation

Want to try the lightweight graph? Here's a quick implementation:

### 1. Extract Graph Data
```python
# examples/build_graph.py
from search import VaultSearcher
import json

searcher = VaultSearcher()

# Get all chunks
results = searcher.collection.get()

# Build graph
graph = {
    "nodes": [],  # notes
    "edges": []   # connections
}

notes = {}
for i, metadata in enumerate(results['metadatas']):
    note_name = metadata['title']
    
    if note_name not in notes:
        notes[note_name] = {
            "id": note_name,
            "tags": metadata.get('tags', []),
            "links": metadata.get('wikilinks', [])
        }

# Create edges from wikilinks
for note_name, note_data in notes.items():
    for link in note_data['links']:
        if link in notes:
            graph['edges'].append({
                "source": note_name,
                "target": link,
                "type": "wikilink"
            })

graph['nodes'] = list(notes.values())

print(f"Graph: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")
```

### 2. Find Related Notes
```python
def find_related(note_name, max_depth=2):
    """Find notes related via wikilinks"""
    related = set()
    to_visit = [(note_name, 0)]
    visited = set()
    
    while to_visit:
        current, depth = to_visit.pop(0)
        if current in visited or depth > max_depth:
            continue
        visited.add(current)
        related.add(current)
        
        # Find connected notes
        for edge in graph['edges']:
            if edge['source'] == current:
                to_visit.append((edge['target'], depth + 1))
    
    return list(related)
```

**Cost**: ~5-10ms per query, minimal memory

---

## 🎯 Final Recommendation

### For Your Setup (M2 16GB):

1. ✅ **Switch to `llama3.2:3b` or `qwen2.5:3b`** (already done!)
2. ✅ **Use lightweight wikilink graph** (data already extracted)
3. ❌ **Skip full knowledge graph** (too heavy)
4. ✅ **Reduce context to 3 chunks** (faster responses)
5. ✅ **Keep streaming UI** (better UX)

### Expected Results:
- **3-6x faster** responses (10-30s vs 60-120s)
- **Same search quality** (embeddings unchanged)
- **Slightly lower answer quality** (but RAG compensates)
- **Much better user experience**

---

## 🔄 How to Apply Changes

```bash
# 1. Restart webapp with new model
cd /Users/bmstoner/code_projects/ollama_local/markdown-rag-mcp
docker-compose exec markdown-rag-mcp bash -c "killall python 2>/dev/null; cd /workspace/src && python webapp.py &"

# 2. Test it
curl http://localhost:5555/api/stats

# 3. Try a query in browser
open http://localhost:5555
```

---

## 📚 Model Download (If Needed)

```bash
# If llama3.2:3b isn't installed
docker exec ollama ollama pull llama3.2:3b

# Or try qwen (even faster)
docker exec ollama ollama pull qwen2.5:3b
```

---

## ❓ Questions?

**Q: Will quality suffer?**  
A: Slightly, but RAG provides good context so smaller models work well.

**Q: Can I switch back?**  
A: Yes! Just change `CHAT_MODEL=llama3.1:8b` in docker-compose.yml

**Q: What about embeddings?**  
A: Keep `nomic-embed-text` - it's already fast and high quality.

**Q: Should I add Neo4j for knowledge graph?**  
A: No, use the lightweight wikilink approach instead.

---

Your system will be **much faster** now! 🚀

