#!/bin/bash
# Production Deployment Script
# Fast Track Phase 8 - Production Architecture

set -e

echo "🚀 Starting Production Deployment..."
echo "=========================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if docker compose is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker found${NC}"

# Build frontend first
echo ""
echo "📦 Building frontend..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml build frontend
echo -e "${GREEN}✅ Frontend built${NC}"

# Stop existing containers
echo ""
echo "🛑 Stopping existing containers..."
docker compose down
echo -e "${GREEN}✅ Containers stopped${NC}"

# Pull latest images
echo ""
echo "📥 Pulling latest images..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml pull
echo -e "${GREEN}✅ Images pulled${NC}"

# Start production stack
echo ""
echo "🚀 Starting production stack..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Wait for services to be healthy
echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Health checks
echo ""
echo "🏥 Checking service health..."

services=(
    "nginx-proxy:80:/health"
    "api-gateway-1:8000:/health"
    "api-gateway-2:8000:/health"
    "auth-service:8014:/health"
    "redis:6379:PING"
)

all_healthy=true

for service in "${services[@]}"; do
    IFS=':' read -r name port endpoint <<< "$service"

    if [ "$endpoint" = "PING" ]; then
        # Redis health check
        if docker exec rag-redis redis-cli ping > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $name is healthy${NC}"
        else
            echo -e "${RED}❌ $name is unhealthy${NC}"
            all_healthy=false
        fi
    else
        # HTTP health check
        if curl -sf "http://localhost:$port$endpoint" > /dev/null; then
            echo -e "${GREEN}✅ $name is healthy${NC}"
        else
            echo -e "${YELLOW}⚠️  $name is not responding (may still be starting)${NC}"
            all_healthy=false
        fi
    fi
done

echo ""
echo "=========================================="

if [ "$all_healthy" = true ]; then
    echo -e "${GREEN}🎉 Production deployment successful!${NC}"
else
    echo -e "${YELLOW}⚠️  Some services are not healthy yet${NC}"
    echo -e "${YELLOW}   Run 'docker compose ps' to check status${NC}"
fi

echo ""
echo "📊 Service URLs:"
echo "  - Frontend:        http://localhost"
echo "  - API Gateway 1:   http://localhost:8000"
echo "  - API Gateway 2:   http://localhost:8001"
echo "  - Auth Service:    http://localhost:8014"
echo "  - Redis:           localhost:6379"
echo ""
echo "📝 Useful commands:"
echo "  - View logs:       docker compose logs -f"
echo "  - Check status:    docker compose ps"
echo "  - Stop services:   docker compose down"
echo "  - Scale API GW:    docker compose up -d --scale api-gateway=3"
echo ""
echo -e "${GREEN}✨ Deployment complete!${NC}"

