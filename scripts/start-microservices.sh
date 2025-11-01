#!/bin/bash
# Microservices Startup Script for RAG Lab

set -e

echo "🚀 RAG Lab Microservices Startup"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker is running${NC}"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ docker-compose not found. Please install it first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ docker-compose is available${NC}"
echo ""

# Check for vault path
if [ -z "$VAULT_PATH" ]; then
    echo -e "${YELLOW}⚠️  VAULT_PATH not set. Using /tmp as default.${NC}"
    echo -e "${YELLOW}   Set it with: export VAULT_PATH=/path/to/your/vault${NC}"
    export VAULT_PATH="/tmp"
else
    echo -e "${GREEN}✅ VAULT_PATH: $VAULT_PATH${NC}"
fi

echo ""
echo "📋 Starting microservices..."
echo ""

# Stop any existing services
echo "🛑 Stopping existing services..."
docker-compose -f docker-compose.microservices.yml down 2>/dev/null || true

echo ""
echo "🏗️  Building and starting services..."
echo ""

# Start services
docker-compose -f docker-compose.microservices.yml up -d --build

echo ""
echo "⏳ Waiting for services to be healthy..."
echo ""

# Wait for services
sleep 10

# Check service health
services=(
    "api-gateway:8000"
    "ingest-service:8001"
    "search-service:8002"
    "chat-service:8003"
    "docling-service:8004"
    "vector-db:8005"
    "embedding-service:8006"
    "graph-service:8007"
)

all_healthy=true

for service in "${services[@]}"; do
    IFS=':' read -r name port <<< "$service"

    if curl -s -f "http://localhost:${port}/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ ${name} (port ${port})${NC}"
    else
        echo -e "${RED}❌ ${name} (port ${port}) - not healthy${NC}"
        all_healthy=false
    fi
done

echo ""

# Check Ollama
if curl -s -f "http://localhost:11434/api/tags" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ llm-service (Ollama) (port 11434)${NC}"
else
    echo -e "${YELLOW}⚠️  llm-service (Ollama) - not ready yet${NC}"
    echo -e "${YELLOW}   It may still be starting up. Wait a minute and check models.${NC}"
fi

echo ""

if [ "$all_healthy" = true ]; then
    echo -e "${GREEN}✅ All services are healthy!${NC}"
else
    echo -e "${YELLOW}⚠️  Some services are not healthy. Check logs with:${NC}"
    echo -e "${YELLOW}   docker-compose -f docker-compose.microservices.yml logs${NC}"
fi

echo ""
echo "📊 Service URLs:"
echo "=================================="
echo -e "  API Gateway:         ${GREEN}http://localhost:8000${NC}"
echo -e "  Web UI:              ${GREEN}http://localhost:5555${NC}"
echo ""
echo "  Ingest Service:      http://localhost:8001/health"
echo "  Search Service:      http://localhost:8002/health"
echo "  Chat Service:        http://localhost:8003/health"
echo "  Docling Service:     http://localhost:8004/health"
echo "  Vector DB:           http://localhost:8005/health"
echo "  Embedding Service:   http://localhost:8006/health"
echo "  Graph Service:       http://localhost:8007/health"
echo "  Ollama LLM:          http://localhost:11434/api/tags"
echo ""

echo "📖 Next Steps:"
echo "=================================="
echo "1. Pull Ollama models:"
echo "   docker exec -it rag-llm-service ollama pull nomic-embed-text"
echo "   docker exec -it rag-llm-service ollama pull llama3.2:3b"
echo ""
echo "2. Open the Web UI:"
echo -e "   ${GREEN}http://localhost:5555${NC}"
echo ""
echo "3. Upload a document:"
echo "   curl -X POST http://localhost:8000/api/upload -F \"file=@document.pdf\""
echo ""
echo "4. Monitor services:"
echo "   curl http://localhost:8000/services | jq ."
echo ""
echo "5. View logs:"
echo "   docker-compose -f docker-compose.microservices.yml logs -f"
echo ""
echo "6. View metrics:"
echo "   curl http://localhost:8000/metrics | jq ."
echo ""

echo -e "${GREEN}✅ RAG Lab is ready!${NC}"
echo ""

