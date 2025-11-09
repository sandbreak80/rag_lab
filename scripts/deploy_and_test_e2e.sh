#!/usr/bin/env bash
set -euo pipefail

echo "=========================================="
echo "E2E Test Deployment & Execution"
echo "Running on AWS Instance"
echo "=========================================="

cd /home/ubuntu/rag_lab

# Step 1: Pull latest code
echo ""
echo "Step 1: Pulling latest code from otel branch..."
git stash save --keep-index --include-untracked "WIP before E2E deployment" || true
git pull origin otel
git stash pop || true

# Step 2: Deploy updated services
echo ""
echo "Step 2: Deploying updated services..."
echo "Building and starting: otel-collector, rag-api-v1, frontend"
docker compose up -d --build otel-collector rag-api-v1 frontend

# Step 3: Wait for services to be healthy
echo ""
echo "Step 3: Waiting for services to become healthy (60s)..."
sleep 60

# Step 4: Sanity checks
echo ""
echo "Step 4: Running sanity checks..."
echo "=========================================="

echo "Checking /live endpoint..."
curl -sf http://localhost:3000/live | jq || echo "⚠️  /live check failed"

echo ""
echo "Checking /ready endpoint..."
curl -sf http://localhost:3000/ready | jq || echo "⚠️  /ready check failed"

echo ""
echo "Checking /health endpoint..."
curl -sf http://localhost:3000/health | jq || echo "⚠️  /health check failed"

echo ""
echo "Testing API query..."
curl -sf -X POST http://localhost:3000/api/v1/rag/query \
  -H 'Content-Type: application/json' \
  -d '{"query":"What is RAG?","user_id":"demo","groups":[]}' | jq '.answer' || echo "⚠️  API query failed"

# Step 5: Verify OTel Collector is healthy
echo ""
echo "Step 5: Checking OTel Collector health..."
docker ps | grep otel-collector
docker logs rag-otel-collector --tail 10 | grep -i "health" || true

# Step 6: Check Prometheus metrics
echo ""
echo "Step 6: Verifying Prometheus metrics..."
curl -sf http://localhost:3000/api/metrics | grep -E "rag_requests_total|rag_latency|llm_tokens" | head -5 || echo "⚠️  Metrics check failed"

# Step 7: Run E2E tests
echo ""
echo "=========================================="
echo "Step 7: Running Playwright E2E Test Suite"
echo "=========================================="

# Use the CI script if it exists, otherwise run directly
if [ -f "scripts/run_e2e_ci.sh" ]; then
    bash scripts/run_e2e_ci.sh
else
    # Fallback: run Playwright directly
    docker compose -f tests/e2e/docker-compose.e2e.yml up --build --abort-on-container-exit --exit-code-from e2e
    E2E_EXIT_CODE=$?
    
    echo ""
    echo "=========================================="
    echo "E2E Test Results"
    echo "=========================================="
    echo "Exit Code: $E2E_EXIT_CODE"
    
    if [ -d "tests/e2e/playwright-report" ]; then
        echo "✅ Reports generated in: tests/e2e/playwright-report/"
        echo "   - HTML: tests/e2e/playwright-report/index.html"
        echo "   - JUnit: tests/e2e/playwright-report/results.xml"
    fi
    
    if [ "$E2E_EXIT_CODE" -eq 0 ]; then
        echo ""
        echo "✅ ALL E2E TESTS PASSED!"
    else
        echo ""
        echo "❌ SOME E2E TESTS FAILED"
        echo "Check reports and logs for details"
    fi
    
    exit "$E2E_EXIT_CODE"
fi

