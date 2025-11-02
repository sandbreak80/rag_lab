#!/bin/bash
# Integration tests for React UI + Backend using curl

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:5173"
API_URL="http://localhost:5555"

PASSED=0
FAILED=0

test_result() {
    local name="$1"
    local status="$2"
    local details="$3"
    
    if [ "$status" = "pass" ]; then
        echo -e "${GREEN}✅${NC} $name"
        [ -n "$details" ] && echo -e "   $details"
        ((PASSED++))
    else
        echo -e "${RED}❌${NC} $name"
        [ -n "$details" ] && echo -e "   ${RED}$details${NC}"
        ((FAILED++))
    fi
}

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}React UI + Backend Integration Tests${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# Test 1: React UI loads
echo -e "${YELLOW}[1/10]${NC} Testing React UI..."
if curl -s "$BASE_URL" | grep -q "Neural Vault"; then
    test_result "React UI loads" "pass" "Status: 200"
else
    test_result "React UI loads" "fail" "Failed to load"
fi
echo ""

# Test 2: API health check
echo -e "${YELLOW}[2/10]${NC} Testing API health..."
RESPONSE=$(curl -s "$API_URL/health")
if echo "$RESPONSE" | grep -q "ok"; then
    test_result "API health check" "pass" "$RESPONSE"
else
    test_result "API health check" "fail" "$RESPONSE"
fi
echo ""

# Test 3: Stats endpoint
echo -e "${YELLOW}[3/10]${NC} Testing stats endpoint..."
RESPONSE=$(curl -s "$API_URL/api/stats")
if echo "$RESPONSE" | grep -q "chunks"; then
    CHUNKS=$(echo "$RESPONSE" | grep -o '"chunks":[0-9]*' | cut -d':' -f2)
    DOCS=$(echo "$RESPONSE" | grep -o '"documents":[0-9]*' | cut -d':' -f2)
    NODES=$(echo "$RESPONSE" | grep -o '"knowledge_graph_nodes":[0-9]*' | cut -d':' -f2)
    test_result "Stats endpoint" "pass" "Chunks: $CHUNKS, Docs: $DOCS, Nodes: $NODES"
else
    test_result "Stats endpoint" "fail" "$RESPONSE"
fi
echo ""

# Test 4: UI proxy to backend
echo -e "${YELLOW}[4/10]${NC} Testing UI → API proxy..."
RESPONSE=$(curl -s "$BASE_URL/api/stats")
if echo "$RESPONSE" | grep -q "chunks"; then
    test_result "UI → API proxy" "pass" "Proxy working correctly"
else
    test_result "UI → API proxy" "fail" "$RESPONSE"
fi
echo ""

# Test 5: Documents list
echo -e "${YELLOW}[5/10]${NC} Testing documents endpoint..."
RESPONSE=$(curl -s "$API_URL/api/documents")
if echo "$RESPONSE" | grep -q "documents"; then
    DOC_COUNT=$(echo "$RESPONSE" | grep -o '"documents":\[' | wc -l)
    test_result "Documents list" "pass" "Endpoint responding"
else
    test_result "Documents list" "fail" "$RESPONSE"
fi
echo ""

# Test 6: Models endpoint
echo -e "${YELLOW}[6/10]${NC} Testing models endpoint..."
RESPONSE=$(curl -s "$API_URL/api/models")
if echo "$RESPONSE" | grep -q "models"; then
    test_result "Models endpoint" "pass" "Models list available"
else
    test_result "Models endpoint" "fail" "$RESPONSE"
fi
echo ""

# Test 7: Presets endpoint
echo -e "${YELLOW}[7/10]${NC} Testing presets endpoint..."
RESPONSE=$(curl -s "$API_URL/api/presets")
if echo "$RESPONSE" | grep -q "name"; then
    test_result "Presets endpoint" "pass" "Presets available"
else
    test_result "Presets endpoint" "fail" "$RESPONSE"
fi
echo ""

# Test 8: Vector DB
echo -e "${YELLOW}[8/10]${NC} Testing Vector DB..."
RESPONSE=$(curl -s "http://localhost:8005/health")
if echo "$RESPONSE" | grep -q "healthy"; then
    test_result "Vector DB connection" "pass" "ChromaDB healthy"
else
    test_result "Vector DB connection" "fail" "$RESPONSE"
fi
echo ""

# Test 9: Knowledge Graph
echo -e "${YELLOW}[9/10]${NC} Testing Knowledge Graph..."
RESPONSE=$(curl -s "http://localhost:8007/health")
if echo "$RESPONSE" | grep -q "healthy\|ok"; then
    test_result "Knowledge Graph service" "pass" "Graph service responding"
else
    test_result "Knowledge Graph service" "fail" "$RESPONSE"
fi
echo ""

# Test 10: Search Service
echo -e "${YELLOW}[10/10]${NC} Testing Search Service..."
RESPONSE=$(curl -s "http://localhost:8002/health")
if curl -s "http://localhost:8002/health" > /dev/null 2>&1; then
    test_result "Search service" "pass" "Search service responding"
else
    test_result "Search service" "fail" "Service unavailable"
fi
echo ""

# Summary
TOTAL=$((PASSED + FAILED))
PERCENTAGE=$((PASSED * 100 / TOTAL))

echo -e "${BLUE}============================================================${NC}"
if [ $PERCENTAGE -eq 100 ]; then
    echo -e "${GREEN}Results: $PASSED/$TOTAL tests passed ($PERCENTAGE%)${NC}"
    echo -e "${GREEN}🎉 All tests passed! Full stack is working!${NC}"
elif [ $PERCENTAGE -ge 70 ]; then
    echo -e "${YELLOW}Results: $PASSED/$TOTAL tests passed ($PERCENTAGE%)${NC}"
    echo -e "${YELLOW}⚠️  Most tests passed. Check failures above.${NC}"
else
    echo -e "${RED}Results: $PASSED/$TOTAL tests passed ($PERCENTAGE%)${NC}"
    echo -e "${RED}❌ Multiple failures. Check services are running.${NC}"
fi
echo -e "${BLUE}============================================================${NC}"
echo ""
echo -e "📱 React UI: $BASE_URL"
echo -e "🔧 Flask API: $API_URL"
echo ""

# Exit with appropriate code
[ $PERCENTAGE -eq 100 ] && exit 0 || exit 1

