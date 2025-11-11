#!/usr/bin/env bash
set -euo pipefail

echo "=========================================="
echo "Running E2E Tests on AWS Instance"
echo "=========================================="

AWS_HOST="ubuntu@16.146.148.184"
REPO_PATH="/home/ubuntu/rag_lab"

echo "Connecting to: $AWS_HOST"
echo "Repository: $REPO_PATH"
echo ""

# Execute commands on AWS instance
ssh $AWS_HOST << 'ENDSSH'
set -euo pipefail

cd /home/ubuntu/rag_lab

echo "=========================================="
echo "Step 1: Pull Latest Code"
echo "=========================================="
git stash save --keep-index --include-untracked "WIP before E2E test run" || true
git pull origin otel
git stash pop || true

echo ""
echo "=========================================="
echo "Step 2: Deploy Updated Services"
echo "=========================================="
docker compose up -d --build rag-api-v1 frontend

echo ""
echo "Waiting for services to be healthy (30s)..."
sleep 30

echo ""
echo "=========================================="
echo "Step 3: Quick Sanity Checks"
echo "=========================================="
echo "Checking /ready..."
curl -sf http://localhost:3000/ready | jq -r '.status' || echo "❌ Failed"

echo "Checking /live..."
curl -sf http://localhost:3000/live | jq -r '.status' || echo "❌ Failed"

echo ""
echo "=========================================="
echo "Step 4: Running Playwright E2E Tests"
echo "=========================================="
bash scripts/run_playwright_docker.sh

EXIT_CODE=$?

echo ""
echo "=========================================="
echo "Step 5: Test Results Summary"
echo "=========================================="

if [ -d "tests/e2e/playwright-report" ]; then
    echo "✅ Reports generated"
    echo ""
    echo "To view HTML report:"
    echo "  python3 -m http.server -d tests/e2e/playwright-report 8888"
    echo "  Then open: http://16.146.148.184:8888/"
    echo ""

    # Show summary if results.xml exists
    if [ -f "tests/e2e/playwright-report/results.xml" ]; then
        echo "Test Summary:"
        grep -o 'tests="[^"]*"' tests/e2e/playwright-report/results.xml | head -1 || true
        grep -o 'failures="[^"]*"' tests/e2e/playwright-report/results.xml | head -1 || true
        grep -o 'errors="[^"]*"' tests/e2e/playwright-report/results.xml | head -1 || true
    fi
fi

exit $EXIT_CODE
ENDSSH

SSH_EXIT=$?

echo ""
echo "=========================================="
echo "Remote Execution Complete"
echo "=========================================="
echo "Exit code: $SSH_EXIT"

if [ $SSH_EXIT -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Some tests failed - check the report"
fi

exit $SSH_EXIT

