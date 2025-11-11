#!/usr/bin/env bash
# ONE-COMMAND E2E TEST EXECUTION
# Copy and paste this entire command into your terminal

ssh ubuntu@16.146.148.184 << 'ENDSSH'
set -euo pipefail

echo "=========================================="
echo "E2E Tests - Automated Execution"
echo "=========================================="

cd /home/ubuntu/rag_lab

# Pull latest
echo "Pulling latest code..."
git pull origin otel

# Deploy services
echo "Deploying services..."
docker compose up -d --build rag-api-v1 frontend
sleep 30

# Sanity checks
echo "Sanity checks..."
curl -sf http://localhost:3000/ready | jq -r '.status'
curl -sf http://localhost:3000/live | jq -r '.status'

# Run tests
echo "Running E2E tests..."
docker compose -f tests/e2e/docker-compose.e2e.yml down 2>/dev/null || true
docker compose -f tests/e2e/docker-compose.e2e.yml up --build --abort-on-container-exit

EXIT_CODE=$?

# Show results
echo ""
echo "=========================================="
echo "Results"
echo "=========================================="

if [ -d "tests/e2e/playwright-report" ]; then
    if [ -f "tests/e2e/playwright-report/results.xml" ]; then
        TOTAL=$(grep -oP 'tests="\K[0-9]+' tests/e2e/playwright-report/results.xml 2>/dev/null || echo "0")
        FAILURES=$(grep -oP 'failures="\K[0-9]+' tests/e2e/playwright-report/results.xml 2>/dev/null || echo "0")

        echo "Total: $TOTAL"
        echo "Failures: $FAILURES"
        echo ""
        echo "View report: python3 -m http.server -d tests/e2e/playwright-report 8888 &"
        echo "Open: http://16.146.148.184:8888/"
    fi
fi

docker compose -f tests/e2e/docker-compose.e2e.yml down 2>/dev/null || true

exit $EXIT_CODE
ENDSSH

