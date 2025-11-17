#!/bin/bash
# Deploy Nginx routing updates to AWS
# Run this script from your local machine (it will SSH to AWS)

set -e

INSTANCE_IP="16.146.148.184"
SSH_KEY="${SSH_KEY:-your-key.pem}"

echo "=== Deploying Nginx Routing Updates to $INSTANCE_IP ==="
echo ""

ssh -i "$SSH_KEY" ubuntu@$INSTANCE_IP << 'ENDSSH'
cd /home/ubuntu/rag_lab

echo "=== Current status ==="
git branch --show-current
git log --oneline -3
echo ""

echo "=== Pulling latest otel branch ==="
git pull origin otel
echo ""

echo "=== Stopping old containers ==="
docker compose stop rag-api-v1 frontend
docker compose rm -f rag-api-v1 frontend
echo ""

echo "=== Building and starting with new nginx configs ==="
docker compose up -d --build rag-api-v1 frontend
echo ""

echo "=== Waiting 20s for startup ==="
sleep 20
echo ""

echo "=== Container status ==="
docker compose ps | grep -E "(rag-api-v1|frontend)"
echo ""

echo "=== Testing health endpoint (should return JSON) ==="
curl -s http://localhost:3000/live | head -10
echo ""
echo ""

echo "=== Testing API endpoint (should return RAG response) ==="
curl -s -X POST http://localhost:3000/api/v1/rag/query \
  -H 'Content-Type: application/json' \
  -d '{"query":"What is RAG?","user_id":"demo","groups":[]}' | jq -r '.answer' | head -5
echo ""

echo "=== Deployment complete! ==="
ENDSSH

echo ""
echo "✅ Done! Now test from your browser:"
echo "   Frontend: http://$INSTANCE_IP:3000"
echo "   Health:   curl http://$INSTANCE_IP:3000/live"
echo "   API:      curl -X POST http://$INSTANCE_IP:3000/api/v1/rag/query -H 'content-type: application/json' -d '{\"query\":\"test\",\"user_id\":\"demo\",\"groups\":[]}'"

