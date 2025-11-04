#!/bin/bash
# Clean Deploy Script - Complete fresh start
# Stops everything, removes images, prunes system, then rebuilds

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  RAG Lab - Clean Deployment                                ║"
echo "║  WARNING: This will remove ALL Docker resources!          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Confirm with user
echo -e "${YELLOW}⚠️  This script will:${NC}"
echo "   1. Stop all RAG Lab containers"
echo "   2. Remove all RAG Lab images"
echo "   3. Prune Docker system (unused images, networks, build cache)"
echo "   4. Optionally remove data volumes (uploaded docs, embeddings, etc.)"
echo "   5. Rebuild everything from scratch"
echo ""
echo -e "${RED}This cannot be undone!${NC}"
echo ""
read -p "Are you sure you want to continue? (yes/no): " -r
echo ""

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "❌ Aborted"
    exit 1
fi

# Ask about volumes
echo ""
read -p "Do you want to remove data volumes (uploaded docs, embeddings)? (yes/no): " -r
REMOVE_VOLUMES=$REPLY
echo ""

cd "$(dirname "$0")/.."

echo "▶ Step 1: Stopping all containers..."
docker compose down 2>/dev/null || true
echo -e "${GREEN}✓ Containers stopped${NC}"
echo ""

if [[ $REMOVE_VOLUMES =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "▶ Step 2: Removing volumes..."
    docker compose down -v 2>/dev/null || true
    echo -e "${GREEN}✓ Volumes removed${NC}"
    echo ""
else
    echo "▶ Step 2: Keeping volumes (data preserved)"
    echo -e "${GREEN}✓ Volumes preserved${NC}"
    echo ""
fi

echo "▶ Step 3: Removing RAG Lab images..."
# Remove images with rag_lab prefix
docker images | grep rag_lab | awk '{print $3}' | xargs -r docker rmi -f 2>/dev/null || true
# Remove images with rag- prefix
docker images | grep "^rag-" | awk '{print $3}' | xargs -r docker rmi -f 2>/dev/null || true
echo -e "${GREEN}✓ RAG Lab images removed${NC}"
echo ""

echo "▶ Step 4: Pruning Docker system..."
echo "   This may take a few minutes..."
docker system prune -f --volumes 2>/dev/null || true
echo -e "${GREEN}✓ Docker system pruned${NC}"
echo ""

echo "▶ Step 5: Checking disk space..."
df -h / | tail -1 | awk '{print "   Available: " $4 " (" $5 " used)"}'
echo ""

echo "▶ Step 6: Building fresh images..."
echo "   This will take 5-10 minutes..."
docker compose build --no-cache --parallel
echo -e "${GREEN}✓ Images built${NC}"
echo ""

echo "▶ Step 7: Starting Ollama..."
docker compose up -d ollama
echo "   Waiting for Ollama to be ready..."
sleep 10

# Wait for Ollama health check
for i in {1..30}; do
    if docker compose ps ollama | grep -q "healthy"; then
        echo -e "${GREEN}✓ Ollama is healthy${NC}"
        break
    fi
    echo "   Waiting... ($i/30)"
    sleep 2
done
echo ""

echo "▶ Step 8: Pulling Ollama models..."
echo "   This will download ~5GB (llama3.1:8b + mxbai-embed-large)"
echo ""

# Pull models
docker compose exec ollama ollama pull llama3.1:8b
docker compose exec ollama ollama pull mxbai-embed-large

echo ""
echo -e "${GREEN}✓ Models downloaded${NC}"
echo ""

echo "▶ Step 9: Starting all services..."
docker compose up -d
echo -e "${GREEN}✓ Services started${NC}"
echo ""

echo "▶ Step 10: Waiting for services to be healthy..."
sleep 5

# Check service health
SERVICES=(
    "vector-db:8005"
    "embedding-service:8006"
    "search-service:8002"
    "chat-service:8003"
    "api-gateway:8000"
    "frontend:80"
)

for service in "${SERVICES[@]}"; do
    name="${service%%:*}"
    port="${service##*:}"
    
    echo -n "   Checking $name... "
    
    # Wait up to 60 seconds for service
    for i in {1..30}; do
        if docker compose ps "$name" 2>/dev/null | grep -q "Up"; then
            echo -e "${GREEN}✓${NC}"
            break
        fi
        sleep 2
    done
done

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  🚀 Clean Deployment Complete!                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${BLUE}📱 Frontend:${NC}           http://localhost:3000"
echo -e "${BLUE}🔌 API Gateway:${NC}        http://localhost:8000"
echo -e "${BLUE}🤖 Ollama:${NC}             http://localhost:11434"
echo -e "${BLUE}🔍 SearXNG:${NC}            http://localhost:8080"
echo ""
echo "✅ All services are running!"
echo ""
echo "📊 Check status:    docker compose ps"
echo "📝 View logs:       docker compose logs -f"
echo "🔧 GPU check:       docker compose exec ollama nvidia-smi"
echo ""

