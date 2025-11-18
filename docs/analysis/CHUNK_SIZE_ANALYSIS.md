# Chunk Size Analysis: Can Top-K 15 Fit in 24,576 Tokens?

## Current Configuration

**Chunk Size Settings** (from `services/api/config.py`):
- **Target Chunk Size**: `450 tokens` (default: `RAG_CHUNK_TARGET_TOKENS=450`)
- **Overlap**: `128 tokens` (default: `RAG_CHUNK_OVERLAP_TOKENS=128`)
- **Chunking Mode**: `fixed` (default: `RAG_CHUNKING_MODE=fixed`)

**Quality Preset Settings**:
- **Context Window**: `24,576 tokens`
- **Max Tokens**: `1,000 tokens` (for response)
- **Top-K**: `15 documents`

## Calculation: Can 15 Chunks Fit?

### Theoretical Maximum (Target Size)
```
15 chunks × 450 tokens = 6,750 tokens
```

### Actual Prompt Breakdown
```
System Prompt:        ~200-300 tokens
User Query:           ~50-100 tokens
15 Chunks (450 avg):  ~6,750 tokens
Formatting Overhead:  ~100-200 tokens
─────────────────────────────────────
Total Prompt:         ~7,100-7,350 tokens
```

### Utilization
```
7,350 tokens / 24,576 tokens = 29.9% utilization
```

**✅ YES, 15 chunks easily fit!** We're using only ~30% of the context window.

### Available for Response
```
24,576 (context window)
- 7,350 (prompt)
─────────────────
= 17,226 tokens available for response
```

With `max_tokens=1,000`, we have **17x more space than needed** for the response.

## Actual Chunk Sizes

**Important**: The target is 450 tokens, but actual chunks may vary:
- **Agentic chunking**: May create chunks slightly larger/smaller based on semantic boundaries
- **Fixed chunking**: Should be close to 450 tokens
- **Regex chunking**: May vary based on document structure

### How to Check Actual Chunk Sizes

We track chunk sizes in Prometheus metrics:
- **Metric**: `rag_chunk_size_tokens` (Histogram)
- **Buckets**: `[64, 128, 256, 384, 512, 640, 800, 1024, 1400, 2000]`

**Query Prometheus**:
```promql
# Average chunk size
avg(rag_chunk_size_tokens)

# P95 chunk size (95th percentile)
histogram_quantile(0.95, rag_chunk_size_tokens)

# P99 chunk size (99th percentile)
histogram_quantile(0.99, rag_chunk_size_tokens)
```

**Or check logs**:
Look for `📊 Prompt Size Analysis:` in backend logs:
```
📊 Prompt Size Analysis:
   System prompt: ~250 tokens
   User query: ~75 tokens
   Retrieved documents (15 docs): ~6,825 tokens
   Total prompt: ~7,150 tokens (29.1% of 24576 context window)
   Available for response: ~17,426 tokens (max_tokens=1000)
```

## Worst Case Scenario

If chunks are larger than expected:
- **P99 chunk size**: Could be ~800-1000 tokens (if documents have large sections)
- **15 chunks × 1000 tokens = 15,000 tokens**
- **Total prompt**: ~15,500 tokens (63% utilization)
- **Still fits!** ✅

## Recommendations

1. **Monitor actual chunk sizes** using Prometheus metrics
2. **Check prompt utilization** in A/B testing results
3. **If utilization >80%**, consider:
   - Reducing `top_k` (e.g., 15 → 12)
   - Increasing `context_window` (if model supports it)
   - Reducing `CHUNK_TARGET_TOKENS` (e.g., 450 → 400)

## Current Status

✅ **15 chunks at 450 tokens each = SAFE**
- Only ~30% context window utilization
- Plenty of room for response generation
- Can handle larger chunks (up to ~1,000 tokens each) if needed

