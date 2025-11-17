# 🔄 Development Workflow & Best Practices

## Overview

This document describes the **proper development workflow** for the RAG Lab project, ensuring code stays in sync across all environments.

---

## 🎯 Core Principle

> **GitHub is the single source of truth. All code changes flow through GitHub.**

```
Local Development → GitHub → AWS Deployment
         ↓            ↓           ↓
      (write)      (review)    (deploy)
```

---

## 🏗️ Three Environments

### 1. **Local Machine (Development)**
- **Purpose:** Write and test code
- **What to do:** Make all code changes here
- **Tools:** VS Code, Cursor, local Git

### 2. **GitHub (Source Control)**
- **Purpose:** Version control, code review, CI/CD
- **What to do:** Push commits, create PRs, track issues
- **Branch:** `security` (main development branch)

### 3. **AWS Ubuntu Instance (Testing/Production)**
- **Purpose:** Deploy and test in production-like environment
- **What to do:** Pull code, deploy, monitor, test
- **What NOT to do:** Edit code directly!

---

## ✅ Proper Development Workflow

### **Step 1: Check Sync Status (Before Making Changes)**

```bash
# Check if all environments are in sync
./scripts/check-sync-status.sh

# If not in sync, follow the recommendations
```

### **Step 2: Create Feature Branch (Optional but Recommended)**

```bash
# For new features or experiments
git checkout -b feature/my-new-feature

# For bug fixes
git checkout -b fix/bug-description

# For quick changes, work directly on security branch
git checkout security
```

### **Step 3: Make Changes Locally**

```bash
# Edit files
vim services/web-search/app/service.py

# Test locally if possible
docker compose up -d web-search
curl http://localhost:8009/health

# Check changes
git status
git diff
```

### **Step 4: Commit Changes**

```bash
# Stage changes
git add .

# Or stage specific files
git add services/web-search/app/service.py

# Commit with meaningful message
git commit -m "feat: add new agentic search feature

- Added LLM query generation
- Improved deduplication logic
- Updated tests"

# Follow conventional commits format:
# feat: new feature
# fix: bug fix
# docs: documentation
# refactor: code refactoring
# test: test changes
# chore: maintenance
```

### **Step 5: Push to GitHub**

```bash
# Push to your feature branch
git push origin feature/my-new-feature

# Or push to security branch
git push origin security
```

### **Step 6: Deploy to AWS**

```bash
# Use the deployment script
./scripts/deploy-to-aws.sh security

# Or deploy specific service
./scripts/deploy-to-aws.sh security web-search

# The script will:
# 1. Check for uncommitted changes
# 2. Verify sync with GitHub
# 3. Pull latest code on AWS
# 4. Build and restart services
# 5. Show health status
```

### **Step 7: Test on AWS**

```bash
# SSH to AWS
ssh -i /Users/bmstoner/SynologyDrive/vcode_projects/your-key.pem ubuntu@54.190.74.93

# Check service status
cd /home/ubuntu/rag_lab
docker compose ps

# Monitor logs
docker compose logs -f web-search

# Test endpoints
curl http://localhost:8009/health
curl -X POST http://localhost:8009/search_agentic -d '...'

# Check monitoring
curl http://localhost:9090/-/healthy  # Prometheus
curl http://localhost:3001/api/health # Grafana
```

### **Step 8: If Issues Found**

```bash
# DO NOT edit files on AWS!
# Exit SSH and go back to local machine

# On Local Machine - Fix the issue
vim services/web-search/app/service.py

# Commit the fix
git add .
git commit -m "fix: resolve deployment issue"
git push origin security

# Deploy again
./scripts/deploy-to-aws.sh security web-search
```

### **Step 9: Merge Feature Branch (If Using)**

```bash
# After testing passes
git checkout security
git merge feature/my-new-feature

# Or create a Pull Request on GitHub for review

# Push merged changes
git push origin security

# Deploy merged code
./scripts/deploy-to-aws.sh security
```

---

## 🚨 Common Mistakes to Avoid

### ❌ **DON'T: Edit Code on AWS**
```bash
# BAD - Never do this!
ssh ubuntu@aws-instance
vim services/web-search/app/service.py  # ❌ WRONG!
```

**Why?** Changes won't be in git, team can't see them, can't roll back, will be lost.

**Instead:** Make changes locally, commit, push, deploy.

---

### ❌ **DON'T: Commit Without Testing**
```bash
# BAD
git add .
git commit -m "untested change"
git push
```

**Why?** Might break production.

**Instead:** Test locally or on AWS before pushing to main branch.

---

### ❌ **DON'T: Have Uncommitted Changes During Deployment**
```bash
# BAD
# (make changes)
./scripts/deploy-to-aws.sh  # ❌ Changes not committed!
```

**Why?** Deployed code won't match local code.

**Instead:** Always commit before deploying.

---

### ❌ **DON'T: Skip Sync Checks**
```bash
# BAD
# (work for hours)
git push  # ❌ Conflicts!
```

**Why?** Might have conflicts, out-of-date code.

**Instead:** Check sync status regularly.

---

## ✅ Best Practices

### 1. **Check Sync Before Starting Work**
```bash
./scripts/check-sync-status.sh
```

### 2. **Commit Frequently**
- Commit small, logical changes
- Don't wait until end of day
- Each commit should work

### 3. **Write Good Commit Messages**
```bash
# Good
git commit -m "feat: add parallel search execution

- Implemented ThreadPoolExecutor for concurrent searches
- Added deduplication logic
- Updated tests to verify parallel behavior"

# Bad
git commit -m "changes"
git commit -m "fix"
git commit -m "wip"
```

### 4. **Use Feature Branches for Large Changes**
```bash
git checkout -b feature/agentic-search
# (make many commits)
git checkout security
git merge feature/agentic-search
```

### 5. **Test Before Pushing to Main Branch**
- Test locally if possible
- Deploy to AWS and test
- Only push to `security` branch when working

### 6. **Use the Deployment Script**
```bash
# Always use this
./scripts/deploy-to-aws.sh security

# Don't manually SSH and git pull
```

### 7. **Monitor After Deployment**
```bash
# Check logs immediately
docker compose logs -f service-name

# Check monitoring dashboards
open http://54.190.74.93:3001  # Grafana
```

---

## 🔧 Useful Commands

### Check What Changed
```bash
# See uncommitted changes
git status
git diff

# See commit history
git log --oneline -10

# See changes between commits
git diff abc123..def456
```

### Undo Changes
```bash
# Undo uncommitted changes
git checkout -- filename.py

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1

# Revert a specific commit
git revert abc123
```

### Sync Commands
```bash
# Update from GitHub
git fetch origin
git pull origin security

# Push to GitHub
git push origin security

# Force push (careful!)
git push origin security --force
```

### Stash Changes
```bash
# Save work in progress
git stash

# List stashes
git stash list

# Apply stash
git stash pop

# Apply specific stash
git stash apply stash@{0}
```

---

## 🔄 Quick Reference

### Daily Workflow
```bash
# 1. Start of day
./scripts/check-sync-status.sh
git pull origin security

# 2. Make changes
vim file.py

# 3. Test locally
docker compose restart service

# 4. Commit
git add .
git commit -m "feat: description"

# 5. Push to GitHub
git push origin security

# 6. Deploy to AWS
./scripts/deploy-to-aws.sh security

# 7. Test on AWS
ssh ubuntu@aws
docker compose logs -f service
```

### Emergency Rollback
```bash
# If deployment breaks production

# Option 1: Revert last commit
git revert HEAD
git push origin security
./scripts/deploy-to-aws.sh security

# Option 2: Roll back to specific commit
git reset --hard abc123
git push origin security --force
./scripts/deploy-to-aws.sh security
```

---

## 📊 Deployment Checklist

Before deploying to AWS, verify:

- [ ] All changes committed
- [ ] Commit message is descriptive
- [ ] Local tests pass
- [ ] No uncommitted changes (`git status`)
- [ ] Pushed to GitHub
- [ ] Sync status is clean
- [ ] Ready to monitor after deployment

After deploying to AWS, verify:

- [ ] Services restarted successfully
- [ ] Health checks pass
- [ ] No errors in logs
- [ ] Endpoints respond correctly
- [ ] Monitoring dashboards show healthy metrics

---

## 🚀 Automation (Future)

### GitHub Actions CI/CD (Recommended)
```yaml
# .github/workflows/deploy.yml
name: Deploy to AWS

on:
  push:
    branches: [ security ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to AWS
        run: ./scripts/deploy-to-aws.sh security
```

### Pre-commit Hooks
```bash
# .git/hooks/pre-commit
#!/bin/bash
# Run linting before commit
python -m flake8 services/
```

### Pre-push Hooks
```bash
# .git/hooks/pre-push
#!/bin/bash
# Check sync status before push
./scripts/check-sync-status.sh
```

---

## 📚 Related Documentation

- **DEPLOYMENT_LOG.md** - Recent deployment history
- **test-enhancements.sh** - Automated testing script
- **QUICK_START_ENHANCEMENTS.md** - Feature documentation
- **IMPLEMENTATION_SUMMARY.md** - Technical details

---

## 🆘 Getting Help

### Check Sync Status
```bash
./scripts/check-sync-status.sh
```

### View Deployment History
```bash
git log --oneline -20
```

### Check AWS Status
```bash
ssh ubuntu@aws "cd rag_lab && docker compose ps"
```

### Emergency Contact
If you're stuck:
1. Check sync status
2. Review this document
3. Check git log for recent changes
4. Don't make ad-hoc changes on AWS!

---

**Remember: GitHub is the source of truth. All changes flow through GitHub.** 🎯
