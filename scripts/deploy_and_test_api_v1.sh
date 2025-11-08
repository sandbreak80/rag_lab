#!/usr/bin/env bash
#
# Deploy and test RAG API v1 on AWS instance
#
# Usage: ./scripts/deploy_and_test_api_v1.sh
#

set -e  # Exit on error

echo "============================================================================"
echo "🚀 RAG API v1 - Deploy and Test"
echo "============================================================================"
echo

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Pull latest code
echo "📥 Step 1/6: Pulling latest code from otel branch..."
git fetch origin
git checkout otel
git pull origin otel
echo -e "${GREEN}✓ Code updated${NC}"
echo

# Step 2: Build the API service
echo "🔨 Step 2/6: Building rag-api-v1 Docker image..."
docker build -f services/api/Dockerfile -t rag-api-v1:latest .
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Build successful${NC}"
else
    echo -e "${RED}✗ Build failed${NC}"
    exit 1
fi
echo

# Step 3: Start the service
echo "🐳 Step 3/6: Starting rag-api-v1 service..."
docker compose up -d rag-api-v1

# Wait for service to be ready
echo "⏳ Waiting for service to be ready (max 60s)..."
for i in {1..30}; do
    if curl -sf http://localhost:8080/live > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Service is live${NC}"
        break
    fi
    echo -n "."
    sleep 2
done
echo

# Step 4: Run smoke tests
echo "🧪 Step 4/6: Running smoke tests..."
echo

echo "Test 1: Liveness probe"
curl -sf http://localhost:8080/live | jq '.'
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Liveness OK${NC}"
else
    echo -e "${RED}✗ Liveness FAIL${NC}"
fi
echo

echo "Test 2: Readiness probe"
curl -sf http://localhost:8080/ready | jq '.'
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Readiness OK${NC}"
else
    echo -e "${YELLOW}⚠ Readiness degraded (may be OK with mocks)${NC}"
fi
echo

echo "Test 3: Basic RAG query"
curl -sS -X POST http://localhost:8080/v1/rag/query \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "What is RAG?",
    "user_id": "smoke_test",
    "groups": []
  }' | jq '{answer: .answer[:100], citations: (.citations | length), security_status, contract_version}'

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ RAG query OK${NC}"
else
    echo -e "${RED}✗ RAG query FAIL${NC}"
fi
echo

echo "Test 4: Metrics endpoint"
curl -sf http://localhost:8080/metrics | head -20
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Metrics OK${NC}"
else
    echo -e "${RED}✗ Metrics FAIL${NC}"
fi
echo

# Step 5: Check logs
echo "📋 Step 5/6: Recent logs..."
docker logs rag-api-v1 --tail 20
echo

# Step 6: Run acceptance tests
echo "🎯 Step 6/6: Running 8 acceptance probes..."
export RAG_API=http://localhost:8080

# Install pytest if not already installed
if ! python3 -c "import pytest" 2>/dev/null; then
    echo "Installing pytest..."
    pip3 install -q pytest requests
fi

pytest tests/test_acceptance_full_contract.py -v --tb=short

if [ $? -eq 0 ]; then
    echo
    echo -e "${GREEN}============================================================================${NC}"
    echo -e "${GREEN}✅ ALL TESTS PASSED - API v1 is ready!${NC}"
    echo -e "${GREEN}============================================================================${NC}"
    echo
    echo "Next steps:"
    echo "1. Review test results above"
    echo "2. Check Grafana dashboards: http://16.146.148.184:3001"
    echo "3. Test from frontend: http://16.146.148.184:3000"
    echo "4. When ready, flip feature flags:"
    echo "   - RAG_ENABLE_OBS=1 (turn on observability)"
    echo "   - RAG_USE_MOCK_*=0 (use real backends)"
else
    echo
    echo -e "${YELLOW}============================================================================${NC}"
    echo -e "${YELLOW}⚠️  SOME TESTS FAILED - Review output above${NC}"
    echo -e "${YELLOW}============================================================================${NC}"
    echo
    echo "Debugging commands:"
    echo "  docker logs rag-api-v1 --tail 50"
    echo "  curl http://localhost:8080/live | jq"
    echo "  curl http://localhost:8080/ready | jq"
    echo "  docker exec -it rag-api-v1 bash"
    exit 1
fi

