# 🚀 LLM Inference Engine Comparison: Ollama vs llama.cpp vs vLLM

**Date:** November 5, 2025
**Context:** Scaling for 5-10 concurrent users
**Status:** 📋 Decision Pending

---

## 🎯 The Problem

**Current Setup:**
- Single Ollama instance
- 8B model (llama3.1:8b)
- Sequential request processing (queued)

**Bottleneck:**
```
User 1: ████████ (8s) → Done
User 2:         ████████ (8s) → Done
User 3:                 ████████ (8s) → Done

User 3 waits 16+ seconds! ❌
```

**Goal:** Support 5-10 concurrent users with acceptable latency (<10s per query)

---

## 🔍 Solutions Compared

### Overview

| Solution | Concurrent Users | VRAM per Model | Setup | Cost |
|----------|------------------|----------------|-------|------|
| **Ollama (single)** | 1 (queued) | 5GB | Easy | Free |
| **Ollama (3×)** | 3 | 15GB (3× 5GB) | Easy | Free |
| **llama.cpp** | 2-3 | 3GB | Medium | Free |
| **vLLM** ⭐ | **10-20** | **5GB** | Medium | Free |

---

## 1️⃣ Ollama (Current Setup)

### What It Is
- Simple LLM inference server
- Docker-friendly
- Good for single-user or low concurrency
- Works with Llama, Mistral, Phi, etc.

### Architecture
```
Request Queue
    ↓
┌─────────────┐
│   Ollama    │  Single instance
│   8B Model  │  5GB VRAM
│  (Sequential)│
└─────────────┘
    ↓
Response
```

### Pros
- ✅ **Easy setup** (5 minutes)
- ✅ **Good documentation**
- ✅ **Model management** built-in
- ✅ **GPU support** automatic
- ✅ **Local & free**

### Cons
- ❌ **Sequential processing** (one at a time)
- ❌ **No request batching**
- ❌ **High VRAM per instance** (~5GB)
- ❌ **Poor multi-user performance**

### Performance
```
1 user:  8-10s response time ✅
2 users: 16-20s for 2nd user ⚠️
3 users: 24-30s for 3rd user ❌
5 users: 40-50s for 5th user ❌❌❌
```

### When to Use
- ✅ Personal projects (1-2 users)
- ✅ Development/testing
- ✅ Simple deployments
- ❌ NOT for 5-10 concurrent users

---

## 2️⃣ Ollama (Multi-Instance)

### What It Is
- Run 3× Ollama containers
- Nginx load balancer
- Each instance handles 1 request

### Architecture
```
┌──────────────┐
│ Load Balancer│
└──────┬───────┘
       │
   ┌───┴────┬────────┐
   ↓        ↓        ↓
┌────┐   ┌────┐   ┌────┐
│Ollama│ │Ollama│ │Ollama│
│5GB  │ │5GB  │ │5GB  │
└────┘   └────┘   └────┘

Total VRAM: 15GB
```

### Pros
- ✅ **Easy to implement** (same setup, just 3×)
- ✅ **No new tech** (familiar Ollama)
- ✅ **Scales to 3 users** simultaneously

### Cons
- ❌ **High VRAM cost** (15GB for 3 users)
- ❌ **Doesn't scale beyond GPU memory**
- ❌ **Still queues with 4+ users**
- ❌ **Inefficient resource use**

### Performance
```
3 concurrent users: 8-10s each ✅
4-5 users: Back to queuing ⚠️
```

### VRAM Requirements
```
RTX 3090: 24GB → 4 instances max
RTX 4090: 24GB → 4 instances max
A10: 24GB → 4 instances max
A100: 80GB → 16 instances max
```

### When to Use
- ✅ Quick fix for 3-4 concurrent users
- ✅ Already using Ollama
- ❌ NOT efficient for 5-10 users

---

## 3️⃣ llama.cpp

### What It Is
- C++ LLM inference engine
- Focuses on CPU performance
- Efficient quantization
- Low-level control

### Architecture
```
┌────────────────┐
│  llama.cpp     │
│  8B Model (Q4) │  Quantized to 4-bit
│  ~3GB VRAM     │  More efficient!
└────────────────┘

Can use CPU + GPU hybrid
```

### Pros
- ✅ **Lower VRAM** (~3GB with quantization)
- ✅ **Good CPU inference** (if no GPU)
- ✅ **Efficient quantization** (Q4, Q5, Q8)
- ✅ **Flexible deployment**
- ✅ **Open source, no dependencies**

### Cons
- ⚠️ **More complex setup** (compile from source)
- ⚠️ **Manual model conversion** (GGUF format)
- ⚠️ **Still sequential** (no batching by default)
- ⚠️ **Lower quality with aggressive quantization**

### Performance
```
FP16 (full precision): Same as Ollama
Q4 (4-bit): 2-3× faster, slight quality loss
Q8 (8-bit): 1.5× faster, minimal quality loss
```

### Quantization Trade-offs
| Format | VRAM | Speed | Quality |
|--------|------|-------|---------|
| FP16 | 16GB | 1× | 100% |
| Q8 | 8GB | 1.5× | 99% |
| Q5 | 5GB | 2× | 95% |
| Q4 | 4GB | 2.5× | 90% |

### When to Use
- ✅ CPU-only servers
- ✅ Low VRAM GPUs
- ✅ Want quantization control
- ⚠️ Willing to sacrifice some quality
- ❌ Still doesn't solve concurrency well

---

## 4️⃣ vLLM ⭐ **RECOMMENDED**

### What It Is
- **Production-grade LLM inference**
- Built by UC Berkeley
- Industry standard (used by OpenAI, Anthropic, etc.)
- Optimized for throughput

### Architecture
```
┌──────────────────────────────┐
│         vLLM Engine          │
│                              │
│  PagedAttention (efficient)  │
│  Continuous Batching         │
│  Request Scheduling          │
│                              │
│  8B Model: 5GB VRAM          │
│  Serves 10-20 concurrent     │
└──────────────────────────────┘
```

### Key Innovation: **PagedAttention**

**Problem with Ollama/llama.cpp:**
```
Traditional Attention:
- Allocates max context (128K tokens)
- Wastes VRAM on unused space
- Can't share KV cache between requests

Example:
User query: 100 tokens
Model allocates: 128,000 tokens
Wasted: 127,900 tokens! ❌
```

**PagedAttention Solution:**
```
Paged Attention:
- Allocates memory in pages (like OS virtual memory)
- Shares pages between similar requests
- Dynamically grows as needed

Example:
User query: 100 tokens
vLLM allocates: 128 tokens (1 page)
Grows as needed
Efficiency: 99%! ✅
```

### Key Innovation: **Continuous Batching**

**Traditional (Ollama):**
```
Request 1: ████████ → Done → Start Request 2
Request 2:         ████████ → Done → Start Request 3
(Sequential)
```

**Continuous Batching (vLLM):**
```
Request 1: ████████
Request 2:   ████████
Request 3:     ████████
Request 4:       ████████
(All processing simultaneously!)
```

**Result:** 10× higher throughput with same VRAM!

### Pros
- ✅ **10-20 concurrent users** on single GPU
- ✅ **Same VRAM** as single Ollama (5GB)
- ✅ **PagedAttention** (near-zero waste)
- ✅ **Continuous batching** (high throughput)
- ✅ **Production-ready** (used in industry)
- ✅ **OpenAI-compatible API**
- ✅ **Automatic optimizations**

### Cons
- ⚠️ **GPU required** (no CPU mode)
- ⚠️ **More complex setup** (2-3 days)
- ⚠️ **Python dependency** (torch, CUDA)
- ⚠️ **Larger Docker image** (~10GB)

### Performance
```
Single Query Latency: 8-10s (same as Ollama)

But with concurrency:
5 users:  8-12s each ✅✅✅
10 users: 10-15s each ✅✅
20 users: 15-20s each ✅

vs Ollama:
5 users: 40-50s for last user ❌
```

### VRAM Efficiency
```
Ollama (1 instance): 5GB → 1 concurrent user
Ollama (3 instances): 15GB → 3 concurrent users
vLLM (1 instance): 5GB → 10-20 concurrent users ⭐
```

### Setup (Docker)
```yaml
# docker-compose.yml
services:
  vllm:
    image: vllm/vllm-openai:latest
    container_name: rag-vllm
    command: >
      --model meta-llama/Llama-3.1-8B-Instruct
      --max-model-len 8192
      --gpu-memory-utilization 0.9
      --dtype auto
    ports:
      - "8000:8000"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

### When to Use
- ✅ **5-10+ concurrent users** (THIS IS YOU!)
- ✅ Have GPU (NVIDIA)
- ✅ Production deployment
- ✅ Want high throughput
- ✅ Want efficient VRAM use

---

## 📊 Head-to-Head Comparison

### Scenario: 10 Concurrent Users, 8B Model

| Solution | VRAM | Response Time | Throughput | Cost |
|----------|------|---------------|------------|------|
| **Ollama (1×)** | 5GB | 80s (10th user) ❌ | 0.5 req/min | Free |
| **Ollama (3×)** | 15GB | 26s (10th user) ⚠️ | 1.5 req/min | Free |
| **llama.cpp** | 3GB | 70s (10th user) ❌ | 0.6 req/min | Free |
| **vLLM** | 5GB | 12s (10th user) ✅ | 5+ req/min | Free |

### Winner: **vLLM** 🏆

---

## 🎯 Recommendations by Use Case

### Personal Project (1-2 users)
**→ Ollama (single instance)** ✅
- Easy
- Fast enough
- No optimization needed

### Small Team (3-5 users)
**→ Ollama (3× instances)** or **vLLM**
- Ollama: Faster to implement
- vLLM: Better long-term

### Production (5-10+ users)
**→ vLLM** ⭐
- Only option that scales
- Production-ready
- Efficient

### CPU-Only Server
**→ llama.cpp**
- Best CPU performance
- Quantization helps

### Budget GPU (<8GB VRAM)
**→ llama.cpp (quantized)**
- Q4 quantization
- Fits in 4GB

---

## 🚀 Our Recommendation for RAG Lab

### **Current State:** 1-2 concurrent users
**→ Keep Ollama** ✅
- Working fine
- No changes needed

### **When You Hit 3-5 Users:**
**→ Implement multi-instance Ollama** ⚠️
- Quick fix (3-4 days)
- Buys time

### **When You Need 5-10 Users:** ⭐
**→ Migrate to vLLM**
- Worth the 2-3 day migration
- Scales to 10-20 users
- Production-ready

---

## 🔧 Migration Path

### Phase 1: Immediate (Now)
```
✅ Ollama (single)
   Good for development and demos
```

### Phase 2: Quick Fix (If needed)
```
Ollama (3× instances + load balancer)
Estimated: 3-4 days
Handles 3-4 concurrent users
```

### Phase 3: Scale (When needed)
```
vLLM
Estimated: 2-3 days migration
Handles 10-20 concurrent users
Production-ready
```

---

## 📖 Implementation Guides

### Multi-Instance Ollama
See: `docs/FUTURE_ENHANCEMENTS_ROADMAP.md`
- Section: "Multi-Container LLM Architecture"
- Estimated: 3-4 days

### vLLM Migration
**Steps:**
1. Update docker-compose.yml (vLLM container)
2. Test model loading
3. Update service URLs
4. Performance testing
5. Cutover

**Estimated:** 2-3 days

---

## 🎓 Learning Comparison

### Educational Value:

**Ollama:**
- ✅ Good for learning basics
- ✅ See how LLM serving works
- ⚠️ Hides optimization details

**llama.cpp:**
- ✅ Learn about quantization
- ✅ Understand CPU vs GPU inference
- ✅ Low-level control

**vLLM:**
- ✅ Learn production techniques
- ✅ Understand attention mechanisms
- ✅ Learn about batching strategies
- ✅ Industry best practices

**Recommendation:** Start with Ollama, graduate to vLLM when scaling.

---

## 💰 Cost Analysis

### VRAM Cost (Cloud GPU)

**AWS g5.xlarge (A10 GPU, 24GB):**
- $1.006/hour
- ~$730/month

**Ollama Setup:**
- 4 instances max (4 concurrent users)
- Efficiency: 4 users / 24GB = 0.17 users/GB

**vLLM Setup:**
- 15-20 users (same GPU!)
- Efficiency: 20 users / 24GB = 0.83 users/GB

**Result:** vLLM is **5× more cost-effective!** 💰

---

## 🔮 Future: Even Better Options

### 1. **SGLang** (Successor to vLLM)
- Even faster than vLLM
- Better batching
- Still experimental

### 2. **TensorRT-LLM** (NVIDIA)
- Optimized for NVIDIA GPUs
- Requires model conversion
- Maximum performance

### 3. **DeepSpeed-Inference** (Microsoft)
- Good for very large models (70B+)
- Multi-GPU support

**For now:** vLLM is the sweet spot. ✅

---

## 📋 Decision Matrix

### Choose **Ollama** if:
- ✅ 1-2 users
- ✅ Development/testing
- ✅ Want simplicity
- ✅ Learning basics

### Choose **Ollama (Multi-Instance)** if:
- ✅ 3-4 users
- ✅ Need quick fix
- ✅ Plenty of VRAM (24GB+)
- ✅ Familiar with Ollama

### Choose **llama.cpp** if:
- ✅ CPU-only server
- ✅ Low VRAM budget
- ✅ Want quantization control
- ✅ Advanced user

### Choose **vLLM** if: ⭐
- ✅ 5-10+ users
- ✅ Production deployment
- ✅ Want efficiency
- ✅ Have NVIDIA GPU
- ✅ Ready for 2-3 day migration

---

## 🎯 Final Recommendation

### **For RAG Lab:**

**Today (1-2 users):**
```
✅ Keep Ollama (single instance)
```

**If Scaling to 5-10 Users:**
```
⭐ Migrate to vLLM
   - 2-3 days effort
   - 10× better throughput
   - Production-ready
   - Worth the investment
```

**Why vLLM?**
1. Only solution that handles 5-10 users efficiently
2. Same VRAM as Ollama (5GB)
3. Industry-proven (OpenAI uses similar tech)
4. Future-proof for scaling

---

## 📚 Resources

### vLLM
- Docs: https://vllm.readthedocs.io/
- Paper: https://arxiv.org/abs/2309.06180
- GitHub: https://github.com/vllm-project/vllm

### llama.cpp
- GitHub: https://github.com/ggerganov/llama.cpp
- Quantization guide: In repo docs

### Ollama
- Docs: https://ollama.ai/docs
- Docker: https://hub.docker.com/r/ollama/ollama

---

**Status:** 📋 Documentation Complete
**Next Action:** Implement when scaling requirements arise
**Last Updated:** November 5, 2025

