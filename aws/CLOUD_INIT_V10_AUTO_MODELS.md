# 🚀 Cloud-Init v10: Automatic Model Pulling

## Overview

**Version 10** of the cloud-init script automatically pulls **ALL 10 Ollama models** during instance creation. No more waiting or manual model pulling!

---

## 🎯 What Changed from v9 to v10

### **v9 (Previous):**
- ✅ Pulls 2 required models: `llama3.1:8b`, `nomic-embed-text`
- ⚠️  Pulls 8 optional models **in background** (may not finish)
- ⚠️  Models may not be ready when you start using the system

### **v10 (Current):**
- ✅ Pulls **ALL 10 models synchronously** during build
- ✅ Shows progress: `[1/10]`, `[2/10]`, etc.
- ✅ All models guaranteed ready when instance is accessible
- ✅ Estimated build time: **25-30 minutes** (network dependent)

---

## 📦 All 10 Models Pulled Automatically

| # | Model | Size | Purpose |
|---|-------|------|---------|
| 1 | **llama3.1:8b** | 4.9GB | Main chat/LLM model |
| 2 | **nomic-embed-text** | 274MB | Primary embedding model |
| 3 | **llama3.2:1b** | 1.3GB | Ultra-fast demos |
| 4 | **llama3.2:3b** | 2.0GB | Query generation (agentic search) |
| 5 | **gemma2:2b** | 1.6GB | Efficient alternative |
| 6 | **gemma2:9b** | 5.4GB | High performance |
| 7 | **mistral:7b** | 4.4GB | Fast production model |
| 8 | **qwen2.5:14b** | 9.0GB | Best quality (16GB GPU) |
| 9 | **mxbai-embed-large** | 669MB | Best retrieval quality |
| 10 | **all-minilm** | 45MB | Tiny/fast embedding |

**Total: ~30GB of models**

---

## ⏱️ Deployment Timeline

### **Phase 1: System Setup (5-8 minutes)**
- Install Docker & Docker Compose
- Install NVIDIA drivers
- Install NVIDIA Container Toolkit
- **Reboot** (to activate GPU drivers)

### **Phase 2: RAG Lab Deployment (18-22 minutes)**
1. Clone RAG Lab repository (1-2 min)
2. Build Docker containers (3-5 min)
3. Start all services (1-2 min)
4. **Pull all 10 Ollama models (12-15 min)** ← New!
5. Create admin user (30 sec)
6. Generate deployment info (30 sec)

**Total: ~25-30 minutes from launch to fully ready**

---

## 🔍 Model Pulling Progress

The cloud-init log shows real-time progress:

```bash
===== Pulling ALL Ollama Models =====
This will take 15-20 minutes depending on network speed

📦 REQUIRED MODELS (2/10)
================================
[1/10] Pulling llama3.1:8b (4.9GB)...
✅ Successfully pulled llama3.1:8b

[2/10] Pulling nomic-embed-text (274MB)...
✅ Successfully pulled nomic-embed-text

📦 OPTIONAL MODELS (8/10)
================================
[3/10] Pulling llama3.2:1b...
✅ Successfully pulled llama3.2:1b

[4/10] Pulling llama3.2:3b...
✅ Successfully pulled llama3.2:3b

... (continues through all 10 models)

📋 ALL DOWNLOADED MODELS:
================================
NAME                        ID              SIZE      MODIFIED
llama3.1:8b                 ...             4.9 GB    Just now
nomic-embed-text:latest     ...             274 MB    Just now
llama3.2:1b                 ...             1.3 GB    Just now
... (all 10 models listed)
```

---

## 📊 Monitoring Deployment Progress

### **Option 1: Check cloud-init status**
```bash
ssh ubuntu@<instance-ip>
sudo cloud-init status --wait
# Shows: "status: done" when complete
```

### **Option 2: Watch the log in real-time**
```bash
ssh ubuntu@<instance-ip>
tail -f /var/log/cloud-init-output.log

# Or the RAG Lab setup log:
tail -f /var/log/rag-lab-setup.log
```

### **Option 3: Check systemd service**
```bash
ssh ubuntu@<instance-ip>
systemctl status rag-lab-deploy.service
# Shows "active (exited)" when complete
```

### **Option 4: Verify models are ready**
```bash
ssh ubuntu@<instance-ip>
docker exec rag-ollama ollama list
# Should show all 10 models
```

---

## 🚀 Launch Command

```bash
cd /Users/bmstoner/code_projects/rag_lab/aws/scripts
./aws-launch-rag-lab.sh

# The script automatically uses v10 cloud-init
# Fallback order: v10 → v9 → v3 → v2 → v1
```

---

## ✅ Benefits of v10

### **1. Fully Ready on First Access**
- All models pre-loaded
- No "model not found" errors
- Immediate use of all features

### **2. Predictable Deployment**
- Known completion time (~30 min)
- All models or none (no partial state)
- Easy to verify completion

### **3. Better Testing**
- Test with any model immediately
- Compare model performance
- No waiting for background pulls

### **4. Production Ready**
- All capabilities available
- No post-deployment setup
- Consistent environment

---

## 🔧 Configuration

### **Modify Models to Pull**

Edit `/aws/cloud-init/cloud-init-rag-lab-v10.yaml`:

```yaml
# Add/remove models from this array:
ALL_OPTIONAL_MODELS=(
  "llama3.2:1b"
  "llama3.2:3b"
  "gemma2:2b"
  "gemma2:9b"
  "mistral:7b"
  "qwen2.5:14b"
  "mxbai-embed-large"
  "all-minilm"
  # Add more here if needed
)
```

### **Adjust Timeouts**

If your network is slow, increase wait times:

```yaml
# Wait longer for Ollama to be ready
for i in {1..60}; do  # Changed from {1..30}
  docker exec rag-ollama ollama list >/dev/null 2>&1 && break
  sleep 5
done
```

---

## 🐛 Troubleshooting

### **Model Pull Fails**

```bash
# Check which models succeeded
docker exec rag-ollama ollama list

# Manually pull missing model
docker exec rag-ollama ollama pull <model-name>
```

### **Deployment Taking Too Long**

```bash
# Check if still running
systemctl status rag-lab-deploy.service

# Check progress
tail -f /var/log/rag-lab-setup.log

# Check network speed
curl -s https://speed.cloudflare.com/__down?bytes=10000000 -o /dev/null -w '%{speed_download}\n'
```

### **Out of Disk Space**

```bash
# Check disk usage
df -h

# Models need ~35GB
# Ensure instance has 50GB+ EBS volume
```

---

## 📈 Comparison: v9 vs v10

| Feature | v9 | v10 |
|---------|-----|------|
| **Required Models** | ✅ 2 models | ✅ 2 models |
| **Optional Models** | ⚠️  Background (may not finish) | ✅ Synchronous (guaranteed) |
| **Models on Completion** | 2-10 (unpredictable) | 10 (always) |
| **Build Time** | 15-20 min | 25-30 min |
| **Ready to Use** | Partially | Fully |
| **Progress Visibility** | Limited | Detailed ([1/10], [2/10]...) |
| **Production Ready** | ⚠️  Needs verification | ✅ Yes |

---

## 🎯 Use Cases

### **Development/Testing**
- Immediately test any model
- Compare model performance
- Switch models without waiting

### **Demos/Presentations**
- All features work out-of-the-box
- No "waiting for model" issues
- Professional first impression

### **Production Deployment**
- Consistent environment
- All capabilities available
- Predictable behavior

### **Lab Exercises**
- Speed vs quality comparisons
- Model routing examples
- Multi-model workflows

---

## 📚 Related Documentation

- **`aws/scripts/aws-launch-rag-lab.sh`** - Launch script (auto-uses v10)
- **`scripts/pull-ollama-models.sh`** - Model definitions
- **`DEVELOPMENT_WORKFLOW.md`** - Deployment best practices
- **`aws/CLOUD_INIT_COMPARISON.md`** - Version history

---

## 🔄 Migration from v9 to v10

### **For New Instances:**
```bash
# Just launch normally - v10 is default
./aws/scripts/aws-launch-rag-lab.sh
```

### **For Existing Instances:**
```bash
# Option 1: Manually pull missing models
ssh ubuntu@<instance-ip>
cd /home/ubuntu/rag_lab
./scripts/pull-ollama-models.sh
# Answer 'y' to pull optional models

# Option 2: Recreate instance with v10
./aws/scripts/terminate-cleanup.sh
./aws/scripts/aws-launch-rag-lab.sh
```

---

## 💡 Pro Tips

1. **Monitor with `watch`:**
   ```bash
   watch -n 5 'docker exec rag-ollama ollama list | wc -l'
   # Watch model count increase
   ```

2. **Check completion:**
   ```bash
   # Should show 10 models + header = 11 lines
   docker exec rag-ollama ollama list | wc -l
   ```

3. **Verify all services:**
   ```bash
   docker compose ps
   # All should show "healthy" or "Up"
   ```

4. **Test immediately:**
   ```bash
   # Test agentic search (uses llama3.2:3b)
   curl -X POST http://localhost:8009/search_agentic \
     -H "Content-Type: application/json" \
     -d '{"query":"test","limit":5}'
   ```

---

## 🏆 Key Improvement

> **"Instance is fully ready when accessible. No post-deployment model pulling required."**

This is how production systems should work - **predictable, complete, and ready to use**.

---

## ✨ Summary

**Cloud-Init v10** ensures all 10 Ollama models are **automatically pulled and ready** when your RAG Lab instance finishes deploying.

**Build time:** ~30 minutes
**Models ready:** 10/10
**Manual steps:** 0
**Production ready:** ✅ Yes

---

**Updated:** Nov 7, 2025
**Version:** 10.0
**Status:** Production Ready ✅

