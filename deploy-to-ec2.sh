#!/bin/bash
# Deployment script for EC2 - Run this on the EC2 instance

set -e

echo "🚀 Starting deployment..."
cd ~/rag_lab

echo "📥 Pulling latest code..."
git pull origin otel

echo "🔨 Rebuilding containers..."
docker compose build --no-cache frontend api-gateway rag-api-v1

echo "🔄 Restarting services..."
docker compose up -d frontend api-gateway rag-api-v1

echo "⏳ Waiting for services to start..."
sleep 10

echo "✅ Checking service status..."
docker compose ps frontend api-gateway rag-api-v1

echo ""
echo "🎉 Deployment complete!"
echo "📊 Check logs with: docker compose logs -f frontend api-gateway rag-api-v1"

