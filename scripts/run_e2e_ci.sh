#!/usr/bin/env bash
set -euo pipefail

echo "=========================================="
echo "RAG Lab E2E Test Suite"
echo "=========================================="
echo ""

# Ensure we're in project root
cd "$(dirname "$0")/.."

# 1. Pull latest from otel branch
echo "1. Pulling latest from otel branch..."
git pull origin otel

echo ""
echo "2. Cleaning up any previous test containers..."
docker compose -f tests/e2e/docker-compose.e2e.yml down --remove-orphans

echo ""
echo "3. Starting E2E test suite..."
echo "   BASE_URL: http://frontend:3000 (internal network)"
echo "   Network: rag_rag-network (external)"
echo ""

# Capture start time
START_TIME=$(date +%s)

# Run tests and capture exit code
set +e
docker compose -f tests/e2e/docker-compose.e2e.yml up --build --abort-on-container-exit --exit-code-from e2e
EXIT_CODE=$?
set -e

# Capture end time
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

echo ""
echo "=========================================="
echo "Test Suite Summary"
echo "=========================================="
echo "Total Time: ${ELAPSED}s"
echo "Exit Code: ${EXIT_CODE}"
echo ""

# Check if reports exist
if [ -f tests/e2e/playwright-report/results.xml ]; then
    echo "Reports Generated:"
    echo "  - HTML: $(pwd)/tests/e2e/playwright-report/index.html"
    echo "  - JUnit: $(pwd)/tests/e2e/playwright-report/results.xml"
    echo ""

    # Parse JUnit results
    if command -v xmllint &> /dev/null; then
        TOTAL=$(xmllint --xpath "string(//testsuite/@tests)" tests/e2e/playwright-report/results.xml 2>/dev/null || echo "?")
        FAILURES=$(xmllint --xpath "string(//testsuite/@failures)" tests/e2e/playwright-report/results.xml 2>/dev/null || echo "?")
        PASSED=$((TOTAL - FAILURES))
        echo "Test Results:"
        echo "  ✅ Passed: ${PASSED}"
        echo "  ❌ Failed: ${FAILURES}"
        echo "  📊 Total: ${TOTAL}"
    else
        # Fallback: grep for test results
        echo "Test Results:"
        grep -E "<testsuite|<testcase" tests/e2e/playwright-report/results.xml | head -20
    fi
else
    echo "⚠️  No test reports found"
fi

echo ""

# If tests failed, dump logs
if [ $EXIT_CODE -ne 0 ]; then
    echo "=========================================="
    echo "❌ Tests FAILED - Dumping Logs"
    echo "=========================================="
    echo ""

    echo "Frontend logs (last 200 lines):"
    docker logs rag-frontend --tail 200 2>&1 || echo "Failed to get frontend logs"

    echo ""
    echo "RAG API v1 logs (last 200 lines):"
    docker logs rag-api-v1 --tail 200 2>&1 || echo "Failed to get api logs"

    echo ""
    echo "Check for screenshots/videos in:"
    echo "  tests/e2e/test-results/"

    if [ -d tests/e2e/test-results ]; then
        find tests/e2e/test-results -type f -name "*.png" -o -name "*.webm" 2>/dev/null | head -10
    fi
fi

echo ""
echo "=========================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ All E2E tests PASSED"
else
    echo "❌ E2E tests FAILED"
fi
echo "=========================================="

exit $EXIT_CODE

