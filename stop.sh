#!/bin/bash
# Neural Vault RAG Lab - Stop Script
# Gracefully stops all services

set -e

echo "════════════════════════════════════════════════════════════════"
echo "  🛑 Neural Vault RAG Lab - Shutdown"
echo "════════════════════════════════════════════════════════════════"
echo ""

COMPOSE_FILE="docker-compose.test.yml"

echo "🛑 Stopping all services..."
docker-compose -f $COMPOSE_FILE down

echo ""
echo "✅ All services stopped"
echo ""
echo "💾 Data volumes preserved:"
echo "   - chromadb-data     (vector embeddings)"
echo "   - bm25-indices      (keyword search)"
echo "   - knowledge-graph   (graph relationships)"
echo "   - uploads           (uploaded documents)"
echo "   - metrics-data      (performance metrics)"
echo ""
echo "To remove volumes (⚠️  deletes all data):"
echo "   docker-compose -f $COMPOSE_FILE down -v"
echo ""
