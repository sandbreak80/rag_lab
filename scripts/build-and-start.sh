#!/bin/bash
# Build and Start RAG Lab - Complete Setup Script
# This script builds all containers, pulls models, and starts the application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Enterprise Agentic AI Platform with Advanced RAG         ║${NC}"
echo -e "${BLUE}║  Build and Start Script                                    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to print step
print_step() {
    echo -e "${GREEN}▶ $1${NC}"
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠  $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Check if Docker is running
print_step "Checking Docker..."
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker Desktop."
    exit 1
fi
print_success "Docker is running"
echo ""

# Check if docker compose is available
print_step "Checking Docker Compose..."
if ! docker compose version &> /dev/null; then
    print_error "Docker Compose plugin not found. Please install Docker Compose."
    print_error "See: https://docs.docker.com/compose/install/"
    exit 1
fi
print_success "Docker Compose is available"
echo ""

# Stop any running containers
print_step "Stopping any running containers..."
docker compose down 2>/dev/null || true
print_success "Containers stopped"
echo ""

# Optional: Clean build (remove volumes)
if [ "$1" == "--clean" ]; then
    print_warning "Clean build requested - removing all volumes..."
    read -p "This will delete all data (documents, embeddings, metrics). Continue? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker compose down -v
        print_success "Volumes removed"
    else
        print_warning "Skipping volume removal"
    fi
    echo ""
fi

# Build Docker images (includes frontend build inside container)
print_step "Building Docker images..."
docker compose build --parallel
print_success "Docker images built"
echo ""

# Start core services (Ollama first)
print_step "Starting Ollama service..."
docker compose up -d ollama
print_success "Ollama started"
echo ""

# Wait for Ollama to be ready
print_step "Waiting for Ollama to be ready..."
MAX_WAIT=60
WAIT_COUNT=0
while ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
    if [ $WAIT_COUNT -ge $MAX_WAIT ]; then
        print_error "Ollama failed to start after ${MAX_WAIT} seconds"
        exit 1
    fi
    echo -n "."
    sleep 1
    ((WAIT_COUNT++))
done
echo ""
print_success "Ollama is ready"
echo ""

# Pull Ollama models
print_step "Pulling Ollama models..."
./scripts/pull-ollama-models.sh
print_success "Models pulled"
echo ""

# Start all other services
print_step "Starting all services..."
docker compose up -d
print_success "All services started"
echo ""

# Wait for services to be healthy
print_step "Waiting for services to be healthy..."
sleep 10

# Check service health
print_step "Checking service health..."
SERVICES=(
    "http://localhost:11434/api/tags:Ollama"
    "http://localhost:8005/health:Vector DB"
    "http://localhost:8006/health:Embedding Service"
    "http://localhost:8002/health:Search Service"
    "http://localhost:8003/health:Chat Service"
    "http://localhost:8000/health:API Gateway"
    "http://localhost:3000:Frontend"
)

ALL_HEALTHY=true
for service in "${SERVICES[@]}"; do
    IFS=':' read -r url name <<< "$service"
    if curl -s -f "$url" > /dev/null 2>&1; then
        print_success "$name is healthy"
    else
        print_warning "$name is not responding yet"
        ALL_HEALTHY=false
    fi
done
echo ""

if [ "$ALL_HEALTHY" = false ]; then
    print_warning "Some services are not ready yet. They may still be starting up."
    print_warning "Check status with: docker compose ps"
    print_warning "Check logs with: docker compose logs -f [service-name]"
    echo ""
fi

# Display service URLs
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  🚀 RAG Lab is Running!                                    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}📱 Frontend:${NC}           http://localhost:3000"
echo -e "${GREEN}🔌 API Gateway:${NC}        http://localhost:8000"
echo -e "${GREEN}🤖 Ollama:${NC}             http://localhost:11434"
echo -e "${GREEN}🔍 SearXNG:${NC}            http://localhost:8080"
echo ""
echo -e "${BLUE}📊 Service Endpoints:${NC}"
echo "   Vector DB:          http://localhost:8005"
echo "   Embedding Service:  http://localhost:8006"
echo "   Search Service:     http://localhost:8002"
echo "   Chat Service:       http://localhost:8003"
echo "   Ingest Service:     http://localhost:8001"
echo "   Docling Service:    http://localhost:8004"
echo "   Knowledge Graph:    http://localhost:8007"
echo "   Reranker:           http://localhost:8008"
echo "   Web Search:         http://localhost:8009"
echo "   Metrics Store:      http://localhost:8011"
echo ""
echo -e "${BLUE}📝 Useful Commands:${NC}"
echo "   View logs:          docker compose logs -f"
echo "   Stop services:      docker compose down"
echo "   Restart service:    docker compose restart [service-name]"
echo "   Check status:       docker compose ps"
echo ""
echo -e "${BLUE}🔧 Configuration:${NC}"
echo "   Edit config.env to change settings"
echo "   Change models: CHAT_MODEL and EMBEDDING_MODEL"
echo ""
echo -e "${GREEN}✨ Ready to use! Open http://localhost:3000 in your browser${NC}"
echo ""

