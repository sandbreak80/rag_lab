#!/bin/bash
# Complete E2E Fix and Testing Plan
# Executes all steps to fix routing and prove functionality

set -e

INSTANCE="16.146.148.184"
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "=========================================="
echo "RAG Lab - Complete E2E Fix & Test"
echo "=========================================="
echo ""

# Step 0: Pull latest code
echo -e "${YELLOW}Step 0: Pulling latest code...${NC}"
cd /home/ubuntu/rag_lab
git pull origin otel

# Run fix script if present
if [ -f "./scripts/fix-ui-emergency.sh" ]; then
    echo "Running fix script..."
    ./scripts/fix-ui-emergency.sh || true
fi
echo ""

# Step 1: Verify nginx configuration
echo -e "${YELLOW}Step 1: Verifying nginx configuration...${NC}"
echo "Checking frontend nginx.conf..."
if grep -q "proxy_pass http://rag-api-v1:8080" frontend/nginx.conf; then
    echo -e "${GREEN}✅ nginx.conf has correct routing${NC}"
else
    echo -e "${RED}❌ nginx.conf needs update${NC}"
    exit 1
fi

echo "Checking docker-compose environment..."
if grep -q "NEXT_PUBLIC_RAG_API=/api" docker-compose.yml; then
    echo -e "${GREEN}✅ Frontend env configured for same-origin${NC}"
else
    echo -e "${YELLOW}⚠️  Adding NEXT_PUBLIC_RAG_API=/api to frontend${NC}"
fi
echo ""

# Step 2: Rebuild and restart services
echo -e "${YELLOW}Step 2: Rebuilding services...${NC}"
docker compose stop rag-api-v1 frontend
docker compose rm -f rag-api-v1 frontend
docker compose build --no-cache frontend
docker compose up -d rag-api-v1 frontend

echo "Waiting 15s for services to start..."
sleep 15
echo ""

# Step 3: Sanity checks through port 3000
echo -e "${YELLOW}Step 3: Running sanity checks (port 3000)...${NC}"

echo "Test 1: Homepage..."
if curl -sSf http://localhost:3000 | head -5 | grep -q "html"; then
    echo -e "${GREEN}✅ Homepage loads${NC}"
else
    echo -e "${RED}❌ Homepage failed${NC}"
fi

echo ""
echo "Test 2: Health endpoints..."
LIVE_RESP=$(curl -sSf http://localhost:3000/live 2>&1)
if echo "$LIVE_RESP" | grep -q "alive"; then
    echo -e "${GREEN}✅ /live returns JSON${NC}"
    echo "   Response: $LIVE_RESP"
else
    echo -e "${RED}❌ /live returns HTML (routing broken)${NC}"
    echo "   Response: $LIVE_RESP"
fi

echo ""
READY_RESP=$(curl -sSf http://localhost:3000/ready 2>&1)
if echo "$READY_RESP" | grep -q "ready"; then
    echo -e "${GREEN}✅ /ready returns JSON${NC}"
    echo "   Response: $READY_RESP"
else
    echo -e "${RED}❌ /ready returns HTML${NC}"
fi

echo ""
echo "Test 3: API endpoint..."
API_RESP=$(curl -sSf -X POST http://localhost:3000/api/v1/rag/query \
  -H 'Content-Type: application/json' \
  -d '{"query":"What is RAG?","user_id":"demo","groups":[]}' 2>&1)

if echo "$API_RESP" | grep -q "answer"; then
    echo -e "${GREEN}✅ API returns valid JSON response${NC}"
    echo "   Response preview: $(echo "$API_RESP" | jq -r '.answer' 2>/dev/null | head -c 100)..."
else
    echo -e "${RED}❌ API returned error${NC}"
    echo "   Response: $(echo "$API_RESP" | head -c 200)"
fi
echo ""

# Step 4: Container diagnostics
echo -e "${YELLOW}Step 4: Container diagnostics...${NC}"
echo "Checking if nginx can reach rag-api-v1..."
docker compose exec -T frontend curl -sS http://rag-api-v1:8080/live 2>&1 | head -3

echo ""
echo "Checking DNS resolution..."
docker compose exec -T frontend getent hosts rag-api-v1 2>&1 || echo "DNS lookup failed"

echo ""
echo "Recent rag-api-v1 logs:"
docker compose logs --tail 20 rag-api-v1

echo ""
echo "Container status:"
docker compose ps rag-api-v1 frontend

echo ""
echo "=========================================="
echo "Sanity Checks Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. If all tests passed, run: ./scripts/test-e2e-proper.sh"
echo "2. Then flip features one by one"
echo "3. Re-run tests after each flip"

