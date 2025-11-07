#!/bin/bash
# Deploy Research Agent UI to AWS
# Date: Nov 7, 2025

set -e

INSTANCE_IP="54.190.74.93"
SSH_KEY="/Users/bmstoner/Downloads/bootcamp.pem"
REMOTE_USER="ubuntu"
REMOTE_DIR="rag_lab"

echo "🚀 Deploying Research Agent UI to AWS"
echo "Instance: $INSTANCE_IP"
echo ""

# Step 1: Copy updated backend files
echo "📦 Step 1: Copying backend files..."
scp -i "$SSH_KEY" \
  services/research-agent/app/service.py \
  "$REMOTE_USER@$INSTANCE_IP:~/$REMOTE_DIR/services/research-agent/app/"

scp -i "$SSH_KEY" \
  services/api-gateway/app/service.py \
  "$REMOTE_USER@$INSTANCE_IP:~/$REMOTE_DIR/services/api-gateway/app/"

echo "✅ Backend files copied"
echo ""

# Step 2: Copy frontend files
echo "📦 Step 2: Copying frontend files..."

# Create research directory on remote
ssh -i "$SSH_KEY" "$REMOTE_USER@$INSTANCE_IP" \
  "mkdir -p ~/$REMOTE_DIR/frontend/src/components/research"

# Copy new component
scp -i "$SSH_KEY" \
  frontend/src/components/research/ResearchAgentPage.tsx \
  "$REMOTE_USER@$INSTANCE_IP:~/$REMOTE_DIR/frontend/src/components/research/"

# Copy updated routing
scp -i "$SSH_KEY" \
  frontend/src/App.tsx \
  "$REMOTE_USER@$INSTANCE_IP:~/$REMOTE_DIR/frontend/src/"

scp -i "$SSH_KEY" \
  frontend/src/components/layout/TabNavigation.tsx \
  "$REMOTE_USER@$INSTANCE_IP:~/$REMOTE_DIR/frontend/src/components/layout/"

# Copy package.json with new dependencies
scp -i "$SSH_KEY" \
  frontend/package.json \
  "$REMOTE_USER@$INSTANCE_IP:~/$REMOTE_DIR/frontend/"

echo "✅ Frontend files copied"
echo ""

# Step 3: Install frontend dependencies
echo "📦 Step 3: Installing frontend dependencies..."
ssh -i "$SSH_KEY" "$REMOTE_USER@$INSTANCE_IP" \
  "cd ~/$REMOTE_DIR/frontend && npm install"

echo "✅ Dependencies installed"
echo ""

# Step 4: Rebuild Docker containers
echo "🐳 Step 4: Rebuilding Docker containers..."
ssh -i "$SSH_KEY" "$REMOTE_USER@$INSTANCE_IP" \
  "cd ~/$REMOTE_DIR && docker compose build frontend research-agent api-gateway"

echo "✅ Containers built"
echo ""

# Step 5: Restart services
echo "🔄 Step 5: Restarting services..."
ssh -i "$SSH_KEY" "$REMOTE_USER@$INSTANCE_IP" \
  "cd ~/$REMOTE_DIR && docker compose up -d frontend research-agent api-gateway"

echo "✅ Services restarted"
echo ""

# Step 6: Wait for services to be healthy
echo "⏳ Step 6: Waiting for services to be healthy..."
sleep 15

# Step 7: Verify deployment
echo "🧪 Step 7: Verifying deployment..."

echo "Checking research agent API..."
ssh -i "$SSH_KEY" "$REMOTE_USER@$INSTANCE_IP" \
  "curl -s http://localhost:8015/status | jq -r '.stats.active_sources' | head -1" && echo "✅ Research Agent API working"

echo "Checking API Gateway proxy..."
ssh -i "$SSH_KEY" "$REMOTE_USER@$INSTANCE_IP" \
  "curl -s http://localhost:8000/api/research-agent/status | jq -r '.stats.active_sources' | head -1" && echo "✅ API Gateway proxy working"

echo "Checking frontend..."
ssh -i "$SSH_KEY" "$REMOTE_USER@$INSTANCE_IP" \
  "curl -s http://localhost:3000 | grep -q 'Research Agent' && echo 'Frontend includes Research Agent'" && echo "✅ Frontend deployed"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ DEPLOYMENT COMPLETE!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 Access your Research Agent UI at:"
echo "   http://$INSTANCE_IP:3000/research"
echo ""
echo "📊 API Endpoints:"
echo "   Status:  http://$INSTANCE_IP:8000/api/research-agent/status"
echo "   Trigger: POST http://$INSTANCE_IP:8000/api/research-agent/trigger/custom"
echo ""
echo "🎉 Ready to fetch AI research content!"

