#!/bin/bash
# Rebuild and restart rag-api-v1 with latest code
# This ensures code changes are picked up

set -e

echo "🔨 Rebuilding rag-api-v1 with latest code..."
echo ""

# Pull latest code first
echo "📥 Pulling latest code..."
git pull github otel || git pull origin otel

echo ""
echo "🔨 Building rag-api-v1..."
docker compose build rag-api-v1

echo ""
echo "🔄 Restarting rag-api-v1 with new image..."
docker compose up -d rag-api-v1

echo ""
echo "⏳ Waiting for service to start..."
sleep 5

echo ""
echo "✅ Rebuild complete!"
echo ""
echo "Check logs to verify new code is running:"
echo "  docker compose logs rag-api-v1 | grep -E '(Web results origin_tools|Top results for LLM)' | head -5"
echo ""

