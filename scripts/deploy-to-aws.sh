#!/bin/bash
# Deploy RAG Lab to AWS Instance
# This script ensures code is in sync and deploys properly

set -e

# Configuration
AWS_HOST="${AWS_HOST:-ubuntu@54.190.74.93}"
AWS_KEY="${AWS_KEY:-/Users/bmstoner/SynologyDrive/vcode_projects/bootcamp.pem}"
BRANCH="${1:-security}"
SERVICE="${2:-all}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}RAG Lab Deployment Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Pre-flight checks
echo -e "${YELLOW}🔍 Pre-flight Checks${NC}"

# Check if we have uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo -e "${RED}❌ ERROR: You have uncommitted changes!${NC}"
    echo ""
    git status --short
    echo ""
    echo -e "${YELLOW}Please commit or stash your changes first:${NC}"
    echo "  git add ."
    echo "  git commit -m 'your message'"
    echo "  OR"
    echo "  git stash"
    exit 1
fi

echo -e "${GREEN}✅ No uncommitted changes${NC}"

# Check if local branch is behind remote
git fetch origin "$BRANCH" 2>/dev/null || true
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse "origin/$BRANCH" 2>/dev/null || echo "")

if [ -n "$REMOTE" ] && [ "$LOCAL" != "$REMOTE" ]; then
    BEHIND=$(git rev-list HEAD..origin/$BRANCH --count)
    AHEAD=$(git rev-list origin/$BRANCH..HEAD --count)

    if [ "$BEHIND" -gt 0 ]; then
        echo -e "${YELLOW}⚠️  Your local branch is $BEHIND commit(s) behind origin/$BRANCH${NC}"
        echo -e "${YELLOW}   Run 'git pull origin $BRANCH' first${NC}"
        exit 1
    fi

    if [ "$AHEAD" -gt 0 ]; then
        echo -e "${YELLOW}⚠️  You have $AHEAD unpushed commit(s)${NC}"
        read -p "Push to GitHub first? (Y/n): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            echo -e "${BLUE}📤 Pushing to GitHub...${NC}"
            git push origin "$BRANCH"
            echo -e "${GREEN}✅ Pushed to GitHub${NC}"
        fi
    fi
fi

# Deploy to AWS
echo ""
echo -e "${BLUE}🚀 Deploying to AWS${NC}"
echo -e "${BLUE}   Branch: $BRANCH${NC}"
echo -e "${BLUE}   Service: $SERVICE${NC}"
echo ""

# Create deployment script
DEPLOY_SCRIPT=$(cat <<'EOF'
set -e
cd /home/ubuntu/rag_lab

echo "📥 Pulling latest changes..."
git fetch origin
CURRENT_COMMIT=$(git rev-parse HEAD)
git pull origin BRANCH_PLACEHOLDER

NEW_COMMIT=$(git rev-parse HEAD)

if [ "$CURRENT_COMMIT" = "$NEW_COMMIT" ]; then
    echo "✅ Already up to date"
else
    echo "✅ Updated from $CURRENT_COMMIT to $NEW_COMMIT"
    git log --oneline "$CURRENT_COMMIT".."$NEW_COMMIT"
fi

echo ""
echo "🔨 Building and deploying..."

if [ "SERVICE_PLACEHOLDER" = "all" ]; then
    echo "Restarting all services (including GPU monitoring)..."
    docker compose build
    docker compose --profile gpu up -d
else
    echo "Restarting SERVICE_PLACEHOLDER..."
    docker compose build SERVICE_PLACEHOLDER
    docker compose up -d SERVICE_PLACEHOLDER
fi

echo ""
echo "⏳ Waiting for services to start..."
sleep 5

echo ""
echo "🏥 Health check..."
docker compose ps

echo ""
echo "✅ Deployment complete!"
EOF
)

# Replace placeholders
DEPLOY_SCRIPT="${DEPLOY_SCRIPT//BRANCH_PLACEHOLDER/$BRANCH}"
DEPLOY_SCRIPT="${DEPLOY_SCRIPT//SERVICE_PLACEHOLDER/$SERVICE}"

# Execute on AWS
ssh -o StrictHostKeyChecking=no -i "$AWS_KEY" "$AWS_HOST" "$DEPLOY_SCRIPT"

# Post-deployment checks
echo ""
echo -e "${BLUE}🧪 Post-deployment Checks${NC}"

# Check specific service health
if [ "$SERVICE" != "all" ]; then
    echo "Checking $SERVICE health..."
    ssh -o StrictHostKeyChecking=no -i "$AWS_KEY" "$AWS_HOST" \
        "docker compose ps $SERVICE"
fi

# Show recent logs
echo ""
echo -e "${BLUE}📋 Recent Logs (last 20 lines):${NC}"
if [ "$SERVICE" != "all" ]; then
    ssh -o StrictHostKeyChecking=no -i "$AWS_KEY" "$AWS_HOST" \
        "docker compose logs --tail 20 $SERVICE"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Test your changes: ssh -i '$AWS_KEY' $AWS_HOST"
echo "  2. Monitor logs: docker compose logs -f $SERVICE"
echo "  3. Run tests: ./test-enhancements.sh"
echo ""
