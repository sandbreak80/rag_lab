# 🎓 RAG Lab - Educational Objectives & Design

**Target Audience:** Students learning RAG (Retrieval-Augmented Generation) systems
**Lab Duration:** 2-3 hours hands-on
**Skill Level:** Intermediate (some ML/AI background helpful)

---

## Lab Purposes

### 1. **Provide Working RAG System** 🚀
- Students get a production-ready RAG they can run on their laptops
- Works with their own documents (PDFs, Markdown, Office files)
- No cloud dependencies - fully local with Ollama
- Take it home and use it for personal knowledge management

### 2. **Demonstrate RAG Complexity** 🧠
- Show that "world-class" RAG is NOT simple
- Multiple components working together
- Trade-offs between quality, speed, and resources
- Counter the "just throw it at ChatGPT" mindset

### 3. **Showcase AI-Assisted Development** 🤖
- Entire project built with AI coding tools (Cursor / VS Code)
- Show students the power of AI pair programming
- Demonstrate modern development workflows
- Inspire confidence: "You can build this too!"

### 4. **Teach RAG Components Through Experimentation** 🔬
- **Start with everything OFF** - baseline (poor quality)
- **Enable features one-by-one** - watch quality improve
- **Measure impact** - metrics change in real-time
- **Understand trade-offs** - quality vs. speed vs. cost

### 5. **Enable Data-Driven Decisions** 📊
- Students learn: "Which features matter for MY data?"
- Balance value, resources, delay, and quality
- No one-size-fits-all answer
- Hands-on experimentation builds intuition

### 6. **First Deep Dive into World-Class RAG** 🏆
- Not a toy demo - production-quality system
- Covers models, embeddings, chunking, retrieval, generation
- Document what each feature does
- Expected value, cost, and latency for each component

---

## Lab Structure

### Phase 1: Setup (15 minutes)
```bash
# Students clone and start the system
git clone https://github.com/sandbreak80/rag_lab.git
cd rag_lab
docker-compose -f docker-compose.test.yml up -d

# Upload their own documents
# System processes and indexes them
```

### Phase 2: Baseline - Everything OFF (15 minutes)
**Configuration:**
- ❌ Query Expansion: OFF
- ❌ BM25 Search: OFF
- ✅ Vector Search: ON (baseline)
- ❌ Knowledge Graph: OFF
- ❌ LLM Re-ranking: OFF
- Simple Chunking (not agentic)
- Basic embedding model

**Expected Results:**
- Precision: ~60-70%
- Recall: ~50-60%
- Latency: ~50ms
- Quality: "Okay, but misses context"

**Learning Goal:** Understand baseline vector search limitations

### Phase 3: Add Features One-by-One (60 minutes)

#### Step 1: Enable Query Expansion ✅
**What it does:** Adds synonyms and related terms to query
**Expected improvement:** +5% recall
**Cost:** +10ms latency, minimal compute
**Best for:** Queries with technical jargon or ambiguous terms

**Students observe:**
- Query "ML" expands to "machine learning, artificial intelligence"
- More relevant documents retrieved
- Metrics update in real-time

---

#### Step 2: Enable BM25 + Hybrid Search ✅
**What it does:** Adds keyword matching, fuses with vector search
**Expected improvement:** +15-20% recall, +5% precision
**Cost:** +30ms latency, 50MB index size
**Best for:** Exact term matching, acronyms, proper nouns

**Students observe:**
- Finds documents that vector search missed
- Better handling of rare terms
- Reciprocal Rank Fusion combines both methods

---

#### Step 3: Enable Agentic Chunking ✅
**What it does:** Intelligent semantic boundaries (vs fixed-size chunks)
**Expected improvement:** +10-15% precision
**Cost:** One-time processing delay (offline)
**Best for:** Structured documents (headings, code, lists)

**Students observe:**
- Chunks respect semantic boundaries
- Code blocks stay together
- Better context preservation

---

#### Step 4: Enable Knowledge Graph ✅
**What it does:** Finds related documents via wikilinks, tags, folders
**Expected improvement:** +5% recall (multi-hop queries)
**Cost:** +50ms latency, graph traversal
**Best for:** Connected knowledge bases, research notes

**Students observe:**
- Related documents surface automatically
- Multi-hop reasoning works
- Network effects in personal knowledge

---

#### Step 5: Enable LLM Re-ranking ✅
**What it does:** LLM scores each result for relevance
**Expected improvement:** +10-15% precision
**Cost:** +2000ms latency (!), high compute
**Best for:** Critical queries where precision matters

**Students observe:**
- Slow but very accurate
- Irrelevant results filtered out
- Quality vs. speed trade-off

---

### Phase 4: Optimization & Trade-offs (30 minutes)

**Students experiment with:**

#### Model Selection
- `llama3.2:1b` - Fast, lightweight, good for summaries
- `llama3.2:3b` - Balanced (default)
- `llama3.2:8b` - Slower but more accurate

#### Embedding Models
- `nomic-embed-text` - 768 dims, fast (default)
- `mxbai-embed-large` - 1024 dims, better quality
- Trade-off: quality vs. memory

#### LLM Parameters
- **Temperature:** 0.0 (factual) vs. 1.0 (creative)
- **Context Window:** 2000 (fast) vs. 8000 (comprehensive)
- **Top-K Results:** 3 (focused) vs. 20 (comprehensive)
- **Max Tokens:** 500 (concise) vs. 2000 (detailed)

**Students discover:**
- No universal "best" configuration
- Depends on: data type, query complexity, hardware
- Balance: quality, speed, resource usage

---

### Phase 5: Real-World Scenarios (30 minutes)

#### Scenario 1: Research Assistant
**Goal:** High precision, multi-hop reasoning
**Config:** All features ON, re-ranking ON, context window 8000
**Trade-off:** Slow (3-5s) but extremely accurate

#### Scenario 2: Quick Lookup
**Goal:** Fast responses for known information
**Config:** Hybrid search only, small context, re-ranking OFF
**Trade-off:** Fast (<100ms) but may miss nuance

#### Scenario 3: Production API
**Goal:** Balance quality and throughput
**Config:** Hybrid + agentic + graph, re-ranking OFF
**Trade-off:** Good quality (~200ms), scalable

**Students learn:** Configure for use case, not maximum features

---

## Key Metrics Explained

### Retrieval Metrics

#### **Precision** (90-95% target)
- % of retrieved documents that are relevant
- "When it retrieves something, is it right?"
- High precision = few false positives
- **Trade-off:** Can sacrifice recall

#### **Recall** (85-90% target)
- % of relevant documents that are retrieved
- "Did we find everything we should have?"
- High recall = didn't miss important docs
- **Trade-off:** May include irrelevant results

#### **Coverage** (100% target)
- % of queries that return any results
- Basic health check
- Should be 100% for production

#### **MRR - Mean Reciprocal Rank** (0.8+ target)
- Position of first relevant result (1/rank)
- MRR of 1.0 = always first result is relevant
- MRR of 0.5 = first relevant at position 2 on average
- **Why it matters:** Users don't scroll

#### **NDCG - Normalized Discounted Cumulative Gain** (0.8+ target)
- Quality of ranking (position matters)
- Rewards relevant docs at top positions
- Penalizes relevant docs buried deep
- **Why it matters:** Ranking quality impacts user experience

### Generation Metrics

#### **Faithfulness** (95%+ target)
- Is the answer grounded in retrieved context?
- Detects hallucinations
- **How measured:** Check if answer uses only retrieved facts

#### **Answer Relevance** (90%+ target)
- Does the answer address the query?
- Not just factual, but on-topic
- **How measured:** Semantic similarity to query

#### **Latency** (Component breakdown)
- Retrieval: 30-50ms (vector/BM25)
- Embedding: 10-20ms (query embedding)
- Graph: 30-50ms (if enabled)
- Re-ranking: 2000-3000ms (if enabled)
- LLM Generation: 50-200ms (depends on model/length)
- **Total:** 100ms (fast) to 3000ms (all features)

#### **Token Usage** (Cost tracking)
- Input tokens: Query + context
- Output tokens: Generated answer
- **Cost:** ~$0.01 per 1000 tokens (Ollama is free, but useful for cloud)

### Performance Metrics

#### **Throughput** (queries/second)
- Fast mode: 20-50 QPS
- Balanced: 5-10 QPS
- Re-ranking: 0.5-1 QPS
- **Impacts:** System capacity, user experience

#### **Resource Usage**
- Memory: 2-8GB (depends on model)
- CPU: Minimal (unless re-ranking)
- GPU: Optional, 10x speedup for embeddings/LLM
- **Impacts:** Deployment cost, scalability

---

## Component Documentation

### 1. Query Expansion
**What:** Enriches query with synonyms, related terms
**How:** LLM or rule-based expansion
**Value:** +5% recall
**Cost:** +10ms latency, minimal compute
**When to use:** Technical queries, ambiguous terms
**When to skip:** Simple factual lookups

### 2. Vector Search (Embeddings)
**What:** Semantic similarity via dense vectors
**How:** Embedding model + cosine similarity
**Value:** Core RAG capability (baseline)
**Cost:** 768-1024 dimensions, ~10ms
**When to use:** Always (baseline)
**When to skip:** Never (it's the foundation)

### 3. BM25 Keyword Search
**What:** Statistical keyword matching (TF-IDF based)
**How:** Inverted index + BM25 scoring
**Value:** +15% recall (exact matches)
**Cost:** +30ms, 50MB index
**When to use:** Technical docs, rare terms, names
**When to skip:** Pure semantic queries

### 4. Hybrid Search (Vector + BM25)
**What:** Fuses vector and keyword results
**How:** Reciprocal Rank Fusion (RRF)
**Value:** +20% recall, +5% precision
**Cost:** +30ms (just BM25 overhead)
**When to use:** Most production systems
**When to skip:** Extreme low-latency requirements

### 5. Agentic Chunking
**What:** Intelligent semantic boundaries
**How:** LLM analyzes document structure
**Value:** +10-15% precision
**Cost:** Offline processing only
**When to use:** Structured docs (code, research)
**When to skip:** Simple text, tight storage

### 6. Knowledge Graph
**What:** Document relationships (wikilinks, tags)
**How:** Graph traversal (BFS)
**Value:** +5% recall (multi-hop)
**Cost:** +50ms, graph storage
**When to use:** Connected notes, research
**When to skip:** Independent documents

### 7. LLM Re-ranking
**What:** LLM scores each result for relevance
**How:** LLM evaluates query-document pairs
**Value:** +10-15% precision
**Cost:** +2000ms (!), high compute
**When to use:** Critical queries, low QPS
**When to skip:** Real-time systems, high traffic

### 8. Entity Extraction
**What:** Extract key concepts, people, technologies
**How:** Regex + optional LLM
**Value:** Better metadata, filtering
**Cost:** Minimal (offline processing)
**When to use:** Large knowledge bases
**When to skip:** Small, simple docs

---

## Expected Learning Outcomes

### By the end of this lab, students will:

1. ✅ **Understand RAG architecture** - Not a black box anymore
2. ✅ **Know the components** - What each piece does and why
3. ✅ **Measure impact** - Use metrics to guide decisions
4. ✅ **Make trade-offs** - Balance quality, speed, cost
5. ✅ **Configure for use case** - No one-size-fits-all
6. ✅ **Deploy locally** - Have a working system to take home
7. ✅ **Appreciate AI tools** - See what's possible with AI coding assistants

### Skills Developed

**Technical:**
- RAG system design and implementation
- Performance measurement and optimization
- Docker and microservices architecture
- Embedding models and vector databases
- LLM integration and prompt engineering

**Analytical:**
- Experimental design (A/B testing)
- Metrics interpretation
- Trade-off analysis
- Data-driven decision making

**Practical:**
- Real-world system configuration
- Debugging and troubleshooting
- Documentation reading
- Performance tuning

---

## Lab Materials Needed

### For Instructors:
- [ ] Slide deck explaining RAG concepts
- [ ] Pre-built test document corpus (20-30 docs)
- [ ] Test questions with ground truth answers (20 questions)
- [ ] Configuration cheat sheet
- [ ] Troubleshooting guide
- [ ] Expected metrics reference table

### For Students:
- [ ] Lab workbook with exercises
- [ ] Metrics interpretation guide
- [ ] Quick reference card (keyboard shortcuts, commands)
- [ ] Post-lab survey for feedback

### Technical Requirements:
- [ ] Laptop with 8GB+ RAM
- [ ] Docker Desktop installed
- [ ] Ollama installed with models
- [ ] GitHub account (to fork the repo)
- [ ] Text editor (VS Code recommended)

---

## Success Metrics for the Lab

### Student Engagement:
- [ ] 90%+ complete all phases
- [ ] 80%+ try at least 3 different configurations
- [ ] 75%+ upload their own documents

### Learning Validation:
- [ ] 85%+ can explain precision vs. recall
- [ ] 80%+ can configure system for a use case
- [ ] 90%+ understand trade-offs

### Satisfaction:
- [ ] 4.5+ / 5.0 average rating
- [ ] 80%+ say they learned something new
- [ ] 70%+ plan to use system after lab

---

## Next Steps: UI Implementation

### Immediate Goals:
1. **Settings Panel** - Let students toggle features
2. **Metrics Dashboard** - Real-time performance display
3. **Comparison Mode** - A/B test configurations
4. **Educational Tooltips** - Explain each setting
5. **Test Dataset** - Pre-built questions for benchmarking

### Design Principles:
- **Single page** - No navigation confusion
- **Visual feedback** - Metrics update immediately
- **Undo-friendly** - Easy to reset and try again
- **Self-documenting** - UI explains itself
- **Performance-aware** - Show latency impacts

### Implementation Order:
1. Create test dataset (20 questions)
2. Add settings panel to UI
3. Implement metrics tracking in backend
4. Build metrics dashboard UI
5. Add comparison mode
6. Write educational tooltips
7. Test with real students

---

**This lab will be AMAZING! 🚀**

Students will leave with:
- A working RAG system they understand
- Knowledge to build their own
- Appreciation for AI-assisted development
- Confidence to tackle complex ML projects

