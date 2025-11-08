# OTEL Sprint - Testing Checklist
**Version:** 1.0
**Purpose:** Comprehensive testing requirements per Cursor rules

---

## 🎯 Testing Philosophy

**Per Cursor Rules:**
> "If you haven't tested it, it's not done."

**Zero Tolerance For:**
- ❌ Blank pages
- ❌ Console errors in production
- ❌ Unhealthy services
- ❌ 500 API responses
- ❌ Missing data in responses

---

## 📋 Daily Testing Checklist

### **Before Every Commit:**

#### 1. Code Quality
```bash
# Linter (Python)
cd services/<service-name>
flake8 app/ --max-line-length=120

# Linter (TypeScript)
cd frontend
npm run lint

# Type checking
npm run type-check
```
**Expected:** ✅ 0 errors

#### 2. Unit Tests
```bash
# Run affected tests
pytest tests/test_<module>.py -v

# Check coverage
pytest tests/ --cov=services --cov-report=term-missing
```
**Expected:** ✅ All tests pass, >80% coverage

#### 3. Frontend Build
```bash
cd frontend
npm run build
```
**Expected:** ✅ Build succeeds, no errors

---

## 🔬 Testing by Day

### **DAY 1: Provenance Tests**

#### Unit Tests
```bash
pytest tests/test_evidence.py -v
```

**Must Pass:**
- `test_evidence_immutability` - Evidence objects are frozen
- `test_evidence_origin_preserved` - origin_tool never changes
- `test_origin_tool_validation` - Only valid origins accepted

#### Integration Tests
```bash
pytest tests/integration/test_search_provenance.py -v
```

**Must Pass:**
- `test_web_results_tagged_correctly` - Web sources have origin_tool="web_search"
- `test_rag_results_tagged_correctly` - RAG sources have origin_tool="rag"
- `test_merge_preserves_origin` - Merging doesn't change origins
- `test_provenance_validator_catches_violations` - Validator works

#### Manual API Test
```bash
# Test web search
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Latest AI news",
    "enable_web_search": true,
    "enable_vector_search": false
  }' | jq '.sources[] | {title, origin_tool}'

# VERIFY: All have origin_tool="web_search"

# Test RAG search
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "test query",
    "enable_web_search": false,
    "enable_vector_search": true
  }' | jq '.sources[] | {title, origin_tool}'

# VERIFY: All have origin_tool="rag"

# Test mixed search
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "AI technology",
    "enable_web_search": true,
    "enable_vector_search": true
  }' | jq '.sources[] | {title, origin_tool}' | jq -s 'group_by(.origin_tool) | map({origin: .[0].origin_tool, count: length})'

# VERIFY: Shows counts for each origin type
```

#### Frontend Test
1. Open http://localhost:3000
2. Open DevTools Console (F12)
3. Run query with web search enabled
4. **VERIFY:**
   - ✅ Source cards show origin badges (🌐 Web, 📚 RAG)
   - ✅ Footer shows breakdown (e.g., "Web: 5, RAG: 3")
   - ✅ No console errors

---

### **DAY 2: Timing & UX Tests**

#### Unit Tests
```bash
pytest tests/test_timing.py -v
```

**Must Pass:**
- `test_timing_collector_measures_operations` - TimingCollector works
- `test_timing_context_manager` - Context manager records duration
- `test_timing_aggregation` - Timings aggregate correctly

#### Integration Tests
```bash
pytest tests/integration/test_waterfall_timing.py -v
```

**Must Pass:**
- `test_all_stages_report_timing` - Every enabled stage reports time
- `test_kg_timing_nonzero` - KG timing > 0ms when enabled
- `test_timing_sum_matches_total` - Sum of stages ≈ total (±10%)

#### Manual API Test
```bash
# Test with all features enabled
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is RAG?",
    "enable_vector_search": true,
    "enable_bm25": true,
    "enable_knowledge_graph": true,
    "enable_reranking": true,
    "enable_web_search": true
  }' | jq '.metrics.timings'

# VERIFY: All these keys present with >0 values
# - vector_search
# - bm25_search
# - kg_expand (must be >0!)
# - rerank
# - web_search
# - llm_generation
# - total_request
```

#### Frontend Test - Waterfall
1. Open http://localhost:3000
2. Go to Settings → Enable all toggles
3. Run a query
4. Check Metrics panel
5. **VERIFY:**
   - ✅ Waterfall shows all enabled stages
   - ✅ KG bar visible with timing
   - ✅ Percentages add up to ~100%
   - ✅ No 0ms stages shown

#### Frontend Test - Copy Buttons
1. Send a query
2. Click copy button on prompt
3. Paste into text editor
4. **VERIFY:** Markdown formatting preserved
5. Click copy button on response
6. Paste into text editor
7. **VERIFY:** Markdown formatting preserved

#### Frontend Test - KG Reset
1. Go to Knowledge Graph page
2. Note entity/edge count
3. Click "Reset Graph"
4. **VERIFY:** Counts immediately show 0

---

### **DAY 3: OTEL Tests**

#### Service Health
```bash
# Check OTel Collector
docker compose ps otel-collector
curl http://localhost:13133/
# VERIFY: Healthy

# Check services
docker compose ps | grep -v Exit
# VERIFY: All services Up and healthy
```

#### Trace Collection Test
```bash
# Send a query
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"query":"test"}' \
  -i | grep X-Trace-Id

# VERIFY: X-Trace-Id header present
# Copy the trace ID

# Check collector logs
docker compose logs otel-collector | grep <trace-id>
# VERIFY: Trace appears in logs
```

#### Prometheus Scrape Test
```bash
# Check OTel Collector metrics endpoint
curl http://localhost:8889/metrics

# VERIFY: Prometheus-format metrics
# Look for otel_* metrics

# Check Prometheus scraping
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job=="otel-collector")'

# VERIFY: Target is UP
```

#### Integration Test
```bash
pytest tests/integration/test_otel_traces.py -v
```

**Must Pass:**
- `test_trace_propagation` - Trace context propagates
- `test_span_attributes` - Custom attributes present
- `test_service_names` - Service names correct

---

### **DAY 4: OpenLLMetry Tests**

#### LLM Span Test
```bash
# Send a query that uses LLM
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"query":"Explain RAG"}' | jq '.metrics'

# VERIFY response includes:
# - llm_model
# - prompt_tokens
# - completion_tokens
# - estimated_cost_usd
```

#### Trace Attributes Test
```bash
# Check chat service logs for OpenLLMetry spans
docker compose logs chat-service | grep -A 10 "llm"

# VERIFY span attributes:
# - llm.provider="ollama"
# - llm.model="llama3.1:8b"
# - llm.prompt_tokens=<number>
# - llm.completion_tokens=<number>
# - llm.total_tokens=<number>
# - llm.estimated_cost_usd=<float>
```

#### Grafana Dashboard Test
1. Open http://localhost:3001
2. Navigate to "RAG Lab - Distributed Traces" dashboard
3. **VERIFY:**
   - ✅ Request traces visible
   - ✅ LLM spans show up
   - ✅ Token metrics displayed
   - ✅ Cost metrics visible

#### Exemplar Test
1. In Grafana, view a latency metric
2. Look for trace ID links
3. Click to view trace
4. **VERIFY:** Trace opens with full details

---

### **DAY 5: Conversation Persistence Tests**

#### Database Tests
```bash
pytest tests/test_conversation_db.py -v
```

**Must Pass:**
- `test_create_conversation` - Can create conversation
- `test_add_message` - Can add messages
- `test_get_messages` - Can retrieve messages
- `test_get_messages_after_id` - Polling filter works

#### API Tests
```bash
# Create conversation
CONV_ID=$(curl -X POST http://localhost:8000/api/conversations \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test"}' | jq -r '.conversation_id')

echo "Created conversation: $CONV_ID"

# Add a message
curl -X POST http://localhost:8000/api/conversations/$CONV_ID/messages \
  -H "Content-Type: application/json" \
  -d '{
    "role": "user",
    "content": "Test message"
  }'

# Get messages
curl http://localhost:8000/api/conversations/$CONV_ID/messages | jq

# VERIFY: Message appears

# Add another message
MSG_ID=$(curl -X POST http://localhost:8000/api/conversations/$CONV_ID/messages \
  -H "Content-Type: application/json" \
  -d '{
    "role": "assistant",
    "content": "Response"
  }' | jq -r '.id')

# Poll for new messages (after first message)
curl "http://localhost:8000/api/conversations/$CONV_ID/messages?after=$MSG_ID" | jq

# VERIFY: Only shows messages after MSG_ID
```

#### Frontend Persistence Test
1. Open http://localhost:3000
2. Open DevTools Network tab
3. Send a message
4. **While response is streaming**, click refresh
5. **VERIFY:**
   - ✅ Page reloads
   - ✅ Conversation ID preserved
   - ✅ Previous messages visible
   - ✅ Polling resumes
   - ✅ Response completes
6. Navigate to Settings page
7. Navigate back to Chat
8. **VERIFY:**
   - ✅ Messages still visible
   - ✅ No duplicates

#### Integration Test
```bash
pytest tests/integration/test_conversation_polling.py -v
```

**Must Pass:**
- `test_conversation_persistence` - Survives refresh
- `test_polling_retrieves_new_messages` - Polling works
- `test_no_duplicate_messages` - No duplication

---

## 🔥 Critical End-to-End Tests

### **Test 1: Full RAG Pipeline**
```bash
# Start clean
docker compose restart

# Wait for services to be healthy
sleep 30

# Run full pipeline test
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the latest developments in AI?",
    "enable_vector_search": true,
    "enable_bm25": true,
    "enable_knowledge_graph": true,
    "enable_reranking": true,
    "enable_web_search": true
  }' | jq > test_result.json

# Verify result
cat test_result.json | jq '{
  answer_length: (.answer | length),
  source_count: (.sources | length),
  has_provenance: (.sources[0] | has("origin_tool")),
  has_timings: (.metrics.timings | keys | length),
  has_trace_id: (.metadata | has("trace_id"))
}'

# MUST HAVE:
# - answer_length > 100
# - source_count > 0
# - has_provenance = true
# - has_timings > 5
# - has_trace_id = true
```

### **Test 2: Provenance Accuracy**
```bash
# Run 10 queries, check provenance
for i in {1..10}; do
  curl -s -X POST http://localhost:8000/api/ask \
    -H "Content-Type: application/json" \
    -d "{\"query\":\"test query $i\",\"enable_web_search\":true}" | \
    jq '.sources[] | select(.origin_tool == null or .origin_tool == "")'
done

# VERIFY: No output (all sources have origin_tool)
```

### **Test 3: Refresh Resilience**
1. Open http://localhost:3000
2. Send a complex query (enable all features)
3. Wait 2 seconds
4. Press F5 (refresh)
5. **VERIFY:**
   - ✅ Page loads
   - ✅ Previous messages visible
   - ✅ Polling resumes
   - ✅ Response completes

### **Test 4: Performance Under Load**
```bash
# Install locust if needed
pip install locust

# Run load test
locust -f tests/load/locustfile.py --host http://localhost:8000 --users 10 --spawn-rate 2 --run-time 2m --headless

# VERIFY:
# - 0% errors
# - p95 < 5s
# - p99 < 10s
```

---

## 🎯 Acceptance Criteria Validation

### **Provenance (Day 1)**
- [ ] ✅ Web sources tagged `web_search`
- [ ] ✅ RAG sources tagged `rag`
- [ ] ✅ Research sources tagged `research_agent`
- [ ] ✅ Footer shows correct counts
- [ ] ✅ Validator catches violations
- [ ] ✅ Integration tests pass

### **Waterfall (Day 2)**
- [ ] ✅ All enabled stages show timing
- [ ] ✅ KG timing > 0ms when enabled
- [ ] ✅ Total ≈ sum(stages) ± 10%
- [ ] ✅ Frontend displays all stages
- [ ] ✅ Copy buttons work

### **OTEL (Day 3)**
- [ ] ✅ Collector healthy
- [ ] ✅ Traces visible in logs
- [ ] ✅ Prometheus scrapes metrics
- [ ] ✅ X-Trace-Id in responses
- [ ] ✅ Service names correct

### **OpenLLMetry (Day 4)**
- [ ] ✅ LLM spans have token counts
- [ ] ✅ Model name in spans
- [ ] ✅ Cost estimation present
- [ ] ✅ Grafana dashboard works
- [ ] ✅ Exemplars link to traces

### **Conversations (Day 5)**
- [ ] ✅ Database schema created
- [ ] ✅ Conversations persist
- [ ] ✅ Polling retrieves new messages
- [ ] ✅ Refresh doesn't lose context
- [ ] ✅ No duplicate messages

---

## 🚨 Regression Testing

### **Must Not Break:**

#### Existing Features
- [ ] ✅ Basic search still works
- [ ] ✅ Settings panel functional
- [ ] ✅ Preset selection works
- [ ] ✅ Documents upload works
- [ ] ✅ Research agent functional
- [ ] ✅ Authentication still works
- [ ] ✅ Prometheus metrics still scraped
- [ ] ✅ Grafana dashboards still load

#### Performance
- [ ] ✅ No >10% latency increase
- [ ] ✅ Memory usage stable
- [ ] ✅ CPU usage acceptable
- [ ] ✅ No memory leaks

#### UI/UX
- [ ] ✅ No blank pages
- [ ] ✅ No console errors
- [ ] ✅ All buttons work
- [ ] ✅ Navigation works
- [ ] ✅ Responsive design intact

---

## 📊 Test Coverage Requirements

### **Target Coverage:**
- Python backend: >80%
- TypeScript frontend: >70%
- Integration tests: All critical paths

### **Check Coverage:**
```bash
# Backend
pytest tests/ --cov=services --cov-report=html
open htmlcov/index.html

# Frontend
cd frontend
npm run test:coverage
open coverage/index.html
```

---

## 🔍 Manual QA Checklist

### **Before Declaring "Done":**

#### Smoke Test (5 minutes)
- [ ] Homepage loads
- [ ] Can send a query
- [ ] Gets a response
- [ ] Sources appear
- [ ] Metrics visible
- [ ] No console errors

#### Feature Test (15 minutes)
- [ ] Provenance tags correct
- [ ] Waterfall complete
- [ ] Copy buttons work
- [ ] KG reset works
- [ ] Conversations persist
- [ ] Polling works
- [ ] Refresh resilient

#### Integration Test (10 minutes)
- [ ] All services healthy
- [ ] Traces in collector
- [ ] Prometheus scraping
- [ ] Grafana dashboards load
- [ ] LLM spans visible
- [ ] Exemplars work

#### Performance Test (10 minutes)
- [ ] Query latency acceptable
- [ ] No timeouts
- [ ] Memory stable
- [ ] CPU reasonable
- [ ] Load test passes

---

## ✅ Sign-off Checklist

### **Before Merge to Main:**

#### Code Quality
- [ ] All linters pass (0 errors)
- [ ] Type checking passes
- [ ] No commented-out code
- [ ] No debug statements
- [ ] No TODOs without issues

#### Testing
- [ ] 100% unit tests pass
- [ ] 100% integration tests pass
- [ ] Manual QA complete
- [ ] Load tests pass
- [ ] Regression tests pass

#### Documentation
- [ ] README updated
- [ ] CHANGELOG updated
- [ ] API docs updated
- [ ] Comments clear
- [ ] Examples work

#### Deployment
- [ ] Docker builds clean
- [ ] Services start successfully
- [ ] Health checks pass
- [ ] Rollback tested
- [ ] Monitoring works

---

## 🎓 Learning from Failures

### **When Tests Fail:**

1. **Don't skip the test** - Fix the code
2. **Understand why** - Root cause analysis
3. **Add more tests** - Prevent regression
4. **Document** - Help future debugging

### **Common Failure Modes:**

#### "Tests pass locally but fail in CI"
- Environment differences
- Timing/race conditions
- Missing dependencies

**Solution:** Make tests more robust, use retries, add timeouts

#### "Frontend works but console has errors"
- Unhandled promise rejections
- PropTypes warnings
- API errors

**Solution:** Add error boundaries, handle promises, validate props

#### "Services start but unhealthy"
- Dependency not ready
- Port conflicts
- Configuration issues

**Solution:** Add healthcheck retries, use depends_on, validate config

---

**Remember:** Testing is not optional. It's the only way to know if it works. 🧪

---

**Document Version:** 1.0
**Last Updated:** 2025-11-08
**Status:** READY FOR USE

