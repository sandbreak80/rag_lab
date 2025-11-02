# Toggle Verification Guide

## Current Status

### ✅ What IS Working:
1. **State Management**: Toggles use `set((state) => ...)` for atomic updates
2. **LocalStorage**: Changes save immediately via Zustand middleware
3. **Config Passing**: ChatInterface passes full config to API on every query
4. **All 6 Presets**: Backend returns all presets correctly

### ❓ What to Verify:

## Manual Test Steps

### Test 1: Verify Toggles Update UI State
1. Open http://localhost:5173/settings
2. Open Browser DevTools (F12)
3. Go to: **Application** → **Local Storage** → `http://localhost:5173`
4. Find the `rag_config` key
5. Click a toggle (e.g., "Query Expansion")
6. **Watch** the `rag_config` value update in real-time
   - Should see `"useQueryExpansion": true` or `false`

**Expected**: ✅ Value changes immediately
**If broken**: ❌ Value doesn't change or changes slowly

---

### Test 2: Verify Toggles Persist Across Reload
1. In Settings, enable several features (e.g., BM25, Hybrid, Query Expansion)
2. Note which toggles are ON
3. **Refresh the page** (Cmd+R)
4. Go back to Settings
5. Check if toggles are still in same positions

**Expected**: ✅ All toggles remember their state
**If broken**: ❌ Toggles reset to defaults

---

### Test 3: Verify Config is Sent to Backend
1. Open DevTools → **Network** tab
2. Go to Chat page
3. Enable "Query Expansion" in Settings
4. Send a chat message: "What is RAG?"
5. In Network tab, find the request to `/api/chat`
6. Click it → **Payload** tab
7. Look for: `"useQueryExpansion": true`

**Expected**: ✅ Request includes all toggle states
**If broken**: ❌ Config not sent or incorrect values

---

### Test 4: Verify Backend Applies Config
1. In Settings, disable ALL features (use "Minimal" preset)
2. Send query: "What is agentic chunking?"
3. Check the response sources/metrics
4. Then, enable ALL features (use "Maximum" preset)
5. Send same query again
6. Compare response time and quality

**Expected**:
- ✅ Minimal: Fast (~30ms), basic sources
- ✅ Maximum: Slower (2000ms+), comprehensive sources with reranking

**If broken**:
- ❌ No difference between minimal and maximum
- ❌ Backend ignoring config

---

## Quick Diagnostic

Run this in browser console while on http://localhost:5173:

```javascript
// Check current config
const config = JSON.parse(localStorage.getItem('rag_config'));
console.table(config);

// Toggle a feature
config.useQueryExpansion = !config.useQueryExpansion;
localStorage.setItem('rag_config', JSON.stringify(config));

// Reload to see if it persists
location.reload();
```

---

## Known Working State

After fixes, the following should be TRUE:

- [x] `toggleFeature` uses `set((state) => ...)` (no stale state)
- [x] `loadPreset` maps snake_case to camelCase correctly
- [x] All 6 presets available in UI
- [x] Config passed to `api.sendMessage(query, config)`
- [x] LocalStorage saves on every change

---

## If Toggles Still Don't Work

### Possible Issues:

1. **React Not Reloading**
   - Hard refresh: Cmd+Shift+R
   - Clear cache and reload

2. **Zustand Store Not Updating**
   - Check console for errors
   - Verify `useConfigStore` selector is correct

3. **Switch Component Broken**
   - Try clicking directly on toggle circle
   - Check if `onCheckedChange` is firing

4. **Backend Not Running**
   - Verify: `curl http://localhost:8000/health`
   - Check Docker: `docker ps | grep api-gateway`

---

## Current Architecture

```
User clicks toggle
  ↓
RAGToggles.tsx calls store.toggleFeature(key)
  ↓
configStore.ts: set((state) => { [key]: !state[key] })
  ↓
saveToLocalStorage('rag_config', newConfig)
  ↓
UI re-renders with new state
  ↓
User sends chat query
  ↓
ChatInterface passes config to api.sendMessage()
  ↓
API sends config to backend microservices
  ↓
Backend applies config to search/reranking/etc
```

Every step in this chain should work now. If toggles still don't work, we need to identify which step is failing.

