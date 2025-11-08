#!/usr/bin/env bash
set -euo pipefail

echo "=========================================="
echo "Running Playwright E2E Tests"
echo "=========================================="
echo ""

# Ensure we're in the project root
cd "$(dirname "$0")/.."

# Run E2E tests in Docker
docker compose run --rm \
  -e BASE_URL="http://frontend:3000" \
  e2e

echo ""
echo "=========================================="
echo "E2E Tests Complete"
echo "=========================================="
echo ""
echo "Reports available at:"
echo "  - HTML: tests/e2e/playwright-report/index.html"
echo "  - JUnit: tests/e2e/playwright-report/results.xml"
echo ""

