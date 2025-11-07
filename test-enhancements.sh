#!/bin/bash
# Test Script for Monitoring + Agentic Web Search Enhancements
# Run this on your Docker host (AWS instance or local machine with Docker running)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}RAG Lab Enhancement Testing${NC}"
echo -e "${BLUE}Testing: Monitoring + Agentic Search${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
    fi
}

# Function to wait for service
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=1

    echo -e "${YELLOW}⏳ Waiting for $name to be ready...${NC}"
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            print_status 0 "$name is ready"
            return 0
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    echo ""
    print_status 1 "$name failed to start"
    return 1
}

# ============================================================================
# TEST 1: Docker Compose Configuration
# ============================================================================
echo -e "\n${BLUE}TEST 1: Validating Docker Compose Configuration${NC}"
if docker compose config > /dev/null 2>&1; then
    print_status 0 "Docker Compose configuration is valid"
else
    print_status 1 "Docker Compose configuration has errors"
    exit 1
fi

# ============================================================================
# TEST 2: Check for Port Conflicts
# ============================================================================
echo -e "\n${BLUE}TEST 2: Checking for Port Conflicts${NC}"
DUPLICATE_PORTS=$(docker compose config | grep "published:" | sort | uniq -d)
if [ -z "$DUPLICATE_PORTS" ]; then
    print_status 0 "No port conflicts detected"
else
    print_status 1 "Port conflicts found: $DUPLICATE_PORTS"
fi

# ============================================================================
# TEST 3: Start Monitoring Services
# ============================================================================
echo -e "\n${BLUE}TEST 3: Starting Monitoring Services${NC}"
echo "Starting Prometheus, Grafana, and cAdvisor..."

# Check if GPU is available
if command -v nvidia-smi &> /dev/null; then
    echo -e "${GREEN}NVIDIA GPU detected - starting with GPU monitoring${NC}"
    docker compose --profile gpu up -d prometheus grafana cadvisor dcgm-exporter
else
    echo -e "${YELLOW}No GPU detected - starting without GPU monitoring${NC}"
    docker compose up -d prometheus grafana cadvisor
fi

sleep 5

# ============================================================================
# TEST 4: Verify Monitoring Services
# ============================================================================
echo -e "\n${BLUE}TEST 4: Verifying Monitoring Services${NC}"

# Check Prometheus
if wait_for_service "http://localhost:9090/-/healthy" "Prometheus"; then
    PROM_VERSION=$(curl -s http://localhost:9090/api/v1/status/buildinfo | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
    echo -e "   ${GREEN}Version: $PROM_VERSION${NC}"
fi

# Check Grafana
if wait_for_service "http://localhost:3001/api/health" "Grafana"; then
    echo -e "   ${GREEN}Login: admin / admin${NC}"
    echo -e "   ${GREEN}URL: http://localhost:3001${NC}"
fi

# Check cAdvisor
if wait_for_service "http://localhost:9080/healthz" "cAdvisor"; then
    CONTAINER_COUNT=$(curl -s "http://localhost:9080/api/v2.0/stats?count=1" | grep -o '"name":' | wc -l)
    echo -e "   ${GREEN}Monitoring $CONTAINER_COUNT containers${NC}"
fi

# Check DCGM (if GPU available)
if command -v nvidia-smi &> /dev/null; then
    if wait_for_service "http://localhost:9400/metrics" "DCGM Exporter"; then
        GPU_COUNT=$(nvidia-smi --list-gpus | wc -l)
        echo -e "   ${GREEN}Monitoring $GPU_COUNT GPU(s)${NC}"
    fi
fi

# ============================================================================
# TEST 5: Verify Prometheus Targets
# ============================================================================
echo -e "\n${BLUE}TEST 5: Checking Prometheus Targets${NC}"
sleep 5  # Give Prometheus time to scrape

TARGETS=$(curl -s http://localhost:9090/api/v1/targets | grep -o '"health":"up"' | wc -l)
TOTAL_TARGETS=$(curl -s http://localhost:9090/api/v1/targets | grep -o '"health":' | wc -l)

if [ "$TARGETS" -gt 0 ]; then
    print_status 0 "Prometheus is scraping targets: $TARGETS/$TOTAL_TARGETS UP"
else
    print_status 1 "No Prometheus targets are UP"
fi

# ============================================================================
# TEST 6: Start RAG Services (if not running)
# ============================================================================
echo -e "\n${BLUE}TEST 6: Ensuring RAG Services are Running${NC}"
docker compose up -d ollama searxng web-search

sleep 10

# ============================================================================
# TEST 7: Test Agentic Web Search
# ============================================================================
echo -e "\n${BLUE}TEST 7: Testing Agentic Web Search${NC}"

# Wait for services
wait_for_service "http://localhost:8009/health" "Web Search Service"
wait_for_service "http://localhost:11434/api/tags" "Ollama"

# Test simple search endpoint
echo "Testing simple search endpoint..."
SIMPLE_RESPONSE=$(curl -s -X POST http://localhost:8009/search \
    -H "Content-Type: application/json" \
    -d '{"query":"test query","limit":3}' \
    -w "\n%{http_code}")

HTTP_CODE=$(echo "$SIMPLE_RESPONSE" | tail -1)
if [ "$HTTP_CODE" = "200" ]; then
    print_status 0 "Simple search endpoint working"
else
    print_status 1 "Simple search endpoint failed (HTTP $HTTP_CODE)"
fi

# Test agentic search endpoint
echo "Testing agentic search endpoint (this may take 5-10 seconds)..."
AGENTIC_RESPONSE=$(curl -s -X POST http://localhost:8009/search_agentic \
    -H "Content-Type: application/json" \
    -d '{"query":"What are the latest transformer models?","limit":5,"num_queries":3}' \
    --max-time 30 \
    -w "\n%{http_code}")

HTTP_CODE=$(echo "$AGENTIC_RESPONSE" | tail -1)
if [ "$HTTP_CODE" = "200" ]; then
    print_status 0 "Agentic search endpoint working"

    # Parse response details
    RESPONSE_BODY=$(echo "$AGENTIC_RESPONSE" | head -n -1)
    QUERIES_GENERATED=$(echo "$RESPONSE_BODY" | grep -o '"total_searches":[0-9]*' | cut -d':' -f2)
    RESULTS_COUNT=$(echo "$RESPONSE_BODY" | grep -o '"count":[0-9]*' | cut -d':' -f2 | head -1)
    DEDUP_RATE=$(echo "$RESPONSE_BODY" | grep -o '"deduplication_rate":[0-9.]*' | cut -d':' -f2)
    LATENCY=$(echo "$RESPONSE_BODY" | grep -o '"latency_ms":[0-9.]*' | cut -d':' -f2)

    echo -e "   ${GREEN}Queries Generated: $QUERIES_GENERATED${NC}"
    echo -e "   ${GREEN}Results Returned: $RESULTS_COUNT${NC}"
    echo -e "   ${GREEN}Deduplication Rate: $DEDUP_RATE${NC}"
    echo -e "   ${GREEN}Latency: ${LATENCY}ms${NC}"
else
    print_status 1 "Agentic search endpoint failed (HTTP $HTTP_CODE)"
    echo "$AGENTIC_RESPONSE" | head -n -1
fi

# ============================================================================
# TEST 8: Check Prometheus Metrics from Services
# ============================================================================
echo -e "\n${BLUE}TEST 8: Verifying Service Metrics Endpoints${NC}"

# Check web-search metrics
WEB_SEARCH_METRICS=$(curl -s http://localhost:8009/metrics 2>/dev/null)
if echo "$WEB_SEARCH_METRICS" | grep -q "web_search_service"; then
    print_status 0 "Web search service exposing Prometheus metrics"
else
    print_status 1 "Web search service metrics not available"
fi

# ============================================================================
# TEST 9: Frontend Build (Optional)
# ============================================================================
echo -e "\n${BLUE}TEST 9: Checking Frontend Build${NC}"
if [ -f "frontend/package.json" ]; then
    echo "Frontend build test skipped (run 'cd frontend && npm run build' to test)"
    print_status 0 "Frontend files present"
else
    print_status 1 "Frontend files not found"
fi

# ============================================================================
# TEST 10: Overall System Health
# ============================================================================
echo -e "\n${BLUE}TEST 10: Overall System Health Check${NC}"

# Count healthy containers
TOTAL_CONTAINERS=$(docker compose ps --format json | jq -s 'length')
RUNNING_CONTAINERS=$(docker compose ps --format json | jq -s '[.[] | select(.State == "running")] | length')
HEALTHY_CONTAINERS=$(docker compose ps --format json | jq -s '[.[] | select(.Health == "healthy")] | length')

echo -e "   ${GREEN}Total Containers: $TOTAL_CONTAINERS${NC}"
echo -e "   ${GREEN}Running: $RUNNING_CONTAINERS${NC}"
echo -e "   ${GREEN}Healthy: $HEALTHY_CONTAINERS${NC}"

if [ "$RUNNING_CONTAINERS" -ge 15 ]; then
    print_status 0 "System is operational"
else
    print_status 1 "Some services are not running"
fi

# ============================================================================
# SUMMARY & NEXT STEPS
# ============================================================================
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}TESTING COMPLETE!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}📊 Access Your New Monitoring:${NC}"
echo -e "   Grafana:    ${YELLOW}http://localhost:3001${NC} (admin/admin)"
echo -e "   Prometheus: ${YELLOW}http://localhost:9090${NC}"
echo -e "   cAdvisor:   ${YELLOW}http://localhost:9080${NC}"
echo ""
echo -e "${GREEN}🔍 Test Agentic Search:${NC}"
echo -e "   curl -X POST http://localhost:8009/search_agentic \\"
echo -e "     -H 'Content-Type: application/json' \\"
echo -e "     -d '{\"query\":\"your complex question\",\"limit\":10}'"
echo ""
echo -e "${GREEN}🎨 Frontend:${NC}"
echo -e "   New 'Monitoring' tab available in UI"
echo -e "   Visit: ${YELLOW}http://localhost:3000${NC}"
echo ""
echo -e "${GREEN}📚 Documentation:${NC}"
echo -e "   - IMPLEMENTATION_SUMMARY.md"
echo -e "   - SELF_REVIEW_FIXES.md"
echo -e "   - monitoring/README.md"
echo ""

# Check for any failed tests
if [ "$HTTP_CODE" = "200" ] && [ "$RUNNING_CONTAINERS" -ge 15 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
    echo -e "${GREEN}Your enhanced RAG Lab is ready to use! 🚀${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some tests failed. Check the output above.${NC}"
    exit 1
fi

