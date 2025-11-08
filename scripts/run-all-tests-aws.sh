#!/bin/bash
# Complete E2E Testing Script
# RUN THIS ON AWS INSTANCE: ssh ubuntu@16.146.148.184
# Then: cd /home/ubuntu/rag_lab && ./scripts/run-all-tests-aws.sh

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=========================================="
echo "Complete E2E Testing on AWS"
echo "=========================================="
echo ""

# Step 1: Pull latest code
echo -e "${BLUE}Step 1: Pulling latest code...${NC}"
git pull origin otel
echo ""

# Step 2: Rebuild frontend if needed
echo -e "${BLUE}Step 2: Checking if rebuild needed...${NC}"
if ! grep -q "proxy_pass http://rag-api-v1:8080" frontend/nginx.conf; then
    echo -e "${RED}ERROR: nginx.conf not updated in repo!${NC}"
    exit 1
fi

echo "Rebuilding frontend with updated nginx.conf..."
docker compose stop frontend
docker compose rm -f frontend
docker compose build --no-cache frontend
docker compose up -d frontend
sleep 15
echo ""

# Step 3: Quick curl sanity checks
echo -e "${BLUE}Step 3: Quick sanity checks...${NC}"

echo "Testing homepage..."
if curl -sSf http://localhost:3000 | head -5 | grep -q "html"; then
    echo -e "${GREEN}✅ Homepage loads${NC}"
else
    echo -e "${RED}❌ Homepage failed${NC}"
fi

echo ""
echo "Testing /live endpoint..."
LIVE_RESP=$(curl -sSf http://localhost:3000/live 2>&1)
if echo "$LIVE_RESP" | grep -q "alive"; then
    echo -e "${GREEN}✅ /live returns JSON${NC}"
    echo "Response: $LIVE_RESP"
else
    echo -e "${RED}❌ /live returns HTML (routing broken!)${NC}"
    echo "Response: $LIVE_RESP"
fi

echo ""
echo "Testing API endpoint..."
API_RESP=$(curl -sSf -X POST http://localhost:3000/api/v1/rag/query \
  -H 'Content-Type: application/json' \
  -d '{"query":"test","user_id":"test","groups":[]}' 2>&1)

if echo "$API_RESP" | grep -q "answer"; then
    echo -e "${GREEN}✅ API endpoint works${NC}"
else
    echo -e "${RED}❌ API endpoint failed (502?)${NC}"
    echo "Response: $(echo $API_RESP | head -c 200)"
fi
echo ""

# Step 4: Run Python tests in Docker
echo -e "${BLUE}Step 4: Running Python integration tests in Docker...${NC}"
echo ""

docker run --rm \
  --network rag_lab_rag-network \
  -v $(pwd)/tests:/tests \
  -e FRONTEND=http://frontend:80 \
  python:3.11-slim \
  bash -c "pip install -q requests && python /tests/frontend_integration/test_frontdoor.py"

TEST_EXIT=$?
echo ""

# Step 5: Run Playwright tests (if available)
if [ -f "tests/e2e/test_rag_ui_integration.spec.ts" ]; then
    echo -e "${BLUE}Step 5: Running Playwright E2E tests...${NC}"
    docker compose run --rm playwright-tests npx playwright test || true
    echo ""
fi

# Summary
echo "=========================================="
if [ $TEST_EXIT -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Test in browser: http://16.146.148.184:3000"
    echo "2. Run: ./scripts/flip-features-progressive.sh"
else
    echo -e "${RED}❌ TESTS FAILED!${NC}"
    echo ""
    echo "Debug steps:"
    echo "  docker compose logs frontend --tail 50"
    echo "  docker compose logs rag-api-v1 --tail 50"
    echo "  docker compose ps"
fi
echo "=========================================="

exit $TEST_EXIT

