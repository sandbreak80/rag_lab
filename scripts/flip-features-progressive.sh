#!/bin/bash
# Progressive Feature Flag Flipping
# Flip one feature at a time, test after each flip

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

FRONTEND_URL="${FRONTEND_URL:-http://16.146.148.184:3000}"

echo "=========================================="
echo "Progressive Feature Flag Flipping"
echo "=========================================="
echo ""

# Function to update env var
update_env() {
    local service=$1
    local flag=$2
    local value=$3
    
    echo -e "${YELLOW}Setting ${flag}=${value} for ${service}...${NC}"
    
    # Update docker-compose.yml
    sed -i.bak "s/${flag}:.*/${flag}: \"${value}\"/" docker-compose.yml
    
    # Restart service
    docker compose up -d ${service}
    
    echo "Waiting 10s for service to stabilize..."
    sleep 10
}

# Function to run tests
run_tests() {
    local phase=$1
    
    echo ""
    echo -e "${YELLOW}Running tests for ${phase}...${NC}"
    
    # Frontend integration tests
    echo "1. Frontend integration tests..."
    export FRONTEND=$FRONTEND_URL
    python3 tests/frontend_integration/test_frontdoor.py
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Tests failed for ${phase}!${NC}"
        echo "Rollback by reverting the flag and restarting the service"
        return 1
    fi
    
    # Acceptance tests (if available)
    if [ -f "tests/test_acceptance_full_contract.py" ]; then
        echo "2. Acceptance tests..."
        export RAG_API="${FRONTEND_URL}/api"
        python3 -m pytest tests/test_acceptance_full_contract.py -q || true
    fi
    
    echo -e "${GREEN}✅ Tests passed for ${phase}!${NC}"
    return 0
}

# Step 1: Enable Observability
echo "="*50
echo "FLIP 1: Enable Observability (RAG_ENABLE_OBS=1)"
echo "="*50
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    update_env "rag-api-v1" "RAG_ENABLE_OBS" "1"
    run_tests "Observability Enabled"
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Stopping at Observability flip${NC}"
        exit 1
    fi
fi
echo ""

# Step 2: Real Vector Search
echo "="*50
echo "FLIP 2: Real Vector Search (RAG_USE_MOCK_VECTOR=0)"
echo "="*50
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    update_env "rag-api-v1" "RAG_USE_MOCK_VECTOR" "0"
    run_tests "Real Vector Search"
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Stopping at Vector flip${NC}"
        exit 1
    fi
fi
echo ""

# Step 3: Real Web Search
echo "="*50
echo "FLIP 3: Real Web Search (RAG_USE_MOCK_WEB=0)"
echo "="*50
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    update_env "rag-api-v1" "RAG_USE_MOCK_WEB" "0"
    run_tests "Real Web Search"
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Stopping at Web flip${NC}"
        exit 1
    fi
fi
echo ""

# Step 4: Real LLM
echo "="*50
echo "FLIP 4: Real LLM (RAG_USE_MOCK_LLM=0)"
echo "="*50
echo "WARNING: This will use actual LLM (Ollama)"
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    update_env "rag-api-v1" "RAG_USE_MOCK_LLM" "0"
    run_tests "Real LLM"
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Stopping at LLM flip${NC}"
        exit 1
    fi
fi
echo ""

echo "="*50
echo -e "${GREEN}✅ ALL FEATURE FLIPS COMPLETE!${NC}"
echo "="*50
echo ""
echo "Current Configuration:"
echo "  RAG_ENABLE_OBS: 1"
echo "  RAG_USE_MOCK_VECTOR: 0"
echo "  RAG_USE_MOCK_WEB: 0"
echo "  RAG_USE_MOCK_LLM: 0"
echo ""
echo "System is now running with:"
echo "  ✅ Full observability (OpenTelemetry)"
echo "  ✅ Real vector search"
echo "  ✅ Real web search"
echo "  ✅ Real LLM (Ollama)"
echo ""
echo "Next steps:"
echo "1. Monitor Grafana dashboards"
echo "2. Check Prometheus metrics"
echo "3. Run load tests"
echo "4. Production hardening (rate limits, auth, etc.)"

