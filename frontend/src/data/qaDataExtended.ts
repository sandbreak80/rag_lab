// Extended Q&A Data - Remaining categories (63+ entries)
// Part 2 of comprehensive Q&A knowledge base

import { QAItem } from './qaData';

export const QA_DATA_EXTENDED: QAItem[] = [
  // ============================================================================
  // KNOWLEDGE GRAPHS (8 Q&A)
  // ============================================================================
  {
    id: 'kg-1',
    question: 'What is a knowledge graph in RAG?',
    answer: `A knowledge graph represents document relationships as nodes and edges.

**Components:**
- **Nodes:** Documents, folders, tags, entities
- **Edges:** Links, mentions, related_to, contains

**Why Useful:**
- Discover multi-hop connections
- Find related documents
- Navigate document relationships
- Enhance search results

**Example:**
\`\`\`
AI-Intro.md → links_to → Machine-Learning.md
AI-Intro.md → has_tag → #tutorial
AI-Intro.md → mentions → entity:Neural Networks
\`\`\`

**This Lab:** Uses NetworkX (Python graph library) with 4 different construction algorithms.`,
    category: 'knowledge-graphs',
    tags: ['knowledge-graph', 'graph', 'relationships'],
    difficulty: 'intermediate',
    estimatedReadTime: 2,
    relatedQuestions: ['kg-2', 'kg-3'],
  },
  {
    id: 'kg-2',
    question: 'What are the 4 knowledge graph algorithms?',
    answer: `This lab supports 4 different KG construction methods:

**1. Wikilinks (Default)**
- Speed: Fast (< 1s)
- Accuracy: High (explicit connections)
- Uses: [[cross-references]] in documents
- Best for: Documents with manual links

**2. Semantic Similarity**
- Speed: Slow (10-30s)
- Accuracy: High (implicit connections)
- Uses: Document embeddings, cosine similarity
- Best for: Discovering topical relationships

**3. Entity Co-occurrence**
- Speed: Medium (5-15s)
- Accuracy: Medium (entity-based)
- Uses: Named entity recognition (NER)
- Best for: Tracking people, orgs, places

**4. Hybrid (All Methods)**
- Speed: Very Slow (30-60s)
- Accuracy: Highest (comprehensive)
- Uses: All three methods combined
- Best for: Maximum quality, research

**Try It:** Go to Documents tab → Select algorithm → Rebuild KG`,
    category: 'knowledge-graphs',
    tags: ['algorithms', 'wikilinks', 'semantic', 'entity', 'hybrid'],
    difficulty: 'intermediate',
    estimatedReadTime: 3,
    relatedQuestions: ['kg-1', 'kg-3', 'kg-4'],
  },
  {
    id: 'kg-3',
    question: 'Wikilinks vs Semantic Similarity: Which is better?',
    answer: `**Wikilinks:**
✅ Fast (< 1s build time)
✅ Accurate (explicit connections)
✅ No embeddings needed
✅ Low memory usage
❌ Requires manual [[links]]
❌ Misses implicit relationships

**Semantic Similarity:**
✅ Discovers implicit connections
✅ No manual linking needed
✅ Finds topically similar docs
❌ Slow (10-30s build time)
❌ Requires embeddings
❌ Higher memory usage

**When to Use:**

**Wikilinks:**
- Production chatbots (speed critical)
- Personal notes (you add [[links]])
- Daily updates (fast rebuild)

**Semantic:**
- Research papers (discover relationships)
- News articles (topic clustering)
- Academic documents (implicit connections)

**Hybrid:**
- Best of both worlds
- Use for quality benchmarking

**This Lab:** Try both and compare results!`,
    category: 'knowledge-graphs',
    tags: ['comparison', 'wikilinks', 'semantic'],
    difficulty: 'intermediate',
    estimatedReadTime: 2,
    relatedQuestions: ['kg-2', 'kg-4'],
  },
  {
    id: 'kg-4',
    question: 'When should I use each KG algorithm?',
    answer: `**Production Use Cases:**

**Wikilinks → Customer Service Chatbot**
- 1000 requests/min
- Need sub-second rebuilds
- Documents have [[cross-refs]]
- Speed > Discovery

**Semantic → Research Paper Search**
- Batch processing acceptable
- Discover implicit relationships
- No manual linking
- Quality > Speed

**Entity → Legal Document Search**
- Track case names, parties, statutes
- Entity-centric queries
- Medium speed acceptable

**Hybrid → Academic Research**
- Maximum quality needed
- Overnight batch processing OK
- Comprehensive coverage required

**Daily Updates:**
- Wikilinks + pre-computed Semantic
- Fast incremental updates
- Full rebuild overnight

**This Lab Default:** Wikilinks (fast, good enough for 80% of queries)`,
    category: 'knowledge-graphs',
    tags: ['use-cases', 'production', 'algorithms'],
    difficulty: 'advanced',
    estimatedReadTime: 2,
    relatedQuestions: ['kg-2', 'kg-3'],
  },
  {
    id: 'kg-5',
    question: 'How do I rebuild the knowledge graph?',
    answer: `**Steps:**
1. Go to **Documents** tab
2. Scroll to "Knowledge Graph: Rebuild with Algorithm"
3. Select algorithm from dropdown:
   - Wikilinks (fast)
   - Semantic Similarity (slow, quality)
   - Entity Co-occurrence (medium)
   - Hybrid (very slow, best quality)
4. Click **"Rebuild KG"** button
5. Wait for completion (time varies by algorithm)
6. View stats: nodes, edges, algorithm used

**When to Rebuild:**
- After uploading new documents
- When switching algorithms
- If graph seems outdated
- To compare algorithm performance

**Warning:** Rebuilding deletes the existing graph!

**Tip:** Use "Reset KG" button to clear without rebuilding.`,
    category: 'knowledge-graphs',
    tags: ['rebuild', 'how-to', 'ui'],
    difficulty: 'beginner',
    estimatedReadTime: 1,
    relatedQuestions: ['kg-2', 'gs-8'],
  },
  {
    id: 'kg-6',
    question: 'What are nodes and edges in the knowledge graph?',
    answer: `**Nodes (Things):**
- **Documents:** Your markdown/PDF files
- **Folders:** Directory structure
- **Tags:** Metadata tags (#ai, #tutorial)
- **Entities:** People, orgs, places (Entity algorithm only)

**Edges (Relationships):**
- **links_to:** Wikilinks [[document]] → document
- **contains:** Folder → document
- **has_tag:** Document → tag
- **similar_to:** Semantic similarity (Semantic algorithm)
- **mentions:** Document → entity (Entity algorithm)

**Example Graph:**
\`\`\`
AI-Intro.md (document node)
  ├─ links_to → Machine-Learning.md
  ├─ has_tag → #tutorial
  ├─ similar_to → Deep-Learning.md (0.85)
  └─ mentions → entity:Neural Networks
\`\`\`

**Graph Traversal:** BFS (Breadth-First Search) up to 2 hops to find related documents.`,
    category: 'knowledge-graphs',
    tags: ['nodes', 'edges', 'graph-theory'],
    difficulty: 'intermediate',
    estimatedReadTime: 2,
    relatedQuestions: ['kg-1', 'kg-7'],
  },
  {
    id: 'kg-7',
    question: 'How does graph traversal work?',
    answer: `Graph traversal finds related documents by walking the graph.

**Algorithm: BFS (Breadth-First Search)**
\`\`\`python
def find_related(start_doc, max_hops=2):
    visited = set()
    queue = [(start_doc, 0)]
    related = []
    
    while queue:
        doc, hops = queue.pop(0)
        
        if hops > max_hops:
            continue
        
        visited.add(doc)
        
        # Get neighbors
        for neighbor in graph.neighbors(doc):
            if neighbor not in visited:
                related.append(neighbor)
                queue.append((neighbor, hops + 1))
    
    return related
\`\`\`

**Example:**
Start: "AI-Intro.md"
- Hop 1: Machine-Learning.md, Deep-Learning.md
- Hop 2: Neural-Networks.md, Transformers.md

**This Lab:** Traverses up to 2 hops for each of the top 5 search results.`,
    category: 'knowledge-graphs',
    tags: ['traversal', 'bfs', 'algorithms'],
    difficulty: 'advanced',
    estimatedReadTime: 2,
    relatedQuestions: ['kg-6'],
    codeExample: `// BFS traversal
function findRelated(startNode: string, maxHops = 2): string[] {
  const visited = new Set<string>();
  const queue: [string, number][] = [[startNode, 0]];
  const related: string[] = [];
  
  while (queue.length > 0) {
    const [node, hops] = queue.shift()!;
    
    if (hops > maxHops) continue;
    
    visited.add(node);
    
    for (const neighbor of graph.neighbors(node)) {
      if (!visited.has(neighbor)) {
        related.push(neighbor);
        queue.push([neighbor, hops + 1]);
      }
    }
  }
  
  return related;
}`,
  },
  {
    id: 'kg-8',
    question: 'What is the performance impact of knowledge graphs?',
    answer: `**Build Time (One-Time):**
- Wikilinks: < 1s
- Semantic: 10-30s
- Entity: 5-15s
- Hybrid: 30-60s

**Query Time (Per Search):**
- Graph traversal: +50ms
- BFS for top 5 results
- 2-hop maximum depth

**Memory:**
- Graph storage: ~1MB (100 docs)
- In-memory: ~10MB loaded
- Negligible for < 1000 docs

**Recall Impact:**
- Wikilinks: +2% recall
- Semantic: +5% recall
- Entity: +3% recall (entity queries)
- Hybrid: +7% recall

**Is It Worth It?**
✅ Yes for: Multi-hop queries, document discovery
❌ No for: Speed-critical apps (< 100ms requirement)

**This Lab:** Enabled in Balanced, Quality, and Production presets.`,
    category: 'knowledge-graphs',
    tags: ['performance', 'impact', 'metrics'],
    difficulty: 'intermediate',
    estimatedReadTime: 2,
    relatedQuestions: ['kg-2', 'perf-1', 'perf-2'],
  },

  // ============================================================================
  // PERFORMANCE & OPTIMIZATION (10 Q&A)
  // ============================================================================
  {
    id: 'perf-1',
    question: 'How do I measure RAG performance?',
    answer: `**Key Metrics:**

**1. Latency (Speed)**
- Total response time (ms)
- Component breakdown (waterfall chart)
- Target: < 2s for balanced config

**2. Recall (Coverage)**
- Relevant docs found / Total relevant docs
- Target: > 90%

**3. Precision (Accuracy)**
- Relevant docs / Total docs returned
- Target: > 85%

**4. Throughput (Scale)**
- Queries per second (QPS)
- Target: > 10 QPS

**Where to See Metrics:**
- **Chat Tab:** Waterfall chart after each response
- **Metrics Tab:** Full query history and analysis
- **Settings Tab:** Real-time system stats

**This Lab:** All metrics tracked automatically. Export to CSV for analysis.`,
    category: 'performance',
    tags: ['metrics', 'measurement', 'monitoring'],
    difficulty: 'intermediate',
    estimatedReadTime: 2,
    relatedQuestions: ['perf-2', 'gs-6'],
  },
  {
    id: 'perf-2',
    question: 'What is latency and why does it matter?',
    answer: `Latency is the time from query submission to response completion.

**Components:**
1. Query Expansion: ~10ms
2. Vector Search: ~35ms
3. BM25 Search: ~15ms
4. Hybrid Fusion: ~10ms
5. Knowledge Graph: ~50ms
6. Re-ranking: ~2000ms (if enabled)
7. Web Search: ~800ms (if enabled)
8. LLM Generation: ~1500ms

**Total (Balanced):** ~1650ms

**Why It Matters:**
- User experience (< 2s feels responsive)
- Scalability (lower latency = higher QPS)
- Cost (faster = more efficient)

**Human Perception:**
- < 100ms: Instant
- 100-300ms: Slight delay
- 300-1000ms: Noticeable
- > 1000ms: Slow

**This Lab:** View waterfall chart to identify bottlenecks!`,
    category: 'performance',
    tags: ['latency', 'speed', 'ux'],
    difficulty: 'beginner',
    estimatedReadTime: 2,
    relatedQuestions: ['perf-1', 'perf-3'],
  },
  {
    id: 'perf-3',
    question: 'How do I identify performance bottlenecks?',
    answer: `**Use the Waterfall Chart:**

1. Ask a question in Chat tab
2. Click "Performance Breakdown" to expand
3. Look at the waterfall chart
4. Identify longest bars

**Common Bottlenecks:**

**LLM Generation (1500ms)**
- Expected for 8B model
- Solution: Use smaller model (3B) or faster GPU

**Re-ranking (2000ms)**
- Very expensive!
- Solution: Disable unless quality is critical

**Web Search (800ms)**
- Network latency
- Solution: Disable for internal docs

**Knowledge Graph (50ms)**
- Graph traversal
- Solution: Disable if speed > discovery

**Vector Search (35ms)**
- Usually not a bottleneck
- Solution: Reduce top_k if needed

**This Lab:** Each component shows time and percentage of total.`,
    category: 'performance',
    tags: ['bottlenecks', 'optimization', 'debugging'],
    difficulty: 'intermediate',
    estimatedReadTime: 2,
    relatedQuestions: ['perf-2', 'perf-4', 'gs-6'],
  },
  {
    id: 'perf-4',
    question: 'What features are most expensive?',
    answer: `**Ranked by Latency Cost:**

**1. LLM Re-ranking: +2000ms** 🔴
- Sends all results to LLM
- Scores each for relevance
- Only use for critical queries

**2. Web Search: +800ms** 🟠
- Network requests to SearXNG
- Crawls multiple search engines
- Use for current events only

**3. LLM Generation: ~1500ms** 🟡
- Model inference time
- Depends on model size and GPU
- Required (can't disable)

**4. Knowledge Graph: +50ms** 🟢
- Graph traversal (BFS)
- Low cost, good value

**5. Hybrid Search: +30ms** 🟢
- Vector + BM25 + fusion
- Excellent value (+20% recall)

**6. Query Expansion: +10ms** 🟢
- Nearly free
- Good recall improvement

**Rule of Thumb:** Disable re-ranking and web search for speed. Keep everything else.`,
    category: 'performance',
    tags: ['cost', 'features', 'optimization'],
    difficulty: 'intermediate',
    estimatedReadTime: 2,
    relatedQuestions: ['perf-3', 'search-9'],
  },
  {
    id: 'perf-5',
    question: 'When should I disable re-ranking?',
    answer: `**Disable Re-ranking When:**
- Real-time applications (< 500ms target)
- High QPS systems (> 100 queries/min)
- Speed is more important than precision
- Using Production preset (already optimized)

**Keep Re-ranking When:**
- Critical queries (legal, medical, research)
- Low query volume (< 10 queries/min)
- Offline analysis
- Quality benchmarking
- Precision > 95% required

**Impact of Disabling:**
- Saves: 2000ms latency
- Loses: 10-15% precision
- Trade-off: Speed vs Quality

**This Lab Presets:**
- Minimal, Fast, Balanced, Quality, Production: Re-ranking OFF
- Maximum: Re-ranking ON (for quality comparison)

**Recommendation:** Only enable for offline analysis or critical queries.`,
    category: 'performance',
    tags: ['reranking', 'optimization', 'trade-offs'],
    difficulty: 'intermediate',
    estimatedReadTime: 2,
    relatedQuestions: ['perf-4', 'search-9'],
  },
  {
    id: 'perf-6',
    question: 'How do I optimize for speed?',
    answer: `**Speed Optimization Strategies:**

**1. Use Fast Preset**
- Pre-configured for speed
- ~60ms latency
- Acceptable quality

**2. Disable Expensive Features**
- ❌ Re-ranking (-2000ms)
- ❌ Web Search (-800ms)
- ❌ Knowledge Graph (-50ms)

**3. Reduce top_k**
- Default: 10 documents
- Try: 5 documents
- Saves: ~20ms

**4. Use Smaller Model**
- llama3.2:1b (100+ tok/s)
- llama3.2:3b (60-80 tok/s)
- vs llama3.1:8b (40-60 tok/s)

**5. Optimize Infrastructure**
- Use GPU (10x faster than CPU)
- Add more RAM (reduce swapping)
- Use SSD (faster disk I/O)

**Expected Results:**
- Minimal config: ~200ms
- Fast config: ~60ms
- Vector-only: ~35ms

**This Lab:** Try "Fast" preset to see speed-optimized configuration.`,
    category: 'performance',
    tags: ['speed', 'optimization', 'latency'],
    difficulty: 'intermediate',
    estimatedReadTime: 2,
    relatedQuestions: ['perf-7', 'perf-8'],
  },
  {
    id: 'perf-7',
    question: 'How do I optimize for quality?',
    answer: `**Quality Optimization Strategies:**

**1. Use Quality or Maximum Preset**
- Pre-configured for quality
- All features enabled
- ~5-10s latency (Maximum)

**2. Enable All Features**
- ✅ Query Expansion (+5% recall)
- ✅ Hybrid Search (+20% recall)
- ✅ Knowledge Graph (+5% recall)
- ✅ Re-ranking (+15% precision)
- ✅ Web Search (current info)

**3. Increase top_k**
- Default: 10 documents
- Try: 15-20 documents
- Better coverage

**4. Use Larger Model**
- qwen2.5:14b (best quality)
- gemma2:9b (high quality)
- vs llama3.2:3b (baseline)

**5. Better Documents**
- Well-written, structured
- Clear headings
- Relevant metadata

**Expected Results:**
- Quality config: 92-96% precision
- Maximum config: 95-98% precision

**This Lab:** Try "Quality" or "Maximum" preset for best results.`,
    category: 'performance',
    tags: ['quality', 'optimization', 'accuracy'],
    difficulty: 'intermediate',
    estimatedReadTime: 2,
    relatedQuestions: ['perf-6', 'perf-9'],
  },
  {
    id: 'perf-8',
    question: 'What are production best practices?',
    answer: `**Production Configuration:**

**1. Use Production Preset** ⭐
- Balanced speed and quality
- 250-350ms latency
- 92-96% precision
- Scalable to 100+ QPS

**2. Enable These Features:**
- ✅ Query Expansion (cheap, good ROI)
- ✅ BM25 + Vector (best recall)
- ✅ Hybrid Fusion (nearly free)
- ✅ Knowledge Graph (comprehensive)

**3. Disable These Features:**
- ❌ LLM Re-ranking (too expensive)
- ❌ Web Search (external dependency)

**4. Infrastructure:**
- 8-16 CPU cores
- 32-64GB RAM
- GPU recommended (10x faster)
- SSD storage

**5. Monitoring:**
- Track latency (p50, p95, p99)
- Monitor error rate
- Log all queries
- Alert on anomalies

**6. Scalability:**
- Add vector DB replicas
- Cache embeddings
- Rate limiting
- Load balancing

**This Lab:** Production preset is deployment-ready!`,
    category: 'performance',
    tags: ['production', 'best-practices', 'deployment'],
    difficulty: 'advanced',
    estimatedReadTime: 3,
    relatedQuestions: ['perf-6', 'perf-7', 'perf-9'],
  },
  {
    id: 'perf-9',
    question: 'What is the speed vs quality trade-off?',
    answer: `**The Fundamental Trade-off:**

**Fast (< 100ms):**
- Vector search only
- No advanced features
- 80% precision, 75% recall
- Use: Autocomplete, real-time search

**Balanced (100-300ms):** ⭐ RECOMMENDED
- Hybrid search + query expansion
- Knowledge graph
- 87% precision, 82% recall
- Use: General purpose, daily use

**Quality (300-1000ms):**
- All features except re-ranking
- Web search enabled
- 92% precision, 88% recall
- Use: Research, complex queries

**Maximum (5-30 minutes):**
- All features including re-ranking
- 96% precision, 92% recall
- Use: Quality benchmarking only

**Key Insight:** Balanced gives 87% quality at 120ms. Maximum gives 96% quality at 30 minutes. The extra 9% costs 15,000x more time!

**This Lab:** Compare presets to see the trade-off visually.`,
    category: 'performance',
    tags: ['trade-offs', 'speed', 'quality'],
    difficulty: 'intermediate',
    estimatedReadTime: 3,
    relatedQuestions: ['perf-6', 'perf-7', 'perf-8'],
  },
  {
    id: 'perf-10',
    question: 'How do I monitor RAG performance over time?',
    answer: `**Monitoring Strategies:**

**1. Use Metrics Tab**
- View query history
- Filter by date/config
- Export to CSV
- Analyze trends

**2. Track Key Metrics:**
- **Latency:** p50, p95, p99
- **Throughput:** Queries per minute
- **Error Rate:** Failed queries / Total
- **Quality:** User feedback (thumbs up/down)

**3. Use Prompt Logs Tab**
- Export to Splunk
- Create dashboards
- Set up alerts
- Anomaly detection

**4. Splunk Dashboards:**
\`\`\`
- Queries/min over time
- Latency p95 trend
- Error rate by service
- Cost per user
- Token usage by model
\`\`\`

**5. Alerts:**
- Latency > 2s for 5 minutes
- Error rate > 5%
- Disk space < 10%
- GPU memory > 90%

**This Lab:** Export metrics to Splunk for full observability.`,
    category: 'performance',
    tags: ['monitoring', 'observability', 'splunk'],
    difficulty: 'advanced',
    estimatedReadTime: 2,
    relatedQuestions: ['perf-1', 'gs-6', 'gs-7'],
  },

  // Continue with remaining categories in next batch...
];

export default QA_DATA_EXTENDED;

