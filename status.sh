#!/bin/bash

# Neural Vault RAG Lab - Status Check
# Shows current status of all services

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}   Neural Vault RAG Lab - System Status${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"

# Function to check service health
check_service() {
    local name=$1
    local url=$2

    echo -ne "${YELLOW}${name}${NC} "

    response=$(curl -sf "$url" 2>/dev/null)

    if [ $? -eq 0 ]; then
        # Try to extract status from JSON
        status=$(echo "$response" | jq -r '.status // "ok"' 2>/dev/null || echo "ok")

        if [ "$status" = "ok" ] || [ "$status" = "healthy" ]; then
            echo -e "${GREEN}✓ Healthy${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠ Running but unhealthy${NC}"
            return 1
        fi
    else
        echo -e "${RED}✗ Down${NC}"
        return 1
    fi
}

# Check Docker
echo -e "${PURPLE}Docker Services:${NC}"
if docker ps > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Docker daemon running${NC}\n"
else
    echo -e "${RED}✗ Docker daemon not running${NC}\n"
    exit 1
fi

# Check Ollama
echo -e "${PURPLE}Ollama:${NC}"
check_service "Ollama API          " "http://localhost:11434/api/tags"

# Check models
if curl -sf http://localhost:11434/api/tags 2>/dev/null | grep -q "llama3.2:3b"; then
    echo -e "  ${GREEN}✓ llama3.2:3b model available${NC}"
else
    echo -e "  ${RED}✗ llama3.2:3b model not found${NC}"
fi

echo ""

# Check Backend Services
echo -e "${PURPLE}Backend Services:${NC}"
check_service "API Gateway         " "http://localhost:8000/health"
check_service "Vector DB           " "http://localhost:8005/health"
check_service "Search Service      " "http://localhost:8002/health"
check_service "Chat Service        " "http://localhost:8003/health"
check_service "Embedding Service   " "http://localhost:8006/health"
check_service "Knowledge Graph     " "http://localhost:8007/health"
check_service "Reranker Service    " "http://localhost:8009/health"

echo ""

# Check Frontend
echo -e "${PURPLE}Frontend:${NC}"
check_service "React Dev Server    " "http://localhost:5173"
check_service "Production UI       " "http://localhost:3000"

echo ""

# Get stats
echo -e "${PURPLE}System Statistics:${NC}"
stats=$(curl -sf http://localhost:8000/api/stats 2>/dev/null)
if [ $? -eq 0 ]; then
    chunks=$(echo "$stats" | jq -r '.chunks // 0')
    docs=$(echo "$stats" | jq -r '.documents | length // 0')
    nodes=$(echo "$stats" | jq -r '.knowledge_graph_nodes // 0')

    echo -e "  Documents:        ${CYAN}${docs}${NC}"
    echo -e "  Chunks:           ${CYAN}${chunks}${NC}"
    echo -e "  Graph Nodes:      ${CYAN}${nodes}${NC}"
else
    echo -e "  ${RED}Unable to fetch stats${NC}"
fi

echo ""

# Docker container status
echo -e "${PURPLE}Container Details:${NC}"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(NAMES|rag-)" | head -15

echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}Access Points:${NC}"
echo -e "  ${PURPLE}React UI:${NC}       http://localhost:5173"
echo -e "  ${PURPLE}API Gateway:${NC}    http://localhost:8000"
echo -e "  ${PURPLE}Ollama:${NC}         http://localhost:11434"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"

