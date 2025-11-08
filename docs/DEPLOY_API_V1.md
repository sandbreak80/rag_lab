# 🚀 Phase B Deployment Guide

**Status**: ✅ **READY TO DEPLOY**
**Date**: November 8, 2025
**Branch**: `otel`

---

## 📋 **Pre-Deployment Checklist**

✅ All imports bulletproofed (relative imports, PYTHONPATH set)
✅ Pipeline modules moved to `services/api/pipeline/`
✅ Docker Compose service added (`rag-api-v1`)
✅ 8 acceptance tests updated to match API contract
✅ Feature flags default to safe (mocks ON, observability OFF)
✅ Deploy script created (`scripts/deploy_and_test_api_v1.sh`)

---

## 🎯 **Quick Deploy (AWS Instance)**

### Option A: Automated Script (Recommended)

```bash
# SSH to AWS instance
ssh -i ~/SynologyDrive/vcode_projects/bootcamp.pem ubuntu@16.146.148.184

# Run deploy script
cd /home/ubuntu/rag_lab
./scripts/deploy_and_test_api_v1.sh
```

This script will:
1. Pull latest code from `otel` branch
2. Build `rag-api-v1` Docker image
3. Start the service via docker-compose
4. Run 4 smoke tests (/live, /ready, /v1/rag/query, /metrics)
5. Run 8 acceptance probes
6. Report results with color-coded output

### Option B: Manual Steps

```bash
# 1. Pull code
cd /home/ubuntu/rag_lab
git checkout otel
git pull origin otel

# 2. Build
docker build -f services/api/Dockerfile -t rag-api-v1:latest .

# 3. Start
docker compose up -d rag-api-v1

# 4. Verify
curl http://localhost:8080/live | jq
curl http://localhost:8080/ready | jq

# 5. Test
curl -X POST http://localhost:8080/v1/rag/query \
  -H 'Content-Type: application/json' \
  -d '{"query":"What is RAG?","user_id":"test","groups":[]}'

# 6. Run acceptance tests
export RAG_API=http://localhost:8080
pytest tests/test_acceptance_full_contract.py -v
```

---

## 🔍 **Smoke Tests (Manual Verification)**

### 1. Liveness Probe
```bash
curl http://localhost:8080/live | jq

# Expected:
{
  "status": "alive",
  "service": "rag-api",
  "version": "1.0.0"
}
```

### 2. Readiness Probe
```bash
curl http://localhost:8080/ready | jq

# Expected (with mocks):
{
  "status": "ready",
  "service": "rag-api",
  "version": "1.0.0",
  "observability_enabled": false
}

# Or (if OTel not healthy):
{
  "status": "not_ready",
  "checks": {
    "otel_collector": "failed",
    "vector_db": "ok (mocked)"
  }
}
```

### 3. Basic RAG Query
```bash
curl -X POST http://localhost:8080/v1/rag/query \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "What is retrieval augmented generation?",
    "user_id": "smoke_test",
    "groups": ["engineering"]
  }' | jq

# Expected fields:
{
  "answer": "Based on the provided documents...",
  "citations": [
    {
      "doc_id": "doc_1",
      "version": "1.0",
      "chunk_id": "chunk_1",
      "char_range": [0, 150],
      "source_uri": "https://...",
      "origin_tool": "rag"
    }
  ],
  "artifacts": {
    "planner": {...},
    "retrieval_log": {...},
    "evidence_map": {...},
    "recency": {...}
  },
  "metrics": {
    "latency_ms": 1234.5,
    "tokens_in": 256,
    "tokens_out": 128,
    "model": "mock-llm",
    "cost_usd": 0.0001
  },
  "security_status": "ok",
  "request_id": "...",
  "trace_id": "...",
  "contract_version": "1.0.0"
}
```

### 4. Metrics Endpoint
```bash
curl http://localhost:8080/metrics | head -30

# Expected metrics:
# HELP rag_requests_total Total RAG requests
# TYPE rag_requests_total counter
rag_requests_total{endpoint="/v1/rag/query",status="200"} 1.0

# HELP rag_request_duration_seconds RAG request latency
# TYPE rag_request_duration_seconds histogram
rag_request_duration_seconds_bucket{endpoint="/v1/rag/query",le="0.5"} 0.0
...
```

---

## 🧪 **Acceptance Tests (Automated)**

### Run All 8 Probes

```bash
export RAG_API=http://localhost:8080
pytest tests/test_acceptance_full_contract.py -v

# Expected output:
tests/test_acceptance_full_contract.py::TestFullContractAcceptance::test_1_liveness_probe PASSED      [ 12%]
tests/test_acceptance_full_contract.py::TestFullContractAcceptance::test_2_readiness_probe PASSED     [ 25%]
tests/test_acceptance_full_contract.py::TestFullContractAcceptance::test_3_basic_rag_query PASSED     [ 37%]
tests/test_acceptance_full_contract.py::TestFullContractAcceptance::test_4_temporal_probe_recency PASSED [ 50%]
tests/test_acceptance_full_contract.py::TestFullContractAcceptance::test_5_provenance_probe_origin_tool PASSED [ 62%]
tests/test_acceptance_full_contract.py::TestFullContractAcceptance::test_6_ab_probe_dimensions PASSED  [ 75%]
tests/test_acceptance_full_contract.py::TestFullContractAcceptance::test_7_guardrail_probe_degradation PASSED [ 87%]
tests/test_acceptance_full_contract.py::TestFullContractAcceptance::test_8_metrics_probe PASSED        [100%]

===================== 8 passed in 2.34s =====================
```

### Run Single Probe
```bash
pytest tests/test_acceptance_full_contract.py::TestFullContractAcceptance::test_3_basic_rag_query -v
```

---

## 🐛 **Troubleshooting**

### Service Won't Start
```bash
# Check logs
docker logs rag-api-v1 --tail 50

# Common issues:
# 1. Port 8080 already in use
#    Solution: docker compose down && docker compose up -d rag-api-v1
#
# 2. Import errors
#    Solution: Check PYTHONPATH in Dockerfile
#
# 3. Missing dependencies
#    Solution: Rebuild image (docker compose build rag-api-v1)
```

### /ready Returns 503
```bash
# Check dependencies
curl http://localhost:8080/ready | jq

# If OTel collector not healthy:
docker logs rag-otel-collector --tail 30

# Restart collector
docker compose restart otel-collector

# Wait and re-check
sleep 10 && curl http://localhost:8080/ready | jq
```

### /v1/rag/query Returns 500
```bash
# Check API logs
docker logs rag-api-v1 --tail 100

# Common causes:
# 1. Import errors (check for ModuleNotFoundError)
# 2. Missing pipeline modules
# 3. Invalid request payload

# Test with minimal payload
curl -X POST http://localhost:8080/v1/rag/query \
  -H 'Content-Type: application/json' \
  -d '{"query":"test","user_id":"test","groups":[]}'
```

### Acceptance Tests Fail
```bash
# Run with verbose output
pytest tests/test_acceptance_full_contract.py -v --tb=long

# Check API is accessible
curl -sf http://localhost:8080/live || echo "API not reachable"

# Verify correct endpoint
export RAG_API=http://localhost:8080
echo $RAG_API

# Run single test
pytest tests/test_acceptance_full_contract.py::TestFullContractAcceptance::test_1_liveness_probe -v
```

---

## 📊 **Post-Deployment Verification**

### 1. Check Service Status
```bash
docker compose ps rag-api-v1

# Expected:
NAME           COMMAND                  SERVICE      STATUS        PORTS
rag-api-v1     "python -m uvicorn …"    rag-api-v1   Up (healthy)  0.0.0.0:8080->8080/tcp
```

### 2. Verify Feature Flags
```bash
docker exec rag-api-v1 env | grep RAG_

# Expected:
RAG_ENABLE_OBS=0
RAG_USE_MOCK_LLM=1
RAG_USE_MOCK_VECTOR=1
RAG_USE_MOCK_WEB=1
RAG_CONTRACT_VERSION=1.0.0
```

### 3. Check OTel Integration
```bash
# Even with RAG_ENABLE_OBS=0, spans should be created (just not exported)
docker logs rag-otel-collector --tail 50 | grep -i span
```

### 4. Check Prometheus
```bash
# Verify metrics are being collected
curl http://localhost:8080/metrics | grep rag_requests_total
```

---

## 🎉 **Success Criteria**

✅ `docker compose ps rag-api-v1` shows `Up (healthy)`
✅ `/live` returns 200
✅ `/ready` returns 200 (or 503 with valid reasons)
✅ `/v1/rag/query` returns 200 with all required fields
✅ `/metrics` returns Prometheus metrics
✅ 8/8 acceptance tests pass
✅ No import errors in logs
✅ Citations include `origin_tool`
✅ Artifacts include all schemas (A-G where applicable)

---

## 🚀 **Next Steps After Deployment**

### Phase C: Enable Real Backends (One at a Time)

1. **Vector Search** (First)
   ```yaml
   RAG_USE_MOCK_VECTOR: "0"
   VECTOR_DB_URL: "http://vector-db:8005"
   ```
   Test: Re-run acceptance suite

2. **Web Search** (Second)
   ```yaml
   RAG_USE_MOCK_WEB: "0"
   ```
   Test: Re-run acceptance suite

3. **LLM** (Third)
   ```yaml
   RAG_USE_MOCK_LLM: "0"
   OLLAMA_URL: "http://ollama:11434"
   ```
   Test: Re-run acceptance suite

4. **Enable Observability** (Last)
   ```yaml
   RAG_ENABLE_OBS: "1"
   ```
   Test: Check OTel spans in collector, Grafana dashboards

### Performance Testing
```bash
# Run GQS evaluation
cd /home/ubuntu/rag_lab
make eval

# Check P95 latency < 3.5s
# Check citation rate >= 0.95
```

### Security Probes
```bash
# Test ACL filtering (different user groups)
# Test existence leak (unprivileged user shouldn't see privileged doc IDs)
# Test payload logging (should be ZERO)
```

---

## 📞 **Support**

If deployment fails or tests don't pass:
1. Check logs: `docker logs rag-api-v1 --tail 100`
2. Review troubleshooting section above
3. Run smoke tests individually
4. Check docker-compose.yml configuration
5. Verify branch is up-to-date: `git pull origin otel`

---

**Deploy Command**: `./scripts/deploy_and_test_api_v1.sh`

**Status**: Ready for production testing! 🎯

