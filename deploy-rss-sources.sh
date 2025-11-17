#!/bin/bash
# Deploy 31 RSS Sources to AWS Instance
# Stress Test: 1,000+ articles with full-text extraction

set -e

AWS_IP="54.190.74.93"
SSH_KEY="/path/to/your-key.pem"

echo "🚀 Deploying Enhanced Research Agent (31 Sources)"
echo "=================================================="
echo ""

echo "📦 Step 1: Copying new scraper..."
scp -i "$SSH_KEY" \
  services/research-agent/app/scrapers/rss_scraper.py \
  ubuntu@$AWS_IP:~/rag_lab/services/research-agent/app/scrapers/

echo ""
echo "📦 Step 2: Copying updated __init__.py..."
scp -i "$SSH_KEY" \
  services/research-agent/app/scrapers/__init__.py \
  ubuntu@$AWS_IP:~/rag_lab/services/research-agent/app/scrapers/

echo ""
echo "📦 Step 3: Copying updated service.py..."
scp -i "$SSH_KEY" \
  services/research-agent/app/service.py \
  ubuntu@$AWS_IP:~/rag_lab/services/research-agent/app/

echo ""
echo "🔄 Step 4: Restarting research-agent service..."
ssh -i "$SSH_KEY" ubuntu@$AWS_IP \
  "cd rag_lab && docker compose restart research-agent"

echo ""
echo "⏳ Step 5: Waiting for service to start (30 seconds)..."
sleep 30

echo ""
echo "✅ Step 6: Verifying sources..."
SOURCE_COUNT=$(ssh -i "$SSH_KEY" ubuntu@$AWS_IP \
  "curl -s http://localhost:8015/sources | jq '.sources | length'")

echo "   Found $SOURCE_COUNT sources"

if [ "$SOURCE_COUNT" -eq 31 ]; then
    echo "   ✅ All 31 sources initialized!"
else
    echo "   ⚠️  Expected 31 sources, found $SOURCE_COUNT"
fi

echo ""
echo "📊 Current status:"
ssh -i "$SSH_KEY" ubuntu@$AWS_IP \
  "curl -s http://localhost:8015/status | jq '.stats'"

echo ""
echo "=================================================="
echo "✅ Deployment Complete!"
echo ""
echo "To trigger the 1,000+ article fetch:"
echo "  ssh -i $SSH_KEY ubuntu@$AWS_IP \"curl -X POST http://localhost:8015/trigger/all\""
echo ""
echo "To monitor progress:"
echo "  ssh -i $SSH_KEY ubuntu@$AWS_IP \"docker logs -f rag-research-agent\""
echo ""

