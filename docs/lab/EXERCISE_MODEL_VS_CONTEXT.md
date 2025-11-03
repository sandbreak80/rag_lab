# 🧪 Lab Exercise: Model Size vs Context Window Optimization

## Learning Objectives
- Understand the trade-offs between model size and context window
- Learn that "bigger isn't always better"
- Discover how to optimize for specific constraints (e.g., 16GB laptop)
- Apply this knowledge to real-world AI deployment scenarios

---

## The Question

**On a 16GB laptop, what performs better for RAG:**
- **Option A:** Large model (8B parameters) + Small context (2K tokens)
- **Option B:** Small model (3B parameters) + Large context (8K tokens)

**Hypothesis:** Most students guess Option A. Let's find out!

---

## Background

### Why This Matters
Enterprise AI deployments face **resource constraints**:
- **Sales laptops:** 16GB RAM
- **Edge devices:** Limited compute
- **Cost optimization:** Smaller = cheaper inference

**Key Insight:** You can't have both maximum model size AND maximum context. You must choose!

### The Trade-off

| Resource | Model Size | Context Window |
|----------|------------|----------------|
| **RAM** | 8B model ≈ 6-8GB | 2K context ≈ 1GB |
| **RAM** | 3B model ≈ 2-3GB | 8K context ≈ 4GB |
| **Total** | ~8GB (fits 16GB laptop) | ~6GB (fits 16GB laptop) |

### Theory

**Large Model Benefits:**
- Better instruction following
- More world knowledge
- Higher quality responses

**Large Context Benefits:**
- More relevant documents in prompt
- Better synthesis across sources
- Reduced information loss

**The Question:** Which has more impact on RAG quality?

---

## Exercise Steps

###  Step 1: Test Large Model + Small Context

1. Go to **Settings** tab
2. Set configuration:
   - **Model:** `llama3.1:8b` (or largest available)
   - **Context Window:** `2048` tokens
   - **Top-K:** `3` documents (limited by small context)
   - **Temperature:** `0.7`
3. Enable **Vector Search** only (baseline)
4. Go to **Chat** tab
5. Ask: "What are the key differences between vector search and hybrid search?"
6. **Record:**
   - Total latency (from waterfall chart)
   - LLM generation time
   - Answer quality (1-5 scale)
   - Sources used

**Expected Results:**
- Latency: ~15-30 seconds
- Quality: Good (model is smart)
- Limitation: Only 3 documents fit in context

---

### Step 2: Test Small Model + Large Context

1. Go to **Settings** tab
2. Set configuration:
   - **Model:** `llama3.2:3b` (or smallest available)
   - **Context Window:** `8192` tokens
   - **Top-K:** `10` documents (more fit in larger context!)
   - **Temperature:** `0.7`
3. Enable **Vector Search** only (baseline)
4. Go to **Chat** tab
5. Ask the **same question**: "What are the key differences between vector search and hybrid search?"
6. **Record:**
   - Total latency (from waterfall chart)
   - LLM generation time
   - Answer quality (1-5 scale)
   - Sources used

**Expected Results:**
- Latency: ~5-10 seconds (smaller model = faster)
- Quality: Good or better (more context = more information)
- Advantage: 10 documents provide richer information

---

### Step 3: Compare Results

| Metric | Large Model + Small Context | Small Model + Large Context |
|--------|----------------------------|----------------------------|
| **Latency** |  |  |
| **Sources** | 3 documents | 10 documents |
| **Quality** |  |  |
| **RAM Usage** | ~8GB | ~6GB |

**Discussion Questions:**
1. Which configuration produced a better answer?
2. Was the difference significant?
3. Which would you deploy for a sales team demo?
4. How does this change for different query types?

---

### Step 4: Test with Complex Query

Now try a more complex question that benefits from multiple sources:

**Query:** "How do query expansion, knowledge graphs, and re-ranking work together to improve RAG quality?"

This requires synthesizing information from **multiple** sources.

**Hypothesis:** Small model + large context should excel here because it can see more source documents.

**Test both configurations and compare!**

---

### Step 5: Find Your Optimal Configuration

1. Start with your constraints:
   - Available RAM: _________ GB
   - Latency budget: _________ ms/query
   - Use case: (Sales demo / Production / Research)

2. Use the Settings → Metrics tab to test combinations:
   - Try 3-4 different model/context combinations
   - Record latency, quality, and sources for each
   - Plot on a chart

3. **Identify your optimal point** where:
   - Latency < budget
   - Quality > acceptable threshold
   - RAM usage < available

---

## Key Takeaways

### Finding #1: Context Often Beats Model Size
For RAG systems specifically, **having more relevant context** often produces better answers than having a smarter model with limited context.

**Why?**
- RAG is retrieval-focused (model just synthesizes)
- More sources = less hallucination
- Smaller models are "good enough" at synthesis

### Finding #2: Latency Improves Dramatically
Smaller models generate tokens **2-3x faster**, which matters for interactive use cases.

### Finding #3: There's No Universal Answer
Optimal configuration depends on:
- **Query complexity:** Simple → small model OK, Complex → need larger
- **Use case:** Interactive demo → optimize latency, Research → optimize quality
- **Resources:** Limited RAM → must choose wisely

### Finding #4: This is Enterprise AI Reality
**Your customers face these exact trade-offs:**
- "Can we run this on our laptops?" (Yes, with smart sizing)
- "How fast will responses be?" (Depends on model size)
- "Can we reduce cloud costs?" (Yes, smaller models = cheaper)

---

## Advanced: The Math

### Context Window Capacity

**Rule of Thumb:** 1 token ≈ 0.75 words

| Context Window | Approximate Capacity |
|----------------|---------------------|
| 2K tokens | ~1,500 words | ~3 documents |
| 4K tokens | ~3,000 words | ~6 documents |
| 8K tokens | ~6,000 words | ~12 documents |
| 32K tokens | ~24,000 words | ~50 documents |

### Model Memory Usage

**Rough Estimates (Q4 quantization):**
- 1B parameters ≈ 0.5-1GB RAM
- 3B parameters ≈ 2-3GB RAM
- 7-8B parameters ≈ 5-8GB RAM
- 13B parameters ≈ 10-13GB RAM

### Total RAM Budget

```
Total RAM needed = Model RAM + Context RAM + Overhead (2-3GB)

Example:
8B model (6GB) + 2K context (1GB) + Overhead (3GB) = 10GB total
3B model (2.5GB) + 8K context (4GB) + Overhead (3GB) = 9.5GB total
```

---

## Connection to Splunk

**Splunk Observability Cloud** can monitor these metrics in production:

- **Model size** → Resource usage dashboards
- **Context window** → Token usage tracking
- **Latency by configuration** → Performance analysis
- **Quality by model** → Custom metrics (thumbs up/down)

**Field Team Message:**
"We help you find the optimal configuration for YOUR constraints, then monitor it in production."

---

## Next Steps

1. **Try other model combinations** available in Ollama
2. **Enable RAG features** (Graph, Re-ranking) and see how they interact with model size
3. **Test on your use case documents** - results may vary by domain
4. **Document your findings** for your customer conversations

---

## Instructor Notes

**Time Required:** 30-45 minutes

**Prerequisites:**
- Completed basic RAG pipeline labs
- Documents uploaded and indexed
- Multiple Ollama models downloaded

**Common Findings:**
- Most students are surprised small model + large context works so well
- Some queries DO need larger models (math, reasoning)
- Latency difference is dramatic and visible
- This exercise changes how they think about model selection

**Discussion Prompts:**
- "How would you explain this to a CTO?"
- "What if latency budget is < 1 second?"
- "How do we monitor this in production?" (→ Splunk)

**Extension Activities:**
- Compare quantization levels (Q4 vs Q8)
- Test with streaming vs non-streaming
- Build a decision matrix for model selection

---

**Lab Version:** 1.0
**Last Updated:** November 2, 2025
**Next Lab:** Query Decomposition & Agentic RAG

