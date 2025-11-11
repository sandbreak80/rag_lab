#!/usr/bin/env bash
# Run this script ON THE AWS INSTANCE (ubuntu@16.146.148.184)

set -euo pipefail

echo "=========================================="
echo "E2E Test Execution on AWS"
echo "=========================================="

cd /home/ubuntu/rag_lab

# Step 1: Pull latest code
echo ""
echo "Step 1: Pulling latest code..."
git pull origin otel

# Step 2: Ensure services are running and updated
echo ""
echo "Step 2: Deploying updated services..."
docker compose up -d --build rag-api-v1 frontend

echo "Waiting for services to be healthy (30s)..."
sleep 30

# Step 3: Quick sanity check
echo ""
echo "Step 3: Sanity checks..."
echo "Checking /ready..."
curl -sf http://localhost:3000/ready | jq -r '.status' || echo "⚠️  Not ready"

echo "Checking /live..."
curl -sf http://localhost:3000/live | jq -r '.status' || echo "⚠️  Not alive"

# Step 4: Run E2E tests using Docker test container
echo ""
echo "=========================================="
echo "Step 4: Running E2E Tests"
echo "=========================================="
echo "Using Docker Playwright container..."
echo "Target: http://16.146.148.184:3000 (external IP)"
echo ""

# Clean up any previous test containers
docker compose -f tests/e2e/docker-compose.e2e.yml down 2>/dev/null || true

# Run the tests
docker compose -f tests/e2e/docker-compose.e2e.yml up --build --abort-on-container-exit

EXIT_CODE=$?

# Step 5: Show results
echo ""
echo "=========================================="
echo "Step 5: Test Results"
echo "=========================================="

if [ -d "tests/e2e/playwright-report" ]; then
    echo "✅ Reports generated:"
    echo "   - HTML: tests/e2e/playwright-report/index.html"
    echo "   - JUnit: tests/e2e/playwright-report/results.xml"
    echo ""

    # Count tests
    if [ -f "tests/e2e/playwright-report/results.xml" ]; then
        TOTAL=$(grep -oP 'tests="\K[0-9]+' tests/e2e/playwright-report/results.xml 2>/dev/null || echo "0")
        FAILURES=$(grep -oP 'failures="\K[0-9]+' tests/e2e/playwright-report/results.xml 2>/dev/null || echo "0")
        ERRORS=$(grep -oP 'errors="\K[0-9]+' tests/e2e/playwright-report/results.xml 2>/dev/null || echo "0")

        echo "Test Summary:"
        echo "  Total: $TOTAL"
        echo "  Failures: $FAILURES"
        echo "  Errors: $ERRORS"
        echo ""
    fi

    echo "To view HTML report:"
    echo "  python3 -m http.server -d tests/e2e/playwright-report 8888 &"
    echo "  Then open: http://16.146.148.184:8888/"
    echo ""
    echo "To stop the HTTP server:"
    echo "  pkill -f 'python3 -m http.server.*8888'"
else
    echo "⚠️  No test reports found"
fi

# Clean up test container
docker compose -f tests/e2e/docker-compose.e2e.yml down 2>/dev/null || true

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✅ ALL E2E TESTS PASSED!"
else
    echo ""
    echo "❌ SOME E2E TESTS FAILED"
    echo "Check the HTML report for details"
fi

exit $EXIT_CODE

