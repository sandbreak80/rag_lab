# 🔄 Action Plan: Sync Local → GitHub → AWS
**Created:** November 7, 2025
**Status:** Ready to Execute

---

## 📊 Current State

### Modified Files (Need Commit)
```
M  BUILD_INFO                                    (version update)
M  CHANGELOG.md                                   (new features documented)
M  services/research-agent/app/scrapers/__init__.py  (25 new scrapers)
M  services/research-agent/app/service.py           (31 sources init)
```

### New Files (Need Add + Commit)
```
??  DEVELOPMENT_WORKFLOW.md                       (this guide!)
??  FUTURE_SCRAPING_ENHANCEMENTS.md              (phase 2 plans)
??  RESEARCH_AGENT_READY_FOR_DEPLOYMENT.md       (deployment doc)
??  RSS_DEPLOYMENT_RESULTS.md                     (test results)
??  RSS_SOURCES_IMPLEMENTATION.md                 (technical doc)
??  SYNC_ACTION_PLAN.md                           (this file)
??  deploy-rss-sources.sh                         (deployment script)
??  scripts/deploy-to-aws.sh                      (reusable script)
??  services/research-agent/app/scrapers/rss_scraper.py  (925 lines!)
??  aws/... (various cloud-init docs)
```

### AWS Instance State
- ✅ Already has latest code (deployed via scp)
- ⚠️ Not synced with git (needs git pull after we push)

---

## 🎯 Step-by-Step Sync Process

### Step 1: Review Changes Locally

```bash
cd /Users/bmstoner/code_projects/rag_lab

# See what changed
git status

# Review diffs (optional but recommended)
git diff services/research-agent/app/service.py
git diff BUILD_INFO
git diff CHANGELOG.md
```

### Step 2: Stage All Changes

```bash
# Stage modified files
git add BUILD_INFO
git add CHANGELOG.md
git add services/research-agent/app/scrapers/__init__.py
git add services/research-agent/app/service.py

# Stage new scraper (the big one!)
git add services/research-agent/app/scrapers/rss_scraper.py

# Stage documentation
git add DEVELOPMENT_WORKFLOW.md
git add FUTURE_SCRAPING_ENHANCEMENTS.md
git add RESEARCH_AGENT_READY_FOR_DEPLOYMENT.md
git add RSS_DEPLOYMENT_RESULTS.md
git add RSS_SOURCES_IMPLEMENTATION.md
git add SYNC_ACTION_PLAN.md

# Stage deployment scripts
git add deploy-rss-sources.sh
git add scripts/deploy-to-aws.sh

# Stage AWS docs (optional)
git add aws/.gitignore
git add aws/CLOUD_INIT_COMPARISON.md
git add aws/CLOUD_INIT_V2_IMPROVEMENTS.md
git add aws/SECURITY_NOTES.md
git add aws/SESSION_SUMMARY_AWS_DEPLOYMENT.md

# Or stage everything at once
git add .
```

### Step 3: Commit with Good Message

```bash
git commit -m "feat: Expand Research Agent from 6 to 31 sources with full-text extraction

Major Features:
- Added 25 new RSS sources from FeedSpot Top 100 AI feeds
- Implemented EnhancedRSSScraper with Trafilatura for full-text extraction
- Created 25 dedicated scraper classes (MarkTechPost, Wired, Google AI, etc.)
- Enhanced initialize_default_sources() to auto-create all 31 sources
- Updated BUILD_INFO to v1.1.0

Technical Details:
- New file: services/research-agent/app/scrapers/rss_scraper.py (925 lines)
- Full-text extraction with Trafilatura (not just RSS summaries)
- User-agent rotation and rate limiting (0.5s delays)
- Fallback to RSS summaries if extraction fails
- 100% idempotent source initialization

Deployment & Testing:
- Deployed to AWS (54.190.74.93) and tested
- Successfully ingested 189 documents (734 chunks)
- 100% success rate on active sources
- Knowledge graph automatically updating
- Daily auto-fetch scheduled at 02:00 UTC

Documentation:
- Added comprehensive development workflow guide
- Documented deployment process and best practices
- Created reusable deployment script
- Detailed technical implementation docs

Results:
- Sources: 6 → 31 (+417%)
- Documents: 80 → 189 (+136%)
- Chunks: 361 → 734 (+103%)
- Expected: 500-700 articles/week

Closes #RSS-EXPANSION"
```

### Step 4: Push to GitHub

```bash
# Push to security branch
git push origin security

# Verify push succeeded
git log -1 --oneline
```

### Step 5: Sync AWS Instance

**Option A: Use New Deployment Script**
```bash
# This will fail because AWS already has the code via scp
# But it will verify sync status

./scripts/deploy-to-aws.sh research-agent
```

**Option B: Manual Sync** (Recommended this time)
```bash
# SSH to AWS
ssh -i /Users/bmstoner/Downloads/bootcamp.pem ubuntu@54.190.74.93

# Navigate to repo
cd ~/rag_lab

# Check current status
git status
git log -1 --oneline

# Pull latest from GitHub
git pull origin security

# Verify sync
git log -1 --oneline

# Exit
exit
```

### Step 6: Verify Everything is Synced

```bash
# On local machine
cd /Users/bmstoner/code_projects/rag_lab

# Get local commit hash
LOCAL_HASH=$(git rev-parse HEAD)
echo "Local: $LOCAL_HASH"

# Get AWS commit hash
AWS_HASH=$(ssh -i /Users/bmstoner/Downloads/bootcamp.pem ubuntu@54.190.74.93 "cd rag_lab && git rev-parse HEAD")
echo "AWS: $AWS_HASH"

# Compare
if [ "$LOCAL_HASH" = "$AWS_HASH" ]; then
    echo "✅ IN SYNC!"
else
    echo "❌ NOT IN SYNC!"
fi
```

---

## 🚀 Future Deployments (Easy Mode)

### For Next Changes

```bash
# 1. Make changes locally
# ... edit files ...

# 2. Test locally
docker compose restart <service>
curl http://localhost:8015/health

# 3. Commit
git add <files>
git commit -m "feat: description"
git push origin security

# 4. Deploy to AWS (automated!)
./scripts/deploy-to-aws.sh <service>

# Done! Script handles: push → pull → restart → verify
```

---

## 📋 Best Practices Checklist

### Before Every Commit
- [ ] Changes tested locally
- [ ] No secrets in code (API keys, passwords)
- [ ] Documentation updated (if needed)
- [ ] BUILD_INFO updated (if version changed)
- [ ] CHANGELOG.md updated (if user-facing change)
- [ ] Lint errors fixed (if applicable)
- [ ] `git diff` reviewed

### Before Every Push
- [ ] All changes committed
- [ ] Commit message is descriptive
- [ ] `git status` shows clean
- [ ] Ready to share with team (if applicable)

### Before Every Deployment
- [ ] Pushed to GitHub
- [ ] AWS instance accessible
- [ ] Services can be restarted safely
- [ ] Monitoring ready (logs, health checks)

---

## 🔍 Useful Commands

### Check Sync Status
```bash
# Local status
git status
git log -1 --oneline

# AWS status
ssh ubuntu@aws "cd rag_lab && git status && git log -1 --oneline"

# GitHub status
git log origin/security -1 --oneline
```

### Compare Commits
```bash
# Local vs GitHub
git log origin/security..HEAD --oneline  # Commits ahead
git log HEAD..origin/security --oneline  # Commits behind

# Local vs AWS
LOCAL=$(git rev-parse HEAD)
AWS=$(ssh ubuntu@aws "cd rag_lab && git rev-parse HEAD")
echo "Match: $([ "$LOCAL" = "$AWS" ] && echo YES || echo NO)"
```

### Emergency Commands
```bash
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Discard all local changes
git reset --hard HEAD

# Revert to specific commit
git reset --hard <commit-hash>

# Stash changes temporarily
git stash
git stash pop  # Restore later
```

---

## 📊 Workflow Diagram

```
┌─────────────────┐
│  Local Machine  │  <- You make changes here
│   (Mac/Cursor)  │
└────────┬────────┘
         │
         │ git add .
         │ git commit -m "..."
         │ git push origin security
         ↓
┌─────────────────┐
│     GitHub      │  <- Single source of truth
│  (Repository)   │
└────────┬────────┘
         │
         │ git pull origin security
         │ (via deployment script)
         ↓
┌─────────────────┐
│  AWS Instance   │  <- Production environment
│ (54.190.74.93)  │
└─────────────────┘
         │
         │ docker compose restart
         │ (services reload code)
         ↓
┌─────────────────┐
│   Running App   │  <- Users access here
│   (Port 3000)   │
└─────────────────┘
```

---

## ✅ Success Criteria

After completing all steps:

- ✅ `git status` shows clean working directory
- ✅ `git log -1` shows your latest commit
- ✅ GitHub repository has your latest commit
- ✅ AWS instance has your latest commit
- ✅ All three (Local/GitHub/AWS) show same commit hash
- ✅ Services running with latest code
- ✅ No uncommitted changes anywhere

---

## 🎉 You'll Know It's Working When...

1. You make a change locally
2. Run `./scripts/deploy-to-aws.sh research-agent`
3. Script shows: "✅ LOCAL AND AWS ARE IN SYNC!"
4. Changes are live on AWS immediately
5. You can roll back by deploying previous commit
6. Team members can pull your changes
7. Everything is tracked in git history

---

## 📞 Need Help?

If things get out of sync:
1. Check this guide's "Emergency Commands" section
2. Review DEVELOPMENT_WORKFLOW.md
3. When in doubt: commit locally, push to GitHub, pull on AWS

**Golden Rule:** Git is your safety net. Commit often, push regularly!

---

**Next Action:** Execute Step 1-6 above to get everything in sync! 🚀

