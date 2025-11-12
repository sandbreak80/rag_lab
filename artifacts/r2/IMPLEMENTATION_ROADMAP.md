# Round 2 UI Fix Sprint - Implementation Roadmap

**Project:** RAG Lab Production Readiness  
**Sprint:** Round 2 UI Fixes & Regressions  
**Date:** 2025-11-12  
**Status:** Phase 1 Complete, 9 Issues Remaining

---

## 📊 Sprint Overview

### ✅ Completed (1/10)
- **Phase 0:** Clean rebuild + baseline ✅
- **Issue #1:** Documents list endpoint ✅

### 🔄 In Progress (0/9)
- None

### ⏳ Pending (9/9)
- Issue #2: Settings preset persistence
- Issue #3: Chat session persistence
- Issue #4: Metrics early-stop logic
- Issue #5: Tokens accounting
- Issue #6: Grafana dashboard restore
- Regression A: Chat sources merge
- Regression B: Chat perf breakdown
- Regression C: Metrics query details
- Phase 8: E2E test suite

---

## 🎯 Issue #2: Settings Preset Persistence

### Objective
Keep selected "quick preset" visible after refresh/navigation.

### Tasks

#### 1. Add Zustand Persist Middleware
**File:** `frontend/src/state/settingsStore.ts`

```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface SettingsState {
  preset?: string;
  temperature: number;
  contextWindow: number;
  topK: number;
  webSearchEnabled: boolean;
  vectorDbEnabled: boolean;
  researchAgentEnabled: boolean;
  promptEnhancementEnabled: boolean;
  // ... other settings
  
  setPreset: (preset: string) => void;
  updateSettings: (settings: Partial<SettingsState>) => void;
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      preset: undefined,
      temperature: 0.7,
      contextWindow: 2048,
      topK: 8,
      webSearchEnabled: true,
      vectorDbEnabled: true,
      researchAgentEnabled: false,
      promptEnhancementEnabled: false,
      
      setPreset: (preset) => set({ preset }),
      updateSettings: (settings) => set(settings),
    }),
    {
      name: 'rag-settings-v1',
      partialize: (state) => ({
        preset: state.preset,
        temperature: state.temperature,
        contextWindow: state.contextWindow,
        topK: state.topK,
        webSearchEnabled: state.webSearchEnabled,
        vectorDbEnabled: state.vectorDbEnabled,
        researchAgentEnabled: state.researchAgentEnabled,
        promptEnhancementEnabled: state.promptEnhancementEnabled,
      }),
    }
  )
);
```

#### 2. Update Settings UI Component
**File:** `frontend/src/components/settings/SettingsPanel.tsx`

```typescript
import { useSettingsStore } from '@/state/settingsStore';

export function SettingsPanel() {
  const { preset, setPreset, ...settings } = useSettingsStore();
  
  // Render preset selector with active state
  return (
    <div>
      <div className="preset-selector">
        {presets.map((p) => (
          <PresetCard
            key={p.id}
            preset={p}
            active={preset === p.id}
            onClick={() => setPreset(p.id)}
            data-testid={preset === p.id ? "preset-selected" : undefined}
          />
        ))}
      </div>
      {/* ... rest of settings */}
    </div>
  );
}
```

### Acceptance Criteria
- [ ] Select preset → navigate away → refresh → selection persists
- [ ] `data-testid="preset-selected"` on active preset
- [ ] localStorage contains `rag-settings-v1` key
- [ ] All toggles persist across sessions

### Proof Artifacts
- `artifacts/r2/fix2_settings_localStorage.json` (dump of localStorage)
- `artifacts/r2/fix2_settings_persist.png` (screenshot showing persistence)
- Playwright spec: `tests/e2e/specs/21_settings_persist.spec.ts`

### Estimated Time
**45-60 minutes**

---

## 🎯 Issue #3: Chat Session Persistence

### Objective
After sending a prompt, refresh/navigate back → the answer renders.

### Tasks

#### 1. Backend: Add Message ID
**File:** `services/api/routes/rag.py`

```python
import uuid
from pydantic import BaseModel

# In-memory store for message status (replace with Redis in production)
message_store = {}

class RagResponse(BaseModel):
    message_id: str  # Add this field
    answer: str
    # ... existing fields

@router.post("/query")
async def query_rag(req: RagQuery):
    message_id = str(uuid.uuid4())
    
    # Store initial status
    message_store[message_id] = {
        "status": "processing",
        "query": req.query,
        "created_at": datetime.utcnow().isoformat()
    }
    
    try:
        # ... existing RAG pipeline ...
        
        # Store completed result
        message_store[message_id] = {
            "status": "completed",
            "query": req.query,
            "answer": answer,
            "citations": citations,
            "sources": sources,
            "metrics": metrics,
            "completed_at": datetime.utcnow().isoformat()
        }
        
        return RagResponse(
            message_id=message_id,
            answer=answer,
            # ... rest of response
        )
    except Exception as e:
        message_store[message_id] = {
            "status": "error",
            "error": str(e)
        }
        raise

@router.get("/result/{message_id}")
async def get_message_result(message_id: str):
    """Get result for a specific message ID"""
    if message_id not in message_store:
        raise HTTPException(404, "Message not found")
    
    return message_store[message_id]
```

#### 2. Frontend: Persist Chat History
**File:** `frontend/src/state/chatStore.ts`

```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface Message {
  id: string;
  message_id?: string;  // Backend message ID
  role: 'user' | 'assistant';
  content: string;
  status: 'pending' | 'completed' | 'error';
  citations?: Citation[];
  sources?: Source[];
  metrics?: Metrics;
}

interface ChatState {
  messages: Message[];
  addMessage: (message: Message) => void;
  updateMessage: (id: string, updates: Partial<Message>) => void;
  pollPendingMessages: () => Promise<void>;
}

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      messages: [],
      
      addMessage: (message) => set((state) => ({
        messages: [...state.messages, message]
      })),
      
      updateMessage: (id, updates) => set((state) => ({
        messages: state.messages.map((m) =>
          m.id === id ? { ...m, ...updates } : m
        )
      })),
      
      pollPendingMessages: async () => {
        const { messages, updateMessage } = get();
        const pending = messages.filter((m) => m.status === 'pending' && m.message_id);
        
        for (const msg of pending) {
          try {
            const response = await fetch(`/api/v1/rag/result/${msg.message_id}`);
            const data = await response.json();
            
            if (data.status === 'completed') {
              updateMessage(msg.id, {
                status: 'completed',
                content: data.answer,
                citations: data.citations,
                sources: data.sources,
                metrics: data.metrics,
              });
            } else if (data.status === 'error') {
              updateMessage(msg.id, {
                status: 'error',
                content: `Error: ${data.error}`,
              });
            }
          } catch (error) {
            console.error(`Failed to poll message ${msg.message_id}:`, error);
          }
        }
      },
    }),
    {
      name: 'rag-chat-history-v1',
    }
  )
);
```

#### 3. Frontend: Poll on Mount
**File:** `frontend/src/pages/ChatPage.tsx`

```typescript
import { useEffect } from 'react';
import { useChatStore } from '@/state/chatStore';

export function ChatPage() {
  const { messages, pollPendingMessages } = useChatStore();
  
  useEffect(() => {
    // Poll for pending messages on mount
    pollPendingMessages();
    
    // Set up interval for active polling
    const interval = setInterval(pollPendingMessages, 2000);
    
    return () => clearInterval(interval);
  }, [pollPendingMessages]);
  
  return (
    <div>
      {messages.map((msg) => (
        <MessageItem
          key={msg.id}
          message={msg}
          data-testid={`chat-message-${msg.id}`}
        />
      ))}
    </div>
  );
}
```

### Acceptance Criteria
- [ ] Send prompt → refresh → answer appears within 10s
- [ ] `data-testid="chat-message-<id>"` on each message
- [ ] `data-testid="chat-answer"` on assistant messages
- [ ] Pending messages show loading state
- [ ] Completed messages persist across sessions

### Proof Artifacts
- `artifacts/r2/fix3_chat_status_response.json` (message lifecycle)
- `artifacts/r2/fix3_chat_resume.png` (screenshot after refresh)
- Playwright spec: `tests/e2e/specs/22_chat_resume.spec.ts`

### Estimated Time
**90-120 minutes**

---

## 🎯 Issue #4: Metrics Early-Stop Obeys Settings

### Objective
If Web Search toggle is **enabled**, do **not** show "Web Skipped" unless early-stop threshold triggered; if **disabled**, always show "Web Skipped (disabled)".

### Tasks

#### 1. Backend: Add Web Reason Field
**File:** `services/api/routes/rag.py`

```python
# In the RAG query handler
web_reason = "ok"  # Default

if not req.web_search_enabled:
    web_reason = "disabled"
    web_skipped = True
elif early_stop_triggered:
    web_reason = "early_stop"
    web_skipped = True
elif web_timeout:
    web_reason = "timeout"
    web_skipped = False  # Ran but timed out
else:
    web_reason = "ok"
    web_skipped = False

# Add to metrics
metrics = {
    "stage_timings": {
        "vector_ms": vector_ms,
        "web_ms": web_ms,
        "llm_ms": llm_ms,
        "total_ms": total_ms,
        "retrieve_parallel_ms": retrieve_parallel_ms,
        "web_skipped": web_skipped,
        "web_reason": web_reason,  # NEW
        "web_enabled": req.web_search_enabled,  # NEW
    }
}
```

#### 2. Frontend: Conditional Badge Rendering
**File:** `frontend/src/components/metrics/StageTimingsDisplay.tsx`

```typescript
interface StageTimings {
  vector_ms: number;
  web_ms: number;
  llm_ms: number;
  total_ms: number;
  retrieve_parallel_ms?: number;
  web_skipped: boolean;
  web_reason?: 'disabled' | 'early_stop' | 'timeout' | 'ok';
  web_enabled?: boolean;
}

export function StageTimingsDisplay({ timings }: { timings: StageTimings }) {
  const renderWebBadge = () => {
    if (!timings.web_skipped) {
      return null;  // Web ran successfully
    }
    
    const badgeConfig = {
      disabled: { color: 'gray', text: 'Web Skipped (Disabled)' },
      early_stop: { color: 'amber', text: 'Web Skipped (Early-stop)' },
      timeout: { color: 'red', text: 'Web Timed Out' },
    };
    
    const config = badgeConfig[timings.web_reason || 'disabled'];
    
    return (
      <Badge
        variant={config.color}
        data-testid="metrics-web-skipped-badge"
        data-reason={timings.web_reason}
      >
        {config.text}
      </Badge>
    );
  };
  
  return (
    <div className="grid grid-cols-2 gap-4">
      <MetricCard label="Vector Search" value={`${timings.vector_ms}ms`} testid="metrics-vector-ms" />
      <MetricCard label="Web Search" value={`${timings.web_ms}ms`} testid="metrics-web-ms">
        {renderWebBadge()}
      </MetricCard>
      <MetricCard label="LLM Generation" value={`${timings.llm_ms}ms`} testid="metrics-llm-ms" />
      <MetricCard label="Total" value={`${timings.total_ms}ms`} testid="metrics-total-ms" />
    </div>
  );
}
```

### Acceptance Criteria
- [ ] Toggle web off → badge shows "Disabled" (gray)
- [ ] Toggle web on + strong vector match → "Early-stop" (amber)
- [ ] Toggle web on + weak match → no badge, `web_ms` renders
- [ ] Timeout scenario → "Web Timed Out" (red)
- [ ] `data-testid="metrics-web-skipped-badge"` with `data-reason` attribute

### Proof Artifacts
- `artifacts/r2/fix4_metrics_api_disabled.json` (web disabled)
- `artifacts/r2/fix4_metrics_api_earlystop.json` (early-stop)
- `artifacts/r2/fix4_metrics_api_ok.json` (web ran)
- `artifacts/r2/fix4_metrics_screenshot.png` (all badge states)
- Contract test: `tests/contract/test_web_skip_logic.py`
- E2E spec: `tests/e2e/specs/23_metrics_webskip.spec.ts`

### Estimated Time
**60-75 minutes**

---

## 🎯 Issue #5: Tokens Accounting

### Objective
Tokens never show 0 unless truly empty; count prompt & completion reliably.

### Tasks

#### 1. Backend: LLM Adapter Token Counting
**File:** `services/api/adapters/llm.py`

```python
import tiktoken  # or use model-specific tokenizer

def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """Count tokens for a given text and model"""
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception:
        # Fallback: rough estimate (4 chars per token)
        return len(text) // 4

async def generate_answer(prompt: str, context: str, model: str = "llama3"):
    """Generate answer with token accounting"""
    full_prompt = f"{context}\n\nQuestion: {prompt}\n\nAnswer:"
    
    tokens_in = count_tokens(full_prompt, model)
    
    # Call LLM
    response = await ollama_client.generate(
        model=model,
        prompt=full_prompt,
    )
    
    answer = response.get("response", "")
    tokens_out = count_tokens(answer, model)
    
    # Also try to get from Ollama response if available
    if "eval_count" in response:
        tokens_out = response["eval_count"]
    if "prompt_eval_count" in response:
        tokens_in = response["prompt_eval_count"]
    
    return {
        "answer": answer,
        "tokens": {
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "tokens_total": tokens_in + tokens_out,
        }
    }
```

#### 2. Backend: OTel Span Attributes
**File:** `services/api/routes/rag.py`

```python
# In the LLM generation span
with tracer.start_as_current_span("llm.generate") as llm_span:
    result = await llm_adapter.generate_answer(...)
    
    # Add token attributes
    llm_span.set_attribute("llm.tokens_in", result["tokens"]["tokens_in"])
    llm_span.set_attribute("llm.tokens_out", result["tokens"]["tokens_out"])
    llm_span.set_attribute("llm.tokens_total", result["tokens"]["tokens_total"])
```

#### 3. Backend: Prometheus Counters
**File:** `services/api/metrics.py`

```python
from prometheus_client import Counter

RAG_LLM_TOKENS = Counter(
    'rag_llm_tokens_total',
    'Total tokens processed by LLM',
    ['direction']  # 'in' or 'out'
)

# In RAG handler
RAG_LLM_TOKENS.labels(direction='in').inc(tokens_in)
RAG_LLM_TOKENS.labels(direction='out').inc(tokens_out)
```

#### 4. Frontend: Prompt Logs Display
**File:** `frontend/src/components/logging/PromptLoggingPage.tsx`

```typescript
// Already has testids from previous work
// Just ensure binding to correct API fields

<div data-testid="promptlog-row">
  <span data-testid="promptlog-model">{log.model}</span>
  <span data-testid="promptlog-tokens-total">{log.tokens_total}</span>
  
  {/* In detail modal */}
  <div>
    <span data-testid="promptlog-tokens-in">{log.tokens_in}</span>
    <span data-testid="promptlog-tokens-out">{log.tokens_out}</span>
  </div>
</div>
```

### Acceptance Criteria
- [ ] Non-zero token counts for normal queries
- [ ] OTel spans show `llm.tokens_in/out/total` attributes
- [ ] Prometheus query returns >0 for `rag_llm_tokens_total`
- [ ] Prompt logs page displays tokens correctly
- [ ] Values roughly match model expectations (±10%)

### Proof Artifacts
- `artifacts/r2/fix5_promptlog_api.json` (non-zero tokens)
- `artifacts/r2/fix5_otel_span.json` (Tempo span with token attrs)
- `artifacts/r2/fix5_prom_query.json` (Prometheus query result)
- `artifacts/r2/fix5_promptlog_screenshot.png`
- Contract test: `tests/contract/test_tokens_accounting.py`
- E2E spec: `tests/e2e/specs/24_prompt_logs_tokens.spec.ts`

### Estimated Time
**75-90 minutes**

---

## 🎯 Issue #6: Grafana Dashboard Restore

### Objective
Bring back the prior "RAG Lab Comprehensive System Overview" dashboard.

### Tasks

#### 1. Export/Locate Dashboard JSON
**Source:** Previous deployment or backup

If not available, create new dashboard with:
- GPU metrics (DCGM exporter)
- System metrics (node-exporter)
- Container metrics (cAdvisor)
- RAG-specific metrics (Prometheus)
- Trace exemplars (Tempo)

#### 2. Import to Grafana
**File:** `monitoring/grafana/dashboards/rag-lab-comprehensive.json`

```bash
# Copy dashboard JSON to provisioning directory
cp rag-lab-comprehensive.json monitoring/grafana/dashboards/

# Restart Grafana to auto-import
docker compose restart grafana
```

#### 3. Update Monitoring Page Link
**File:** `frontend/src/pages/MonitoringPage.tsx`

```typescript
const GRAFANA_COMPREHENSIVE_URL = `${GRAFANA_BASE_URL}/d/rag-lab-comprehensive/rag-lab-comprehensive-system-overview?orgId=1&refresh=10s`;

export function MonitoringPage() {
  return (
    <div>
      {/* Existing link */}
      <a href={GRAFANA_URL} data-testid="grafana-link">
        Open Grafana
      </a>
      
      {/* New comprehensive dashboard link */}
      <a href={GRAFANA_COMPREHENSIVE_URL} data-testid="grafana-link-comprehensive">
        System Overview Dashboard
      </a>
    </div>
  );
}
```

### Acceptance Criteria
- [ ] Dashboard accessible at new URL
- [ ] All panels load without errors
- [ ] GPU metrics show data (if GPU present)
- [ ] System metrics show data
- [ ] Link from Monitoring page works
- [ ] `data-testid="grafana-link-comprehensive"` present

### Proof Artifacts
- `artifacts/r2/fix6_grafana_dashboard.json` (exported JSON)
- `artifacts/r2/fix6_grafana_screenshot.png` (dashboard view)
- `artifacts/r2/fix6_gpu_panels.png` (GPU metrics if available)
- E2E spec: `tests/e2e/specs/monitoring_links.spec.ts` (updated)

### Estimated Time
**30-45 minutes** (if dashboard JSON exists)  
**90-120 minutes** (if creating from scratch)

---

## 🎯 Regression A: Chat Sources Merge

### Objective
Verify web sources show in Chat when web enabled.

### Current Status
Backend logic already implemented in previous sprint:
- `sources[]` array merges RAG + Web + Research
- `origin_tool` field distinguishes source types

### Tasks

#### 1. Verify Backend Response
**Test:** Send query with web enabled, verify `sources[]` contains web items

```bash
curl -X POST http://localhost:3000/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "web_search_enabled": true
  }' | jq '.sources[] | select(.origin_tool == "web")'
```

#### 2. Verify Frontend Rendering
**File:** `frontend/src/components/chat/SourceCard.tsx`

Already updated to handle `origin_tool` and display icons:
- RAG: FileText icon
- Web: Globe icon
- Research: Sparkles icon

### Acceptance Criteria
- [ ] Query with web enabled returns web sources
- [ ] Frontend renders web sources with Globe icon
- [ ] `data-testid="source-item"` with `data-origin="web"`
- [ ] Sources list shows mix of RAG and Web

### Proof Artifacts
- `artifacts/r2/fixA_sources_response.json` (API response with web sources)
- `artifacts/r2/fixA_chat_sources_screenshot.png`
- E2E spec: `tests/e2e/specs/25_chat_sources_merge.spec.ts`

### Estimated Time
**30 minutes** (verification + test)

---

## 🎯 Regression B: Chat Perf Breakdown

### Objective
Chat performance breakdown shows full stack timings (vector, web, llm, total).

### Current Status
Backend already returns all timing fields in `metrics.stage_timings`.

### Tasks

#### 1. Verify MessageItem Component
**File:** `frontend/src/components/chat/MessageItem.tsx`

Ensure it reads all timing fields:

```typescript
interface StageTimings {
  vector_ms: number;
  web_ms: number;
  llm_ms: number;
  total_ms: number;
  retrieve_parallel_ms?: number;
  web_skipped?: boolean;
}

export function MessageItem({ message }: { message: Message }) {
  const timings = message.metrics?.stage_timings;
  
  if (!timings) return null;
  
  return (
    <div data-testid="perf-breakdown">
      <div data-testid="perf-vector-ms">{timings.vector_ms}ms</div>
      <div data-testid="perf-web-ms">{timings.web_ms}ms</div>
      <div data-testid="perf-llm-ms">{timings.llm_ms}ms</div>
      <div data-testid="perf-total-ms">{timings.total_ms}ms</div>
      {timings.retrieve_parallel_ms && (
        <div data-testid="perf-parallel-ms">{timings.retrieve_parallel_ms}ms</div>
      )}
    </div>
  );
}
```

### Acceptance Criteria
- [ ] All timing fields render in Chat
- [ ] `data-testid="perf-breakdown"` on container
- [ ] Individual testids for each timing field
- [ ] Parallel retrieval time shown when present
- [ ] Web skipped badge shown when applicable

### Proof Artifacts
- `artifacts/r2/fixB_chat_perf_response.json`
- `artifacts/r2/fixB_chat_perf_screenshot.png`
- E2E spec: `tests/e2e/specs/26_chat_perf_breakdown.spec.ts`

### Estimated Time
**30 minutes** (verification + test)

---

## 🎯 Regression C: Metrics Query Details

### Objective
Metrics page "Query Details" shows full stack timings (not just LLM).

### Current Status
`StageTimingsDisplay` component already created and used on Metrics page.

### Tasks

#### 1. Verify Metrics Page Integration
**File:** `frontend/src/components/metrics/MetricsPage.tsx`

Ensure `StageTimingsDisplay` is rendered with latest query data:

```typescript
import { StageTimingsDisplay } from './StageTimingsDisplay';

export function MetricsPage() {
  const [latestTimings, setLatestTimings] = useState<StageTimings | null>(null);
  
  useEffect(() => {
    // Fetch latest query timings
    fetch('/api/v1/rag/query/latest')
      .then(res => res.json())
      .then(data => setLatestTimings(data.metrics?.stage_timings));
  }, []);
  
  return (
    <div>
      <MetricsOverview />
      
      {latestTimings && (
        <div data-testid="metrics-query-details">
          <h3>Latest Query Performance</h3>
          <StageTimingsDisplay timings={latestTimings} />
        </div>
      )}
    </div>
  );
}
```

### Acceptance Criteria
- [ ] Metrics page shows full timing breakdown
- [ ] `data-testid="metrics-query-details"` on container
- [ ] All timing fields visible (vector, web, llm, total)
- [ ] Updates when new query runs

### Proof Artifacts
- `artifacts/r2/fixC_metrics_query_details_response.json`
- `artifacts/r2/fixC_metrics_query_details_screenshot.png`
- E2E spec: `tests/e2e/specs/23_metrics_webskip.spec.ts` (extended)

### Estimated Time
**30 minutes** (verification + test)

---

## 🎯 Phase 8: E2E Test Suite

### Objective
Run full Playwright suite and achieve ≥18/21 core tests passing.

### Tasks

#### 1. Create New Test Specs
Based on issues fixed above:
- `tests/e2e/specs/20_documents_list.spec.ts`
- `tests/e2e/specs/21_settings_persist.spec.ts`
- `tests/e2e/specs/22_chat_resume.spec.ts`
- `tests/e2e/specs/23_metrics_webskip.spec.ts`
- `tests/e2e/specs/24_prompt_logs_tokens.spec.ts`
- `tests/e2e/specs/25_chat_sources_merge.spec.ts`
- `tests/e2e/specs/26_chat_perf_breakdown.spec.ts`

#### 2. Update Existing Specs
- `tests/e2e/specs/15_monitoring.spec.ts` (add comprehensive dashboard link)

#### 3. Run Full Suite
```bash
bash scripts/run_e2e.sh
```

#### 4. Generate Reports
- HTML report: `tests/e2e/playwright-report/index.html`
- JUnit XML: `tests/e2e/playwright-report/results.xml`
- Screenshots: `tests/e2e/playwright-report/screenshots/`

### Acceptance Criteria
- [ ] ≥18/21 core tests passing
- [ ] New specs cover all fixed issues
- [ ] HTML report generated
- [ ] Screenshots captured for failures
- [ ] No console errors in passing tests

### Proof Artifacts
- `tests/e2e/playwright-report/index.html` (full report)
- `artifacts/r2/e2e_summary.txt` (pass/fail counts)
- `artifacts/r2/e2e_screenshots/` (failure screenshots)

### Estimated Time
**60-90 minutes** (test creation + debugging)

---

## 📊 Sprint Summary

### Total Estimated Time
- Issue #2: 45-60 min
- Issue #3: 90-120 min
- Issue #4: 60-75 min
- Issue #5: 75-90 min
- Issue #6: 30-120 min (depends on dashboard availability)
- Regression A: 30 min
- Regression B: 30 min
- Regression C: 30 min
- Phase 8: 60-90 min

**Total: 7-10 hours** (1-2 full work days)

### Priority Order
1. **Issue #2** (Settings persistence) - Quick win, high user impact
2. **Regression A, B, C** (Verifications) - Low effort, high confidence
3. **Issue #4** (Metrics early-stop) - Medium complexity, important UX
4. **Issue #5** (Tokens accounting) - Medium complexity, observability critical
5. **Issue #3** (Chat persistence) - High complexity, high value
6. **Issue #6** (Grafana dashboard) - Low priority unless GPU monitoring needed
7. **Phase 8** (E2E suite) - Final validation

### Success Metrics
- [ ] All 9 issues resolved
- [ ] ≥18/21 E2E tests passing
- [ ] All proof artifacts generated
- [ ] Documentation updated
- [ ] Code committed with proper messages
- [ ] Ready for production deployment

---

## 📝 Commit Strategy

**One commit per issue:**
```
fix(r2-ui-002): settings preset persistence with zustand
fix(r2-ui-003): chat session persistence with message polling
fix(r2-ui-004): metrics early-stop obeys settings
fix(r2-ui-005): tokens accounting in llm + otel + prometheus
fix(r2-ui-006): restore grafana comprehensive dashboard
fix(r2-reg-a): verify chat sources merge rag + web
fix(r2-reg-b): verify chat perf breakdown full timings
fix(r2-reg-c): verify metrics query details full timings
test(r2-e2e): add comprehensive e2e coverage for r2 fixes
```

**Final summary commit:**
```
docs(r2): complete round 2 ui fix sprint with artifacts

- Resolved 9 UI issues + 3 regressions
- Added 7 new E2E specs
- Generated full proof artifacts
- Achieved 18/21 E2E tests passing
- Ready for production deployment

Closes: #2, #3, #4, #5, #6, Regression A/B/C
```

---

**Status:** Ready for Execution  
**Next Action:** Begin Issue #2 (Settings Persistence)

