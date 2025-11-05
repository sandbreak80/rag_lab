# Testing New Features - Build 20251105.3

**Build Date:** November 5, 2025
**Status:** ✅ Ready for Testing
**Test Results:** 11/11 Passed

---

## 🆕 What's New in This Build

### 1. **Intelligence Features** (Settings Tab)
- 🔮 **Prompt Enhancement** - Auto-enhance queries using AI frameworks
- 🎯 **Auto Model Routing** - Automatically select optimal LLM model

### 2. **Data Source Controls** (Settings Tab)
- 📄 **Vector Database** - Toggle uploaded documents
- 🔬 **Research Agent** - Toggle research discoveries (91 items)
- 🌐 **Web Search** - Toggle real-time web results
- 🕸️ **Knowledge Graph** - Toggle entity relations

### 3. **Build System**
- Version tracking with build numbers
- Pre-QA checklist automation
- Comprehensive test suite

---

## 🧪 Testing Guide

### Step 1: Access the UI

**Open in browser:**
```
http://localhost:3000
```

**Expected:** Modern React UI with tabs:
- 💬 Chat
- 📊 Performance
- 📤 Upload
- ⚙️ Settings

---

### Step 2: Test Settings Tab

#### A. Navigate to Settings
1. Click **⚙️ Settings** tab
2. Scroll down to find new sections:
   - 🧠 **Intelligence Features** (NEW)
   - 📚 **Data Sources** (NEW)

#### B. Test Intelligence Features

**🔮 Prompt Enhancement Toggle**

**Test 1: Off → On**
1. Toggle "Prompt Enhancement" to **ON**
2. Expected: Toggle slides right, turns blue
3. Open browser console (F12)
4. Go to Chat tab
5. Type: "How does RAG work?"
6. Send query
7. Check Network tab → Look for enhanced query in request

**Test 2: On → Off**
1. Toggle "Prompt Enhancement" to **OFF**
2. Expected: Toggle slides left, turns gray
3. Send another query
4. Verify standard query (no enhancement)

**🎯 Auto Model Routing Toggle**

**Test 1: Manual Model Selection (Off)**
1. Keep "Auto Model Routing" **OFF**
2. In Model Configuration section, select a specific model
3. Send a query
4. Verify that specific model is used

**Test 2: Automatic Selection (On)**
1. Toggle "Auto Model Routing" to **ON**
2. Send a simple query: "What is AI?"
   - Expected: Uses fast model (llama3.2:3b)
3. Send a complex query: "Analyze the architectural tradeoffs between monolithic and microservices patterns in the context of ML model serving infrastructure"
   - Expected: Uses powerful model (qwen2.5:14b)

#### C. Test Data Source Toggles

**📄 Vector Database**

**Test 1: All Sources Enabled (Default)**
1. Ensure all toggles are **ON**
2. Send query: "What documents do we have?"
3. Expected: Results from all sources

**Test 2: Vector DB Only**
1. Toggle OFF: Research Agent, Web Search, Knowledge Graph
2. Keep ON: Vector Database only
3. Send query about uploaded content
4. Expected: Only results from uploaded docs

**Test 3: Vector DB Disabled**
1. Toggle OFF: Vector Database
2. Toggle ON: Other sources
3. Send query
4. Expected: No results from uploaded docs

**🔬 Research Agent**

**Test 1: Research Content Included**
1. Toggle ON: Research Agent
2. Toggle OFF: Other sources
3. Send query: "Latest AI research trends"
4. Expected: Results from 91 auto-discovered papers

**Test 2: Research Content Excluded**
1. Toggle OFF: Research Agent
2. Send same query
3. Expected: No research papers in results

**🌐 Web Search**

**Test 1: Web Search Enabled**
1. Toggle ON: Web Search
2. Send query: "Current news about GPT-4"
3. Expected: Real-time web results included

**Test 2: Web Search Disabled**
1. Toggle OFF: Web Search
2. Send same query
3. Expected: Only local results, no web content

**🕸️ Knowledge Graph**

**Test 1: Graph Enabled**
1. Toggle ON: Knowledge Graph
2. Send query about entities in your documents
3. Expected: Related entities included

**Test 2: Graph Disabled**
1. Toggle OFF: Knowledge Graph
2. Send same query
3. Expected: No entity relations

---

### Step 3: Test Combinations

#### Scenario 1: Research-Only Mode
```
✅ Vector Database: OFF
✅ Research Agent: ON
✅ Web Search: OFF
✅ Knowledge Graph: OFF
```

**Query:** "Recent advances in RAG systems"

**Expected:**
- Results from 91 auto-discovered papers
- No web search results
- No uploaded document results

---

#### Scenario 2: Maximum Intelligence
```
✅ Prompt Enhancement: ON
✅ Auto Model Routing: ON
✅ All Data Sources: ON
```

**Query:** "Compare hybrid search vs vector search and explain when to use each"

**Expected:**
1. Query is enhanced (check network request)
2. Complex query → routed to qwen2.5:14b
3. Results from all sources combined
4. High-quality, comprehensive answer

---

#### Scenario 3: Fast & Simple
```
✅ Prompt Enhancement: OFF
✅ Auto Model Routing: OFF
✅ Model: llama3.2:3b
✅ Vector Database: ON (only)
```

**Query:** "What is RAG?"

**Expected:**
- Fast response (< 2 seconds)
- Simple, direct answer
- Only from uploaded documents

---

### Step 4: Verify Persistence

1. Change settings (toggle features on/off)
2. **Refresh the page** (F5)
3. Go back to Settings tab
4. **Expected:** Your settings are preserved (LocalStorage)

---

### Step 5: Test Performance Tab

1. Click **📊 Performance** tab
2. Send several queries with different settings
3. **Expected:** See metrics for:
   - Response times
   - Token counts
   - Model used
   - Sources accessed

---

### Step 6: API Integration Test

**Test Backend Services Directly:**

```bash
# Test Prompt Classifier
curl -X POST http://localhost:8017/classify \
  -H "Content-Type: application/json" \
  -d '{"query": "How does RAG work?"}'

# Expected: JSON with intent, complexity, recommendations
```

```bash
# Test Prompt Enhancement
curl -X POST http://localhost:8012/enhance \
  -H "Content-Type: application/json" \
  -d '{"query": "Compare vector vs keyword search", "documents": []}'

# Expected: Enhanced query with strategy
```

```bash
# Test Model Router
curl -X POST http://localhost:8018/route \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain quantum computing", "context": {}}'

# Expected: Selected model + reasoning
```

```bash
# Test Research Agent Status
curl http://localhost:8015/status

# Expected: Stats showing 91 items, 6 sources
```

---

## 🐛 Known Issues to Watch For

### Minor Issues (Non-Blocking)
1. **Prompt Classifier shows "unhealthy"**
   - Impact: None (still functional)
   - Cause: Health check timeout
   - Fix: Planned for next build

2. **Build info not in all services**
   - Impact: None (tracking only)
   - Status: prompt-classifier has it, others pending

### What to Report
If you encounter:
- ❌ Toggles don't work (stay gray/don't save)
- ❌ Queries fail after toggling features
- ❌ Page crashes or shows errors
- ❌ Data source toggles have no effect on results
- ❌ Settings don't persist after refresh

**Report with:**
- Which toggle/feature
- Browser console errors (F12 → Console)
- Steps to reproduce

---

## 📊 Expected Performance

### Response Times (Approximate)
| Configuration | Expected Time |
|---------------|---------------|
| Simple query, 3B model, no enhancement | < 2s |
| Complex query, 14B model, with enhancement | 5-10s |
| With web search enabled | +2-5s |
| Research agent results | No additional delay |

### GPU Usage
- **During query:** 50-80% GPU utilization
- **Idle:** 0% GPU utilization
- **VRAM:** ~8-10 GB used (3 models loaded)

---

## ✅ Success Criteria

### All Tests Pass If:
- ✅ All toggles work (on/off, persist after refresh)
- ✅ Prompt enhancement visibly changes queries
- ✅ Model routing selects appropriate models
- ✅ Data source filters affect results
- ✅ No console errors
- ✅ Settings persist across page reloads
- ✅ API tests return expected responses
- ✅ Performance metrics display correctly

---

## 🎯 Quick Smoke Test (2 minutes)

**Bare minimum to verify build:**

1. **Open UI:** http://localhost:3000 ✓
2. **Go to Settings:** See new sections ✓
3. **Toggle something:** Prompt Enhancement ON ✓
4. **Send a query:** Get response ✓
5. **Refresh page:** Settings still ON ✓

**If all 5 pass:** Build is good! ✅

---

## 📞 Quick Commands

### View Logs
```bash
# Frontend logs
docker logs rag-frontend

# Backend service logs
docker logs rag-prompt-enhancement
docker logs rag-model-router
```

### Restart Services
```bash
# Restart all
docker compose restart

# Restart specific
docker compose restart frontend
```

### Run Tests Again
```bash
cd /home/ubuntu/rag_lab
./scripts/test-all-services.sh
```

### Check Build Info
```bash
cat BUILD_INFO
cat build_history.log
```

---

## 🚀 What to Test Next (Optional)

### Advanced Testing
1. **Load Testing:** Multiple concurrent users
2. **Stress Testing:** Toggle features rapidly
3. **Edge Cases:** Very long queries, special characters
4. **Mobile:** Test on phone/tablet browsers
5. **Different Browsers:** Chrome, Firefox, Safari

### Integration Testing
1. **Chat → Upload → Settings:** Full workflow
2. **Multiple tabs open:** Settings sync
3. **API Gateway:** Test via gateway instead of direct services

---

## 📝 Test Results Template

```
## Test Session: [Date/Time]
Tester: [Name]
Build: 20251105.3

### Intelligence Features
- [ ] Prompt Enhancement toggle works
- [ ] Auto Model Routing works
- [ ] Enhanced queries visible in network tab

### Data Sources
- [ ] Vector DB toggle works
- [ ] Research Agent toggle works
- [ ] Web Search toggle works
- [ ] Knowledge Graph toggle works

### Persistence
- [ ] Settings survive page refresh

### Performance
- [ ] Response times acceptable
- [ ] No errors in console
- [ ] Metrics display correctly

### Overall
- [ ] PASS / FAIL
- Notes: [Any issues or observations]
```

---

**Happy Testing! 🎉**

If everything works, we're ready for production deployment!

