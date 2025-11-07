# Code Sync Workflow - AWS ↔ GitHub

## 🚨 **CRITICAL: Preventing Code Loss**

All code changes must flow through GitHub to prevent loss. Never make changes directly on AWS without syncing back.

---

## 📋 **Recommended Workflow**

### **Option 1: Local Development (BEST PRACTICE)**

```bash
# 1. Make changes locally
cd /Users/bmstoner/code_projects/rag_lab
# ... edit files ...

# 2. Test locally (if possible)
docker compose up -d

# 3. Commit to GitHub
git add .
git commit -m "your changes"
git push origin security

# 4. Deploy to AWS
./scripts/deploy-to-aws.sh

# 5. Test on AWS
# Visit http://54.190.74.93:3000
```

**Benefits:**
- ✅ All changes tracked in Git
- ✅ Easy to revert
- ✅ Can test locally first
- ✅ No risk of loss

---

### **Option 2: Emergency AWS Fixes (USE SPARINGLY)**

If you MUST make changes directly on AWS:

```bash
# 1. SSH to AWS
ssh -i "bootcamp.pem" ubuntu@54.190.74.93

# 2. Make your changes
cd /home/ubuntu/rag_lab
# ... edit files ...

# 3. IMMEDIATELY commit and push
git add .
git commit -m "emergency fix: description"
git push origin security

# 4. Pull changes locally
# (on your local machine)
cd /Users/bmstoner/code_projects/rag_lab
git pull origin security
```

**⚠️ Risks:**
- Easy to forget to push
- No local testing
- Can cause merge conflicts

---

## 🔄 **Automated Sync Check Script**

Use this script to check if AWS and GitHub are in sync:

```bash
./scripts/check-sync-status.sh
```

This checks:
- ✅ Uncommitted changes on AWS
- ✅ Unpushed commits on AWS  
- ✅ Differences between local, AWS, and GitHub

---

## 🛡️ **Preventing Code Loss**

### **Daily Habits:**

1. **Start of Day:**
   ```bash
   cd /Users/bmstoner/code_projects/rag_lab
   git pull origin security
   ```

2. **Before Making Changes:**
   ```bash
   # Check sync status
   ./scripts/check-sync-status.sh
   ```

3. **After Making Changes:**
   ```bash
   # Commit and push
   git add .
   git commit -m "describe your changes"
   git push origin security
   
   # Deploy to AWS
   ./scripts/deploy-to-aws.sh
   ```

4. **End of Day:**
   ```bash
   # Verify everything is pushed
   ./scripts/check-sync-status.sh
   ```

---

## 📝 **Git Best Practices**

### **Commit Messages:**

Good commit messages:
```bash
git commit -m "feat: add GPU monitoring to dashboard"
git commit -m "fix: container network metrics not displaying"
git commit -m "docs: add code sync workflow guide"
```

Bad commit messages:
```bash
git commit -m "update"
git commit -m "fixes"
git commit -m "wip"
```

### **When to Commit:**

✅ **Commit when:**
- Feature is working
- Bug is fixed
- Tests pass
- Documentation updated

❌ **Don't commit:**
- Broken code
- Incomplete features
- Debug print statements
- Temporary test files

---

## 🚨 **Emergency Recovery**

### **If You Made Changes on AWS and Forgot to Push:**

```bash
# SSH to AWS
ssh -i "bootcamp.pem" ubuntu@54.190.74.93

# Check what changed
cd /home/ubuntu/rag_lab
git status
git diff

# Commit and push
git add .
git commit -m "emergency: recovered uncommitted changes"
git push origin security

# Pull locally
# (on local machine)
cd /Users/bmstoner/code_projects/rag_lab
git pull origin security
```

### **If Local and AWS Diverged:**

```bash
# On local machine
cd /Users/bmstoner/code_projects/rag_lab

# See what's different
git fetch origin
git diff origin/security

# If AWS has changes you want:
git pull origin security

# If local has changes you want:
git push origin security

# If both have important changes (merge conflict):
git pull origin security
# ... resolve conflicts ...
git add .
git commit -m "merge: resolved local/AWS differences"
git push origin security
```

---

## 📊 **Monitoring Sync Status**

### **Check GitHub Last Commit:**
Visit: https://github.com/sandbreak80/rag_lab/commits/security

### **Check AWS Last Commit:**
```bash
ssh -i "bootcamp.pem" ubuntu@54.190.74.93 \
  "cd /home/ubuntu/rag_lab && git log -1 --oneline"
```

### **Check Local Last Commit:**
```bash
cd /Users/bmstoner/code_projects/rag_lab
git log -1 --oneline
```

**All three should match!**

---

## 🔧 **Cleanup Commands**

### **Remove Backup Files on AWS:**
```bash
ssh -i "bootcamp.pem" ubuntu@54.190.74.93 \
  "cd /home/ubuntu/rag_lab && find . -name '*.backup' -delete && find . -name '*.pre-*' -delete"
```

### **Reset AWS to GitHub State:**
```bash
ssh -i "bootcamp.pem" ubuntu@54.190.74.93 \
  "cd /home/ubuntu/rag_lab && git fetch origin && git reset --hard origin/security"
```

⚠️ **Warning:** This discards ALL uncommitted changes on AWS!

---

## ✅ **Quick Reference**

### **Typical Development Flow:**

1. **Local:** Make changes
2. **Local:** `git add . && git commit -m "..." && git push origin security`
3. **Deploy:** `./scripts/deploy-to-aws.sh`
4. **Test:** Visit http://54.190.74.93:3000
5. **Verify:** `./scripts/check-sync-status.sh`

### **Before Shutting Down for the Day:**

```bash
# Check everything is pushed
./scripts/check-sync-status.sh

# Should see: "✅ All systems in sync!"
```

---

## 🎯 **Summary**

**Golden Rules:**
1. ✅ **Always** commit and push to GitHub
2. ✅ **Always** use local → GitHub → AWS flow
3. ✅ **Check** sync status regularly
4. ❌ **Never** leave uncommitted changes on AWS
5. ❌ **Never** make changes directly on AWS without pushing

**Remember:** GitHub is your source of truth. If it's not in GitHub, it doesn't exist!

---

## 📞 **Quick Help**

**Q: I made changes on AWS and forgot to commit. What do I do?**  
A: SSH to AWS, commit, push immediately. Then pull locally.

**Q: How do I know if AWS and GitHub are in sync?**  
A: Run `./scripts/check-sync-status.sh`

**Q: I have merge conflicts. Help!**  
A: This means you made changes in both places. You'll need to manually resolve conflicts or choose one version.

**Q: Can I test on AWS before committing?**  
A: Yes, but commit and push AS SOON AS you're done testing!

---

**Last Updated:** 2025-11-07  
**Maintained By:** RAG Lab Team

