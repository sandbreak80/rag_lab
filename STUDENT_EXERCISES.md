# 🎓 RAG Lab - Student Exercises

**Course:** Neural Networks & AI Systems  
**Module:** Retrieval Augmented Generation  
**Duration:** 3-4 hours  
**Difficulty:** Intermediate

---

## Learning Objectives

By completing these exercises, you will:
- Understand RAG architecture and components
- Measure and optimize system performance
- Make data-driven configuration decisions
- Deploy a production-ready RAG system

---

## Prerequisites

- Basic Python knowledge
- Understanding of neural networks
- Docker installed
- 2+ hours of dedicated time

---

## Setup

1. Start the RAG Lab:
```bash
cd rag_lab
docker-compose -f docker-compose.test.yml up -d
```

2. Open UI: http://localhost:5555

3. Wait for all services to be healthy (~30 seconds)

---

## Exercise 1: Baseline Performance (15 min)

### Objective
Establish baseline metrics for comparison.

### Steps

1. Click the ⚙️ settings button (bottom-left)
2. Load the **Minimal** preset
3. Close settings panel
4. Ask a question: "What is vector search?"
5. Observe the metrics dashboard appear
6. Click "Show Details" to see the breakdown

### Questions to Answer

**Q1.1:** What is the total latency for the minimal configuration?  
**A:** _________ ms

**Q2.2:** Which component takes the most time?  
**A:** ☐ Query Expansion  ☐ Vector Search  ☐ BM25  ☐ Fusion

**Q1.3:** What is the estimated precision?  
**A:** _________ %

**Q1.4:** How many results were returned?  
**A:** _________ documents

### Reflection

Write 2-3 sentences about what "baseline" means in the context of system optimization:

```
Your answer here:




```

---

## Exercise 2: Hybrid Search Benefits (20 min)

### Objective
Understand the value of combining vector and keyword search.

### Part A: Vector Only

1. Load **Minimal** preset (vector only)
2. Ask: "What are neural networks?"
3. Note the latency: _______ ms
4. Note the precision: _______ %
5. Read the top result

### Part B: Hybrid Search

1. Load **Balanced** preset (hybrid)
2. Ask the SAME question: "What are neural networks?"
3. Note the latency: _______ ms  
4. Note the precision: _______ %
5. Read the top result

### Part C: Comparison

1. Click "⚖️ Compare Configurations" button
2. Review the side-by-side comparison
3. Read the generated insights

### Questions to Answer

**Q2.1:** How much slower is hybrid search?  
**A:** _________ ms (_______ % increase)

**Q2.2:** How much better is the precision?  
**A:** _________ percentage points better

**Q2.3:** Is the latency increase worth the quality improvement?  
**A:** ☐ Yes  ☐ No  ☐ Depends on use case

**Q2.4:** When would you choose vector-only over hybrid?  
**A:**
```
Your answer here:




```

---

## Exercise 3: Performance Profiling (25 min)

### Objective
Identify bottlenecks in the RAG pipeline.

### Steps

1. Load **Quality** preset
2. Ask: "Explain how embeddings work"
3. Expand the detailed metrics view
4. Analyze the latency breakdown

### Data Collection

Fill in the table:

| Component | Time (ms) | % of Total | Active? |
|-----------|-----------|------------|---------|
| Query Expansion | _____ | _____ | ☐ Yes ☐ No |
| Vector Search | _____ | _____ | ☐ Yes ☐ No |
| BM25 Search | _____ | _____ | ☐ Yes ☐ No |
| Fusion | _____ | _____ | ☐ Yes ☐ No |
| Knowledge Graph | _____ | _____ | ☐ Yes ☐ No |
| LLM Re-ranking | _____ | _____ | ☐ Yes ☐ No |
| **TOTAL** | _____ | 100% | - |

### Analysis Questions

**Q3.1:** Which component is the bottleneck (takes most time)?  
**A:** _________________

**Q3.2:** If you had to reduce latency by 50ms, which component would you disable?  
**A:** _________________

**Q3.3:** What would you lose by disabling that component?  
**A:**
```
Your answer here:



```

**Q3.4:** The Knowledge Graph adds _____ ms. Is that acceptable for a 5% recall improvement?  
**A:** ☐ Yes  ☐ No

**Q3.5:** Calculate efficiency: (Results Found) / (Total Latency in seconds)  
**A:** _______ results per second

---

## Exercise 4: The Re-ranking Trade-off (20 min)

### Objective
Understand the extreme cost of LLM re-ranking.

### Part A: Without Re-ranking

1. Load **Quality** preset (re-ranking OFF)
2. Ask: "What are the best practices for RAG systems?"
3. Record metrics:
   - Latency: _______ ms
   - Precision: _______ %
   - Top result relevance (1-10): _______

### Part B: With Re-ranking

1. Open settings, enable "LLM Re-ranking" toggle
2. Ask the SAME question again
3. Record metrics:
   - Latency: _______ ms
   - Precision: _______ %
   - Top result relevance (1-10): _______

### Cost-Benefit Analysis

**Q4.1:** How much slower is re-ranking?  
**A:** _________ ms (______ x slower)

**Q4.2:** How much did precision improve?  
**A:** _________ percentage points

**Q4.3:** If your system handles 100 queries/minute, would re-ranking be feasible?  
**A:** ☐ Yes  ☐ No

**Calculation:**
```
Time per query with re-ranking: _______ ms
Max queries per minute: 60,000ms / _______ ms = _______ queries/minute
Your requirement: 100 queries/minute
Feasible? _______
```

**Q4.4:** In what scenarios would re-ranking be worth the cost?  
**A:**
```
Your answer here:





```

---

## Exercise 5: Web Search Integration (20 min)

### Objective
Compare local knowledge base vs external web data.

### Part A: Local Only

1. Load **Balanced** preset
2. Ask: "What happened in the news today?"
3. Note the answer quality: _________________

### Part B: With Web Search

1. Open settings
2. Enable "Web Search (SearXNG)" toggle
3. Ask the SAME question
4. Note the answer quality: _________________
5. Review metrics:
   - Web docs returned: _______
   - Web latency: _______ ms

### Questions

**Q5.1:** Did web search provide more recent information?  
**A:** ☐ Yes  ☐ No

**Q5.2:** How much latency did web search add?  
**A:** _________ ms

**Q5.3:** When should you use web search vs local knowledge base?  
**A:**
```
Local KB is better for:


Web search is better for:


```

---

## Exercise 6: Configuration Optimization (30 min)

### Objective
Design an optimal configuration for a specific use case.

### Scenario

You're building a **customer support chatbot** with these requirements:
- Response time: < 200ms (target)
- Good enough quality (don't need perfect)
- 500 queries per minute (peak)
- Cost-conscious (minimize LLM usage)

### Your Task

1. Start with **Balanced** preset
2. Experiment with toggles to meet requirements
3. Test with 3 different questions
4. Record your final configuration

### Your Configuration

```
☐ Query Expansion
☐ BM25 Search
☐ Hybrid Fusion
☐ Knowledge Graph
☐ LLM Re-ranking
☐ Web Search

Top-K: _______
Model: _______
Temperature: _______
```

### Performance Results

| Metric | Your Config | Target | Met? |
|--------|-------------|--------|------|
| Avg Latency | _____ ms | < 200ms | ☐ |
| Queries/min capacity | _____ | 500 | ☐ |
| Precision | _____ % | > 80% | ☐ |

### Justification

Explain why you chose this configuration (3-4 sentences):

```
Your answer here:






```

---

## Exercise 7: A/B Testing (25 min)

### Objective
Use data to compare two configurations.

### Scenario

Your team is debating: "Should we enable Knowledge Graph?" Let's use data to decide.

### Configuration A: Without Graph

1. Load **Balanced** preset
2. Ensure Knowledge Graph is OFF
3. Ask: "How do vector databases work?"
4. Record metrics (save for comparison)

### Configuration B: With Graph

1. Enable "Knowledge Graph" toggle
2. Ask the SAME question
3. Record metrics

### Comparison Modal

1. Click "⚖️ Compare Configurations"
2. Review the insights

### Analysis

Fill in the comparison:

| Metric | Config A (No Graph) | Config B (With Graph) | Difference |
|--------|---------------------|----------------------|------------|
| Latency | _____ ms | _____ ms | _____ ms |
| Results | _____ | _____ | _____ |
| Precision | _____ % | _____ % | _____ pp |
| Method | _____ | _____ | - |

**Winner:** Config _____ (A or B)

### Decision

**Q7.1:** Based on this data, should you enable Knowledge Graph?  
**A:** ☐ Yes  ☐ No  ☐ Depends

**Q7.2:** What's your reasoning? (3-4 sentences)
```
Your answer here:






```

**Q7.3:** What other factors would you consider besides these metrics?  
**A:**
```
Your answer here:




```

---

## Exercise 8: Production Deployment (20 min)

### Objective
Prepare a production-ready RAG system.

### Steps

1. Review the **Production** preset details
2. Load the Production preset
3. Test with 5 different queries
4. Record average metrics

### Production Metrics

| Query | Latency | Precision | Quality (1-10) |
|-------|---------|-----------|----------------|
| 1. | _____ ms | _____ % | _____ |
| 2. | _____ ms | _____ % | _____ |
| 3. | _____ ms | _____ % | _____ |
| 4. | _____ ms | _____ % | _____ |
| 5. | _____ ms | _____ % | _____ |
| **Average** | _____ ms | _____ % | _____ |

### Production Checklist

Verify the production preset:

- ☐ Latency < 400ms (acceptable for production)
- ☐ Precision > 85% (good quality)
- ☐ No expensive re-ranking (scalable)
- ☐ Hybrid search enabled (best recall)
- ☐ Knowledge graph enabled (comprehensive)
- ☐ Reasonable top-k (not excessive)

### Deployment Questions

**Q8.1:** Would you deploy this to production?  
**A:** ☐ Yes  ☐ No

**Q8.2:** What changes would you make before deploying?  
**A:**
```
Your answer here:





```

**Q8.3:** How would you monitor this in production?  
**A:**
```
Your answer here:




```

---

## Exercise 9: Cost Analysis (15 min)

### Objective
Understand the resource cost of each component.

### Component Costs

Research and estimate costs:

| Component | Latency Cost | Compute Cost | Value Added |
|-----------|--------------|--------------|-------------|
| Query Expansion | +10ms | Low | +5% recall |
| BM25 Search | +20ms | Low (50MB index) | +15% recall |
| Hybrid Fusion | +30ms | Low | +20% recall |
| Knowledge Graph | +50ms | Medium (graph traversal) | +5% recall |
| LLM Re-ranking | +2000ms | High (LLM calls) | +10% precision |
| Web Search | +800ms | Medium (network) | +5 fresh docs |

### ROI Analysis

**Q9.1:** Which component has the best ROI (value / cost)?  
**A:** _________________

**Calculation:**
```
Hybrid Fusion: 20% recall / 30ms = 0.67 recall points per ms
BM25 Search: 15% recall / 20ms = _____ recall points per ms
Knowledge Graph: 5% recall / 50ms = _____ recall points per ms
LLM Re-ranking: 10% precision / 2000ms = _____ precision points per ms
```

**Q9.2:** Which component has the worst ROI?  
**A:** _________________

**Q9.3:** If you had a budget of 200ms total, which components would you enable?  
**A:**
```
Your answer here:





```

---

## Exercise 10: Final Challenge (30 min)

### Objective
Design three configurations for different use cases.

### Use Case 1: Autocomplete (< 50ms)

**Requirements:**
- Latency: < 50ms (critical)
- Quality: acceptable (not perfect)
- Usage: 1000 queries/minute

**Your Configuration:**
```
Components enabled:


Top-K: _____
Model: _____
Expected latency: _____ ms
Expected precision: _____ %
```

### Use Case 2: Research Assistant (quality focused)

**Requirements:**
- Latency: < 500ms (acceptable)
- Quality: excellent (critical)
- Usage: 10 queries/minute

**Your Configuration:**
```
Components enabled:


Top-K: _____
Model: _____
Expected latency: _____ ms
Expected precision: _____ %
```

### Use Case 3: Production API (balanced)

**Requirements:**
- Latency: < 300ms (important)
- Quality: very good (important)
- Usage: 100 queries/minute
- Cost: optimize for scale

**Your Configuration:**
```
Components enabled:


Top-K: _____
Model: _____
Expected latency: _____ ms
Expected precision: _____ %
```

### Comparison

| Use Case | Latency | Quality | Cost | Best For |
|----------|---------|---------|------|----------|
| Autocomplete | _____ | _____ | _____ | _____ |
| Research | _____ | _____ | _____ | _____ |
| Production | _____ | _____ | _____ | _____ |

---

## Bonus Exercise: Custom Preset (Optional)

### Challenge

Create your own preset for a specific use case of your choice.

**Your Use Case:** _____________________

**Requirements:**
```
Latency target: _____ ms
Quality target: _____ %
Volume: _____ queries/minute
Special needs:


```

**Your Configuration:**
```json
{
  "name": "YourPresetName",
  "description": "...",
  "config": {
    "use_query_expansion": true/false,
    "use_bm25": true/false,
    "use_hybrid": true/false,
    "use_graph": true/false,
    "use_reranking": true/false,
    "use_web_search": true/false,
    "top_k": _____
  },
  "llm_config": {
    "model": "llama3.2:3b",
    "temperature": _____,
    "max_tokens": _____,
    "context_window": _____
  }
}
```

**Test Results:**
```
Average latency: _____ ms
Average precision: _____ %
Meets requirements: ☐ Yes ☐ No
```

---

## Submission Checklist

Before submitting, ensure you've completed:

- ☐ All 10 core exercises
- ☐ All questions answered
- ☐ All tables filled in
- ☐ Calculations shown
- ☐ Reflections written (3-4 sentences each)
- ☐ Screenshots attached (optional but recommended)
- ☐ Bonus exercise (optional)

---

## Grading Rubric

| Section | Points | Criteria |
|---------|--------|----------|
| Exercises 1-3 | 30 | Data collection accuracy, analysis quality |
| Exercises 4-6 | 30 | Understanding of tradeoffs, justifications |
| Exercises 7-9 | 30 | Critical thinking, cost-benefit analysis |
| Exercise 10 | 10 | Creative problem-solving, completeness |
| **Total** | **100** | |

**Extra Credit:** Bonus exercise (+10 points)

---

## Learning Outcomes Assessment

After completing these exercises, you should be able to:

- ☐ Explain RAG architecture components
- ☐ Measure system performance accurately
- ☐ Identify bottlenecks in pipelines
- ☐ Make data-driven optimization decisions
- ☐ Calculate cost-benefit ratios
- ☐ Design configurations for specific use cases
- ☐ Conduct A/B tests and interpret results
- ☐ Deploy production-ready RAG systems

---

## Additional Resources

- Comprehensive Documentation: `/COMPREHENSIVE_DOCUMENTATION.md`
- Lab Guide: Built into UI (📖 button)
- GitHub Repository: https://github.com/sandbreak80/rag_lab
- RAG Research Papers: [Link to be added]

---

## Support

Questions? Issues?
- Open GitHub issue
- Check documentation
- Review lab guide in UI

---

**Good luck! Have fun learning RAG! 🚀**

---

*Educational RAG Lab v1.0 - Built for Neural Networks Course*

