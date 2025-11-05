#!/bin/bash
# Pre-QA Deployment Checklist
# Run this before deploying to QA environment

set -e

echo "=========================================="
echo "  RAG Lab - Pre-QA Deployment Checklist"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
}

fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    exit 1
}

warn() {
    echo -e "${YELLOW}⚠️  WARN${NC}: $1"
}

info() {
    echo -e "ℹ️  $1"
}

# Check 1: Build number updated
echo "1️⃣  Checking build number..."
current_build=$(grep "^BUILD_NUMBER=" BUILD_INFO | cut -d'=' -f2)
today=$(date +%Y%m%d)
build_date=$(echo $current_build | cut -d'.' -f1)

if [ "$build_date" == "$today" ]; then
    pass "Build number is current: $current_build"
else
    warn "Build number may be outdated: $current_build"
    info "Run: ./scripts/increment-build.sh"
fi
echo ""

# Check 2: All services defined
echo "2️⃣  Checking service definitions..."
services=(
    "vector-db"
    "ingest-service"
    "search-service"
    "chat-service"
    "api-gateway"
    "prompt-classifier"
    "prompt-enhancement"
    "model-router"
    "research-agent"
    "ollama"
)

for service in "${services[@]}"; do
    if docker compose config --services | grep -q "^${service}$"; then
        echo "   ✓ $service"
    else
        fail "$service not found in docker-compose.yml"
    fi
done
pass "All core services defined"
echo ""

# Check 3: Docker running
echo "3️⃣  Checking Docker..."
if ! docker info > /dev/null 2>&1; then
    fail "Docker is not running"
fi
pass "Docker is running"
echo ""

# Check 4: All services healthy
echo "4️⃣  Checking service health..."
unhealthy=0
running=$(docker ps --format "{{.Names}}" | grep "^rag-" || true)

if [ -z "$running" ]; then
    warn "No services currently running"
    info "Start services: docker compose up -d"
else
    for container in $running; do
        health=$(docker inspect --format='{{.State.Health.Status}}' $container 2>/dev/null || echo "none")
        status=$(docker inspect --format='{{.State.Status}}' $container 2>/dev/null || echo "unknown")

        if [ "$health" == "healthy" ] || ([ "$health" == "none" ] && [ "$status" == "running" ]); then
            echo "   ✓ $container"
        else
            echo "   ✗ $container ($health/$status)"
            unhealthy=$((unhealthy + 1))
        fi
    done

    if [ $unhealthy -eq 0 ]; then
        pass "All running services are healthy"
    else
        warn "$unhealthy service(s) unhealthy"
    fi
fi
echo ""

# Check 5: Test core endpoints
echo "5️⃣  Testing core endpoints..."
endpoints=(
    "http://localhost:8017/health:Prompt Classifier"
    "http://localhost:8012/health:Prompt Enhancement"
    "http://localhost:8018/health:Model Router"
    "http://localhost:8015/health:Research Agent"
    "http://localhost:8000/health:API Gateway"
)

for endpoint in "${endpoints[@]}"; do
    url=$(echo $endpoint | cut -d':' -f1-3)
    name=$(echo $endpoint | cut -d':' -f4-)

    if curl -sf $url > /dev/null 2>&1; then
        # Check if build_number is in response
        response=$(curl -s $url)
        if echo "$response" | grep -q "build_number"; then
            echo "   ✓ $name (with build info)"
        else
            echo "   ✓ $name (no build info)"
        fi
    else
        echo "   ✗ $name - endpoint not responding"
        unhealthy=$((unhealthy + 1))
    fi
done

if [ $unhealthy -eq 0 ]; then
    pass "All endpoints responding"
else
    warn "Some endpoints not responding"
fi
echo ""

# Check 6: GPU available (if needed)
echo "6️⃣  Checking GPU..."
if command -v nvidia-smi &> /dev/null; then
    gpu_free=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -1)
    if [ $gpu_free -gt 1000 ]; then
        pass "GPU available with ${gpu_free}MB free"
    else
        warn "GPU has only ${gpu_free}MB free"
    fi
else
    warn "nvidia-smi not available (GPU not detected)"
fi
echo ""

# Check 7: Research agent stats
echo "7️⃣  Checking research agent..."
if curl -sf http://localhost:8015/status > /dev/null 2>&1; then
    stats=$(curl -s http://localhost:8015/status | jq -r '.stats')
    items=$(echo $stats | jq -r '.total_items // 0')
    success=$(echo $stats | jq -r '.success_rate // 0')

    if [ $items -gt 0 ]; then
        pass "Research agent has $items items ($success% success rate)"
    else
        warn "Research agent has no items ingested"
    fi
else
    warn "Research agent not responding"
fi
echo ""

# Check 8: Documentation current
echo "8️⃣  Checking documentation..."
if [ -f "docs/dev_notes/SESSION_COMPLETE_NOV_5_2025.md" ]; then
    pass "Session documentation exists"
else
    warn "Session documentation missing"
fi

if [ -f "docs/QUICK_REFERENCE.md" ]; then
    pass "Quick reference exists"
else
    warn "Quick reference missing"
fi
echo ""

# Summary
echo "=========================================="
echo "  Summary"
echo "=========================================="
echo ""
info "Build: $current_build"
info "Services: $(docker ps | grep rag- | wc -l) running"
info "GPU: $(nvidia-smi --query-gpu=memory.used --format=csv,noheader 2>/dev/null || echo 'N/A')"
echo ""

echo "📋 Pre-QA Checklist Complete!"
echo ""
echo "🚀 Ready to deploy? Run:"
echo "   docker compose down"
echo "   docker compose build"
echo "   docker compose up -d"
echo ""
echo "🧪 Run tests:"
echo "   ./scripts/test-all-services.sh"
echo ""

