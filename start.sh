#!/bin/bash
# Neural Vault RAG Lab - Start Script
# Starts all services in the correct order with health checks

set -e

echo "════════════════════════════════════════════════════════════════"
echo "  🚀 Neural Vault RAG Lab - Startup"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Configuration
COMPOSE_FILE="docker-compose.test.yml"
ENV_FILE="config.env"

# Check if config.env exists
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Error: $ENV_FILE not found!"
    echo "   Please create it from config.env template"
    exit 1
fi

# Check if Ollama is running (required for embeddings and LLM)
echo "🔍 Checking prerequisites..."
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Warning: Ollama not detected at localhost:11434"
    echo "   Make sure Ollama is running with required models:"
    echo "   - llama3.2:3b (chat)"
    echo "   - nomic-embed-text (embeddings)"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ Ollama detected"
fi

echo ""
echo "📦 Starting services..."
echo ""

# Stop any existing containers
docker-compose -f $COMPOSE_FILE down 2>/dev/null || true

# Start services
docker-compose -f $COMPOSE_FILE up -d

echo ""
echo "⏳ Waiting for services to initialize (30 seconds)..."
sleep 30

echo ""
echo "🔍 Health Check..."
echo ""

# Function to check service health
check_service() {
    local name=$1
    local url=$2
    local status=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    
    if [ "$status" = "200" ]; then
        echo "   ✅ $name"
        return 0
    else
        echo "   ❌ $name (HTTP $status)"
        return 1
    fi
}

# Check all services
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
echo "📊 System Status:"
docker-compose -f $COMPOSE_FILE ps --format "table {{.Service}}\t{{.Status}}" | head -20

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  ✅ Neural Vault RAG Lab - Ready!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "🌐 Access Points:"
echo "   API Gateway:  http://localhost:8000"
echo "   React UI:     http://localhost:5173"
echo "   Metrics:      http://localhost:8011"
echo ""
echo "📖 Quick Commands:"
echo "   View logs:    docker-compose -f $COMPOSE_FILE logs -f [service]"
echo "   Stop all:     ./stop.sh"
echo "   Restart:      ./restart.sh"
echo "   Rebuild:      ./rebuild.sh"
echo ""
echo "🧪 Test the system:"
echo '   curl -X POST http://localhost:8000/api/ask \'
echo '     -H "Content-Type: application/json" \'
echo '     -d '"'"'{"query":"What is RAG?","topK":5}'"'"
echo ""
