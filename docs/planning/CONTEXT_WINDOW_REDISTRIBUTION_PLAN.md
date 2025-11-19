# Context Window Redistribution Plan

## Current State

| Preset | Model | Current Context Window | GPU Memory (estimated) | Status |
|--------|-------|----------------------|------------------------|--------|
| Minimal | llama3.2:1b | 4096 | ~1.2GB | ✅ OK |
| Fast | llama3.2:1b | 8192 | ~1.5GB | ✅ OK |
| Balanced | llama3.1:8b | 16384 | ~6.5GB | ✅ OK |
| Quality | qwen2.5:14b | 24576 | ~10.5GB | ⚠️ Close to limit |
| Maximum | qwen2.5:14b | 24576 | ~10.5GB | ⚠️ Close to limit |
| Production | mistral:7b | 20480 | ~7-8GB | ✅ OK |

## Problem

1. **Quality and Maximum both use 24576** - No differentiation
2. **Quality preset is at GPU memory limit** - Only ~4.5GB headroom on 15GB GPU
3. **No progressive scaling** - Context windows don't scale smoothly with preset quality
4. **Production uses 20K** - Higher than Balanced (16K) but lower than Quality (24K) - inconsistent

## Proposed Distribution

### Strategy
- **Progressive scaling**: Each preset should have a larger context window than the previous
- **GPU memory safety**: Ensure qwen2.5:14b presets stay under 11GB total
- **Model-appropriate sizing**: Match context window to model capabilities
- **Production stability**: Conservative settings for production use

### New Distribution

| Preset | Model | Proposed Context Window | GPU Memory (estimated) | Rationale |
|--------|-------|------------------------|------------------------|-----------|
| Minimal | llama3.2:1b | **4096** | ~1.2GB | Keep - baseline |
| Fast | llama3.2:1b | **8192** | ~1.5GB | Keep - fast queries |
| Balanced | llama3.1:8b | **16384** | ~6.5GB | Keep - good balance |
| Quality | qwen2.5:14b | **20480** | ~10GB | **Reduce from 24576** - safer, still excellent |
| Maximum | qwen2.5:14b | **24576** | ~10.5GB | Keep - maximum safe for 14B model |
| Production | mistral:7b | **16384** | ~7GB | **Reduce from 20480** - more conservative for stability |

### Benefits

1. **Progressive scaling**: 4K → 8K → 16K → 20K → 24K (smooth progression)
2. **GPU memory safety**: Quality preset now has ~5GB headroom (vs ~4.5GB)
3. **Clear differentiation**: Quality (20K) vs Maximum (24K) - 4K difference
4. **Production stability**: Lower context window reduces memory pressure
5. **Model-appropriate**:
   - Small models (1B): 4K-8K
   - Medium models (7B-8B): 16K
   - Large models (14B): 20K-24K

## Implementation

### Files to Update
1. `config/presets.json` - Update context_window values
2. No frontend changes needed - presets are loaded dynamically from API

### Testing Checklist
- [ ] Verify presets load correctly in Settings page
- [ ] Verify presets load correctly in A/B Testing page
- [ ] Test each preset to ensure context window is applied
- [ ] Verify GPU memory usage stays within limits
- [ ] Test Maximum preset with 24K context window

## Rollout Plan

1. Update `config/presets.json`
2. Commit and push to `otel` branch
3. Deploy to EC2
4. Restart API Gateway to reload presets
5. Test in UI (Settings and A/B Testing pages)
6. Monitor GPU memory usage

## Notes

- **No breaking changes**: Frontend loads presets dynamically, so no code changes needed
- **Backward compatible**: Existing saved configs won't be affected
- **Easy to adjust**: Can fine-tune values based on real-world usage

