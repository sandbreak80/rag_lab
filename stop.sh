#!/bin/bash

# Neural Vault RAG Lab - Shutdown Script
# Gracefully stops all services

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   Stopping Neural Vault RAG Lab...${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"

cd "$(dirname "$0")"

# Stop React dev server
echo -e "${YELLOW}[1/3] Stopping React dev server...${NC}"
pkill -f "vite" 2>/dev/null && echo -e "${GREEN}✓ React stopped${NC}" || echo -e "${YELLOW}⚠ React not running${NC}"

# Stop Docker services
echo -e "\n${YELLOW}[2/3] Stopping Docker services...${NC}"
docker-compose -f docker-compose.test.yml down

# Optional: Stop Ollama (commented out by default - you may want to keep it running)
# echo -e "\n${YELLOW}[3/3] Stopping Ollama...${NC}"
# docker stop ollama

echo -e "\n${YELLOW}[3/3] Cleaning up...${NC}"
rm -f .startup_pids
echo -e "${GREEN}✓ Cleanup complete${NC}"

echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Neural Vault RAG Lab stopped${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"

echo -e "${YELLOW}💡 To start again, run: ${NC}./start.sh"

