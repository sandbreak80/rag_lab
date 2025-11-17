#!/bin/bash

# Code Sync Status Checker
# Verifies that local, AWS, and GitHub are all in sync

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    RAG Lab - Code Sync Status Checker                   ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════════════╝${NC}"
echo

# AWS Configuration
AWS_IP="${AWS_IP:-54.190.74.93}"
AWS_KEY="${AWS_KEY:-/path/to/your-key.pem}"
AWS_USER="${AWS_USER:-ubuntu}"
AWS_PATH="/home/ubuntu/rag_lab"

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ Error: Not in rag_lab directory${NC}"
    echo "Current directory: $(pwd)"
    exit 1
fi

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}1. LOCAL STATUS${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Get local branch and commit
LOCAL_BRANCH=$(git branch --show-current)
LOCAL_COMMIT=$(git log -1 --oneline)
LOCAL_STATUS=$(git status --short)

echo -e "Branch: ${GREEN}${LOCAL_BRANCH}${NC}"
echo -e "Commit: ${GREEN}${LOCAL_COMMIT}${NC}"

if [ -z "$LOCAL_STATUS" ]; then
    echo -e "Status: ${GREEN}✅ Clean (no uncommitted changes)${NC}"
else
    echo -e "Status: ${YELLOW}⚠️  Uncommitted changes detected:${NC}"
    git status --short | head -10
    if [ $(git status --short | wc -l) -gt 10 ]; then
        echo "... and $(( $(git status --short | wc -l) - 10 )) more files"
    fi
fi

# Check for unpushed commits
UNPUSHED=$(git log origin/${LOCAL_BRANCH}..HEAD --oneline 2>/dev/null || echo "")
if [ -z "$UNPUSHED" ]; then
    echo -e "Unpushed: ${GREEN}✅ None${NC}"
else
    echo -e "Unpushed: ${YELLOW}⚠️  $(echo "$UNPUSHED" | wc -l) commit(s) not pushed to GitHub${NC}"
    echo "$UNPUSHED" | head -5
    if [ $(echo "$UNPUSHED" | wc -l) -gt 5 ]; then
        echo "... and $(( $(echo "$UNPUSHED" | wc -l) - 5 )) more commits"
    fi
fi

echo

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}2. GITHUB STATUS${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Fetch latest from GitHub
echo "Fetching latest from GitHub..."
git fetch origin ${LOCAL_BRANCH} 2>&1 | head -3

GITHUB_COMMIT=$(git log origin/${LOCAL_BRANCH} -1 --oneline 2>/dev/null || echo "Unable to fetch")
echo -e "Latest: ${GREEN}${GITHUB_COMMIT}${NC}"

# Check if local is behind GitHub
BEHIND=$(git log HEAD..origin/${LOCAL_BRANCH} --oneline 2>/dev/null || echo "")
if [ -z "$BEHIND" ]; then
    echo -e "Status: ${GREEN}✅ Up to date with GitHub${NC}"
else
    echo -e "Status: ${YELLOW}⚠️  Local is $(echo "$BEHIND" | wc -l) commit(s) behind GitHub${NC}"
    echo "$BEHIND" | head -5
fi

echo

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}3. AWS INSTANCE STATUS${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check if AWS is accessible
if ! ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -i "$AWS_KEY" ${AWS_USER}@${AWS_IP} "echo connected" >/dev/null 2>&1; then
    echo -e "${RED}❌ Cannot connect to AWS instance${NC}"
    echo "Instance: ${AWS_IP}"
    echo "Make sure the instance is running and SSH key is correct"
    echo
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}⚠️  LOCAL SYNC CHECK ONLY (AWS unavailable)${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════════════════════════════════════════${NC}"
    exit 0
fi

echo -e "Instance: ${GREEN}${AWS_IP}${NC}"

# Get AWS status
AWS_INFO=$(ssh -o StrictHostKeyChecking=no -i "$AWS_KEY" ${AWS_USER}@${AWS_IP} "
    cd ${AWS_PATH} 2>/dev/null || exit 1
    echo 'BRANCH:'
    git branch --show-current 2>/dev/null || echo 'N/A'
    echo 'COMMIT:'
    git log -1 --oneline 2>/dev/null || echo 'N/A'
    echo 'STATUS:'
    git status --short 2>/dev/null || echo 'N/A'
    echo 'UNPUSHED:'
    git log origin/\$(git branch --show-current)..HEAD --oneline 2>/dev/null || echo ''
" 2>/dev/null || echo "ERROR")

if [ "$AWS_INFO" = "ERROR" ]; then
    echo -e "${RED}❌ Error accessing AWS repository${NC}"
    exit 1
fi

# Parse AWS info
AWS_BRANCH=$(echo "$AWS_INFO" | sed -n '/BRANCH:/,/COMMIT:/p' | grep -v "BRANCH:" | grep -v "COMMIT:" | tr -d '\n')
AWS_COMMIT=$(echo "$AWS_INFO" | sed -n '/COMMIT:/,/STATUS:/p' | grep -v "COMMIT:" | grep -v "STATUS:" | tr -d '\n')
AWS_STATUS=$(echo "$AWS_INFO" | sed -n '/STATUS:/,/UNPUSHED:/p' | grep -v "STATUS:" | grep -v "UNPUSHED:")
AWS_UNPUSHED=$(echo "$AWS_INFO" | sed -n '/UNPUSHED:/,$p' | grep -v "UNPUSHED:")

echo -e "Branch: ${GREEN}${AWS_BRANCH}${NC}"
echo -e "Commit: ${GREEN}${AWS_COMMIT}${NC}"

if [ -z "$AWS_STATUS" ] || [ "$AWS_STATUS" = "N/A" ]; then
    echo -e "Status: ${GREEN}✅ Clean (no uncommitted changes)${NC}"
else
    echo -e "Status: ${YELLOW}⚠️  Uncommitted changes on AWS:${NC}"
    echo "$AWS_STATUS" | head -10
fi

if [ -z "$AWS_UNPUSHED" ]; then
    echo -e "Unpushed: ${GREEN}✅ None${NC}"
else
    echo -e "Unpushed: ${YELLOW}⚠️  $(echo "$AWS_UNPUSHED" | wc -l) commit(s) not pushed from AWS${NC}"
    echo "$AWS_UNPUSHED" | head -5
fi

echo

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}4. SYNC SUMMARY${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Determine overall sync status
ISSUES=0

# Check if branches match
if [ "$LOCAL_BRANCH" != "$AWS_BRANCH" ]; then
    echo -e "${YELLOW}⚠️  Branch mismatch: Local(${LOCAL_BRANCH}) vs AWS(${AWS_BRANCH})${NC}"
    ((ISSUES++))
fi

# Check if commits match
LOCAL_COMMIT_HASH=$(echo "$LOCAL_COMMIT" | awk '{print $1}')
AWS_COMMIT_HASH=$(echo "$AWS_COMMIT" | awk '{print $1}')

if [ "$LOCAL_COMMIT_HASH" != "$AWS_COMMIT_HASH" ]; then
    echo -e "${YELLOW}⚠️  Commit mismatch: Local and AWS are not in sync${NC}"
    echo "   Local: $LOCAL_COMMIT"
    echo "   AWS:   $AWS_COMMIT"
    ((ISSUES++))
fi

# Check for uncommitted changes
if [ -n "$LOCAL_STATUS" ]; then
    echo -e "${YELLOW}⚠️  Local has uncommitted changes${NC}"
    ((ISSUES++))
fi

if [ -n "$AWS_STATUS" ] && [ "$AWS_STATUS" != "N/A" ]; then
    echo -e "${YELLOW}⚠️  AWS has uncommitted changes${NC}"
    ((ISSUES++))
fi

# Check for unpushed commits
if [ -n "$UNPUSHED" ]; then
    echo -e "${YELLOW}⚠️  Local has unpushed commits${NC}"
    ((ISSUES++))
fi

if [ -n "$AWS_UNPUSHED" ]; then
    echo -e "${YELLOW}⚠️  AWS has unpushed commits${NC}"
    ((ISSUES++))
fi

# Check if behind GitHub
if [ -n "$BEHIND" ]; then
    echo -e "${YELLOW}⚠️  Local is behind GitHub (needs pull)${NC}"
    ((ISSUES++))
fi

echo

if [ $ISSUES -eq 0 ]; then
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    ✅ ALL SYSTEMS IN SYNC! ✅                             ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${YELLOW}╔══════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║              ⚠️  SYNC ISSUES DETECTED: ${ISSUES} issue(s)                        ║${NC}"
    echo -e "${YELLOW}╚══════════════════════════════════════════════════════════════════════════╝${NC}"
    echo
    echo -e "${BLUE}💡 RECOMMENDATIONS:${NC}"
    echo
    
    if [ -n "$UNPUSHED" ]; then
        echo "📤 Push local commits to GitHub:"
        echo "   git push origin ${LOCAL_BRANCH}"
        echo
    fi
    
    if [ -n "$BEHIND" ]; then
        echo "📥 Pull latest from GitHub:"
        echo "   git pull origin ${LOCAL_BRANCH}"
        echo
    fi
    
    if [ -n "$LOCAL_STATUS" ]; then
        echo "💾 Commit local changes:"
        echo "   git add ."
        echo "   git commit -m \"your message\""
        echo "   git push origin ${LOCAL_BRANCH}"
        echo
    fi
    
    if [ -n "$AWS_UNPUSHED" ]; then
        echo "📤 Push AWS commits to GitHub:"
        echo "   ssh -i \"$AWS_KEY\" ${AWS_USER}@${AWS_IP}"
        echo "   cd ${AWS_PATH} && git push origin ${AWS_BRANCH}"
        echo
    fi
    
    if [ -n "$AWS_STATUS" ] && [ "$AWS_STATUS" != "N/A" ]; then
        echo "💾 Commit AWS changes:"
        echo "   ssh -i \"$AWS_KEY\" ${AWS_USER}@${AWS_IP}"
        echo "   cd ${AWS_PATH}"
        echo "   git add . && git commit -m \"...\" && git push origin ${AWS_BRANCH}"
        echo
    fi
    
    echo -e "${BLUE}📖 See docs/CODE_SYNC_WORKFLOW.md for detailed guidance${NC}"
    
    exit 1
fi
