#!/bin/bash
# Stop RAG Lab - Stop all services

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
echo -e "${BLUE}║  Stopping RAG Lab                                          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Stop services
echo -e "${YELLOW}⏸  Stopping all services...${NC}"
docker compose down

echo ""
echo -e "${GREEN}✓ All services stopped${NC}"
echo ""
echo -e "${BLUE}💡 TIP:${NC} To remove all data (volumes), run:"
echo "   docker compose down -v"
echo ""
echo -e "${BLUE}💡 TIP:${NC} To start again, run:"
echo "   ./scripts/build-and-start.sh"
echo ""

