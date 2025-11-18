# Quality Presets Reference

This document provides detailed information about each quality preset available in the RAG Lab system. Presets are pre-configured combinations of RAG settings, LLM parameters, and intelligence features optimized for different use cases.

## Overview

The RAG Lab includes 6 quality presets, each designed for specific scenarios:

1. **Minimal** - Fastest, lowest resource usage
2. **Fast** - Quick responses with basic quality
3. **Balanced** (Recommended) - Good balance of speed and quality
4. **Quality** - High quality with comprehensive features
5. **Maximum** - Best quality, all features enabled
6. **Production** - Production-ready configuration

---

## 1. Minimal Preset

**Use Case:** Quick answers, low latency requirements, minimal resource usage

### RAG Configuration
- **Top-K Results:** 3
- **Rerank Top-K:** 3
- **Web Search:** Disabled
- **Web Docs:** 0
- **Web Pages:** 1
- **Knowledge Graph:** Disabled
- **Reranking:** Disabled
- **Query Expansion:** Disabled
- **BM25 Search:** Disabled
- **Hybrid Search:** Disabled

### Intelligence Features
- **Prompt Enhancement:** Disabled
- **Auto Model Routing:** Disabled
- **Query Decomposition:** Disabled
- **Self-RAG:** Disabled
- **Show Reasoning Process:** Disabled

### LLM Configuration
- **Model:** `llama3.2:1b` (1 billion parameters - smallest, fastest)
- **Temperature:** 0.5 (balanced creativity)
- **Max Tokens:** 500 (moderate responses)
- **Context Window:** 4,096 tokens

### Expected Performance
- **Precision:** 60-70%
- **Recall:** 50-60%
- **Latency:** 30-50ms
- **Use Case:** Baseline measurement, minimal resource usage

### Resource Usage
- **GPU Memory:** Minimal (~2GB)
- **CPU Usage:** Low
- **Response Time:** Fastest

---

## 2. Fast Preset

**Use Case:** Quick responses with acceptable quality, moderate resource usage

### RAG Configuration
- **Top-K Results:** 5
- **Rerank Top-K:** 5
- **Web Search:** Disabled
- **Web Docs:** 0
- **Web Pages:** 1
- **Knowledge Graph:** Disabled
- **Reranking:** Disabled
- **Query Expansion:** Enabled
- **BM25 Search:** Disabled
- **Hybrid Search:** Disabled

### Intelligence Features
- **Prompt Enhancement:** Disabled
- **Auto Model Routing:** Disabled
- **Query Decomposition:** Disabled
- **Self-RAG:** Disabled
- **Show Reasoning Process:** Disabled

### LLM Configuration
- **Model:** `llama3.2:1b` (1 billion parameters - smallest, fastest)
- **Temperature:** 0.3 (focused, less creative)
- **Max Tokens:** 300 (short responses)
- **Context Window:** 8,192 tokens

### Expected Performance
- **Precision:** 65-75%
- **Recall:** 55-65%
- **Latency:** 40-60ms
- **Use Case:** Quick lookups, autocomplete, real-time search

### Resource Usage
- **GPU Memory:** Low (~4GB)
- **CPU Usage:** Low-Medium
- **Response Time:** Fast

---

## 3. Balanced Preset (Recommended)

**Use Case:** Default configuration - good balance of speed, quality, and resource usage

### RAG Configuration
- **Top-K Results:** 10
- **Rerank Top-K:** 10
- **Web Search:** Disabled
- **Web Docs:** 5
- **Web Pages:** 2
- **Knowledge Graph:** Disabled
- **Reranking:** Disabled
- **Query Expansion:** Enabled
- **BM25 Search:** Enabled
- **Hybrid Search:** Enabled

### Intelligence Features
- **Prompt Enhancement:** Enabled
- **Auto Model Routing:** Disabled
- **Query Decomposition:** Disabled
- **Self-RAG:** Disabled
- **Show Reasoning Process:** Enabled

### LLM Configuration
- **Model:** `llama3.1:8b` (8 billion parameters - good quality/performance balance)
- **Temperature:** 0.5 (balanced creativity)
- **Max Tokens:** 500 (moderate responses)
- **Context Window:** 16,384 tokens

### Expected Performance
- **Precision:** 85-90%
- **Recall:** 80-85%
- **Latency:** 100-150ms
- **Use Case:** General purpose, daily use, most applications

### Resource Usage
- **GPU Memory:** Medium (~8GB)
- **CPU Usage:** Medium
- **Response Time:** Moderate

---

## 4. Quality Preset

**Use Case:** High quality responses, comprehensive results, research and analysis

### RAG Configuration
- **Top-K Results:** 15
- **Rerank Top-K:** 15
- **Web Search:** Enabled
- **Web Docs:** 20
- **Web Pages:** 5
- **Knowledge Graph:** Enabled
- **Reranking:** Disabled (weighted scoring used instead)
- **Query Expansion:** Enabled
- **BM25 Search:** Enabled
- **Hybrid Search:** Enabled

### Intelligence Features
- **Prompt Enhancement:** Enabled
- **Auto Model Routing:** Enabled
- **Query Decomposition:** Enabled
- **Self-RAG:** Disabled
- **Show Reasoning Process:** Enabled

### LLM Configuration
- **Model:** `qwen2.5:14b` (14 billion parameters - high quality)
- **Temperature:** 0.3 (focused, accurate)
- **Max Tokens:** 1,000 (comprehensive responses)
- **Context Window:** 24,576 tokens (large context for more documents)

### Expected Performance
- **Precision:** 90-95%
- **Recall:** 85-92%
- **Latency:** 200-300ms
- **Use Case:** Research, complex queries, comprehensive results, analysis

### Resource Usage
- **GPU Memory:** High (~14GB)
- **CPU Usage:** Medium-High
- **Response Time:** Moderate-Slow

### Prompt Size Analysis
With **Top-K: 15** and **Context Window: 24,576 tokens**:
- **Estimated Prompt Size:** ~7,000-8,500 tokens
- **Utilization:** ~30-35% of context window
- **Available for Response:** ~16,000-17,000 tokens
- **Status:** ✅ All RAG data fits comfortably

---

## 5. Maximum Preset

**Use Case:** Best possible quality, all features enabled, comprehensive analysis

### RAG Configuration
- **Top-K Results:** 20
- **Rerank Top-K:** 10
- **Web Search:** Enabled
- **Web Docs:** 20
- **Web Pages:** 8
- **Knowledge Graph:** Enabled
- **Reranking:** Enabled
- **Query Expansion:** Enabled
- **BM25 Search:** Enabled
- **Hybrid Search:** Enabled

### Intelligence Features
- **Prompt Enhancement:** Enabled
- **Auto Model Routing:** Enabled
- **Query Decomposition:** Enabled
- **Self-RAG:** Enabled
- **Show Reasoning Process:** Enabled

### LLM Configuration
- **Model:** `qwen2.5:14b` (14 billion parameters - highest quality)
- **Temperature:** 0.1 (very focused, minimal creativity)
- **Max Tokens:** 1,500 (very comprehensive responses)
- **Context Window:** 32,768 tokens (maximum context)

### Expected Performance
- **Precision:** 95-98%
- **Recall:** 90-95%
- **Latency:** 5-30 minutes (hardware dependent)
- **Use Case:** 🎓 Quality benchmark - NOT for production use

### Notes
🎓 **LEARNING POINTS:**
1. Maximum quality comes at extreme latency cost (5-30 min vs < 1s for Balanced)
2. Start during break/lunch - demonstrates why this approach is impractical for interactive use
3. Useful for establishing quality ceiling on your hardware
4. Cancel button stops UI but Ollama continues processing (single LLM limitation)
5. Production systems need: streaming, request queuing, or multiple LLM instances
6. Compare Maximum results with Balanced/Production to see if extra quality is worth the wait
7. Students should determine their own optimal preset based on quality/latency needs

### Resource Usage
- **GPU Memory:** Very High (~16GB)
- **CPU Usage:** High
- **Response Time:** Slow

### Prompt Size Analysis
With **Top-K: 20** and **Context Window: 32,768 tokens**:
- **Estimated Prompt Size:** ~10,000-12,000 tokens
- **Utilization:** ~30-37% of context window
- **Available for Response:** ~20,000-22,000 tokens
- **Status:** ✅ All RAG data fits comfortably

---

## 6. Production Preset

**Use Case:** Production deployment, optimized for reliability and consistency

### RAG Configuration
- **Top-K Results:** 12
- **Rerank Top-K:** 12
- **Web Search:** Enabled
- **Web Docs:** 10
- **Web Pages:** 3
- **Knowledge Graph:** Enabled
- **Reranking:** Disabled
- **Query Expansion:** Enabled
- **BM25 Search:** Enabled
- **Hybrid Search:** Enabled

### Intelligence Features
- **Prompt Enhancement:** Enabled
- **Auto Model Routing:** Enabled
- **Query Decomposition:** Disabled
- **Self-RAG:** Disabled
- **Show Reasoning Process:** Disabled (for cleaner production responses)

### LLM Configuration
- **Model:** `mistral:7b` (7 billion parameters - good quality, reliable)
- **Temperature:** 0.3 (focused, consistent)
- **Max Tokens:** 1,000 (detailed responses)
- **Context Window:** 20,480 tokens

### Expected Performance
- **Precision:** 92-96%
- **Recall:** 88-93%
- **Latency:** 250-350ms
- **Use Case:** Production deployments, API services, world-class RAG

### Notes
This is your take-home configuration. Excellent quality with acceptable latency. Scalable and production-ready.

### Resource Usage
- **GPU Memory:** Medium-High (~10GB)
- **CPU Usage:** Medium
- **Response Time:** Moderate

---

## Comparison Matrix

| Preset | Top-K | Context Window | Model | Max Tokens | Latency | Precision | GPU Memory |
|--------|-------|----------------|-------|------------|---------|-----------|------------|
| Minimal | 3 | 4,096 | llama3.2:1b | 500 | 30-50ms | 60-70% | ~2GB |
| Fast | 5 | 8,192 | llama3.2:1b | 300 | 40-60ms | 65-75% | ~2GB |
| Balanced | 10 | 16,384 | llama3.1:8b | 500 | 100-150ms | 85-90% | ~8GB |
| Quality | 15 | 24,576 | qwen2.5:14b | 1,000 | 200-300ms | 90-95% | ~14GB |
| Maximum | 20 | 32,768 | qwen2.5:14b | 1,500 | 5-30 min | 95-98% | ~16GB |
| Production | 12 | 20,480 | mistral:7b | 1,000 | 250-350ms | 92-96% | ~7GB |

## Feature Comparison

| Feature | Minimal | Fast | Balanced | Quality | Maximum | Production |
|---------|---------|------|----------|---------|---------|------------|
| Web Search | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Knowledge Graph | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Reranking | ❌ | ❌ | ❌ | ❌* | ✅ | ❌ |
| Query Expansion | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| BM25 Search | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Hybrid Search | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Prompt Enhancement | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Auto Model Routing | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Query Decomposition | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ |
| Self-RAG | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Show Reasoning | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ |

*Quality preset uses weighted scoring instead of reranking

## Choosing the Right Preset

### Use Minimal when:
- You need the fastest possible response
- Resource constraints are tight
- Simple, factual queries
- Testing or development

### Use Fast when:
- Quick responses are important
- Moderate quality is acceptable
- General purpose queries
- Limited GPU memory

### Use Balanced when:
- You want a good default configuration
- Balanced speed and quality
- Most general queries
- **Recommended starting point**

### Use Quality when:
- High quality is critical
- Research and analysis tasks
- Complex queries requiring comprehensive results
- You have sufficient GPU memory (14GB+)

### Use Maximum when:
- Best possible quality is required
- Comprehensive analysis needed
- Research papers and critical analysis
- You have high-end GPU (16GB+)

### Use Production when:
- Deploying to production
- Consistent, reliable performance needed
- Clean, professional responses
- Balanced resource usage

## Context Window Utilization

### Quality Preset Example:
- **Context Window:** 24,576 tokens
- **Top-K:** 15 documents
- **Average Chunk Size:** ~450 tokens (target)
- **Estimated Prompt Size:** ~7,000-8,500 tokens
- **Utilization:** ~30-35%
- **Available for Response:** ~16,000-17,000 tokens
- **Status:** ✅ Comfortable margin

### Maximum Preset Example:
- **Context Window:** 32,768 tokens
- **Top-K:** 20 documents
- **Average Chunk Size:** ~450 tokens (target)
- **Estimated Prompt Size:** ~10,000-12,000 tokens
- **Utilization:** ~30-37%
- **Available for Response:** ~20,000-22,000 tokens
- **Status:** ✅ Comfortable margin (but latency is 5-30 minutes!)

### Production Preset Example:
- **Context Window:** 20,480 tokens
- **Top-K:** 12 documents
- **Average Chunk Size:** ~450 tokens (target)
- **Estimated Prompt Size:** ~6,000-7,000 tokens
- **Utilization:** ~30-35%
- **Available for Response:** ~13,000-14,000 tokens
- **Status:** ✅ Comfortable margin with good latency

## Notes

1. **Reranking vs Weighted Scoring:** The Quality preset disables reranking but uses weighted scoring to prioritize RAG/Research sources over web sources.

2. **Model Selection:** Models are chosen based on:
   - Parameter count (affects quality and speed)
   - Context window support
   - Performance characteristics
   - Resource requirements

3. **Temperature Settings:** Lower temperatures (0.2-0.3) provide more focused, accurate responses. Higher temperatures (0.5-0.7) allow more creativity.

4. **Context Window:** Larger context windows allow more documents to be included in the prompt, improving recall but increasing latency.

5. **Top-K vs Context Window:** The number of documents (Top-K) must fit within the context window along with the system prompt, user query, and response space.

## Monitoring

Use the A/B Testing page to compare presets and monitor:
- Prompt size utilization
- Response quality
- Latency
- Token usage
- Source diversity

The prompt size metrics will show if all RAG data fits within the context window for each preset.

