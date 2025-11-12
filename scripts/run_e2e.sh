#!/usr/bin/env bash
set -euo pipefail

echo "=========================================="
echo "Running Playwright E2E Tests"
echo "=========================================="
echo ""

# Ensure we're in the project root
cd "$(dirname "$0")/.."

# Run E2E tests in Docker
# BASE_URL is set in docker-compose.yml to http://frontend:80
# (frontend container listens on port 80 internally, mapped to host 3000)
docker compose run --rm e2e

echo ""
echo "=========================================="
echo "E2E Tests Complete"
echo "=========================================="
echo ""
echo "Reports available at:"
echo "  - HTML: tests/e2e/playwright-report/index.html"
echo "  - JUnit: tests/e2e/playwright-report/results.xml"
echo ""

