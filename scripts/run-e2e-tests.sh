#!/bin/bash
# Run Playwright E2E tests via Docker
# Usage: ./scripts/run-e2e-tests.sh [options]

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}RAG Lab - Playwright E2E Tests${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""

# Parse arguments
TEST_TARGET="${1:-http://16.146.148.184:3000}"
RUN_MODE="${2:-docker}"  # docker or local

if [ "$RUN_MODE" = "docker" ]; then
    echo -e "${YELLOW}Running tests in Docker container...${NC}"
    echo -e "Target: ${TEST_TARGET}"
    echo ""

    # Ensure frontend and API are running
    echo -e "${YELLOW}Checking if frontend and API are running...${NC}"
    docker compose ps frontend rag-api-v1 | grep -q "Up" || {
        echo -e "${YELLOW}Starting frontend and rag-api-v1...${NC}"
        docker compose up -d frontend rag-api-v1
        echo -e "${YELLOW}Waiting 20s for services to be ready...${NC}"
        sleep 20
    }

    # Run Playwright tests
    echo -e "${GREEN}Running Playwright tests...${NC}"
    docker compose run --rm \
        -e BASE_URL="$TEST_TARGET" \
        e2e \
        sh -c "
            cd /workspace/tests/e2e &&
            npm install --legacy-peer-deps &&
            npx playwright install --with-deps &&
            npx playwright test --reporter=list
        "

    TEST_EXIT_CODE=$?

    if [ $TEST_EXIT_CODE -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✅ All tests passed!${NC}"
        echo ""
        echo -e "View HTML report:"
        echo -e "  open tests/e2e/playwright-report/index.html"
    else
        echo ""
        echo -e "${RED}❌ Tests failed with exit code $TEST_EXIT_CODE${NC}"
        echo ""
        echo -e "Check logs above and HTML report:"
        echo -e "  open tests/e2e/playwright-report/index.html"
    fi

elif [ "$RUN_MODE" = "local" ]; then
    echo -e "${YELLOW}Running tests locally...${NC}"
    echo -e "Target: ${TEST_TARGET}"
    echo ""

    # Check if Playwright is installed
    if ! command -v npx &> /dev/null; then
        echo -e "${RED}Error: npx not found. Install Node.js first.${NC}"
        exit 1
    fi

    # Install Playwright if needed
    if ! npx playwright --version &> /dev/null; then
        echo -e "${YELLOW}Installing Playwright...${NC}"
        npm install -D @playwright/test
        npx playwright install --with-deps
    fi

    # Run tests
    echo -e "${GREEN}Running Playwright tests locally...${NC}"
    BASE_URL="$TEST_TARGET" npx playwright test --reporter=list

    TEST_EXIT_CODE=$?

    if [ $TEST_EXIT_CODE -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✅ All tests passed!${NC}"
        echo ""
        echo -e "View HTML report:"
        echo -e "  npx playwright show-report tests/e2e/playwright-report"
    else
        echo ""
        echo -e "${RED}❌ Tests failed with exit code $TEST_EXIT_CODE${NC}"
        echo ""
        echo -e "Debug with UI mode:"
        echo -e "  BASE_URL=$TEST_TARGET npx playwright test --ui"
    fi

else
    echo -e "${RED}Invalid run mode: $RUN_MODE${NC}"
    echo -e "Usage: $0 [target_url] [docker|local]"
    exit 1
fi

echo ""
echo -e "${GREEN}======================================${NC}"

exit $TEST_EXIT_CODE

