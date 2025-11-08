#!/bin/bash
# Emergency UI Fix - Deploy Updated Frontend with Correct API Routing
# This fixes the 502 error by rebuilding frontend with new nginx.conf

set -e

INSTANCE="16.146.148.184"
SSH_KEY="${SSH_KEY:-bootcamp.pem}"

echo "=================================================="
echo "🚨 EMERGENCY UI FIX - Deploying Updated Frontend"
echo "=================================================="
echo ""

echo "Issue: Frontend nginx still pointing to old api-gateway"
echo "Fix: Rebuild frontend with updated nginx.conf"
echo ""

# Check if we can SSH
if [ ! -f "$SSH_KEY" ]; then
    echo "❌ SSH key not found: $SSH_KEY"
    echo ""
    echo "Please run this command manually on the AWS instance:"
    echo ""
    echo "ssh -i $SSH_KEY ubuntu@$INSTANCE << 'ENDSSH'"
    echo "cd /home/ubuntu/rag_lab"
    echo "git pull origin otel"
    echo "docker compose stop frontend"
    echo "docker compose rm -f frontend"
    echo "docker compose build --no-cache frontend"
    echo "docker compose up -d frontend"
    echo "sleep 10"
    echo "curl http://localhost:3000/live"
    echo "ENDSSH"
    echo ""
    exit 1
fi

echo "Connecting to AWS instance..."
ssh -i "$SSH_KEY" ubuntu@$INSTANCE << 'ENDSSH'
set -e

echo "=== Step 1: Pull latest code ==="
cd /home/ubuntu/rag_lab
git pull origin otel

echo ""
echo "=== Step 2: Verify nginx config has correct routing ==="
if grep -q "proxy_pass http://rag-api-v1:8080" frontend/nginx.conf; then
    echo "✅ nginx.conf has correct routing to rag-api-v1:8080"
else
    echo "❌ nginx.conf still has old routing!"
    exit 1
fi

echo ""
echo "=== Step 3: Stop old frontend ==="
docker compose stop frontend
docker compose rm -f frontend

echo ""
echo "=== Step 4: Rebuild frontend (no cache) ==="
docker compose build --no-cache frontend

echo ""
echo "=== Step 5: Start new frontend ==="
docker compose up -d frontend

echo ""
echo "=== Step 6: Wait for startup ==="
sleep 15

echo ""
echo "=== Step 7: Test health endpoint ==="
HEALTH_RESPONSE=$(curl -s http://localhost:3000/live)
echo "Response: $HEALTH_RESPONSE"

if echo "$HEALTH_RESPONSE" | grep -q "alive"; then
    echo "✅ Frontend now routing correctly to rag-api-v1!"
else
    echo "⚠️ Still getting HTML - may need more time"
fi

echo ""
echo "=== Step 8: Test API endpoint ==="
API_RESPONSE=$(curl -s -X POST http://localhost:3000/api/v1/rag/query \
  -H 'Content-Type: application/json' \
  -d '{"query":"test","user_id":"smoke","groups":[]}' | head -c 100)
  
echo "API Response preview: $API_RESPONSE"

echo ""
echo "=== Step 9: Check Ollama ==="
docker compose ps ollama

echo ""
echo "=== DEPLOYMENT COMPLETE ==="
ENDSSH

echo ""
echo "=================================================="
echo "✅ Frontend Deployment Complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Test UI: http://$INSTANCE:3000"
echo "2. Try a chat query"
echo "3. Verify no 502 errors"
echo ""

