#!/usr/bin/env bash
set -euo pipefail

echo "=========================================="
echo "Running Playwright E2E Tests (Local)"
echo "=========================================="

cd tests/e2e

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm ci
fi

# Set defaults
export BASE_URL=${BASE_URL:-http://localhost:3000}
export PW_HEADLESS=${PW_HEADLESS:-1}

echo "Base URL: $BASE_URL"
echo "Headless: $PW_HEADLESS"
echo ""

npx playwright test

EXIT_CODE=$?

echo ""
echo "=========================================="
echo "Test Results"
echo "=========================================="

if [ -d "playwright-report" ]; then
    echo "✅ Reports generated:"
    echo "   HTML: tests/e2e/playwright-report/index.html"
    echo "   JUnit: tests/e2e/playwright-report/results.xml"
    echo ""
    echo "To view HTML report:"
    echo "   npx playwright show-report"
fi

exit $EXIT_CODE

