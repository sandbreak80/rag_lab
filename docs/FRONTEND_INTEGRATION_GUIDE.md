# Frontend Integration Guide - RAG API v1

**Complete guide to wire the new observability-rich RAG API into your chat UI.**

---

## 🎯 What's Ready

✅ **Backend**: API deployed at `rag-api-v1:8080` (8/8 acceptance tests passed)
✅ **Routing**: Nginx same-origin `/api/*` → `rag-api-v1` (no CORS)
✅ **Client**: `frontend/src/services/ragApiV1.ts` (askRagV1 function)
✅ **Components**: Citations, Provenance, Metrics, JSON Inspector

---

## 📋 Integration Steps

### 1. Deploy Updated Nginx Configs (REQUIRED FIRST)

From your **local machine** with SSH access to AWS:

```bash
cd /path/to/rag_lab
./scripts/deploy-nginx-routing.sh
```

Or manually:
```bash
ssh -i your-key.pem ubuntu@16.146.148.184
cd /home/ubuntu/rag_lab
git pull origin otel
docker compose up -d --build rag-api-v1 frontend
```

**Verify routing works:**
```bash
# Health check
curl http://16.146.148.184:3000/live

# API test
curl -X POST http://16.146.148.184:3000/api/v1/rag/query \
  -H 'Content-Type: application/json' \
  -d '{"query":"test","user_id":"demo","groups":[]}'
```

If you get JSON responses (not HTML), routing is working ✅

---

### 2. Wire API Client in Chat Component

**Find your chat/ask component** (likely `frontend/src/components/ChatInterface.tsx` or similar)

**Add imports:**
```tsx
import { askRagV1 } from '../services/ragApiV1';
import { CitationsDrawer } from '../components/CitationsDrawer';
import { ProvenanceBadges } from '../components/ProvenanceBadges';
import { MetricsRow } from '../components/MetricsRow';
import { JSONInspector } from '../components/JSONInspector';
```

**Add state for API response:**
```tsx
const [ragResponse, setRagResponse] = useState<any>(null);
const [isLoading, setIsLoading] = useState(false);
```

**Replace existing API call:**
```tsx
const handleSubmit = async (query: string) => {
  setIsLoading(true);
  try {
    // NEW: Call RAG API v1 with observability
    const response = await askRagV1({
      query,
      user_id: 'demo',  // TODO: Replace with real auth
      groups: [],       // TODO: Replace with SSO groups
      top_k: 8
    });

    setRagResponse(response);

    // Display answer
    console.log('Answer:', response.answer);
    console.log('Citations:', response.citations.length);
    console.log('Trace ID:', response.trace_id);

  } catch (error) {
    console.error('RAG API error:', error);
  } finally {
    setIsLoading(false);
  }
};
```

**Render response with observability:**
```tsx
{ragResponse && (
  <div className="space-y-4">
    {/* Main answer */}
    <div className="prose dark:prose-invert max-w-none">
      {ragResponse.answer}
    </div>

    {/* Provenance & Security badges */}
    <ProvenanceBadges
      securityStatus={ragResponse.security_status}
      recencyPassed={ragResponse.artifacts?.recency?.passed}
      aclFiltered={ragResponse.artifacts?.retrieval_log?.acl_filtered_count}
    />

    {/* Citations drawer */}
    <CitationsDrawer citations={ragResponse.citations} />

    {/* Metrics (trace, tokens, cost, latency) */}
    <MetricsRow
      traceId={ragResponse.trace_id}
      tokensIn={ragResponse.metrics?.tokens_in}
      tokensOut={ragResponse.metrics?.tokens_out}
      costUsd={ragResponse.metrics?.cost_usd}
      latencyMs={ragResponse.metrics?.latency_ms}
      abBucket={ragResponse.artifacts?.ab_evaluation?.bucket}
    />

    {/* JSON artifacts inspector (dev/debugging) */}
    <JSONInspector artifacts={ragResponse.artifacts} />
  </div>
)}
```

---

### 3. Thread Auth (SSO → perms_tag)

Once SSO is integrated, replace stub values:

```tsx
// Get from your auth context/store
const { user } = useAuth();

const response = await askRagV1({
  query,
  user_id: user.id,           // Real user ID
  groups: user.groups || [],  // Real groups from SSO
  dept: user.dept || null,    // Optional dept
  top_k: 8
});
```

The API will:
1. Build `perms_tag` from `user_id + groups + dept`
2. Apply ACL pre-filtering at retrieval
3. Return `acl_filtered_count` in artifacts

---

### 4. Styling Tips

The components use Tailwind. Adjust as needed:

**CitationsDrawer**: Collapsible list of sources
```tsx
<CitationsDrawer
  citations={ragResponse.citations}
  className="mt-4"  // Add spacing
/>
```

**ProvenanceBadges**: Small pills showing origin/security/recency
```tsx
<ProvenanceBadges
  securityStatus={ragResponse.security_status}
  recencyPassed={ragResponse.artifacts?.recency?.passed}
  aclFiltered={ragResponse.artifacts?.retrieval_log?.acl_filtered_count}
  className="flex gap-2"  // Layout
/>
```

**MetricsRow**: Trace link + token counts
```tsx
<MetricsRow
  traceId={ragResponse.trace_id}
  tokensIn={ragResponse.metrics?.tokens_in}
  tokensOut={ragResponse.metrics?.tokens_out}
  costUsd={ragResponse.metrics?.cost_usd}
  latencyMs={ragResponse.metrics?.latency_ms}
  grafanaUrl="http://16.146.148.184:3001"  // Optional: link to Grafana
/>
```

**JSONInspector**: Toggle to view/download artifacts
```tsx
<JSONInspector
  artifacts={ragResponse.artifacts}
  collapsed={true}  // Start collapsed
/>
```

---

## 🧪 Testing Checklist

### Smoke Tests (Manual)

1. **Navigational query**:
   - Ask: "Where is the Phase 2 quickstart?"
   - Expect: Link in citations, `origin_tool=RAG`

2. **Policy/procedure query**:
   - Ask: "How do I run acceptance probes?"
   - Expect: Numbered steps, multiple citations

3. **Temporal query**:
   - Ask: "What changed in Phase B today?"
   - Expect: Recency badge shows pass/fail

### Console Checks

Open browser DevTools → Console:
```js
// Should see trace IDs
console.log('Trace:', response.trace_id);

// Should see all 7 schemas (A-G)
console.log('Artifacts:', Object.keys(response.artifacts));
// Expected: planner, retrieval_log, evidence_map, guardrail_report, etc.

// Should see citations with provenance
console.log('Citations:', response.citations);
// Each should have: doc_id, version, chunk_id, char_range, source_uri, origin_tool
```

### Network Tab

Check request/response:
```http
POST /api/v1/rag/query
Content-Type: application/json

{
  "query": "What is RAG?",
  "user_id": "demo",
  "groups": []
}
```

Response should be **JSON** (not HTML). If you get HTML, Nginx routing is broken.

---

## 🔧 Troubleshooting

### Issue: CORS errors in browser console

**Cause**: Nginx routing not working
**Fix**: Ensure frontend nginx proxies `/api/` → `rag-api-v1:8080`

```nginx
location /api/ {
    proxy_pass http://rag-api-v1:8080;
    proxy_set_header traceparent $http_traceparent;
    proxy_set_header tracestate $http_tracestate;
}
```

Redeploy: `docker compose up -d --build frontend`

### Issue: 502 Bad Gateway

**Cause**: `rag-api-v1` not running or unhealthy
**Fix**: Check container status

```bash
docker compose ps rag-api-v1
docker compose logs rag-api-v1 --tail 50
```

Restart: `docker compose up -d rag-api-v1`

### Issue: Empty artifacts in response

**Cause**: Feature flags disabled or mocks too simplistic
**Fix**: Enable observability

```bash
# In docker-compose.yml for rag-api-v1
RAG_ENABLE_OBS: "1"
```

Restart: `docker compose up -d rag-api-v1`

### Issue: No citations

**Cause**: Mock LLM not generating citations
**Fix**: This is expected with mocks. Citations will populate when real LLM is enabled.

---

## 🚀 Next Steps

After UI works:

1. **Enable observability**: `RAG_ENABLE_OBS=1`
2. **Flip mocks off** (one at a time):
   - `RAG_USE_MOCK_VECTOR=0` → test
   - `RAG_USE_MOCK_WEB=0` → test
   - `RAG_USE_MOCK_LLM=0` → test
3. **Add Grafana links**: Point `MetricsRow` to your Grafana instance
4. **Add auth**: Wire SSO `user_id` and `groups` into `askRagV1`
5. **Run acceptance suite**: Ensure 8/8 green after each change

---

## 📚 Component Reference

### `askRagV1(request: RagRequest): Promise<RagResponse>`

**Request:**
```ts
{
  query: string;        // User question
  user_id: string;      // Auth user ID
  groups?: string[];    // SSO groups for ACL
  dept?: string;        // Optional dept
  top_k?: number;       // Max results (default 8)
}
```

**Response:**
```ts
{
  answer: string;              // Generated answer
  citations: Citation[];       // Source citations
  artifacts: Artifacts;        // Schemas A-G
  metrics: Metrics;            // Tokens, cost, latency
  security_status: string;     // "ok" | "degraded" | "blocked"
  trace_id: string;            // OTel trace ID
  request_id: string;          // Request ID
  contract_version: string;    // "1.0.0"
}
```

### `CitationsDrawer`

**Props:**
```ts
{
  citations: Citation[];     // From response.citations
  className?: string;        // Tailwind classes
}
```

**Behavior**: Collapsible list of sources with copy-to-clipboard

### `ProvenanceBadges`

**Props:**
```ts
{
  securityStatus: string;      // "ok" | "degraded" | "blocked"
  recencyPassed?: boolean;     // Recency gate result
  aclFiltered?: number;        // ACL filtered count
  className?: string;
}
```

**Behavior**: Shows colored badges for security, recency, ACL

### `MetricsRow`

**Props:**
```ts
{
  traceId: string;
  tokensIn?: number;
  tokensOut?: number;
  costUsd?: number;
  latencyMs?: number;
  abBucket?: string;          // A/B test bucket
  grafanaUrl?: string;        // Link to Grafana
  className?: string;
}
```

**Behavior**: Displays metrics, links trace ID to Grafana

### `JSONInspector`

**Props:**
```ts
{
  artifacts: Artifacts;        // Full artifacts object
  collapsed?: boolean;         // Start collapsed
  className?: string;
}
```

**Behavior**: Toggle to view/download JSON artifacts

---

## ✅ Success Criteria

- [ ] No CORS errors in browser console
- [ ] API responses are JSON (not HTML)
- [ ] Citations display with `origin_tool` badges
- [ ] Trace IDs link to Grafana (when configured)
- [ ] Security status badge shows "ok"
- [ ] Recency badge reflects freshness
- [ ] Metrics show tokens, cost, latency
- [ ] JSON inspector reveals all 7 artifacts

**When all pass**: Your observability-rich RAG UI is production-ready! 🎉

