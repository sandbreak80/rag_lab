# RAG Lab Roadmap

**Target Audience:** Splunk/Cisco Field Teams (Architects, SEs, Sales Leaders)

**Current Status:** 85% Ready - Strong RAG foundation, missing critical teaching tools

---

## ✅ COMPLETED (Current State)

### Core RAG Pipeline
- ✅ Query Expansion (synonym/related terms)
- ✅ Vector Search (semantic similarity)
- ✅ BM25 Keyword Search (exact term matching)
- ✅ Hybrid Search (RRF fusion)
- ✅ Knowledge Graph (4 algorithms: wikilinks, semantic, entity, hybrid)
- ✅ LLM Re-ranking (precision improvement)
- ✅ Web Search (SearXNG integration)
- ✅ Agentic Chunking (LLM-powered intelligent splitting)

### Infrastructure
- ✅ Microservices architecture (12 services)
- ✅ Docker Compose orchestration
- ✅ Persistent storage (ChromaDB, BM25 indices, KG, uploads)
- ✅ API Gateway with metrics
- ✅ Health checks and monitoring endpoints

### UI/UX
- ✅ React + TypeScript frontend (port 5173)
- ✅ Multi-tab interface (Chat, Documents, Settings, Metrics, Lab Guide, Q&A, Feedback)
- ✅ Document upload (PDF, Office, Markdown, TXT - up to 50MB)
- ✅ RAG feature toggles (enable/disable to see impact)
- ✅ Configuration presets (Minimal, Fast, Balanced, Quality, Maximum, Production)
- ✅ Model selector (dynamic from Ollama)
- ✅ KG algorithm selector with comparison
- ✅ Database reset for LLM poisoning labs

### Documentation
- ✅ Comprehensive lab guides
- ✅ AI fundamentals teaching
- ✅ RAG features deep dive
- ✅ Architecture documentation
- ✅ KG algorithm comparison exercise
- ✅ Model comparison exercise framework
- ✅ Performance optimization guide

---

## 🔥 PHASE 1: CRITICAL (In Progress - Week 1)

**Goal:** Make the lab ready for initial field team delivery

### Priority 1A: Fix Core UX Issues (2 hours)
**Status:** 🚧 IN PROGRESS

1. **Chat Persistence** (30 min)
   - **Issue:** Chat history lost on page refresh
   - **Solution:** Persist messages to localStorage
   - **Impact:** Better UX, students can navigate tabs without losing context

2. **Validate RAG Toggles** (1 hour)
   - **Issue:** Need to verify all toggles actually work
   - **Tests:** Query Expansion, BM25, Hybrid, Graph, Reranking, Web Search
   - **Impact:** Core functionality - students must see feature impact

### Priority 1B: Critical Teaching Tools (6 hours)
**Status:** 📋 PLANNED

3. **Response Time Waterfall Chart** (4-6 hours) ⭐ **CRITICAL**
   - **Why:** Students need to SEE the latency cost of each feature
   - **Implementation:**
     - Add Recharts to frontend
     - Create waterfall/stacked bar chart component
     - Show time breakdown: Query Expansion → Vector Search → BM25 → Hybrid Fusion → KG → Re-ranking → Web Search → LLM
     - Display on Metrics tab + inline after each query
   - **Learning Objective:** "Maximum preset takes 30 min because re-ranking (2s) + web search (60s) + large model (5 min)"
   - **Impact:** 🔥 Core teaching tool - demonstrates quality vs latency trade-offs

4. **Model Size vs Context Window Lab** (2-3 hours) ⭐ **HIGH EDUCATIONAL VALUE**
   - **Why:** Teaches cost/performance optimization (critical enterprise skill)
   - **Implementation:**
     - Add context window slider to Settings
     - Create comparison exercise (like KG algorithms)
     - Test: "Llama 3.2 1B + 8K context" vs "Llama 3.1 8B + 2K context"
   - **Learning Objective:** "Bigger model ≠ always better. Context window matters!"
   - **Impact:** 🔥 Students learn to optimize for their constraints (16GB laptops)

**Phase 1 Total Time:** 8-11 hours
**Phase 1 Completion Target:** End of Week 1

---

## ⚡ PHASE 2: HIGH VALUE ENHANCEMENTS (Week 2-3)

**Goal:** Add features that significantly improve educational value

### 2A: Quick Wins (2-4 hours)

1. **Metadata Filtering UI** (2 hours)
   - Filters: Document Type, Date Range, Tags, Author
   - Impact: +5% precision, teaches metadata importance
   - Effort: Low (metadata already tracked)

2. **Chat History Export** (2 hours)
   - Export conversation as Markdown/PDF
   - Students can save experiments for reports
   - Ties into "prompt logging" best practices

### 2B: Advanced RAG Features (8-12 hours)

3. **Query Decomposition** (4-6 hours)
   - Break complex questions into sub-queries
   - Parallel search, synthesize results
   - Impact: +18% on complex questions
   - Learning: LLM orchestration, agentic behavior
   - Example: "Compare hybrid search vs vector-only AND explain knowledge graphs"
     - → Sub-query 1: "hybrid search performance"
     - → Sub-query 2: "vector search performance"
     - → Sub-query 3: "what are knowledge graphs"
     - → Synthesize combined answer

4. **Prompt Logging & Analysis** (3-4 hours)
   - Log all prompts to metrics database
   - Show students what enterprise AI systems capture
   - Display: timestamp, user, query, model, tokens, latency, cost estimate
   - **Splunk Tie-in:** "This is what you'd send to Splunk Observability Cloud"

5. **Token Usage Tracking** (1-2 hours)
   - Track prompt tokens, completion tokens, total tokens
   - Show cumulative cost (if using paid APIs)
   - Learning: AI operations cost management

**Phase 2 Total Time:** 10-18 hours

---

## 🔮 PHASE 3: ADVANCED FEATURES (Month 2+)

**Goal:** Cutting-edge RAG techniques and production readiness

### 3A: Self-RAG (8-10 hours)
- Iterative refinement with LLM self-critique
- Impact: +20% complex handling, -15% hallucination
- Learning: Advanced RAG architectures
- **Status:** Research phase - very cutting edge

### 3B: LLM Routing (4-6 hours)
- Route to different models based on query complexity
- Simple query → Llama 3.2 1B (fast)
- Complex query → Llama 3.1 8B (accurate)
- Learning: Cost optimization, query classification

### 3C: Evaluation Framework (6-8 hours)
- Knowledge pairs (question → expected answer)
- Automated RAG metrics: Recall, Precision, Faithfulness, Answer Relevance
- Compare configurations automatically
- Learning: How to measure RAG quality

---

## 🛡️ PHASE 4: AI SECURITY LAB (Separate Offering)

**Goal:** Dedicated lab for AI security concerns

### Features:
- Prompt injection detection
- Emoji smuggling prevention
- Buffer overflow protection
- Context window overflow handling
- Jailbreak attempt logging
- Content filtering

**Why Separate:**
- Different learning objective (security vs RAG quality)
- Different audience (security teams vs field teams)
- Splunk security products tie-in

**Delivery:** Q2 2025 (after main RAG lab launch)

---

## 🏢 PHASE 5: PRODUCTION & ENTERPRISE (Month 3+)

**Goal:** Take learnings to production

### 5A: Splunk Observability Integration
- OpenTelemetry instrumentation
- LLM observability (groundedness, cost, latency)
- System metrics (CPU, RAM, GPU)
- Docker container stats
- End-to-end trace visualization

### 5B: AWS Bedrock Migration
- Production LLM service (vs local Ollama)
- Claude 3, GPT-4, etc.
- Cost comparison lab
- Learning: On-prem vs cloud trade-offs

### 5C: Multi-LLM Orchestration
- Multiple Ollama instances
- Request queuing
- Load balancing
- Learning: Production scalability

---

## ❌ OUT OF SCOPE / FUTURE CONSIDERATIONS

### Not Planned (Wrong Focus):
- **Multimodal Output (PPT/Docs):** Different product demo, not RAG learning
- **Database SQL Integration:** Agentic AI, not RAG focus
- **MCP Integration:** Too bleeding edge, not stable enough
- **Docker Scaling Infrastructure:** Operations topic, not AI learning

### Parking Lot (Maybe Later):
- Graph visualization (D3.js/Cytoscape)
- PageRank scoring for KG nodes
- Community detection in KG
- Temporal knowledge graph
- Citation analysis
- Advanced NER (spaCy/BERT)

---

## 📊 FEATURE PRIORITIZATION MATRIX

| Feature | Lab Value | Complexity | Priority | Phase |
|---------|-----------|------------|----------|-------|
| Response Time Waterfall | ⭐⭐⭐⭐⭐ | Medium | CRITICAL | 1 |
| Model vs Context Lab | ⭐⭐⭐⭐⭐ | Low | CRITICAL | 1 |
| Chat Persistence | ⭐⭐⭐⭐☆ | Low | Must-Do | 1 |
| Toggle Validation | ⭐⭐⭐⭐⭐ | Low | Must-Do | 1 |
| Metadata Filtering | ⭐⭐⭐☆☆ | Low | Should-Do | 2 |
| Query Decomposition | ⭐⭐⭐⭐☆ | Medium | Should-Do | 2 |
| Prompt Logging | ⭐⭐⭐☆☆ | Low | Should-Do | 2 |
| Token Tracking | ⭐⭐⭐☆☆ | Low | Should-Do | 2 |
| Self-RAG | ⭐⭐⭐⭐☆ | High | Nice-to-Have | 3 |
| LLM Routing | ⭐⭐⭐☆☆ | Medium | Nice-to-Have | 3 |
| AI Security Lab | ⭐⭐⭐⭐☆ | High | Separate Offering | 4 |
| Splunk O11y | ⭐⭐⭐⭐⭐ | High | Future State | 5 |
| AWS Bedrock | ⭐⭐⭐☆☆ | Medium | Future State | 5 |

---

## 🎯 SUCCESS CRITERIA

### Phase 1 Complete When:
- ✅ Chat persists across page refreshes
- ✅ All RAG toggles validated and working
- ✅ Waterfall chart shows timing for each RAG component
- ✅ Model/context comparison exercise documented
- ✅ Students can see latency trade-offs visually

### Phase 2 Complete When:
- ✅ Metadata filters working in UI
- ✅ Query decomposition demonstrated
- ✅ Prompt logging captured and displayed
- ✅ Token usage tracked and shown

### Lab Ready for Field Delivery When:
- Phase 1 complete ✅
- All documentation updated ✅
- Screenshots taken for lab guide ✅
- End-to-end testing passed ✅
- Instructor guide created ✅

---

## 🚀 DELIVERY TIMELINE

| Phase | Timeline | Hours | Status |
|-------|----------|-------|--------|
| **Phase 1 (Critical)** | Week 1 | 8-11 hours | 🚧 In Progress |
| **Phase 2 (High Value)** | Week 2-3 | 10-18 hours | 📋 Planned |
| **Phase 3 (Advanced)** | Month 2+ | 18-24 hours | 🔮 Research |
| **Phase 4 (Security)** | Q2 2025 | TBD | 💭 Concept |
| **Phase 5 (Production)** | Q2-Q3 2025 | TBD | 💭 Concept |

---

## 💡 KEY INSIGHTS

### What Makes This Lab Unique:
1. **Not just a RAG demo** - students can toggle features and see impact
2. **Multiple KG algorithms** - unique educational comparison
3. **Full microservices architecture** - production-ready reference
4. **Splunk integration roadmap** - product value demonstration
5. **Built in 1 week by AI + 1 person** - case study for field teams

### Core Learning Objectives:
1. **Quality vs Latency Trade-offs** - Maximum preset takes 30 min, Balanced takes < 1s
2. **Cost Optimization** - Small model + large context can beat large model + small context
3. **Feature Impact** - Each RAG component has measurable effect on precision/recall
4. **Production Considerations** - Monitoring, scaling, cost management
5. **Splunk Value** - Where Splunk fits in AI/LLM observability

### Critical Success Factor:
**Students must SEE and FEEL the trade-offs, not just read about them.**
→ This is why the waterfall chart is CRITICAL.

---

## 📝 NOTES

- Lab is **85% ready** - strong foundation, missing critical teaching tools
- **15% gap** is in visualization and teaching aids, not RAG features
- Focus on **teaching tools** over **more RAG features**
- Keep **self-referential**: Lab docs ingested into RAG for testing
- Maintain **AI development case study**: Built in < 1 week by AI + 1 person

---

**Last Updated:** November 2, 2025
**Next Review:** After Phase 1 completion
