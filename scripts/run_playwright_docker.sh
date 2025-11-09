#!/usr/bin/env bash
set -euo pipefail

echo "=========================================="
echo "Running Playwright E2E Tests (Docker)"
echo "=========================================="

# Runs inside the compose network against http://frontend:3000

NETWORK="${NETWORK:-rag_rag-network}"
BASE_URL="${BASE_URL:-http://frontend:3000}"

echo "Network: $NETWORK"
echo "Base URL: $BASE_URL"
echo ""

docker run --rm \
  --network "$NETWORK" \
  -e BASE_URL="$BASE_URL" \
  -e PW_HEADLESS=1 \
  -e CI=true \
  -v "$PWD":/work \
  -w /work \
  mcr.microsoft.com/playwright:v1.48.2-jammy \
  bash -lc "cd tests/e2e && npm ci && npx playwright test"

EXIT_CODE=$?

echo ""
echo "=========================================="
echo "Test Results"
echo "=========================================="

if [ -d "tests/e2e/playwright-report" ]; then
    echo "✅ Reports generated:"
    echo "   HTML: tests/e2e/playwright-report/index.html"
    echo "   JUnit: tests/e2e/playwright-report/results.xml"
    echo ""
    echo "To view HTML report:"
    echo "   python3 -m http.server -d tests/e2e/playwright-report 8888"
    echo "   Then open: http://localhost:8888/"
fi

exit $EXIT_CODE

