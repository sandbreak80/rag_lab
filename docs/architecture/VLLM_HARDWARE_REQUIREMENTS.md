# vLLM Hardware Requirements

## Current Status: **Disabled** ✋

vLLM is **commented out** in `docker-compose.yml` due to GPU compatibility issues with our current hardware.

---

## Why vLLM Isn't Working Now

### Hardware Limitation: **Tesla T4**
- **Compute Capability:** 7.5
- **VRAM:** 16GB
- **Issue:** vLLM v0.11.0 requires compute capability ≥8.0 for full feature support
  - Flash Attention 2 needs 8.0+
  - FlashInfer has compatibility issues with 7.5
  - V1 engine sampling layer doesn't respect fallback flags

### What We Tried
1. ✅ **AWQ 4-bit quantization** (`hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4`)
   - Model loaded successfully (5.37GB VRAM)
   - But engine core failed to initialize
2. ✅ **Disabled FlashInfer** (`--disable-flashinfer`)
3. ✅ **Forced V0 engine** (`VLLM_USE_V1=0`)
4. ✅ **XFormers backend** (`VLLM_ATTENTION_BACKEND=XFORMERS`)
5. ❌ **Result:** Engine still crashes during initialization

---

## ✅ Recommended Hardware for vLLM

### **NVIDIA A4000** (Ideal Upgrade)
- **Compute Capability:** 8.6 ✅
- **VRAM:** 16GB GDDR6 ✅
- **Architecture:** Ampere (full Flash Attention 2 support)
- **Status:** **Fully compatible with vLLM**

### Other Compatible GPUs
| GPU | Compute | VRAM | vLLM Support | Notes |
|-----|---------|------|--------------|-------|
| **A4000** | 8.6 | 16GB | ✅ Full | Recommended upgrade |
| **A5000** | 8.6 | 24GB | ✅ Full | Better for larger models |
| **A6000** | 8.6 | 48GB | ✅ Full | Best for 70B+ models |
| **RTX 4090** | 8.9 | 24GB | ✅ Full | Consumer option |
| **L4** | 8.9 | 24GB | ✅ Full | Cloud GPU option |
| T4 (current) | 7.5 | 16GB | ⚠️ Partial | Flash Attention issues |

---

## Why vLLM? (Future Benefits)

### Performance Advantages
- **10-20x throughput** vs Ollama for concurrent users
- **PagedAttention:** Efficient KV cache management
- **Continuous batching:** Dynamic request scheduling
- **Prefix caching:** Faster repeated prompts

### When to Use vLLM
- ✅ **5-10+ concurrent users**
- ✅ High-throughput production deployments
- ✅ Multi-tenant RAG systems
- ✅ Real-time chat applications

### When Ollama is Fine
- ✅ **1-4 concurrent users** (current use case)
- ✅ Development & testing
- ✅ Single-user deployments
- ✅ Compute capability < 8.0

---

## Quick Activation (After Hardware Upgrade)

Once you have an **A4000 or better GPU**:

1. **Uncomment vLLM service** in `docker-compose.yml`
```bash
# Lines 62-97: Remove the # comments
```

2. **Start vLLM**
```bash
docker compose up -d vllm
docker logs -f rag-vllm
```

3. **Update services to use vLLM API**
   - Model Router: Point to `http://vllm:8000/v1`
   - Prompt Enhancement: Use vLLM endpoint
   - Chat Service: Add vLLM option

4. **Test performance**
```bash
# Compare throughput
hey -n 100 -c 10 http://localhost:8100/v1/completions  # vLLM
hey -n 100 -c 10 http://localhost:11434/api/generate   # Ollama
```

---

## Current Solution: **Ollama** 🦙

We're using **Ollama** for now because:
- ✅ Works perfectly on Tesla T4
- ✅ Handles 1-4 concurrent users well
- ✅ Same models, easy setup
- ✅ Good enough for development

### Performance Baseline
- **Single user:** Sub-second response times ✅
- **2-3 users:** Acceptable latency (~2-3s) ✅
- **5+ users:** Consider vLLM upgrade ⚠️

---

## References
- [vLLM Documentation](https://docs.vllm.ai/)
- [GPU Compute Capabilities](https://developer.nvidia.com/cuda-gpus)
- [Our LLM Comparison](./LLM_INFERENCE_COMPARISON.md)

