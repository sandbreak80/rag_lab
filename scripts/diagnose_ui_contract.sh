#!/usr/bin/env bash
set -euo pipefail

echo "=========================================="
echo "UI Contract Route Diagnostics"
echo "Testing: http://16.146.148.184:3000"
echo "=========================================="

BASE_URL="http://16.146.148.184:3000"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_route() {
    local name="$1"
    local url="$2"
    local method="${3:-GET}"
    local data="${4:-}"

    echo -n "Testing ${name}... "

    if [ "$method" = "POST" ] && [ -n "$data" ]; then
        status=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$url" 2>/dev/null || echo "000")
    else
        status=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    fi

    if [ "$status" = "200" ] || [ "$status" = "202" ]; then
        echo -e "${GREEN}✅ ${status}${NC}"
        return 0
    elif [ "$status" = "404" ]; then
        echo -e "${RED}❌ 404 (Not Found)${NC}"
        return 1
    elif [ "$status" = "501" ]; then
        echo -e "${YELLOW}⚠️  501 (Not Implemented - Expected)${NC}"
        return 0
    elif [ "$status" = "502" ] || [ "$status" = "503" ]; then
        echo -e "${RED}❌ ${status} (Service Unavailable)${NC}"
        return 1
    else
        echo -e "${YELLOW}⚠️  ${status}${NC}"
        return 0
    fi
}

echo ""
echo "=== Core API Endpoints ==="
check_route "Live" "${BASE_URL}/live"
check_route "Ready" "${BASE_URL}/ready"
check_route "Health" "${BASE_URL}/health"
check_route "Metrics" "${BASE_URL}/api/metrics"

echo ""
echo "=== RAG Query Endpoint ==="
check_route "RAG Query" "${BASE_URL}/api/v1/rag/query" "POST" '{"query":"test","user_id":"demo","groups":[]}'

echo ""
echo "=== Document Management ==="
check_route "Documents List" "${BASE_URL}/api/v1/documents"
check_route "Documents Upload" "${BASE_URL}/api/v1/documents" "POST"

echo ""
echo "=== Agent Endpoints (Stubs) ==="
check_route "Agent Start" "${BASE_URL}/api/v1/agent/start" "POST" '{"query":"test"}'

echo ""
echo "=== Monitoring Proxies ==="
check_route "Prometheus Ready" "${BASE_URL}/prom/-/ready"
check_route "Prometheus Query" "${BASE_URL}/prom/api/v1/query?query=up"
check_route "Grafana" "${BASE_URL}/graf/"

echo ""
echo "=========================================="
echo "Detailed API Response Check"
echo "=========================================="

echo ""
echo "Testing RAG Query Response Structure..."
response=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d '{"query":"What is RAG?","user_id":"demo","groups":[]}' \
    "${BASE_URL}/api/v1/rag/query" 2>/dev/null || echo "{}")

if echo "$response" | jq -e '.answer' >/dev/null 2>&1; then
    echo -e "${GREEN}✅ answer field present${NC}"
else
    echo -e "${RED}❌ answer field missing${NC}"
fi

if echo "$response" | jq -e '.citations' >/dev/null 2>&1; then
    echo -e "${GREEN}✅ citations field present${NC}"
    citation_count=$(echo "$response" | jq '.citations | length' 2>/dev/null || echo 0)
    echo "   Citations count: $citation_count"
else
    echo -e "${RED}❌ citations field missing${NC}"
fi

if echo "$response" | jq -e '.artifacts' >/dev/null 2>&1; then
    echo -e "${GREEN}✅ artifacts field present${NC}"
else
    echo -e "${RED}❌ artifacts field missing${NC}"
fi

if echo "$response" | jq -e '.metrics' >/dev/null 2>&1; then
    echo -e "${GREEN}✅ metrics field present${NC}"

    if echo "$response" | jq -e '.metrics.latency_ms' >/dev/null 2>&1; then
        latency=$(echo "$response" | jq -r '.metrics.latency_ms' 2>/dev/null)
        echo "   Latency: ${latency}ms"
    fi

    if echo "$response" | jq -e '.metrics.breakdown' >/dev/null 2>&1; then
        echo -e "${GREEN}   ✅ metrics.breakdown present${NC}"
    else
        echo -e "${YELLOW}   ⚠️  metrics.breakdown missing (add to RAG handler)${NC}"
    fi
else
    echo -e "${RED}❌ metrics field missing${NC}"
fi

if echo "$response" | jq -e '.trace_id' >/dev/null 2>&1; then
    echo -e "${GREEN}✅ trace_id field present${NC}"
else
    echo -e "${YELLOW}⚠️  trace_id field missing${NC}"
fi

if echo "$response" | jq -e '.security_status' >/dev/null 2>&1; then
    echo -e "${GREEN}✅ security_status field present${NC}"
else
    echo -e "${YELLOW}⚠️  security_status field missing${NC}"
fi

echo ""
echo "=========================================="
echo "Metrics Endpoint Check"
echo "=========================================="

metrics=$(curl -s "${BASE_URL}/api/metrics" 2>/dev/null || echo "")

if echo "$metrics" | grep -q "rag_requests_total"; then
    echo -e "${GREEN}✅ rag_requests_total present${NC}"
else
    echo -e "${RED}❌ rag_requests_total missing${NC}"
fi

if echo "$metrics" | grep -q "rag_latency"; then
    echo -e "${GREEN}✅ rag_latency metrics present${NC}"
else
    echo -e "${YELLOW}⚠️  rag_latency metrics missing${NC}"
fi

if echo "$metrics" | grep -q "llm_tokens"; then
    echo -e "${GREEN}✅ llm_tokens metrics present${NC}"
else
    echo -e "${YELLOW}⚠️  llm_tokens metrics missing${NC}"
fi

echo ""
echo "=========================================="
echo "Summary"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Review any ❌ or ⚠️  items above"
echo "2. If routes are 404, rebuild and restart services:"
echo "   docker compose up -d --build rag-api-v1 frontend"
echo "3. If metrics.breakdown is missing, update routes/rag.py"
echo "4. Run full E2E test suite:"
echo "   bash scripts/run_e2e_ci.sh"
echo ""

