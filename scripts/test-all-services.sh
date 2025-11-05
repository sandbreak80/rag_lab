#!/bin/bash
# Test all RAG Lab services
# Run this as part of QA process

set -e

echo "=========================================="
echo "  RAG Lab - Service Test Suite"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

pass_count=0
fail_count=0

test_pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    pass_count=$((pass_count + 1))
}

test_fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    fail_count=$((fail_count + 1))
}

test_start() {
    echo -e "${BLUE}🧪 TEST${NC}: $1"
}

# Test 1: Prompt Classifier
test_start "Prompt Classifier - Health Check"
if response=$(curl -sf http://localhost:8017/health); then
    if echo "$response" | jq -e '.build_number' > /dev/null 2>&1; then
        build=$(echo "$response" | jq -r '.build_number')
        test_pass "Health check OK with build $build"
    else
        test_pass "Health check OK (no build info)"
    fi
else
    test_fail "Health check failed"
fi

test_start "Prompt Classifier - Classification"
if response=$(curl -sf -X POST http://localhost:8017/classify \
    -H "Content-Type: application/json" \
    -d '{"query": "How does RAG work?"}'); then

    intent=$(echo "$response" | jq -r '.intent')
    complexity=$(echo "$response" | jq -r '.complexity')

    if [ -n "$intent" ] && [ "$intent" != "null" ]; then
        test_pass "Classification returned intent=$intent, complexity=$complexity"
    else
        test_fail "Classification returned invalid response"
    fi
else
    test_fail "Classification request failed"
fi
echo ""

# Test 2: Prompt Enhancement
test_start "Prompt Enhancement - Health Check"
if response=$(curl -sf http://localhost:8012/health); then
    if echo "$response" | jq -e '.components' > /dev/null 2>&1; then
        test_pass "Health check OK with components"
    else
        test_pass "Health check OK"
    fi
else
    test_fail "Health check failed"
fi

test_start "Prompt Enhancement - Enhancement"
if response=$(curl -sf -X POST http://localhost:8012/enhance \
    -H "Content-Type: application/json" \
    -d '{"query": "What is vector search?", "documents": []}'); then

    strategy=$(echo "$response" | jq -r '.enhancement_strategy // .strategy // "unknown"')

    if [ -n "$strategy" ] && [ "$strategy" != "null" ]; then
        test_pass "Enhancement returned strategy=$strategy"
    else
        test_fail "Enhancement returned invalid response"
    fi
else
    test_fail "Enhancement request failed"
fi
echo ""

# Test 3: Model Router
test_start "Model Router - Health Check"
if response=$(curl -sf http://localhost:8018/health); then
    models=$(echo "$response" | jq -r '.available_models | length')
    test_pass "Health check OK with $models models available"
else
    test_fail "Health check failed"
fi

test_start "Model Router - Routing"
if response=$(curl -sf -X POST http://localhost:8018/route \
    -H "Content-Type: application/json" \
    -d '{"query": "Explain neural networks", "context": {}}'); then

    model=$(echo "$response" | jq -r '.model')

    if [ -n "$model" ] && [ "$model" != "null" ]; then
        test_pass "Routing selected model=$model"
    else
        test_fail "Routing returned invalid response"
    fi
else
    test_fail "Routing request failed"
fi
echo ""

# Test 4: Research Agent
test_start "Research Agent - Health Check"
if response=$(curl -sf http://localhost:8015/health); then
    scheduler=$(echo "$response" | jq -r '.scheduler_running')
    test_pass "Health check OK, scheduler=$scheduler"
else
    test_fail "Health check failed"
fi

test_start "Research Agent - Status"
if response=$(curl -sf http://localhost:8015/status); then
    items=$(echo "$response" | jq -r '.stats.total_items')
    sources=$(echo "$response" | jq -r '.stats.active_sources')
    test_pass "Status OK: $items items from $sources sources"
else
    test_fail "Status request failed"
fi

test_start "Research Agent - Sources"
if response=$(curl -sf http://localhost:8015/sources); then
    count=$(echo "$response" | jq -r 'length')
    test_pass "Sources OK: $count sources configured"
else
    test_fail "Sources request failed"
fi
echo ""

# Test 5: Ollama
test_start "Ollama - Health Check"
if response=$(curl -sf http://localhost:11434/api/tags); then
    models=$(echo "$response" | jq -r '.models | length')
    test_pass "Ollama OK with $models models loaded"
else
    test_fail "Ollama not responding"
fi
echo ""

# Test 6: Integration Test - Full Chain
test_start "Integration - Classify → Enhance → Route"

# Step 1: Classify
query="How can I optimize my RAG system for production?"
if class_result=$(curl -sf -X POST http://localhost:8017/classify \
    -H "Content-Type: application/json" \
    -d "{\"query\": \"$query\"}"); then

    complexity=$(echo "$class_result" | jq -r '.complexity')
    echo "   Step 1: Classified as complexity=$complexity"

    # Step 2: Enhance
    if enh_result=$(curl -sf -X POST http://localhost:8012/enhance \
        -H "Content-Type: application/json" \
        -d "{\"query\": \"$query\", \"documents\": [], \"config\": {\"classification\": $class_result}}"); then

        strategy=$(echo "$enh_result" | jq -r '.enhancement_strategy // .strategy // "unknown"')
        echo "   Step 2: Enhanced with strategy=$strategy"

        # Step 3: Route
        if route_result=$(curl -sf -X POST http://localhost:8018/route \
            -H "Content-Type: application/json" \
            -d "{\"query\": \"$query\", \"context\": {}}"); then

            model=$(echo "$route_result" | jq -r '.model')
            echo "   Step 3: Routed to model=$model"

            test_pass "Full chain completed: $complexity → $strategy → $model"
        else
            test_fail "Routing step failed"
        fi
    else
        test_fail "Enhancement step failed"
    fi
else
    test_fail "Classification step failed"
fi
echo ""

# Summary
echo "=========================================="
echo "  Test Summary"
echo "=========================================="
echo ""
echo -e "${GREEN}✅ Passed: $pass_count${NC}"
echo -e "${RED}❌ Failed: $fail_count${NC}"
echo ""

if [ $fail_count -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    echo ""
    echo "✅ System is ready for QA deployment"
    exit 0
else
    echo -e "${RED}⚠️  Some tests failed!${NC}"
    echo ""
    echo "❌ Fix issues before deploying to QA"
    exit 1
fi

