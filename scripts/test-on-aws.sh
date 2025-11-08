#!/bin/bash
# Run this script ON THE AWS INSTANCE (not locally!)
# Tests the frontend integration using Docker containers

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "Frontend Integration Tests (Port 3000)"
echo "Running on AWS instance"
echo "=========================================="
echo ""

# Test 1: Run Python frontend integration tests in Docker
echo -e "${YELLOW}Running frontend integration tests...${NC}"
docker run --rm \
  --network rag_lab_rag-network \
  -v $(pwd)/tests:/tests \
  -e FRONTEND=http://frontend:80 \
  python:3.11-slim \
  bash -c "pip install -q requests && python /tests/frontend_integration/test_frontdoor.py"

TEST_EXIT=$?

if [ $TEST_EXIT -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
else
    echo ""
    echo -e "${RED}❌ TESTS FAILED!${NC}"
    exit 1
fi

echo ""
echo "=========================================="
echo "Next: Test in browser manually"
echo "  Open: http://16.146.148.184:3000"
echo "  Ask: 'What is RAG?'"
echo "  Verify: No 502 errors"
echo "=========================================="

