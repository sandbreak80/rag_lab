#!/bin/bash
# Clean Rebuild Script for Ubuntu Server
# Completely rebuilds RAG Lab from scratch with validation

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${BLUE}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to check command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Start
echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║        RAG Lab - Clean Rebuild Script                    ║"
echo "║        Complete From-Scratch Deployment                  ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check prerequisites
print_step "Step 0: Checking prerequisites..."

if ! command_exists docker; then
    print_error "Docker not found. Please install Docker first."
    exit 1
fi

if ! command_exists git; then
    print_error "Git not found. Please install Git first."
    exit 1
fi

if ! command_exists nvidia-smi; then
    print_warning "nvidia-smi not found. GPU support may not be available."
fi

print_success "Prerequisites check passed"
echo ""

# Step 1: Stop existing containers
print_step "Step 1: Stopping existing containers..."
if docker compose ps -q 2>/dev/null | grep -q .; then
    docker compose down
    print_success "Containers stopped"
else
    print_success "No containers running"
fi
echo ""

# Step 2: Clean Docker system
print_step "Step 2: Cleaning Docker system..."

# Remove RAG containers
print_step "   Removing RAG containers..."
CONTAINERS=$(docker ps -a | grep rag- | awk '{print $1}' || true)
if [ -n "$CONTAINERS" ]; then
    echo "$CONTAINERS" | xargs docker rm -f
    print_success "   RAG containers removed"
else
    print_success "   No RAG containers to remove"
fi

# Remove RAG images
print_step "   Removing RAG images..."
IMAGES=$(docker images | grep rag- | awk '{print $3}' || true)
if [ -n "$IMAGES" ]; then
    echo "$IMAGES" | xargs docker rmi -f
    print_success "   RAG images removed"
else
    print_success "   No RAG images to remove"
fi

# Prune Docker system
print_step "   Pruning Docker system..."
docker system prune -af > /dev/null 2>&1
print_success "   Docker system pruned"

# Ask about volumes
echo ""
print_warning "Volume cleanup (deletes uploaded documents):"
read -p "   Remove all volumes? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker volume prune -f > /dev/null 2>&1
    print_success "   Volumes removed"
else
    print_success "   Volumes kept"
fi
echo ""

# Step 3: Pull latest code
print_step "Step 3: Pulling latest code from GitHub..."

# Check for uncommitted changes
if ! git diff-index --quiet HEAD -- 2>/dev/null; then
    print_warning "Uncommitted changes detected"
    read -p "   Discard local changes? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git reset --hard HEAD
        git clean -fd
        print_success "   Local changes discarded"
    else
        print_error "Cannot proceed with uncommitted changes"
        exit 1
    fi
fi

# Fetch and pull
git fetch origin
BEHIND=$(git rev-list HEAD..origin/main --count 2>/dev/null || echo "0")
if [ "$BEHIND" -gt 0 ]; then
    print_step "   Pulling $BEHIND new commits..."
    git pull origin main
    print_success "   Code updated"
else
    print_success "   Already up to date"
fi

# Show current commit
COMMIT=$(git log --oneline -1)
print_success "   Current commit: $COMMIT"
echo ""

# Step 4: Verify configuration
print_step "Step 4: Verifying configuration..."

# Check config.env
if [ ! -f "config.env" ]; then
    print_error "config.env not found!"
    exit 1
fi

CHAT_MODEL=$(grep "^CHAT_MODEL=" config.env | cut -d'=' -f2)
EMBEDDING_MODEL=$(grep "^EMBEDDING_MODEL=" config.env | cut -d'=' -f2)
print_success "   Chat model: $CHAT_MODEL"
print_success "   Embedding model: $EMBEDDING_MODEL"

# Check GPU support in docker-compose.yml
if grep -q "driver: nvidia" docker-compose.yml; then
    print_success "   GPU support: ENABLED"
else
    print_warning "   GPU support: DISABLED"
fi
echo ""

# Step 5: Clean build
print_step "Step 5: Building all services (no cache)..."
print_warning "This will take 5-10 minutes..."
echo ""

START_BUILD=$(date +%s)
docker compose build --no-cache --progress=plain 2>&1 | grep -E "^#|=>" || true
END_BUILD=$(date +%s)
BUILD_TIME=$((END_BUILD - START_BUILD))

print_success "Build completed in ${BUILD_TIME}s"
echo ""

# Step 6: Start services
print_step "Step 6: Starting all services..."
docker compose up -d

print_step "   Waiting for services to be healthy (30s)..."
sleep 30

# Check service status
print_step "   Checking service status..."
SERVICES=$(docker compose ps --format json | jq -r '.Service' 2>/dev/null || docker compose ps --services)
HEALTHY=0
TOTAL=0

for service in $SERVICES; do
    TOTAL=$((TOTAL + 1))
    STATUS=$(docker compose ps $service --format "{{.Status}}" 2>/dev/null || echo "unknown")
    if echo "$STATUS" | grep -q "Up"; then
        print_success "   $service: UP"
        HEALTHY=$((HEALTHY + 1))
    else
        print_error "   $service: $STATUS"
    fi
done

print_success "Services: $HEALTHY/$TOTAL healthy"
echo ""

# Step 7: Pull required Ollama models
print_step "Step 7: Pulling required Ollama models..."
print_warning "This will take 5-10 minutes..."
echo ""

START_MODELS=$(date +%s)

# Pull chat model
print_step "   Pulling $CHAT_MODEL..."
docker compose exec -T ollama ollama pull "$CHAT_MODEL"
print_success "   $CHAT_MODEL downloaded"

# Pull embedding model
print_step "   Pulling $EMBEDDING_MODEL..."
docker compose exec -T ollama ollama pull "$EMBEDDING_MODEL"
print_success "   $EMBEDDING_MODEL downloaded"

END_MODELS=$(date +%s)
MODELS_TIME=$((END_MODELS - START_MODELS))

print_success "Models downloaded in ${MODELS_TIME}s"
echo ""

# Step 8: Optional models
print_step "Step 8: Optional models for lab exercises"
echo "   Available models:"
echo "   - llama3.2:1b (tiny, fast)"
echo "   - llama3.2:3b (small, balanced)"
echo "   - gemma2:2b (small, Google)"
echo "   - gemma2:9b (medium, high quality)"
echo "   - mistral:7b (medium, popular)"
echo "   - qwen2.5:14b (large, high quality)"
echo "   - mxbai-embed-large (alternative embedding)"
echo "   - all-minilm (lightweight embedding)"
echo ""
read -p "Pull optional models? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_step "   Pulling optional models (10-20 minutes)..."
    
    docker compose exec -T ollama ollama pull llama3.2:1b &
    docker compose exec -T ollama ollama pull llama3.2:3b &
    docker compose exec -T ollama ollama pull gemma2:2b &
    docker compose exec -T ollama ollama pull gemma2:9b &
    docker compose exec -T ollama ollama pull mistral:7b &
    docker compose exec -T ollama ollama pull qwen2.5:14b &
    docker compose exec -T ollama ollama pull mxbai-embed-large &
    docker compose exec -T ollama ollama pull all-minilm &
    
    wait
    print_success "   Optional models downloaded"
else
    print_success "   Skipping optional models"
fi
echo ""

# Step 9: Validation
print_step "Step 9: Running validation tests..."
echo ""

VALIDATION_PASSED=0
VALIDATION_TOTAL=0

# Test 1: API Gateway health
print_step "   Test 1: API Gateway health..."
VALIDATION_TOTAL=$((VALIDATION_TOTAL + 1))
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    print_success "   API Gateway: HEALTHY"
    VALIDATION_PASSED=$((VALIDATION_PASSED + 1))
else
    print_error "   API Gateway: FAILED"
fi

# Test 2: Ollama service
print_step "   Test 2: Ollama service..."
VALIDATION_TOTAL=$((VALIDATION_TOTAL + 1))
if curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
    print_success "   Ollama: WORKING"
    VALIDATION_PASSED=$((VALIDATION_PASSED + 1))
else
    print_error "   Ollama: FAILED"
fi

# Test 3: Frontend
print_step "   Test 3: Frontend access..."
VALIDATION_TOTAL=$((VALIDATION_TOTAL + 1))
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000)
if [ "$HTTP_CODE" = "200" ]; then
    print_success "   Frontend: ACCESSIBLE"
    VALIDATION_PASSED=$((VALIDATION_PASSED + 1))
else
    print_error "   Frontend: FAILED (HTTP $HTTP_CODE)"
fi

# Test 4: GPU detection
print_step "   Test 4: GPU detection..."
VALIDATION_TOTAL=$((VALIDATION_TOTAL + 1))
if command_exists nvidia-smi; then
    if nvidia-smi > /dev/null 2>&1; then
        print_success "   GPU: DETECTED"
        VALIDATION_PASSED=$((VALIDATION_PASSED + 1))
    else
        print_warning "   GPU: NOT DETECTED"
    fi
else
    print_warning "   GPU: nvidia-smi not available"
fi

# Test 5: Model list
print_step "   Test 5: Model availability..."
VALIDATION_TOTAL=$((VALIDATION_TOTAL + 1))
MODEL_COUNT=$(docker compose exec -T ollama ollama list 2>/dev/null | tail -n +2 | wc -l)
if [ "$MODEL_COUNT" -ge 2 ]; then
    print_success "   Models: $MODEL_COUNT available"
    VALIDATION_PASSED=$((VALIDATION_PASSED + 1))
else
    print_error "   Models: Only $MODEL_COUNT found (expected 2+)"
fi

echo ""
print_success "Validation: $VALIDATION_PASSED/$VALIDATION_TOTAL tests passed"
echo ""

# Summary
TOTAL_TIME=$(($(date +%s) - START_BUILD + BUILD_TIME))
echo -e "${GREEN}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║        🎉 CLEAN REBUILD COMPLETE! 🎉                      ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo "Summary:"
echo "--------"
echo "Build Time: ${BUILD_TIME}s"
echo "Model Download Time: ${MODELS_TIME}s"
echo "Total Time: ${TOTAL_TIME}s"
echo ""
echo "Services: $HEALTHY/$TOTAL healthy"
echo "Validation: $VALIDATION_PASSED/$VALIDATION_TOTAL passed"
echo ""
echo "Access the application:"
echo "  Frontend: http://$(hostname -I | awk '{print $1}'):3000"
echo "  API Gateway: http://$(hostname -I | awk '{print $1}'):8000"
echo ""

if [ "$VALIDATION_PASSED" -eq "$VALIDATION_TOTAL" ]; then
    print_success "✅ All validations passed - System ready for use!"
else
    print_warning "⚠️  Some validations failed - Check logs for details"
    echo ""
    echo "To check logs:"
    echo "  docker compose logs -f"
fi

echo ""
echo "Next steps:"
echo "  1. Open http://$(hostname -I | awk '{print $1}'):3000 in browser"
echo "  2. Go to Learning Hub to see 100+ Q&A entries"
echo "  3. Test Chat with: 'What is RAG?'"
echo "  4. Check detailed metrics in waterfall chart"
echo "  5. Try web search with toggle enabled"
echo ""
print_success "Happy testing! 🚀"

