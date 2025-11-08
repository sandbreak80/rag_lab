# Week 1 OTEL Deployment - Executive Summary
**Branch:** `otel`
**Status:** ✅ **READY TO EXECUTE**
**Start Date:** Monday (Next Week)

---

## 🎯 What We're Building

**Goal:** Add enterprise-grade observability while fixing critical demo-blocking bugs.

### Three Pillars:
1. **Fix Critical Bugs** - Provenance tracking, streaming resilience, complete timings
2. **Add OpenTelemetry** - Distributed tracing + LLM observability
3. **Enable Splunk Export** - Enterprise compliance requirement

---

## 📅 5-Day Sprint Overview

### **Day 1: Provenance Immutability** 🔴 **BLOCKER**
**Goal:** Every source has correct `origin_tool` tag

**Deliverables:**
- Immutable `Evidence` class
- Search service uses Evidence objects
- Frontend shows origin badges
- Provenance validator

**Acceptance:**
```bash
# Web query shows web_search origin
curl -X POST http://localhost:8000/api/ask \
  -d '{"query":"Latest AI news", "enable_web_search":true}' | \
  jq '.sources[] | {title, origin_tool}'

# Should see: origin_tool: "web_search" for web sources
```

---

### **Day 2: Complete Waterfall + UX** ⚡ **HIGH IMPACT**
**Goal:** All timings visible, UX polish

**Deliverables:**
- Timing instrumentation in all services
- KG timing > 0ms
- Copy-as-markdown buttons
- KG reset invalidates caches

**Acceptance:**
- Waterfall shows all enabled components
- KG timing visible when KG enabled
- Copy buttons work for prompt + response

---

### **Day 3: OpenTelemetry Foundation** 🔭 **INFRASTRUCTURE**
**Goal:** Deploy OTEL without disrupting Prometheus

**Deliverables:**
- OTel Collector container
- API Gateway instrumented
- Search Service instrumented
- Prometheus scrapes OTEL metrics

**Acceptance:**
- Traces visible in collector logs
- Grafana shows OTEL metrics
- Response headers include `X-Trace-Id`

---

### **Day 4: OpenLLMetry** 🤖 **LLM OBSERVABILITY**
**Goal:** Track LLM token usage and costs

**Deliverables:**
- OpenLLMetry installed in chat service
- LLM spans with token counts
- Model selection traced
- Grafana dashboard for traces

**Acceptance:**
- LLM spans show: model, prompt_tokens, completion_tokens, cost
- Grafana links to traces via exemplars
- Model router decisions tracked

---

### **Day 5: Conversation Persistence** 💾 **RESILIENCE**
**Goal:** Conversations survive refresh

**Deliverables:**
- SQLite conversation database
- Polling API endpoint
- Frontend polling hook
- Complete documentation

**Acceptance:**
- Start query → refresh page → conversation resumes
- No duplicate messages
- Documentation complete

---

## 📊 Success Metrics

By end of Week 1:

| Metric | Target | How to Measure |
|--------|--------|----------------|
| **Provenance Accuracy** | 100% | All web sources tagged `web_search` |
| **Waterfall Completeness** | 90%+ | All enabled stages show timing |
| **Trace Coverage** | >90% | Requests with traces |
| **LLM Token Tracking** | 100% | All LLM calls have token counts |
| **Conversation Persistence** | Works | Refresh doesn't lose context |
| **Test Pass Rate** | 100% | All tests green |
| **Demo Success Rate** | 95%+ | No failures during demo |

---

## 🚦 Risk Mitigation

### **High Risk Items**

1. **OTEL Learning Curve** 🟡 MEDIUM
   - **Risk:** First time using OpenTelemetry
   - **Mitigation:** Use auto-instrumentation, start with 2 services
   - **Fallback:** Skip Splunk export first week, add Week 2

2. **Conversation Persistence Complexity** 🟡 MEDIUM
   - **Risk:** Full SSE/WebSocket is 2-3 days of work
   - **Mitigation:** Use polling approach (simpler, 1 day)
   - **Upgrade Path:** Add SSE in Week 2

3. **Timeline Optimism** 🟠 HIGH
   - **Risk:** 8 days of work in 5 day schedule
   - **Mitigation:** Focus on Tier 0 (blockers), defer stretch goals
   - **Buffer:** Week 2 available for overflow

---

## 📋 Pull Request Strategy

### **5 PRs, Sequential Merge**

#### **PR #1: Provenance Fix**
- **Size:** ~8 files changed
- **Risk:** LOW
- **Review Time:** 2 hours
- **Merge:** Day 1 EOD

#### **PR #2: Waterfall & UX**
- **Size:** ~10 files changed
- **Risk:** LOW
- **Review Time:** 2 hours
- **Merge:** Day 2 EOD

#### **PR #3: OTEL Foundation**
- **Size:** ~12 files changed (docker-compose, configs, 2 services)
- **Risk:** MEDIUM
- **Review Time:** 4 hours
- **Merge:** Day 3 EOD

#### **PR #4: OpenLLMetry**
- **Size:** ~6 files changed
- **Risk:** LOW
- **Review Time:** 2 hours
- **Merge:** Day 4 EOD

#### **PR #5: Conversation Persistence**
- **Size:** ~8 files changed
- **Risk:** MEDIUM
- **Review Time:** 3 hours
- **Merge:** Day 5 EOD

**Total:** 44 files changed, 13 hours review time

---

## 🧪 Testing Requirements

### **Per Cursor Rules:**

✅ **MANDATORY before declaring complete:**

#### 1. **Unit Tests**
```bash
pytest tests/test_evidence.py -v
pytest tests/test_timing.py -v
pytest tests/test_conversation_db.py -v
```

#### 2. **Integration Tests**
```bash
pytest tests/integration/test_search_provenance.py -v
pytest tests/integration/test_otel_traces.py -v
pytest tests/integration/test_conversation_polling.py -v
```

#### 3. **API Tests**
```bash
curl http://localhost:8000/health  # Must return 200
curl http://localhost:8000/services  # All services healthy
```

#### 4. **Frontend Tests**
```bash
cd frontend && npm run build  # Must succeed
docker compose build frontend  # Must succeed
```

#### 5. **End-to-End Tests**
- Homepage loads without blank page
- Console has no JavaScript errors
- API endpoints return 200 status
- Services are healthy
- Data flows correctly

#### 6. **Browser Console**
- Open http://localhost:3000
- F12 → Console
- **Zero errors** (cosmetic warnings OK)

---

## 📚 Documentation Deliverables

### **Required Documents:**

1. ✅ **OTEL Implementation Guide** (Day 5)
   - Architecture diagram
   - Configuration examples
   - Splunk setup instructions
   - Troubleshooting guide

2. ✅ **Conversation Persistence Guide** (Day 5)
   - Database schema
   - Polling API documentation
   - Frontend integration

3. ✅ **README Updates** (Day 5)
   - Observability section
   - Quick start for traces
   - Grafana dashboard links

4. ✅ **CHANGELOG.md** (End of Week)
   - Version bump: 1.3.0 → 1.4.0
   - All features listed
   - Breaking changes (if any)

---

## 🔄 Deployment Process

### **End of Week Deployment:**

#### **Step 1: Merge All PRs**
```bash
git checkout main
git merge otel --no-ff
```

#### **Step 2: Tag Release**
```bash
git tag -a v1.4.0 -m "OpenTelemetry + Provenance + Persistence"
git push origin v1.4.0
```

#### **Step 3: Deploy**
```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

#### **Step 4: Verify**
```bash
docker compose ps  # All healthy
curl http://localhost:8000/health
curl http://localhost:8889/metrics | grep trace
```

#### **Step 5: Smoke Tests**
- Run a query end-to-end
- Check provenance tags
- Verify traces in Grafana
- Refresh during query → should resume

### **Rollback Plan**

If deployment fails:
```bash
git checkout v1.3.0
docker compose down
docker compose up -d
```

**Rollback Triggers:**
- Any service unhealthy
- >10% latency increase
- Console errors
- Test failures

---

## 📞 Communication Plan

### **Daily Standups:**

**Morning (9 AM):**
- What did I complete yesterday?
- What am I working on today?
- Any blockers?

**Evening (5 PM):**
- What got done?
- What's pending?
- Any risks for tomorrow?

### **Status Updates:**

**Daily:**
- Update TODO status
- Commit code with clear messages
- Update CHANGELOG.md

**End of Week:**
- Final status report
- Demo to stakeholders
- Lessons learned

---

## 🎯 Week 2 Preview

If Week 1 succeeds, Week 2 focuses on:

1. **Contract Sentinel** (2 days)
   - Emit artifacts A-G
   - Schema validation

2. **A/B Grader** (1 day)
   - 7-dimension scoring
   - Comparison UI

3. **Query Decomposition** (2 days)
   - Planner sub-queries
   - Self-RAG refinement

4. **Documents Pagination** (1 day)
   - Server-side pagination
   - UI improvements

---

## ✅ Final Checklist

### **Before Starting:**
- [ ] Read full deployment plan (`OTEL_DEPLOYMENT_PLAN.md`)
- [ ] Review TODO list (24 items)
- [ ] Verify environment (Docker, Git, Node.js)
- [ ] Backup current state
- [ ] Set up development environment

### **Daily:**
- [ ] Mark TODO items in_progress
- [ ] Write tests first (TDD)
- [ ] Commit frequently with clear messages
- [ ] Run linter before committing
- [ ] Update CHANGELOG.md
- [ ] Mark completed TODOs

### **Before PR:**
- [ ] All tests pass
- [ ] Linter clean
- [ ] TypeScript type checking passes
- [ ] Frontend builds successfully
- [ ] Documentation updated
- [ ] CHANGELOG.md updated

### **Before Merge to Main:**
- [ ] All PRs reviewed and approved
- [ ] All acceptance criteria met
- [ ] Load tests completed
- [ ] Deployment plan reviewed
- [ ] Rollback plan tested

---

## 🚀 Let's Execute!

**Current Status:** ✅ Branch `otel` created and ready
**Next Step:** Mark first TODO as `in_progress` and start Day 1!

**Command to Start:**
```bash
# Already on otel branch
git status

# Start Day 1 Task 1.1: Evidence Schema
code services/common/evidence.py
```

---

**Questions Before Starting?**
- Review the full plan in `OTEL_DEPLOYMENT_PLAN.md` (2,358 lines)
- Check TODO list for all 24 tasks
- Verify all tools are ready (Docker, Python, Node.js)

**Let's build enterprise-grade observability!** 🔭

---

**Document Version:** 1.0
**Last Updated:** 2025-11-08
**Branch:** otel
**Status:** READY TO EXECUTE

