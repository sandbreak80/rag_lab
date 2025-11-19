# Max Tokens Analysis Across Presets

## Current State

| Preset | Model | Context Window | Max Tokens | Available (typical) | Utilization | Status |
|--------|-------|----------------|------------|---------------------|-------------|--------|
| Minimal | llama3.2:1b | 4096 | 500 | ~3000 | 17% | ⚠️ Low |
| Fast | llama3.2:1b | 8192 | 300 | ~7000 | 4% | ⚠️ Very Low |
| Balanced | llama3.1:8b | 16384 | 500 | ~10000 | 5% | ⚠️ Very Low |
| Quality | qwen2.5:14b | 20480 | 1000 | ~7000 | 14% | ⚠️ Low |
| Maximum | qwen2.5:14b | 24576 | 1500 | ~14000 | 11% | ⚠️ Low |
| Production | mistral:7b | 16384 | 1000 | ~8000 | 13% | ⚠️ Low |

## Real-World Data from Logs

**Balanced Preset:**
- Available for response: ~10,112 tokens
- Max tokens: 500
- **Only using 5% of available capacity!**

**Quality Preset:**
- Available for response: ~6,947 tokens
- Max tokens: 1000
- **Only using 14% of available capacity**

## Analysis

### Problems with Current Values

1. **Severely Underutilized** - Most presets use <15% of available response tokens
2. **Inconsistent** - Fast preset (300) is lower than Minimal (500), despite larger context window
3. **Not Progressive** - Max tokens don't scale with preset quality/context window
4. **Limiting Quality** - Complex queries may need longer responses but are cut off

### Use Case Considerations

**Minimal (Baseline):**
- Use case: Baseline measurement, simple Q&A
- Current: 500 tokens (~375 words)
- **Recommendation: 500-750 tokens** - Keep low for baseline, but allow some expansion

**Fast Mode:**
- Use case: Quick lookups, autocomplete, real-time search
- Current: 300 tokens (~225 words) - **TOO LOW!**
- **Recommendation: 500-800 tokens** - Quick but not truncated

**Balanced (Recommended):**
- Use case: General purpose, daily use, most applications
- Current: 500 tokens (~375 words) - **TOO LOW for general purpose!**
- Available: ~10,000 tokens
- **Recommendation: 1500-2000 tokens** - Comprehensive answers

**Quality:**
- Use case: Research, complex queries, comprehensive results
- Current: 1000 tokens (~750 words) - **TOO LOW for research!**
- Available: ~7,000 tokens
- **Recommendation: 2000-3000 tokens** - Detailed, comprehensive responses

**Maximum:**
- Use case: Educational benchmark, quality ceiling
- Current: 1500 tokens (~1125 words) - **TOO LOW for maximum quality!**
- Available: ~14,000 tokens
- **Recommendation: 3000-4000 tokens** - Maximum detail and comprehensiveness

**Production:**
- Use case: Production deployments, API services
- Current: 1000 tokens (~750 words) - **Reasonable but could be higher**
- Available: ~8,000 tokens
- **Recommendation: 1500-2000 tokens** - Professional, comprehensive responses

## Proposed New Distribution

| Preset | Current | Proposed | Rationale |
|--------|---------|----------|-----------|
| Minimal | 500 | **750** | Allow baseline to be slightly more comprehensive |
| Fast | 300 | **600** | Quick but not truncated (2x increase) |
| Balanced | 500 | **2000** | General purpose needs comprehensive answers (4x increase) |
| Quality | 1000 | **2500** | Research needs detailed responses (2.5x increase) |
| Maximum | 1500 | **3500** | Maximum quality needs maximum detail (2.3x increase) |
| Production | 1000 | **1800** | Professional, comprehensive responses (1.8x increase) |

## Benefits

1. **Better Utilization** - Use 20-30% of available tokens (vs 5-15% currently)
2. **Progressive Scaling** - Max tokens scale with preset quality
3. **No Truncation** - Complex queries can get full answers
4. **Better Quality** - More room for detailed, comprehensive responses
5. **Still Safe** - Well within available capacity (no risk of exceeding context window)

## Trade-offs

### Pros:
- ✅ More comprehensive answers
- ✅ Better for complex queries
- ✅ No truncation issues
- ✅ Better utilization of context window

### Cons:
- ⚠️ Slightly longer latency (more tokens to generate)
- ⚠️ Slightly higher cost (more output tokens)
- ⚠️ May be verbose for simple queries (but LLM can be concise if needed)

## Recommendation

**YES, we should increase max_tokens across all presets!**

The current values are **severely conservative** and are limiting response quality. The proposed values:
- Still leave plenty of headroom (70-80% of available tokens unused)
- Scale appropriately with preset quality
- Allow comprehensive answers for complex queries
- Are well within safe limits

## Implementation

Update `config/presets.json` with new max_tokens values as proposed above.

