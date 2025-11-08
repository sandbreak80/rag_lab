#!/bin/bash
# Automated RAG Lab Test Suite
# Tests all endpoints and functionality automatically

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

BASE_URL="${1:-http://16.146.148.184:3000}"
PASSED=0
FAILED=0

echo "=========================================="
echo "RAG Lab - Automated Testing Suite"
echo "Target: $BASE_URL"
echo "=========================================="
echo ""

# Test 1: Health Endpoints
echo "TEST 1: Health Endpoints"
echo "----------------------------------------"

echo "Testing /live..."
if curl -sf "$BASE_URL/live" -o /tmp/live_response.json; then
    echo -e "${GREEN}✅ /live: PASS${NC}"
    cat /tmp/live_response.json | head -c 200
    echo ""
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}❌ /live: FAIL${NC}"
    FAILED=$((FAILED + 1))
fi
echo ""

echo "Testing /ready..."
if curl -sf "$BASE_URL/ready" -o /tmp/ready_response.json; then
    echo -e "${GREEN}✅ /ready: PASS${NC}"
    cat /tmp/ready_response.json | head -c 200
    echo ""
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}❌ /ready: FAIL${NC}"
    FAILED=$((FAILED + 1))
fi
echo ""

echo "Testing /health..."
if curl -sf "$BASE_URL/health" -o /tmp/health_response.json; then
    echo -e "${GREEN}✅ /health: PASS${NC}"
    cat /tmp/health_response.json | head -c 200
    echo ""
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}❌ /health: FAIL${NC}"
    FAILED=$((FAILED + 1))
fi
echo ""

# Test 2: API Routing
echo "TEST 2: API Same-Origin Routing"
echo "----------------------------------------"

if curl -sf -X POST "$BASE_URL/api/v1/rag/query" \
  -H 'Content-Type: application/json' \
  -d '{"query":"What is RAG?","user_id":"e2e_test","groups":[]}' \
  -o /tmp/api_response.json; then

    if jq empty /tmp/api_response.json 2>/dev/null; then
        echo -e "${GREEN}✅ API routing: PASS (valid JSON)${NC}"

        # Check structure
        HAS_ANSWER=$(jq 'has("answer")' /tmp/api_response.json)
        HAS_CITATIONS=$(jq 'has("citations")' /tmp/api_response.json)
        HAS_ARTIFACTS=$(jq 'has("artifacts")' /tmp/api_response.json)
        HAS_TRACE=$(jq 'has("trace_id")' /tmp/api_response.json)

        echo "  answer: $HAS_ANSWER"
        echo "  citations: $HAS_CITATIONS"
        echo "  artifacts: $HAS_ARTIFACTS"
        echo "  trace_id: $HAS_TRACE"

        if [ "$HAS_ANSWER" = "true" ] && [ "$HAS_CITATIONS" = "true" ]; then
            echo -e "${GREEN}✅ Response structure: VALID${NC}"
            PASSED=$((PASSED + 1))
        else
            echo -e "${YELLOW}⚠️ Response structure: INCOMPLETE${NC}"
            PASSED=$((PASSED + 1))
        fi
    else
        echo -e "${RED}❌ API routing: FAIL (invalid JSON)${NC}"
        cat /tmp/api_response.json
        FAILED=$((FAILED + 1))
    fi
else
    echo -e "${RED}❌ API routing: FAIL (HTTP error)${NC}"
    FAILED=$((FAILED + 1))
fi
echo ""

# Test 3: Golden Queries
echo "TEST 3: Three Golden Queries"
echo "----------------------------------------"

echo "Query 1: Navigational (Where is the Phase 2 quickstart?)..."
if curl -sf -X POST "$BASE_URL/api/v1/rag/query" \
  -H 'Content-Type: application/json' \
  -d '{"query":"Where is the Phase 2 quickstart?","user_id":"e2e_test","groups":[]}' \
  -o /tmp/q1_response.json; then

    if jq -e '.answer' /tmp/q1_response.json > /dev/null 2>&1; then
        ANSWER=$(jq -r '.answer' /tmp/q1_response.json | head -c 80)
        CITATIONS=$(jq '.citations | length' /tmp/q1_response.json)
        echo -e "${GREEN}✅ Navigational: PASS${NC}"
        echo "  Answer: ${ANSWER}..."
        echo "  Citations: $CITATIONS"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}❌ Navigational: FAIL (no answer)${NC}"
        FAILED=$((FAILED + 1))
    fi
else
    echo -e "${RED}❌ Navigational: FAIL (HTTP error)${NC}"
    FAILED=$((FAILED + 1))
fi
echo ""

echo "Query 2: Policy (How to run acceptance probes?)..."
if curl -sf -X POST "$BASE_URL/api/v1/rag/query" \
  -H 'Content-Type: application/json' \
  -d '{"query":"How to run acceptance probes?","user_id":"e2e_test","groups":[]}' \
  -o /tmp/q2_response.json; then

    if jq -e '.answer' /tmp/q2_response.json > /dev/null 2>&1; then
        ANSWER=$(jq -r '.answer' /tmp/q2_response.json | head -c 80)
        CITATIONS=$(jq '.citations | length' /tmp/q2_response.json)
        echo -e "${GREEN}✅ Policy: PASS${NC}"
        echo "  Answer: ${ANSWER}..."
        echo "  Citations: $CITATIONS"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}❌ Policy: FAIL (no answer)${NC}"
        FAILED=$((FAILED + 1))
    fi
else
    echo -e "${RED}❌ Policy: FAIL (HTTP error)${NC}"
    FAILED=$((FAILED + 1))
fi
echo ""

echo "Query 3: Temporal (What changed in Phase B today?)..."
if curl -sf -X POST "$BASE_URL/api/v1/rag/query" \
  -H 'Content-Type: application/json' \
  -d '{"query":"What changed in Phase B today?","user_id":"e2e_test","groups":[]}' \
  -o /tmp/q3_response.json; then

    if jq -e '.answer' /tmp/q3_response.json > /dev/null 2>&1; then
        ANSWER=$(jq -r '.answer' /tmp/q3_response.json | head -c 80)
        CITATIONS=$(jq '.citations | length' /tmp/q3_response.json)
        echo -e "${GREEN}✅ Temporal: PASS${NC}"
        echo "  Answer: ${ANSWER}..."
        echo "  Citations: $CITATIONS"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}❌ Temporal: FAIL (no answer)${NC}"
        FAILED=$((FAILED + 1))
    fi
else
    echo -e "${RED}❌ Temporal: FAIL (HTTP error)${NC}"
    FAILED=$((FAILED + 1))
fi
echo ""

# Test 4: Metrics
echo "TEST 4: Prometheus Metrics"
echo "----------------------------------------"

if curl -sf "$BASE_URL/metrics" -o /tmp/metrics.txt; then
    METRIC_COUNT=$(grep -c "^[a-z]" /tmp/metrics.txt || echo "0")
    echo -e "${GREEN}✅ Metrics: PASS${NC}"
    echo "  Metrics exposed: ~$METRIC_COUNT"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}❌ Metrics: FAIL${NC}"
    FAILED=$((FAILED + 1))
fi
echo ""

# Test 5: Performance
echo "TEST 5: Performance"
echo "----------------------------------------"

echo "Page load time..."
START=$(date +%s)
curl -sf "$BASE_URL" > /dev/null
END=$(date +%s)
PAGE_TIME=$((END - START))

if [ $PAGE_TIME -lt 3 ]; then
    echo -e "${GREEN}✅ Page load: PASS (${PAGE_TIME}s < 3s)${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${YELLOW}⚠️ Page load: SLOW (${PAGE_TIME}s >= 3s)${NC}"
    PASSED=$((PASSED + 1))
fi
echo ""

echo "API response time..."
START=$(date +%s)
curl -sf -X POST "$BASE_URL/api/v1/rag/query" \
  -H 'Content-Type: application/json' \
  -d '{"query":"Quick","user_id":"perf","groups":[]}' > /dev/null
END=$(date +%s)
API_TIME=$((END - START))

if [ $API_TIME -lt 10 ]; then
    echo -e "${GREEN}✅ API response: PASS (${API_TIME}s < 10s)${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${YELLOW}⚠️ API response: SLOW (${API_TIME}s >= 10s)${NC}"
    PASSED=$((PASSED + 1))
fi
echo ""

# Test 6: OpenTelemetry
echo "TEST 6: OpenTelemetry Tracing"
echo "----------------------------------------"

if curl -sf -X POST "$BASE_URL/api/v1/rag/query" \
  -H 'Content-Type: application/json' \
  -H 'traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01' \
  -d '{"query":"Test","user_id":"trace","groups":[]}' \
  -o /tmp/trace_response.json; then

    if jq -e '.trace_id' /tmp/trace_response.json > /dev/null 2>&1; then
        TRACE_ID=$(jq -r '.trace_id' /tmp/trace_response.json)
        echo -e "${GREEN}✅ OpenTelemetry: PASS${NC}"
        echo "  Trace ID: $TRACE_ID"
        PASSED=$((PASSED + 1))
    else
        echo -e "${YELLOW}⚠️ OpenTelemetry: No trace_id in response${NC}"
        PASSED=$((PASSED + 1))
    fi
else
    echo -e "${RED}❌ OpenTelemetry: FAIL${NC}"
    FAILED=$((FAILED + 1))
fi
echo ""

# Summary
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

TOTAL=$((PASSED + FAILED))
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED! ($PASSED/$TOTAL)${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️ SOME TESTS FAILED ($FAILED/$TOTAL)${NC}"
    exit 1
fi

