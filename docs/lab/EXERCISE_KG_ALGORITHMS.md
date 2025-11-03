# Lab Exercise: Knowledge Graph Algorithm Comparison

## Overview
This exercise demonstrates how different knowledge graph construction algorithms affect document retrieval quality in RAG systems. Students will build the same knowledge graph using four different algorithms and compare their performance.

## Learning Objectives
By the end of this exercise, students will understand:
- Trade-offs between speed, accuracy, and computational cost
- How explicit vs implicit connections affect retrieval
- When to use each algorithm in production
- How to make informed architectural decisions

## Prerequisites
- Completed "Getting Started" lab
- At least 50+ documents ingested
- Basic understanding of RAG pipelines
- Knowledge of graph theory concepts (nodes, edges)

## Duration
- Hands-on: 30-45 minutes
- Discussion: 15-20 minutes
- Total: 45-65 minutes

---

## Exercise Steps

### Part 1: Understand the Algorithms (5 minutes)

Navigate to **Documents** tab and locate the **Knowledge Graph: Rebuild with Algorithm** section.

Review each algorithm's characteristics:

**1. Wikilinks (Default)**
- Speed: Fast (< 1s)
- Accuracy: High (explicit connections)
- Cost: Low (no embeddings needed)
- Best for: Documents with [[cross-references]]

**2. Semantic Similarity**
- Speed: Slow (10-30s)
- Accuracy: High (implicit connections)
- Cost: High (requires embeddings)
- Best for: Discovering implicit topical relationships

**3. Entity Co-occurrence**
- Speed: Medium (5-15s)  
- Accuracy: Medium (entity-based)
- Cost: Medium (simple NER)
- Best for: Tracking entities (people, orgs, places) across documents

**4. Hybrid**
- Speed: Very Slow (30-60s)
- Accuracy: Highest (comprehensive)
- Cost: Highest (all methods)
- Best for: Maximum quality, research use cases

**Question 1**: Which algorithm would you choose for a production customer service chatbot? Why?

**Question 2**: Which algorithm is best for academic research papers? Why?

---

### Part 2: Baseline - Build with Wikilinks (5 minutes)

1. Select **Wikilinks** from the algorithm dropdown
2. Click **Rebuild KG**
3. Wait for completion (~1 second)
4. Note the stats in the success message:
   - Nodes: ______
   - Edges: ______
   - Algorithm: wikilinks

5. Navigate to **Chat** tab
6. Ask: **"What documents are related to AI fundamentals?"**
7. Count the sources returned: ______
8. Rate relevance (1-5): ______

**Screenshot this result** for comparison later.

---

### Part 3: Semantic Similarity (10 minutes)

1. Return to **Documents** tab
2. Select **Semantic Similarity** from dropdown
3. Read the algorithm info panel:
   - What does "cosine > 0.7" mean?
   - Why does this require embeddings?
4. Click **Rebuild KG**
5. Wait for completion (~10-30 seconds)
6. Note the stats:
   - Nodes: ______
   - Edges: ______
   - How many more/fewer edges than Wikilinks? ______

7. Return to **Chat** tab  
8. Ask the **same question**: "What documents are related to AI fundamentals?"
9. Count sources: ______
10. Rate relevance (1-5): ______

**Compare with Wikilinks:**
- Are the sources different? Yes / No
- Which gave better results? __________
- Why do you think that is? ____________________________________

**Question 3**: Did semantic similarity find connections that wikilinks missed? Give an example.

**Question 4**: Why might semantic similarity be slower? Discuss the computational requirements.

---

### Part 4: Entity Co-occurrence (10 minutes)

1. Return to **Documents** tab
2. Select **Entity Co-occurrence**
3. Review algorithm info:
   - What is NER (Named Entity Recognition)?
   - What types of entities are extracted?
4. Click **Rebuild KG**
5. Wait for completion (~5-15 seconds)
6. Note the stats:
   - Nodes: ______ (should include entity nodes!)
   - Edges: ______
   - Entities: ______ (if shown separately)

7. Return to **Chat**
8. Ask: **"What documents mention Splunk?"**
9. Count sources: ______
10. Rate relevance (1-5): ______

11. Try another entity-based query:
    - **"Which documents discuss AppDynamics?"**
    - Sources: ______
    - Relevance: ______

**Question 5**: How is entity-based retrieval different from semantic similarity?

**Question 6**: When would entity co-occurrence be most valuable in production?

---

### Part 5: Hybrid - Maximum Quality (10 minutes)

1. Return to **Documents** tab
2. Select **Hybrid (All Methods)**
3. Review the warning about build time
4. Click **Rebuild KG**
5. **Start a timer** ⏱️
6. Wait for completion
7. **Stop timer**: ______ seconds

8. Note the stats:
   - Nodes: ______
   - Edges: ______
   - Compare to previous builds: More / Same / Fewer?

9. Return to **Chat**
10. Ask the original question: **"What documents are related to AI fundamentals?"**
11. Count sources: ______
12. Rate relevance (1-5): ______

**Cost-Benefit Analysis:**
- Hybrid took ______ seconds vs Wikilinks' ~1 second
- That's ______x slower
- Did results justify the wait? Yes / No / Maybe
- What's the impact on user experience?

**Question 7**: In what scenarios is the 30-60 second build time acceptable?

**Question 8**: How could you optimize this for production? (Hint: pre-build, cache, incremental updates)

---

### Part 6: Side-by-Side Comparison (10 minutes)

Fill out this comparison table:

| Metric | Wikilinks | Semantic | Entity | Hybrid |
|--------|-----------|----------|--------|--------|
| Build Time | ~1s | | | |
| Total Nodes | | | | |
| Total Edges | | | | |
| Sources Returned | | | | |
| Relevance (1-5) | | | | |
| Your Preference | ☐ | ☐ | ☐ | ☐ |

**Discussion Questions:**

1. **Which algorithm found the most connections?** _____________

2. **Which gave the best retrieval results?** _____________

3. **What's the relationship between edges and retrieval quality?**
   - More edges = better results? Yes / No / Depends
   - Explain: _______________________________________________

4. **For a production system serving 1000 requests/minute:**
   - Which algorithm would you choose? _____________
   - How would you mitigate its weaknesses? _____________

5. **For an academic research tool with complex queries:**
   - Which algorithm? _____________
   - Why? _____________

---

### Part 7: Advanced - Custom Comparisons (Optional, 10 minutes)

Try these specialized queries with each algorithm:

**Query 1**: "What is the relationship between RAG and prompt engineering?"
- Best algorithm: _____________
- Why: _____________

**Query 2**: "Find documents about monitoring and observability"
- Best algorithm: _____________
- Why: _____________

**Query 3**: "What companies are mentioned in our documentation?"
- Best algorithm: _____________
- Why: _____________

---

## Key Takeaways

### Algorithm Selection Criteria

Use **Wikilinks** when:
- ✅ Documents have explicit cross-references
- ✅ Speed is critical (< 1s builds)
- ✅ Resource constraints (low memory/CPU)
- ❌ But: Misses implicit relationships

Use **Semantic Similarity** when:
- ✅ Need to discover implicit topical connections
- ✅ Documents lack explicit references
- ✅ Embeddings already available
- ❌ But: Requires significant compute and embeddings

Use **Entity Co-occurrence** when:
- ✅ Tracking specific entities across documents
- ✅ Entity-centric queries ("What mentions X?")
- ✅ Moderate speed requirements
- ❌ But: Simple NER may miss complex entities

Use **Hybrid** when:
- ✅ Quality > speed (research, offline processing)
- ✅ Comprehensive coverage needed
- ✅ Can pre-build and cache
- ❌ But: Too slow for real-time updates

### Production Recommendations

**Real-time RAG Systems:**
- Start with Wikilinks (fast, good enough for 80% of cases)
- Pre-build semantic similarity graph overnight
- Use cached graph during day
- Rebuild incrementally on new docs

**Research/Analysis Systems:**
- Use Hybrid for comprehensive coverage
- Build time is acceptable for batch processing
- Higher quality justifies longer build

**Enterprise Search:**
- Entity co-occurrence for people/org tracking
- Combine with wikilinks for speed
- Update entity graph on document changes only

---

## Splunk Integration (Future State)

**Monitoring Different Algorithms:**
- Track build time per algorithm
- Monitor edge creation rate
- Alert on graph quality degradation
- Compare retrieval precision/recall
- Optimize threshold (cosine similarity, entity frequency)

**With Splunk Observability Cloud, you would:**
1. Instrument each KG building method
2. Track: build time, node/edge count, memory usage
3. Correlate with retrieval quality metrics
4. A/B test algorithms in production
5. Auto-select optimal algorithm based on query patterns

---

## Assessment

To verify understanding, answer these questions:

**1. Why does semantic similarity require more computational resources?**
   a) It loads more documents  
   b) It calculates similarity for all document pairs  
   c) It uses a larger database  
   d) It requires internet access  
   **Answer: ____ Explanation: __________**

**2. What type of queries benefit most from entity co-occurrence?**
   a) Topical similarity ("documents about AI")  
   b) Specific mentions ("documents mentioning Apple")  
   c) Wikilink navigation  
   d) Semantic clustering  
   **Answer: ____ Explanation: __________**

**3. For a customer service chatbot with 10K docs, updating 50 docs/day:**
   - Which algorithm would you use? _____________
   - How would you handle updates? _____________
   - What's your update strategy? _____________

**4. Your KG build time increased from 10s to 60s after adding 1000 docs:**
   - Which algorithm are you likely using? _____________
   - Why did it slow down? _____________
   - How would you optimize? _____________

**5. Design Challenge: You need:**
   - Sub-second query responses
   - High quality results
   - Daily document updates (100 new docs)
   - 24/7 availability

   **Your architecture:** (describe your approach)
   _______________________________________________
   _______________________________________________
   _______________________________________________

---

## Conclusion

Knowledge graph construction is not one-size-fits-all. The "best" algorithm depends on:
- **Use case** (real-time vs batch, entity-centric vs topical)
- **Resources** (CPU, memory, embeddings availability)
- **Quality requirements** (good enough vs maximum precision)
- **Update frequency** (static vs dynamic corpus)

In production AI systems, **you'll often use multiple algorithms**:
- Wikilinks for fast baseline
- Semantic similarity for topic discovery (pre-computed)
- Entity co-occurrence for specific entity tracking
- Hybrid for critical research queries

The RAG Lab lets you **experience these trade-offs firsthand**, preparing you for real-world AI architecture decisions.

---

## Additional Resources

- `docs/RAG_FEATURES.md` - Knowledge graph deep dive
- `docs/ARCHITECTURE.md` - System architecture
- `docs/PERFORMANCE.md` - Performance optimization
- Splunk Blog: "LLM Observability Explained"

## Instructor Notes

**Time Management:**
- Part 1-3: Core concepts (20 min)
- Part 4-5: Advanced comparison (20 min)
- Part 6: Discussion (15 min)
- Part 7: Optional advanced topics

**Discussion Prompts:**
- "Who chose hybrid? Why?"
- "Who chose wikilinks? Defend your choice."
- "How would Splunk help optimize this decision?"
- "What would you monitor in production?"

**Common Misconceptions:**
- More edges ≠ always better (can introduce noise)
- Hybrid ≠ always best (diminishing returns, cost)
- Semantic ≠ always accurate (embedding quality matters)
- Entity extraction ≠ perfect (simple NER has limits)

**Extension Activities:**
- Visualize the knowledge graph
- Calculate graph metrics (density, centrality)
- Implement custom algorithm (co-citation, temporal)
- A/B test algorithms on specific query sets

