# Production Hardening Checklist

**Post-deployment security, reliability, and observability hardening.**

---

## 🔒 Security

### [ ] 1. Lock Down CORS (Already Done ✅)
- Same-origin routing via Nginx
- No `Access-Control-Allow-Origin: *`
- If cross-origin needed, use strict allowlist

### [ ] 2. Authentication & Authorization
**Current**: Stub `user_id="demo"`, `groups=[]`

**Production**:
```nginx
# Nginx + OIDC sidecar
location /api/ {
    auth_request /oauth2/auth;
    proxy_set_header X-User-Id $auth_user_id;
    proxy_set_header X-Groups $auth_groups;
    proxy_pass http://rag-api-v1:8080;
}
```

**API trusts only these headers** (validate in middleware):
```python
user_id = request.headers.get('X-User-Id')
groups = request.headers.get('X-Groups', '').split(',')
```

### [ ] 3. Rate Limiting
**Nginx** (already configured):
```nginx
limit_req_zone $binary_remote_addr zone=api_rps:10m rate=10r/s;
location /api/ {
    limit_req zone=api_rps burst=20 nodelay;
}
```

**API** (add per-user limits):
```python
from fastapi_limiter import FastAPILimiter
@app.post("/v1/rag/query")
@limiter.limit("5/minute")  # Per user_id
async def rag_query(...):
```

### [ ] 4. Security Headers (Already Set ✅)
```nginx
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'; ..." always;
```

### [ ] 5. Input Validation
**Query length**:
```python
class RagQuery(BaseModel):
    query: str = Field(..., max_length=500)
    groups: list[str] = Field(default=[], max_items=20)
```

**No PII logging** (already enforced):
```python
# NEVER log query/answer content
logger.info("RAG query", extra={
    "request_id": req_id,
    "user_id": user_id,
    "trace_id": trace_id,
    # NO: "query": query  ❌
})
```

### [ ] 6. Secrets Management
**Current**: Env vars in `docker-compose.yml`

**Production**: Use AWS Secrets Manager / Vault
```yaml
environment:
  - OPENAI_API_KEY=${OPENAI_API_KEY}  # From secrets
  - VECTOR_AUTH_TOKEN=${VECTOR_TOKEN}
```

---

## ⏱️ Timeouts & Budgets

### [ ] 7. Per-Stage Timeouts
```python
# In pipeline handler
TIMEOUTS = {
    "retrieval": 2.0,   # Vector/lexical search
    "rerank": 1.5,      # Cross-encoder
    "llm": 60.0,        # LLM generation
    "guardrails": 1.0,  # Security check
}

async with timeout(TIMEOUTS["retrieval"]):
    candidates = await retrieval_adapter.search(...)
```

### [ ] 8. End-to-End Budget
```python
E2E_BUDGET_MS = 75_000  # 75s (matches Nginx timeout)

start = time.perf_counter()
# ... pipeline stages ...
elapsed = (time.perf_counter() - start) * 1000
if elapsed > E2E_BUDGET_MS:
    logger.warning("SLA exceeded", extra={"elapsed_ms": elapsed})
```

### [ ] 9. Nginx Timeouts (Already Tuned ✅)
```nginx
proxy_connect_timeout 5s;
proxy_read_timeout 75s;
proxy_send_timeout 75s;
```

---

## 🔄 Reliability

### [ ] 10. Health Checks (Already Configured ✅)
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/ready"]
  interval: 10s
  timeout: 2s
  retries: 12
```

**Liveness** (`/live`): Always 200 if process up  
**Readiness** (`/ready`): Only 200 if deps connected

### [ ] 11. Resource Limits
```yaml
rag-api-v1:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 4G
      reservations:
        cpus: '1'
        memory: 2G
```

### [ ] 12. Restart Policy (Already Set ✅)
```yaml
restart: unless-stopped
```

### [ ] 13. Graceful Shutdown
```python
@app.on_event("shutdown")
async def shutdown():
    # Drain in-flight requests
    await asyncio.sleep(5)
    # Close connections
    await vector_client.close()
    await redis_client.close()
```

### [ ] 14. Circuit Breakers
```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
async def call_llm(prompt):
    # Will open circuit after 5 failures
    return await llm_client.generate(prompt)
```

---

## 📊 Observability

### [ ] 15. Enable OpenTelemetry (After UI Works)
```yaml
RAG_ENABLE_OBS: "1"
```

**Verify 20 semantic attributes** in traces:
```bash
curl http://localhost:3000/api/v1/rag/query ... \
  -H 'traceparent: 00-$(uuidgen | tr -d -)-$(uuidgen | cut -c1-16)-01'
```

Check Jaeger/Tempo for:
- `rag.request.contract_version`
- `rag.retrieve.candidate_count`
- `llm.tokens.input`, `llm.tokens.output`
- `rag.citations.count`

### [ ] 16. Prometheus Metrics
**Already exposed**: `http://localhost:3000/metrics`

**Add scrape config**:
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'rag-api-v1'
    static_configs:
      - targets: ['rag-api-v1:9309']
```

**Key metrics**:
- `gqs_p95_latency_seconds` < 3.5s
- `gqs_citation_rate` >= 0.95
- `gqs_freshness_violations_total` == 0
- `gqs_provenance_missing_total` == 0

### [ ] 17. Grafana Dashboards
**Panels** (from `otel/span_semantics.md`):
1. Request rate (by intent)
2. P95 latency (by stage)
3. Token usage (in/out)
4. Citation rate
5. Guardrail status
6. ACL filtered count
7. Freshness violations

**Import**: `otel/grafana-rag-dashboard.json` (create this)

### [ ] 18. Alerts
```yaml
# Prometheus alerts
groups:
  - name: rag_api
    rules:
      - alert: HighLatency
        expr: gqs_p95_latency_seconds > 3.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "RAG API P95 latency > 3.5s"

      - alert: FreshnessViolations
        expr: rate(gqs_freshness_violations_total[5m]) > 0
        for: 5m
        labels:
          severity: critical

      - alert: LowCitationRate
        expr: gqs_citation_rate < 0.95
        for: 10m
        labels:
          severity: warning

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.005
        for: 5m
        labels:
          severity: critical
```

---

## 🧪 Testing Gates

### [ ] 19. Acceptance Suite (CI Gate)
```yaml
# .github/workflows/test.yml
- name: Run Acceptance Tests
  run: |
    docker compose up -d rag-api-v1
    export RAG_API=http://localhost:8080
    pytest tests/test_acceptance_full_contract.py -v
```

**Must pass 8/8** before merge.

### [ ] 20. Golden Question Set Evaluation
```bash
make eval
# Produces: evals/gqs_report.jsonl

# Check thresholds:
# - Citation rate >= 0.95
# - Hallucination rate < 2%
# - P95 latency < 3.5s cold, < 1.8s warm
```

**Attach report to PR**.

### [ ] 21. Load Testing
```python
# locust -f tests/load_test.py --host http://localhost:3000

from locust import HttpUser, task, between

class RagUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def ask_rag(self):
        self.client.post("/api/v1/rag/query", json={
            "query": "What is RAG?",
            "user_id": f"user_{self.user_id}",
            "groups": []
        })
```

**Targets**:
- P95 < 3.5s at 10 RPS
- Error rate < 0.5%
- No memory leaks over 1 hour

---

## 🚦 Feature Flags (Gradual Rollout)

### [ ] 22. Flip Mocks Off (One at a Time)

**Step 1: Vector**
```yaml
RAG_USE_MOCK_VECTOR: "0"
```
Run acceptance tests → Must stay 8/8 ✅

**Step 2: Web**
```yaml
RAG_USE_MOCK_WEB: "0"
```
Run acceptance tests → Must stay 8/8 ✅

**Step 3: LLM**
```yaml
RAG_USE_MOCK_LLM: "0"
```
Run acceptance tests → Must stay 8/8 ✅

**Rollback**: Set flags back to `"1"` if any test fails.

### [ ] 23. A/B Testing (Optional)
```yaml
RAG_AB_TEST: "1"
```

**Compare**:
- Bucket A: Extractive-first prompt
- Bucket B: Abstractive prompt

**Metric**: Δ(B-A) on `faithfulness` and `completeness` (95% CI)

---

## 📝 Operations

### [ ] 24. Runbooks
Create docs for:
- **No hits**: Vector DB down? Index empty?
- **Latency spike**: LLM throttling? Network issue?
- **Hallucination spike**: Prompt drift? Low citation rate?
- **Freshness violations**: Ingest pipeline stalled?

### [ ] 25. On-Call & Ownership
- **DRI**: Assign owner for `rag-api-v1`
- **Rotation**: Weekly eval report attached to PR
- **Escalation**: Pagerduty/OpsGenie integration

### [ ] 26. Deployment Hygiene
**Tagging**:
```bash
docker tag rag-api-v1:latest rag-api-v1:1.0.0
docker push rag-api-v1:1.0.0
```

**Rollback**:
```bash
docker compose -p rag_lab_prod pull
docker compose -p rag_lab_prod up -d
```

**Separate envs**:
```bash
# Staging
docker compose -f docker-compose.staging.yml up -d

# Production
docker compose -f docker-compose.prod.yml up -d
```

---

## ✅ Go/No-Go Checklist

Before enabling in production:

- [ ] 8/8 acceptance tests pass
- [ ] GQS eval: citation rate >= 0.95, hallucination < 2%
- [ ] Load test: P95 < 3.5s at 10 RPS, error rate < 0.5%
- [ ] OTel spans include 20 semantic attributes
- [ ] Prometheus metrics scraped
- [ ] Grafana dashboard shows data
- [ ] Alerts configured (latency, freshness, errors)
- [ ] Auth wired (SSO groups → perms_tag)
- [ ] Rate limits active (10 r/s per IP, 5 r/m per user)
- [ ] Secrets in vault (not hardcoded)
- [ ] Runbooks written
- [ ] DRI assigned
- [ ] Rollback plan tested

**If all green → SHIP IT 🚀**

---

## 🔄 Post-Launch

### Week 1
- Monitor dashboards hourly
- Run GQS eval daily
- Check for anomalies (latency spikes, citation drops)

### Week 2
- Review A/B test results (if enabled)
- Tune timeouts based on P95
- Adjust rate limits based on traffic

### Month 1
- Curate golden set (trim to 150-200 questions)
- Add domain-specific queries
- Refine prompts based on feedback

---

## 📚 References

- **Acceptance Tests**: `tests/test_acceptance_full_contract.py`
- **OTel Semantics**: `otel/span_semantics.md`
- **GQS Schema**: `evals/gqs_schema.md`
- **Deployment Script**: `scripts/deploy-nginx-routing.sh`
- **Frontend Integration**: `docs/FRONTEND_INTEGRATION_GUIDE.md`

**Questions?** Check existing docs or Slack `#rag-lab-ops`

