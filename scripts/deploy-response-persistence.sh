#!/bin/bash
# Deployment script for response persistence feature
# Run this on the EC2 instance

set -e

echo "🚀 Deploying Response Persistence Feature"
echo "=========================================="
echo ""

cd ~/rag_lab || { echo "Error: ~/rag_lab not found"; exit 1; }

echo "1. Pulling latest changes from otel branch..."
git pull origin otel

echo ""
echo "2. Building rag-api-v1 with new response cache..."
docker compose build rag-api-v1

echo ""
echo "3. Restarting services..."
docker compose restart rag-api-v1 frontend

echo ""
echo "4. Waiting for services to stabilize..."
sleep 5

echo ""
echo "5. Checking service status..."
docker ps --filter "name=rag-api-v1" --format "table {{.Names}}\t{{.Status}}"
docker ps --filter "name=frontend" --format "table {{.Names}}\t{{.Status}}"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Test: Send a message, then refresh during processing - response should appear automatically!"

