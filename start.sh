#!/bin/bash

# Neural Vault RAG Lab - Startup Script
# Ensures all dependencies are running before starting services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ASCII Art Banner
echo -e "${CYAN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   ███╗   ██╗███████╗██╗   ██╗██████╗  █████╗ ██╗         ║
║   ████╗  ██║██╔════╝██║   ██║██╔══██╗██╔══██╗██║         ║
║   ██╔██╗ ██║█████╗  ██║   ██║██████╔╝███████║██║         ║
║   ██║╚██╗██║██╔══╝  ██║   ██║██╔══██╗██╔══██║██║         ║
║   ██║ ╚████║███████╗╚██████╔╝██║  ██║██║  ██║███████╗    ║
║   ╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝    ║
║                                                           ║
║              Educational RAG Lab - Startup                ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo -e "${BLUE}Starting Neural Vault RAG Lab...${NC}\n"

# Function to check if a service is running
check_service() {
    local service_name=$1
    local check_cmd=$2
    
    echo -ne "${YELLOW}Checking ${service_name}...${NC} "
    
    if eval "$check_cmd" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Running${NC}"
        return 0
    else
        echo -e "${RED}✗ Not running${NC}"
        return 1
    fi
}

# Function to wait for a service to be ready
wait_for_service() {
    local service_name=$1
    local health_url=$2
    local max_attempts=30
    local attempt=0
    
    echo -ne "${YELLOW}Waiting for ${service_name}...${NC} "
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -sf "$health_url" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Ready${NC}"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
        echo -ne "."
    done
    
    echo -e "${RED}✗ Timeout${NC}"
    return 1
}

# Step 1: Check Docker
echo -e "${PURPLE}[1/5] Checking Docker...${NC}"
if ! check_service "Docker daemon" "docker ps"; then
    echo -e "${RED}Error: Docker is not running!${NC}"
    echo -e "${YELLOW}Please start Docker Desktop and try again.${NC}"
    exit 1
fi

# Step 2: Check Ollama
echo -e "\n${PURPLE}[2/5] Checking Ollama...${NC}"
if ! check_service "Ollama service" "docker ps | grep ollama"; then
    echo -e "${YELLOW}Starting Ollama container...${NC}"
    docker start ollama || {
        echo -e "${RED}Error: Could not start Ollama${NC}"
        echo -e "${YELLOW}Run: docker run -d -p 11434:11434 --name ollama ollama/ollama${NC}"
        exit 1
    }
    sleep 5
fi

# Verify Ollama is responding
if ! wait_for_service "Ollama API" "http://localhost:11434/api/tags"; then
    echo -e "${RED}Error: Ollama is not responding${NC}"
    exit 1
fi

# Check for required models
echo -ne "${YELLOW}Checking for llama3.2:3b model...${NC} "
if curl -s http://localhost:11434/api/tags | grep -q "llama3.2:3b"; then
    echo -e "${GREEN}✓ Found${NC}"
else
    echo -e "${YELLOW}⚠ Not found${NC}"
    echo -e "${YELLOW}Pulling llama3.2:3b model (this may take a few minutes)...${NC}"
    docker exec ollama ollama pull llama3.2:3b
fi

# Step 3: Start Docker Services
echo -e "\n${PURPLE}[3/5] Starting Docker Services...${NC}"
cd "$(dirname "$0")"

echo -e "${YELLOW}Building and starting services...${NC}"
docker-compose -f docker-compose.test.yml up -d --build

# Step 4: Wait for services to be healthy
echo -e "\n${PURPLE}[4/5] Waiting for services to be ready...${NC}"

declare -A SERVICES=(
    ["API Gateway"]="http://localhost:8000/health"
    ["Vector DB"]="http://localhost:8005/health"
    ["Search Service"]="http://localhost:8002/health"
    ["Chat Service"]="http://localhost:8003/health"
    ["Embedding Service"]="http://localhost:8006/health"
)

all_healthy=true
for service_name in "${!SERVICES[@]}"; do
    health_url="${SERVICES[$service_name]}"
    if ! wait_for_service "$service_name" "$health_url"; then
        all_healthy=false
    fi
done

# Step 5: Start Frontend
echo -e "\n${PURPLE}[5/5] Starting Frontend...${NC}"

# Kill any existing React dev server
pkill -f "vite" 2>/dev/null || true
sleep 2

echo -e "${YELLOW}Starting React dev server...${NC}"
cd frontend
npm run dev > /tmp/react_dev.log 2>&1 &
REACT_PID=$!

# Wait for React to be ready
sleep 5
if curl -sf http://localhost:5173 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ React UI ready${NC}"
else
    echo -e "${RED}✗ React UI failed to start${NC}"
    all_healthy=false
fi

cd ..

# Final Status
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"

if [ "$all_healthy" = true ]; then
    echo -e "${GREEN}✅ All services started successfully!${NC}"
    echo -e "\n${CYAN}Access the application:${NC}"
    echo -e "  ${PURPLE}React UI:${NC}       http://localhost:5173"
    echo -e "  ${PURPLE}Production UI:${NC}  http://localhost:3000"
    echo -e "  ${PURPLE}API Gateway:${NC}    http://localhost:8000"
    echo -e "\n${CYAN}Service Status:${NC}"
    docker-compose -f docker-compose.test.yml ps
    echo -e "\n${YELLOW}💡 Pro Tip:${NC} Open http://localhost:5173 in your browser"
    echo -e "${YELLOW}   Go to Settings → Load 'Maximum Quality' preset to enable all RAG features${NC}"
else
    echo -e "${RED}⚠️  Some services failed to start${NC}"
    echo -e "${YELLOW}Check logs with: docker-compose -f docker-compose.test.yml logs${NC}"
    exit 1
fi

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"

# Save PIDs for cleanup script
echo "REACT_PID=$REACT_PID" > .startup_pids

echo -e "${GREEN}🚀 Neural Vault RAG Lab is ready!${NC}\n"

