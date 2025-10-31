# 🔒 Model Persistence Explained

## The Short Answer

**YES! Models persist during upgrades.** They're stored in a Docker volume, not in the container.

---

## Visual Explanation

```
┌─────────────────────────────────────────────────────────┐
│  Your MacBook Pro M2                                    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  Docker                                         │    │
│  │                                                 │    │
│  │  ┌──────────────────────┐                      │    │
│  │  │  Container: ollama   │  ← TEMPORARY         │    │
│  │  │  ├─ Ollama software  │    (gets replaced)   │    │
│  │  │  ├─ Runtime process  │                      │    │
│  │  │  └─ Port: 11434      │                      │    │
│  │  └──────────┬───────────┘                      │    │
│  │             │                                   │    │
│  │             │ Uses (but doesn't own)            │    │
│  │             ↓                                   │    │
│  │  ┌──────────────────────┐                      │    │
│  │  │  Volume: ollama      │  ← PERSISTENT        │    │
│  │  │  ├─ llama3.1:8b      │    (never deleted    │    │
│  │  │  ├─ qwen2.5:7b       │     on upgrade)      │    │
│  │  │  ├─ deepseek-r1:7b   │                      │    │
│  │  │  ├─ gemma2:9b        │    Total: ~30GB      │    │
│  │  │  ├─ llama3.2:3b      │                      │    │
│  │  │  ├─ qwen3:4b         │                      │    │
│  │  │  ├─ nomic-embed-text │                      │    │
│  │  │  └─ llava:7b         │                      │    │
│  │  └──────────────────────┘                      │    │
│  │                                                 │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## What Happens During an Upgrade?

### ❌ OLD WAY (Without Volumes - BAD!)

```
Before:                    After:
┌──────────┐              ┌──────────┐
│Container │              │Container │
│ + Models │  → DELETE → │ (empty)  │
└──────────┘              └──────────┘
        ↓                        ↓
   Models LOST!            Need to re-download!
```

### ✅ DOCKER WAY (With Volumes - GOOD!)

```
Before:                         After:
┌──────────┐                   ┌──────────┐
│Container │──┐                │Container │──┐
│ (old)    │  │                │ (new)    │  │
└──────────┘  │                └──────────┘  │
              ↓                              ↓
         ┌─────────┐                    ┌─────────┐
         │ Volume  │  → PRESERVED → →   │ Volume  │
         │ Models  │                    │ Models  │
         └─────────┘                    └─────────┘
              ↑                              ↑
         Still there!                   Same models!
```

---

## Step-by-Step: What upgrade_ollama.sh Does

```bash
1. docker stop ollama
   ┌──────────┐
   │Container │ ← Stops running
   │ (old)    │
   └─────┬────┘
         │ disconnects
         ↓
    ┌─────────┐
    │ Volume  │ ← Models stay here (untouched)
    │ Models  │
    └─────────┘

2. docker rm ollama
   ┌──────────┐
   │Container │ ← Deleted completely
   │ (old)    │ ← Gone forever
   └──────────┘
         
    ┌─────────┐
    │ Volume  │ ← Still perfectly safe!
    │ Models  │
    └─────────┘

3. docker run -v ollama:/root/.ollama
   ┌──────────┐
   │Container │ ← New container created
   │ (new)    │
   └─────┬────┘
         │ connects to
         ↓
    ┌─────────┐
    │ Volume  │ ← Same volume, same models!
    │ Models  │
    └─────────┘
```

---

## Proof It Works

We just ran the upgrade and here's what happened:

```bash
Before upgrade:
NAME                       SIZE      MODIFIED    
llama3.1:8b               4.9 GB    3 hours ago    
qwen2.5:7b                4.7 GB    2 hours ago    
# ... 8 models total

⬇️  UPGRADE HAPPENED ⬇️

After upgrade:
NAME                       SIZE      MODIFIED    
llama3.1:8b               4.9 GB    3 hours ago    ← SAME!
qwen2.5:7b                4.7 GB    2 hours ago    ← SAME!
# ... ALL 8 models still there!
```

**Result: 0 bytes downloaded, all models preserved!**

---

## Model Updates: A Different Story

### When DO You Need to Re-download?

Models themselves can have updates:

```
January 2025: llama3.1:8b (v1) released
         ↓
    You download it (4.9GB)
         ↓
March 2025: llama3.1:8b (v2) released ← New version!
         ↓
    You need to run: ollama pull llama3.1:8b
         ↓
    Downloads v2 (only changed parts)
```

### How Model Updates Work

```bash
# Scenario 1: Model hasn't changed
$ docker exec ollama ollama pull llama3.1:8b
✓ Already up to date

# Scenario 2: Model was updated
$ docker exec ollama ollama pull llama3.1:8b
⬇️  Downloading changes... (500MB)
✓ Updated successfully
```

---

## Storage Location (Deep Dive)

### Logical View (What You See)

```
ollama list
├─ llama3.1:8b
├─ qwen2.5:7b
├─ deepseek-r1:7b
└─ ...
```

### Physical Storage (Where It Actually Is)

```
macOS:
/var/lib/docker/volumes/ollama/_data/
├─ models/
│  ├─ manifests/
│  ├─ blobs/
│  │  ├─ sha256-abc123... (4.9GB) ← llama3.1
│  │  ├─ sha256-def456... (4.7GB) ← qwen2.5
│  │  └─ ...
│  └─ ...
└─ ...
```

---

## Dangerous Commands (⚠️ Don't Run These Unless You Mean It!)

### ❌ This DELETES EVERYTHING:

```bash
docker volume rm ollama  # ← Models gone forever!
```

### ❌ This Also DELETES EVERYTHING:

```bash
docker run ... (without -v ollama:/root/.ollama)
# ← Creates new empty container, can't see old models
```

### ✅ Safe Commands:

```bash
docker stop ollama          # ← Safe
docker restart ollama       # ← Safe
docker rm ollama           # ← Safe (volume persists)
./upgrade_ollama.sh        # ← Safe (preserves volume)
```

---

## Quick Test: Verify Persistence

Run this to prove models persist:

```bash
# See models now
docker exec ollama ollama list

# Restart container (simpler than upgrade)
docker restart ollama

# Wait 5 seconds
sleep 5

# Models still there!
docker exec ollama ollama list
```

---

## Summary: Two Types of Updates

| Update Type | Frequency | Command | Models Preserved? |
|------------|-----------|---------|-------------------|
| **Ollama Software** | Monthly | `./upgrade_ollama.sh` | ✅ YES |
| **Model Files** | As needed | `./check_model_updates.sh` | ✅ YES (old + new) |

**Both are safe operations that preserve your data!**

---

## Common Questions

**Q: If I upgrade Ollama, do I lose my models?**  
A: No! They're stored separately in a Docker volume.

**Q: Do models update automatically?**  
A: No. You must manually pull updates with `ollama pull <model>`.

**Q: How often should I update models?**  
A: Check quarterly, or when you hear about new versions.

**Q: Can I back up my models?**  
A: Yes! Back up the Docker volume: `docker volume inspect ollama`

**Q: What if I delete the container?**  
A: No problem! Models are in the volume, not the container.

**Q: What if I delete the volume?**  
A: ⚠️ All models are deleted! You'll need to re-download (~30GB).

**Q: How much disk space do I need?**  
A: Currently using ~30GB. Plan for 50GB to be safe.

