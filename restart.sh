#!/bin/bash
# Neural Vault RAG Lab - Restart Script
# Restarts specific services or all services

set -e

COMPOSE_FILE="docker-compose.test.yml"

echo "════════════════════════════════════════════════════════════════"
echo "  🔄 Neural Vault RAG Lab - Restart"
echo "════════════════════════════════════════════════════════════════"
echo ""

if [ -z "$1" ]; then
    echo "🔄 Restarting all services..."
    docker-compose -f $COMPOSE_FILE restart

    echo ""
    echo "⏳ Waiting for services to initialize (15 seconds)..."
    sleep 15

    echo ""
    echo "✅ All services restarted"
else
    echo "🔄 Restarting $1..."
    docker-compose -f $COMPOSE_FILE restart "$1"

    echo ""
    echo "⏳ Waiting for service to initialize (5 seconds)..."
    sleep 5

    echo ""
    echo "✅ $1 restarted"
fi

echo ""
echo "📊 Current status:"
docker-compose -f $COMPOSE_FILE ps --format "table {{.Service}}\t{{.Status}}"
echo ""

