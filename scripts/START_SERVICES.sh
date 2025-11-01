#!/bin/bash

# Start All RAG Lab Microservices
# Includes: Knowledge Graph, Re-ranker, Entity Extraction

echo "🚀 Starting RAG Lab Microservices..."
echo ""

# Start all services
docker-compose -f docker-compose.test.yml up -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 15

echo ""
echo "🔍 Checking service health..."

services=(
    "8001:ingest-service"
    "8002:search-service"
    "8003:chat-service"
    "8004:docling-service"
    "8005:vector-db"
    "8006:embedding-service"
    "8007:knowledge-graph"
    "8008:reranker"
    "5555:webapp"
)

all_healthy=true
for service in "${services[@]}"; do
    port="${service%%:*}"
    name="${service#*:}"
    
    if curl -s -f http://localhost:$port/health > /dev/null 2>&1; then
        echo "✅ $name ($port)"
    else
        echo "❌ $name ($port) - Not healthy"
        all_healthy=false
    fi
done

echo ""
if [ "$all_healthy" = true ]; then
    echo "✅ All services are healthy!"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Build BM25 index:"
    echo "      curl -X POST http://localhost:8002/index/build"
    echo ""
    echo "   2. Build knowledge graph:"
    echo "      curl -X POST http://localhost:8007/build"
    echo ""
    echo "   3. Access web UI:"
    echo "      http://localhost:5555"
    echo ""
    echo "   4. View metrics:"
    echo "      for port in 8001 8002 8003 8004 8005 8006 8007 8008; do"
    echo "        echo \"Port \$port:\""
    echo "        curl -s http://localhost:\$port/metrics | jq ."
    echo "      done"
else
    echo "⚠️  Some services are not healthy. Check logs:"
    echo "   docker-compose -f docker-compose.test.yml logs [service-name]"
fi
