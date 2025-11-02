#!/bin/bash
# Neural Vault RAG Lab - Status Script
# Shows detailed status of all services

set -e

COMPOSE_FILE="docker-compose.test.yml"

echo "════════════════════════════════════════════════════════════════"
echo "  📊 Neural Vault RAG Lab - System Status"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "🐳 Docker Services:"
docker-compose -f $COMPOSE_FILE ps --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "💾 Data Volumes:"
docker volume ls | grep "rag_lab" | awk '{printf "   %-30s %s\n", $2, ""}'

echo ""
echo "🔍 Service Health Checks:"

check_service() {
    local name=$1
    local url=$2
    local response=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null || echo "000")
    local body=$(echo "$response" | head -n -1)
    local status=$(echo "$response" | tail -n 1)
    
    if [ "$status" = "200" ]; then
        echo "   ✅ $name - Healthy"
        if echo "$body" | jq . > /dev/null 2>&1; then
            echo "$body" | jq -r '.service // .status // empty' | sed 's/^/      /'
        fi
    elif [ "$status" = "000" ]; then
        echo "   ❌ $name - Unreachable"
    else
        echo "   ⚠️  $name - HTTP $status"
    fi
}

check_service "API Gateway      " "http://localhost:8000/health"
check_service "Ingest Service   " "http://localhost:8001/health"
check_service "Search Service   " "http://localhost:8002/health"
check_service "Chat Service     " "http://localhost:8003/health"
check_service "Vector DB        " "http://localhost:8005/health"
check_service "Embedding Service" "http://localhost:8006/health"
check_service "Knowledge Graph  " "http://localhost:8007/health"
check_service "Reranker         " "http://localhost:8008/health"
check_service "Web Search       " "http://localhost:8009/health"
check_service "Metrics Store    " "http://localhost:8011/health"

echo ""
echo "📈 Quick Stats:"
curl -s http://localhost:8005/stats 2>/dev/null | jq -r 'if .total_chunks then "   Vector DB: \(.total_chunks) chunks" else empty end' || echo "   Vector DB: N/A"
curl -s http://localhost:8007/stats 2>/dev/null | jq -r 'if .nodes then "   Knowledge Graph: \(.nodes) nodes, \(.edges) edges" else empty end' || echo "   Knowledge Graph: N/A"
curl -s http://localhost:8011/stats 2>/dev/null | jq -r 'if .total_queries then "   Metrics: \(.total_queries) queries tracked" else empty end' || echo "   Metrics: N/A"

echo ""
echo "🌐 Access Points:"
echo "   API Gateway:  http://localhost:8000"
echo "   React UI:     http://localhost:5173"
echo "   Old UI:       http://localhost:5555"
echo "   Metrics:      http://localhost:8011"
echo ""
