# 🎯 Model Selection Guide for 16GB GPU

## Overview

This guide helps you choose the right models for different lab exercises and production scenarios. All models are optimized for a 16GB NVIDIA GPU.

---

## 📊 Quick Reference Table

| Model | Size | Context | Speed | Quality | Use Case |
|-------|------|---------|-------|---------|----------|
| **llama3.2:1b** | 1GB | 128K | ⚡⚡⚡⚡⚡ | ⭐⭐ | Speed demos, edge devices |
| **llama3.2:3b** | 2GB | 128K | ⚡⚡⚡⚡ | ⭐⭐⭐ | Fast responses, testing |
| **gemma2:2b** | 2GB | 8K | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ | Efficient, high quality |
| **mistral:7b** | 4GB | 32K | ⚡⚡⚡ | ⭐⭐⭐⭐ | Fast production |
| **llama3.1:8b** | 4.7GB | 128K | ⚡⚡⚡ | ⭐⭐⭐⭐ | **Default** - Best balance |
| **gemma2:9b** | 5.5GB | 8K | ⚡⚡ | ⭐⭐⭐⭐⭐ | High quality, efficient |
| **qwen2.5:14b** | 9GB | 32K | ⚡⚡ | ⭐⭐⭐⭐⭐ | Best quality for 16GB |

---

## 🎓 Lab Exercise Recommendations

### Exercise 1: Speed vs Quality Trade-off

**Goal:** Demonstrate how model size affects response speed and quality

**Models to compare:**
- `llama3.2:1b` (1GB) - Fastest, 100+ tokens/sec
- `llama3.1:8b` (4.7GB) - Balanced, 40-60 tokens/sec
- `qwen2.5:14b` (9GB) - Best quality, 20-30 tokens/sec

**Test prompt:**
```
Explain the difference between RAG and fine-tuning for LLMs. Include pros and cons of each approach.
```

**Expected results:**
- 1B: Fast but may miss nuances
- 8B: Good balance of speed and depth
- 14B: Comprehensive, detailed, but slower

---

### Exercise 2: Context Window vs Model Size

**Goal:** Show GPU memory trade-offs between model size and context length

**Scenario A: Large Context, Small Model**
- Model: `llama3.2:3b` (2GB)
- Context: 128K tokens (~400 pages)
- Use case: Processing entire books, long documents

**Scenario B: Small Context, Large Model**
- Model: `qwen2.5:14b` (9GB)
- Context: 32K tokens (~100 pages)
- Use case: High-quality reasoning on focused content

**Test:**
1. Upload a 50-page PDF
2. Try with 3B model (should handle easily)
3. Try with 14B model (may hit memory limits with full context)

---

### Exercise 3: Embedding Model Comparison

**Goal:** Compare retrieval quality across embedding models

**Models:**
- `nomic-embed-text` (274M) - **Default**, reliable, proven
- `mxbai-embed-large` (335M) - Best retrieval (may have stability issues)
- `all-minilm` (23M) - Tiny, fast, good for demos

**Test:**
1. Upload 20 technical documents
2. Build knowledge graph with each embedding model
3. Run same queries and compare:
   - Retrieval accuracy (relevant sources)
   - Response quality
   - Speed

---

## 🏭 Production Recommendations

### Scenario 1: High-Volume, Fast Responses
**Best choice:** `mistral:7b` or `llama3.1:8b`
- Fast inference (40-60 tok/s)
- Good quality
- Moderate memory footprint
- Can handle multiple concurrent users

### Scenario 2: Best Quality, Lower Volume
**Best choice:** `qwen2.5:14b` or `gemma2:9b`
- Highest quality responses
- Deep reasoning capabilities
- Slower but more accurate
- Best for complex queries

### Scenario 3: Edge Deployment, Resource-Constrained
**Best choice:** `llama3.2:3b` or `gemma2:2b`
- Small memory footprint
- Fast inference
- Acceptable quality for most use cases
- Can run on consumer hardware

### Scenario 4: Long Document Processing
**Best choice:** `llama3.2:3b` or `llama3.1:8b`
- Large context windows (128K)
- Can process entire documents
- Good balance of speed and quality

---

## 🔬 Technical Details

### GPU Memory Usage (Approximate)

| Model | Model Weights | Context (4K) | Context (32K) | Context (128K) |
|-------|---------------|--------------|---------------|----------------|
| llama3.2:1b | 1GB | 1.2GB | 1.5GB | 2.5GB |
| llama3.2:3b | 2GB | 2.3GB | 3GB | 5GB |
| llama3.1:8b | 4.7GB | 5GB | 6.5GB | 10GB |
| qwen2.5:14b | 9GB | 9.5GB | 11GB | 15GB |

**Note:** 128K context with 14B model will use ~15GB, leaving only 1GB for other operations. May cause OOM errors under load.

---

### Performance Benchmarks (16GB RTX 4080)

| Model | Tokens/Sec | Time to First Token | Total Time (500 tokens) |
|-------|------------|---------------------|-------------------------|
| llama3.2:1b | 100-120 | 50ms | 5s |
| llama3.2:3b | 60-80 | 80ms | 8s |
| llama3.1:8b | 40-60 | 150ms | 12s |
| qwen2.5:14b | 20-30 | 300ms | 20s |

---

## 🎯 Model Selection Decision Tree

```
START: What's your priority?

├─ SPEED (< 10s response)
│  ├─ Quality OK: llama3.2:3b
│  └─ Quality important: llama3.1:8b
│
├─ QUALITY (best answers)
│  ├─ Fast enough: gemma2:9b
│  └─ Best possible: qwen2.5:14b
│
├─ LONG DOCUMENTS (> 50 pages)
│  ├─ Speed: llama3.2:3b (128K context)
│  └─ Quality: llama3.1:8b (128K context)
│
└─ RESOURCE-CONSTRAINED
   ├─ Minimum viable: llama3.2:1b
   └─ Best small model: gemma2:2b
```

---

## 🚀 Getting Started

### Pull All Recommended Models

```bash
# Required (always needed)
docker compose exec ollama ollama pull llama3.1:8b
docker compose exec ollama ollama pull nomic-embed-text

# Optional (for lab exercises)
docker compose exec ollama ollama pull llama3.2:1b
docker compose exec ollama ollama pull llama3.2:3b
docker compose exec ollama ollama pull gemma2:2b
docker compose exec ollama ollama pull gemma2:9b
docker compose exec ollama ollama pull mistral:7b
docker compose exec ollama ollama pull qwen2.5:14b
```

Or use the automated script:

```bash
cd scripts
./pull-ollama-models.sh
# Answer 'y' when prompted for optional models
```

---

## 📝 Embedding Model Notes

### nomic-embed-text (Default)
- ✅ Proven, reliable, widely used
- ✅ 8192 token context
- ✅ Excellent retrieval quality
- ✅ No known stability issues

### mxbai-embed-large
- ⚠️ May cause 500 errors in some setups
- ✅ Slightly better retrieval in benchmarks
- ⚠️ Use only if nomic-embed-text doesn't meet needs

### all-minilm
- ✅ Tiny (23MB), very fast
- ⚠️ Lower quality than larger models
- ✅ Good for demos, testing, edge devices

---

## 🔍 Why These Models?

Based on [Ollama's model library](https://ollama.com/library?sort=popular), these models were selected for:

1. **Popularity & Support:** Top models with active communities
2. **16GB GPU Optimization:** All fit comfortably with room for context
3. **Educational Value:** Clear trade-offs for lab exercises
4. **Production Viability:** Real-world use cases
5. **Variety:** Different architectures (Llama, Gemma, Qwen, Mistral)

---

## 📚 Additional Resources

- [Ollama Model Library](https://ollama.com/library?sort=popular)
- [Lab Exercise: Model Size vs Context Window](./lab/EXERCISE_MODEL_VS_CONTEXT.md)
- [GPU Setup Guide](./deployment/GPU_SETUP.md)
- [Performance Tuning](./PERFORMANCE_TUNING.md)

---

## 🎓 Splunk/Cisco Field Team Value

### Key Teaching Points

1. **Resource Trade-offs:**
   - Model size vs context window
   - Speed vs quality
   - Memory vs throughput

2. **Production Decisions:**
   - When to use small vs large models
   - How to benchmark for your use case
   - Cost implications (GPU hours)

3. **Monitoring & Metrics:**
   - Track tokens/sec in Splunk
   - Alert on slow responses
   - Capacity planning based on model choice

4. **Customer Conversations:**
   - "What model should we use?" → Show this guide
   - "Why is it slow?" → Explain model size trade-offs
   - "Can we process longer documents?" → Context window discussion

---

**Last Updated:** November 4, 2025  
**GPU Target:** 16GB NVIDIA (RTX 4080, A4000, etc.)  
**Ollama Version:** Latest (0.5.x+)

