#!/bin/bash
# Check Sync Status between Local, GitHub, and AWS
# Ensures all environments are in sync

set -e

AWS_HOST="${AWS_HOST:-ubuntu@54.190.74.93}"
AWS_KEY="${AWS_KEY:-/Users/bmstoner/SynologyDrive/vcode_projects/bootcamp.pem}"
BRANCH="${1:-security}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Sync Status Check${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 1. Local Status
echo -e "${BLUE}📍 Local Machine Status${NC}"
echo "Current branch: $(git branch --show-current)"
echo "Current commit: $(git rev-parse --short HEAD)"
echo "Commit message: $(git log -1 --pretty=%B | head -1)"

if ! git diff-index --quiet HEAD --; then
    echo -e "${RED}⚠️  WARNING: Uncommitted changes detected!${NC}"
    git status --short
else
    echo -e "${GREEN}✅ No uncommitted changes${NC}"
fi

# 2. GitHub Status
echo ""
echo -e "${BLUE}🐙 GitHub Status${NC}"
git fetch origin "$BRANCH" 2>/dev/null || true

LOCAL_COMMIT=$(git rev-parse HEAD)
REMOTE_COMMIT=$(git rev-parse "origin/$BRANCH" 2>/dev/null || echo "unknown")

if [ "$LOCAL_COMMIT" = "$REMOTE_COMMIT" ]; then
    echo -e "${GREEN}✅ Local and GitHub are in sync${NC}"
    echo "   Commit: $(git rev-parse --short HEAD)"
else
    BEHIND=$(git rev-list HEAD..origin/$BRANCH --count 2>/dev/null || echo "0")
    AHEAD=$(git rev-list origin/$BRANCH..HEAD --count 2>/dev/null || echo "0")
    
    if [ "$BEHIND" -gt 0 ]; then
        echo -e "${YELLOW}⚠️  Local is $BEHIND commit(s) BEHIND GitHub${NC}"
        echo "   Action: git pull origin $BRANCH"
    fi
    
    if [ "$AHEAD" -gt 0 ]; then
        echo -e "${YELLOW}⚠️  Local is $AHEAD commit(s) AHEAD of GitHub${NC}"
        echo "   Action: git push origin $BRANCH"
        echo ""
        echo "   Unpushed commits:"
        git log origin/$BRANCH..HEAD --oneline | head -5
    fi
fi

# 3. AWS Status
echo ""
echo -e "${BLUE}☁️  AWS Instance Status${NC}"

AWS_COMMIT=$(ssh -o StrictHostKeyChecking=no -i "$AWS_KEY" "$AWS_HOST" \
    "cd /home/ubuntu/rag_lab && git rev-parse --short HEAD 2>/dev/null" || echo "unknown")

AWS_BRANCH=$(ssh -o StrictHostKeyChecking=no -i "$AWS_KEY" "$AWS_HOST" \
    "cd /home/ubuntu/rag_lab && git branch --show-current 2>/dev/null" || echo "unknown")

if [ "$AWS_COMMIT" = "unknown" ]; then
    echo -e "${RED}❌ Cannot connect to AWS instance${NC}"
else
    echo "AWS branch: $AWS_BRANCH"
    echo "AWS commit: $AWS_COMMIT"
    
    LOCAL_COMMIT_SHORT=$(git rev-parse --short HEAD)
    
    if [ "$AWS_COMMIT" = "$LOCAL_COMMIT_SHORT" ]; then
        echo -e "${GREEN}✅ AWS and Local are in sync${NC}"
    else
        echo -e "${RED}⚠️  AWS is OUT OF SYNC with Local${NC}"
        echo "   Local:  $LOCAL_COMMIT_SHORT"
        echo "   AWS:    $AWS_COMMIT"
        echo "   Action: ./scripts/deploy-to-aws.sh $BRANCH"
    fi
fi

# 4. Summary
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Summary${NC}"
echo -e "${BLUE}========================================${NC}"

IN_SYNC=true

if ! git diff-index --quiet HEAD --; then
    echo -e "${RED}❌ Uncommitted changes exist${NC}"
    IN_SYNC=false
fi

if [ "$LOCAL_COMMIT" != "$REMOTE_COMMIT" ]; then
    echo -e "${YELLOW}⚠️  Local and GitHub not in sync${NC}"
    IN_SYNC=false
fi

if [ "$AWS_COMMIT" != "$LOCAL_COMMIT_SHORT" ] && [ "$AWS_COMMIT" != "unknown" ]; then
    echo -e "${RED}⚠️  AWS not in sync with Local${NC}"
    IN_SYNC=false
fi

if [ "$IN_SYNC" = true ]; then
    echo -e "${GREEN}✅ All environments are in sync!${NC}"
    echo ""
    echo "Safe to make changes and deploy."
else
    echo ""
    echo -e "${YELLOW}📋 Recommended Actions:${NC}"
    if ! git diff-index --quiet HEAD --; then
        echo "  1. Commit your changes: git add . && git commit -m 'message'"
    fi
    if [ "$AHEAD" -gt 0 ]; then
        echo "  2. Push to GitHub: git push origin $BRANCH"
    fi
    if [ "$BEHIND" -gt 0 ]; then
        echo "  2. Pull from GitHub: git pull origin $BRANCH"
    fi
    if [ "$AWS_COMMIT" != "$LOCAL_COMMIT_SHORT" ] && [ "$AWS_COMMIT" != "unknown" ]; then
        echo "  3. Deploy to AWS: ./scripts/deploy-to-aws.sh $BRANCH"
    fi
fi

echo ""

