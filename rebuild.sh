#!/bin/bash
# Neural Vault RAG Lab - Rebuild Script
# Rebuilds specific services or all services from scratch

set -e

COMPOSE_FILE="docker-compose.test.yml"

echo "════════════════════════════════════════════════════════════════"
echo "  🔨 Neural Vault RAG Lab - Rebuild"
echo "════════════════════════════════════════════════════════════════"
echo ""

if [ -z "$1" ]; then
    echo "🔨 Rebuilding ALL services..."
    echo ""

    # Stop all services
    docker-compose -f $COMPOSE_FILE down

    # Start with build flag
    docker-compose -f $COMPOSE_FILE up -d --build

    echo ""
    echo "⏳ Waiting for services to initialize (30 seconds)..."
    sleep 30

    echo ""
    echo "✅ All services rebuilt and started"
else
    echo "🔨 Rebuilding $1..."
    echo ""

    # Stop specific service
    docker-compose -f $COMPOSE_FILE stop "$1"
    docker-compose -f $COMPOSE_FILE rm -f "$1"

    # Rebuild and start
    docker-compose -f $COMPOSE_FILE up -d --build "$1"

    echo ""
    echo "⏳ Waiting for service to initialize (10 seconds)..."
    sleep 10

    echo ""
    echo "✅ $1 rebuilt and started"
fi

echo ""
echo "📊 Current status:"
docker-compose -f $COMPOSE_FILE ps --format "table {{.Service}}\t{{.Status}}"
echo ""

