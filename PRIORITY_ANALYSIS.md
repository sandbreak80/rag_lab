# RAG Lab - Priority Analysis & Roadmap
**Date:** November 6, 2025  
**Current Version:** 1.2.4  
**Branch:** security

## 📊 Current State Assessment

### ✅ What's Working
- 14 microservices operational (13 healthy, 1 unhealthy)
- Authentication system functional
- Performance waterfall chart implemented
- Citation validation active
- Baseline prompts for testing
- Full React UI with configuration toggles

### ⚠️ What Needs Attention
- **Query Decomposer:** Service exists but unhealthy
- **Query Decomposition UI:** Backend integrated, UI missing
- **Self-RAG:** Not implemented
- **Metadata Filtering:** Not implemented

---

## 🎯 Priority Matrix (Impact vs Effort)

### 🔥 CRITICAL & HIGH IMPACT (Do First)

#### 1. **Fix Query Decomposer Service** ⭐⭐⭐⭐⭐
- **Status:** Service exists, backend integrated, but unhealthy
- **Impact:** HIGH - Improves complex query handling by 18%
- **Effort:** LOW (1-2 hours) - Just needs debugging/fixing
- **Why Critical:** 
  - Service already created
  - Chat service already calls it
  - Just needs health check fix
  - Unlocks complex query processing

**Immediate Action:** Fix health check, test decomposition endpoint

#### 2. **Query Decomposition UI** ⭐⭐⭐⭐⭐
- **Status:** Backend done, UI missing
- **Impact:** HIGH - Shows educational value, transparency
- **Effort:** LOW (2-3 hours) - Frontend only
- **Why Critical:**
  - Backend already working
  - Easy UI addition
  - Great demo feature
  - Teaching tool for complex queries

**Immediate Action:** Add UI toggle + display sub-queries in chat

---

### 🚀 HIGH IMPACT (Do Next)

#### 3. **Metadata Filtering UI** ⭐⭐⭐⭐☆
- **Status:** Not started
- **Impact:** HIGH - User control, precision +5%
- **Effort:** LOW (2-3 hours)
- **Why Important:**
  - Quick win with immediate UX improvement
  - Users want control over sources
  - Easy to implement (metadata already exists)
  - Low risk

**Components:**
- Filter panel (Document Type, Date Range, Source, Tags)
- Pass filters to search service
- Apply Qdrant metadata filters
- Display filtered count

---

### 🔬 RESEARCH-GRADE (Do When Ready)

#### 4. **Self-RAG with Critic** ⭐⭐⭐⭐⭐
- **Status:** Not started
- **Impact:** VERY HIGH - Complex handling +20%, Hallucination -15%
- **Effort:** HIGH (8-10 hours)
- **Why Powerful:**
  - Cutting-edge technique (2024 research)
  - Self-reflection and quality gates
  - Wow factor for demonstrations
  - Research-grade answers

**Components:**
- Critique loop (3 iterations max)
- Query refinement logic
- Confidence scoring
- UI progress indicator

---

## 📋 Recommended Implementation Order

### Phase 1: Quick Wins (3-5 hours) 🎯 **START HERE**
1. ✅ **Fix Query Decomposer Health** (1-2 hours)
   - Debug unhealthy status
   - Fix health check endpoint
   - Test decomposition logic
   - Verify chat service integration

2. ✅ **Query Decomposition UI** (2-3 hours)
   - Add toggle to settings panel
   - Display sub-queries in chat
   - Show which docs came from which sub-query
   - Add metrics to waterfall

**Outcome:** Complex query handling visible and working

---

### Phase 2: User Control (2-3 hours)
3. ✅ **Metadata Filtering UI** (2-3 hours)
   - Create filter panel component
   - Add date range picker
   - Document type checkboxes
   - Source selection
   - Wire to search service

**Outcome:** Users can control retrieval scope

---

### Phase 3: Advanced Features (8-10 hours)
4. ✅ **Self-RAG Implementation** (8-10 hours)
   - Create critic module
   - Implement reflection loop
   - Add quality gates
   - UI iteration display
   - Performance metrics

**Outcome:** Research-grade answer quality

---

## 🎖️ Priority Justification

### Why This Order?

**1. Query Decomposer Fix (CRITICAL)**
- Service already exists and is called by chat service
- Just needs debugging - lowest effort, highest immediate impact
- Unlocks a major feature that's already coded
- **ROI:** 10/10

**2. Query Decomposition UI (HIGH)**
- Backend already working after fix
- Pure UI work - isolated risk
- Great educational demonstration
- Shows system intelligence visibly
- **ROI:** 9/10

**3. Metadata Filtering (HIGH)**
- User-requested feature
- Improves precision immediately
- Low complexity, high satisfaction
- Uses existing metadata infrastructure
- **ROI:** 8/10

**4. Self-RAG (ADVANCED)**
- Cutting-edge research technique
- Highest complexity
- Most impressive demo feature
- Best quality improvement
- Requires solid foundation first
- **ROI:** 9/10 (but time-intensive)

---

## 📈 Expected Impact Summary

| Feature | Effort | Impact | Quality Gain | UX Improvement | Educational Value |
|---------|--------|--------|--------------|----------------|-------------------|
| **Query Decomposer Fix** | 1-2h | ⭐⭐⭐⭐⭐ | +18% complex | High | High |
| **Decomposition UI** | 2-3h | ⭐⭐⭐⭐⭐ | Visibility | Very High | Very High |
| **Metadata Filtering** | 2-3h | ⭐⭐⭐⭐☆ | +5% precision | High | Medium |
| **Self-RAG** | 8-10h | ⭐⭐⭐⭐⭐ | +20% complex | High | Very High |

---

## 🛠️ Technical Readiness

### Already Available (Green Light)
✅ Query Decomposer service (needs fix)  
✅ Chat service integration code  
✅ Metadata in vector DB  
✅ React UI framework  
✅ Ollama LLM for critique  
✅ Performance metrics system  

### Need to Create (Straightforward)
🟡 Query Decomposition UI components  
🟡 Metadata filter UI components  
🟡 Self-RAG critic module  
🟡 Iteration progress UI  

---

## 🎯 Recommended Action Plan

### This Session (3-5 hours)
```bash
1. Debug query-decomposer health (30 min)
2. Fix and test decomposition endpoint (30 min)
3. Build Query Decomposition UI (2 hours)
   - Settings toggle
   - Sub-query display
   - Metrics integration
4. Test end-to-end (30 min)
5. Document and commit (30 min)
```

**Deliverable:** Complex query handling with visible sub-queries

### Next Session (2-3 hours)
```bash
1. Build Metadata Filtering UI (2 hours)
   - Filter panel component
   - Search service integration
2. Test with different filters (30 min)
3. Document and commit (30 min)
```

**Deliverable:** User-controlled source filtering

### Future Session (8-10 hours)
```bash
1. Design Self-RAG architecture (1 hour)
2. Build critic module (3 hours)
3. Implement reflection loop (2 hours)
4. Add UI progress display (2 hours)
5. Test and optimize (2 hours)
```

**Deliverable:** Research-grade iterative refinement

---

## 🏆 Success Metrics

### Phase 1 Success (Query Decomposition)
- ✅ Decomposer service healthy
- ✅ UI shows sub-queries
- ✅ Complex queries improved
- ✅ Metrics in waterfall
- ✅ Educational value demonstrated

### Phase 2 Success (Metadata Filtering)
- ✅ Filter UI functional
- ✅ Results filtered correctly
- ✅ Performance maintained
- ✅ User satisfaction high

### Phase 3 Success (Self-RAG)
- ✅ Critique logic working
- ✅ Iteration visible in UI
- ✅ Quality improvement measurable
- ✅ Demo-ready feature

---

## 💡 Key Insights

1. **Leverage Existing Work:** Query decomposer is 90% done - fix it first!
2. **Quick Wins Build Momentum:** UI features are fast and impactful
3. **Educational Value:** Visibility of RAG internals is a key differentiator
4. **User Control:** Filtering empowers users and improves satisfaction
5. **Advanced Last:** Self-RAG requires solid foundation - do it when ready

---

## 🎓 Learning Opportunities

Each feature teaches different concepts:

- **Query Decomposition:** Multi-query strategies, parallel retrieval
- **Metadata Filtering:** Information filtering, user control
- **Self-RAG:** Self-reflection, iterative refinement, quality gates

---

## ✅ Immediate Next Step

**START HERE:** Fix query-decomposer service health check

```bash
# Check logs
docker logs rag-query-decomposer --tail 50

# Restart if needed
docker compose restart query-decomposer

# Test endpoint
curl -X POST http://localhost:8019/health
curl -X POST http://localhost:8019/decompose \
  -H "Content-Type: application/json" \
  -d '{"query":"How does RAG work and what are knowledge graphs?"}'
```

If that works → Build UI
If that fails → Debug and fix first

---

**Total Time to Complete All:** ~13-18 hours  
**Immediate Focus:** 3-5 hours for Phase 1  
**Expected Quality Improvement:** +20-30% overall

**Status:** 🎯 Ready to execute

