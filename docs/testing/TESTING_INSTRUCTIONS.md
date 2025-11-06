# 🧪 Feature 1: Waterfall Chart - Testing Instructions

**Status:** ✅ Deployed and ready to test
**URL:** http://localhost:3000
**Date:** November 6, 2025

---

## 🎯 What You're Testing

The **Response Time Waterfall Chart** - a visual breakdown of RAG pipeline performance.

This shows:
- Where time is spent in the pipeline
- Trade-offs between speed and quality
- Impact of each RAG component

---

## 📋 Test Plan

### Test 1: Minimal Preset (Baseline Speed)
**Goal:** Verify fast baseline performance

1. **Open:** http://localhost:3000
2. **Click:** "Presets" dropdown → Select "Minimal"
3. **Verify these are OFF:**
   - Query Expansion: OFF
   - BM25: OFF
   - Hybrid Search: OFF
   - Knowledge Graph: OFF
   - Re-ranking: OFF
   - Web Search: OFF
   - Research Agent: ON (shouldn't affect this query)

4. **Ask:** "What is a transformer in machine learning?"
5. **Wait for response** (~1-3 seconds expected)
6. **Click:** "▶ Show" under "Performance Breakdown"

**Expected Waterfall:**
- ✅ **Vector Search**: Moderate time (300-500ms)
- ✅ **LLM Generation**: Most time (1-2s)
- ✅ **Everything else**: Zero or minimal
- ✅ **Total**: Fast! (~1.5-2.5s)

**What to Note:**
- How many stages appear?
- Which stage takes longest?
- Does the chart load correctly?
- Are percentages adding up to 100%?

---

### Test 2: Maximum Preset (All Features)
**Goal:** Verify all stages appear and timing is accurate

1. **Click:** "Presets" dropdown → Select "Maximum"
2. **Verify these are ON:**
   - Query Expansion: ON
   - BM25: ON
   - Hybrid Search: ON
   - Knowledge Graph: ON (if you built it)
   - Re-ranking: ON (adds ~2s)
   - Web Search: ON ⚠️ (will dominate!)
   - Research Agent: ON

3. **Ask:** "Compare hybrid search versus vector-only search performance"
4. **Wait patiently** (~5-20 seconds with web search!)
5. **Click:** "▶ Show" under "Performance Breakdown"

**Expected Waterfall:**
- ✅ **Query Expansion**: Small (~50-200ms)
- ✅ **Vector Search**: Moderate (~300-500ms)
- ✅ **BM25 Search**: Moderate (~200-400ms)
- ✅ **Hybrid Fusion**: Tiny (~20-50ms)
- ✅ **Knowledge Graph**: Moderate if enabled (~100-300ms)
- ✅ **Re-ranking**: Large if enabled (~1-3s)
- ✅ **Web Search**: HUGE if enabled (~3-15s!) 🔥
- ✅ **LLM Generation**: Large (~1-3s)

**What to Note:**
- Web search dominates timing (usually 50-80% of total)
- All stages appear with non-zero times
- Colors are distinct and readable
- Hover tooltips work

---

### Test 3: Metrics Page View
**Goal:** Verify waterfall works in Metrics tab

1. **Ask 3-5 different questions** with different presets
2. **Click:** "Metrics" tab in top navigation
3. **See:** Query history table
4. **Click:** "View Details" on any query
5. **See:** Full waterfall chart in modal

**Expected:**
- ✅ Modal opens with query details
- ✅ Waterfall chart displays (full size, not compact)
- ✅ All metrics visible
- ✅ Configuration shown
- ✅ Category summaries at bottom

**What to Note:**
- Is the full chart more readable than inline?
- Are all queries saved with metrics?
- Can you compare presets easily?

---

### Test 4: Different Query Types
**Goal:** Test various query complexities

**Try these queries with different presets:**

**Simple factual:**
- "What is RAG?"
- "Define vector search"
- "Explain embeddings"

**Complex comparison:**
- "Compare BM25 vs vector search"
- "What's the difference between RAG and fine-tuning?"

**Multi-part:**
- "Explain transformers and how they relate to RAG"
- "What is query expansion and why use it?"

**For each:**
1. Note which preset you used
2. Check the waterfall
3. Compare timing differences

---

### Test 5: Edge Cases

**No results query:**
- Ask: "sdfkjhsdfkjhsdkfjh nonsense query"
- Expected: Fast response, minimal waterfall (search + quick LLM)

**Very long query:**
- Ask a paragraph-length question
- Expected: Longer query expansion time if enabled

**Sequential queries:**
- Ask 3 queries in a row quickly
- Expected: All show waterfalls, no crashes

---

## 🎯 What to Look For

### ✅ Visual Quality
- [ ] Colors are distinct and professional
- [ ] Bars are proportional to timing
- [ ] Text is readable
- [ ] Hover tooltips appear correctly
- [ ] Percentages sum to 100%
- [ ] Layout is clean and organized

### ✅ Accuracy
- [ ] Timing seems reasonable (LLM dominates simple queries)
- [ ] Web search shows as expensive when enabled
- [ ] Security validation is fast (<100ms)
- [ ] Query expansion is moderate (50-200ms)
- [ ] Total time matches what you experienced

### ✅ Functionality
- [ ] Inline view works (click "▶ Show")
- [ ] Metrics page view works
- [ ] Works with all presets
- [ ] Updates for each query
- [ ] Category summaries accurate

### ✅ Teaching Value
- [ ] Makes trade-offs obvious (speed vs features)
- [ ] Easy to see bottlenecks
- [ ] Helps understand preset differences
- [ ] Could use this in a presentation

---

## 🐛 Issues to Report

If you find issues, note:
1. **What preset** were you using?
2. **What query** did you ask?
3. **What happened** (vs what you expected)?
4. **Screenshot** if visual issue
5. **Browser console errors** (F12 → Console)

---

## 📊 Feedback Questions

After testing, please answer:

### Value
1. Is this useful for understanding RAG trade-offs? (1-10)
2. Would this help explain RAG to students? (1-10)
3. Is it visually appealing? (1-10)

### UX
4. Is the inline view too cluttered?
5. Should it be expanded by default?
6. Are the colors intuitive?
7. Should we add more detail?

### Features
8. What's missing?
9. What would make it better?
10. Any confusing parts?

---

## 🚀 While You Test

I'm building Features 2-4 in parallel:

**Feature 2:** Query Decomposition
- Breaks complex queries into sub-queries
- Parallel search execution
- UI shows decomposition

**Feature 3:** Self-RAG
- Iterative refinement loop
- Quality assessment
- Shows iteration progress

**Feature 4:** Metadata Filtering
- Filter by document type
- Filter by date range
- Filter by source

---

## ✅ Success = All Tests Pass!

If everything works as described above, Feature 1 is **production-ready** and we can move to polish or Features 2-4!

**Enjoy testing!** 🎉

