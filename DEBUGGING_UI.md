# Debugging the UI - What to Check

## 🔍 How to Debug

### Step 1: Open Browser DevTools
```
1. Open http://localhost:5555
2. Press F12 (or right-click → Inspect)
3. Go to "Console" tab
```

### Step 2: Look for These Messages

#### ✅ **Good Signs (What You Should See):**
```javascript
✅ Marked.js configured successfully
Stats loaded: {chat_model: "llama3.1:8b", total_chunks: 1141, ...}
```

#### ❌ **Bad Signs (Errors to Report):**
```javascript
❌ Marked.js not loaded!
❌ Error configuring marked: ...
TypeError: marked.parse is not a function
TypeError: Cannot read property 'parse' of undefined
Uncaught ReferenceError: marked is not defined
```

### Step 3: Ask a Question

Type something like "What is AI?" and click Ask.

#### ✅ **What You Should See in Console:**
```javascript
Status: 🔍 Searching vault...
Status: 📝 Context retrieved. Generating answer...
(Then text starts appearing)
```

#### ❌ **Errors to Look For:**
```javascript
Parse error: ...
Render error: ...
TypeError: ...
Fetch failed: ...
```

---

## 🧪 Test Pages

### Simple Test Page (No Styling)
```
http://localhost:8889/test_ui.html
```

This tests:
- ✅ API connectivity
- ✅ Streaming responses
- ✅ Basic parsing
- ❌ NO fancy UI (isolates the problem)

**Click "Test Chat"** and watch the console!

### Main UI
```
http://localhost:5555
```

---

## 🐛 Common Problems & Solutions

### Problem 1: "marked is not defined"

**Symptom**: Console shows `ReferenceError: marked is not defined`

**Cause**: CDN library not loading (network issue or ad blocker)

**Fix**:
```javascript
// Check if CDN is blocked
// In console, type:
typeof marked
// Should return: "object" or "function"
// If "undefined", CDN is blocked
```

**Solution**: Disable ad blockers, check network tab

---

### Problem 2: "marked.parse is not a function"

**Symptom**: Console shows `TypeError: marked.parse is not a function`

**Cause**: Old version of marked.js loaded

**Fix**: I've added fallback code that tries:
1. `marked.parse(text)` (new API)
2. `marked(text)` (old API)
3. Plain text (no markdown)

---

### Problem 3: Responses Not Showing

**Symptom**: Button changes but no text appears

**Possible Causes**:

#### A. **Ollama Not Responding**
```javascript
// Console shows:
Error: Cannot connect to Ollama
```

**Check**:
```bash
docker ps | grep ollama
# Should show: ollama container running

curl http://localhost:11434/api/tags
# Should return: list of models
```

**Fix**:
```bash
docker restart ollama
```

#### B. **Streaming Not Working**
```javascript
// Console shows:
Status: 🔍 Searching vault...
Status: 📝 Context retrieved...
// But then nothing...
```

**Check Network Tab**:
1. F12 → Network tab
2. Ask a question
3. Click on `/api/chat` request
4. Look at "Response" tab
5. Should see JSON streaming in

#### C. **Parse Errors**
```javascript
// Console shows lots of:
Parse error: Unexpected token...
```

**Cause**: Response format mismatch

**Check**:
```bash
curl -X POST http://localhost:5555/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"test"}' | head -20
  
# Should see:
{"type": "status", "message": "🔍 Searching vault..."}
{"type": "chunk", "content": "text here"}
```

---

### Problem 4: Chunk Count Shows 0

**Symptom**: Header shows "📦 0 chunks"

**Fixed**: Should now show 1,141 chunks

**If still broken**:
```javascript
// In console, type:
fetch('/api/stats').then(r => r.json()).then(console.log)

// Should show:
{
  total_chunks: 1141,
  chat_model: "llama3.1:8b",
  ...
}
```

---

### Problem 5: Button Stuck on "Thinking..."

**Symptom**: Button never changes from "⏳ Thinking..."

**Causes**:
1. Ollama crashed
2. Network timeout
3. JavaScript error

**Check**:
```javascript
// Console should show error like:
TypeError: ...
or
Fetch failed: ...
```

**Fix**: Restart everything
```bash
docker-compose restart markdown-rag-mcp
docker restart ollama
```

---

## 📊 What Each Component Does

### 1. Stats Loading (On Page Load)
```javascript
fetch('/api/stats')
  → Returns: {total_chunks: 1141, chat_model: "..."}
  → Updates header
```

### 2. Question Submission
```javascript
User clicks "Ask"
  → Button: "⏳ Thinking..."
  → Creates user message bubble
  → Calls: POST /api/chat
```

### 3. Backend Processing
```python
/api/chat endpoint:
  1. Search vault (RAG)
     → yield {"type": "status", "message": "🔍 Searching..."}
  2. Call Ollama
     → yield {"type": "status", "message": "📝 Context retrieved..."}
  3. Stream response
     → yield {"type": "chunk", "content": "word"} × many times
  4. Send sources
     → yield {"type": "end", "sources": [...]}
```

### 4. Frontend Rendering
```javascript
For each line received:
  - Parse JSON
  - If type="status": Update button text
  - If type="chunk": Append to answer, render markdown
  - If type="end": Show sources
  - If type="error": Show error message
```

---

## 🔧 Quick Fixes

### Reset Everything
```bash
# Stop all
docker-compose down
docker stop ollama

# Start fresh
docker start ollama
docker-compose up -d

# Wait 10 seconds
sleep 10

# Test
curl http://localhost:11434/api/tags
curl http://localhost:5555/api/stats
```

### Check Logs
```bash
# Webapp logs
docker-compose logs markdown-rag-mcp --tail=50

# Ollama logs
docker logs ollama --tail=50
```

### Hard Refresh Browser
```
Mac: cmd + shift + R
Windows: ctrl + shift + R
```

---

## 📝 What to Report

If still broken, please provide:

1. **Console Output** (F12 → Console tab, copy all red errors)
2. **Network Tab** (F12 → Network, click /api/chat request, show Response)
3. **Stats API Response**:
   ```bash
   curl http://localhost:5555/api/stats
   ```
4. **Chat API Test**:
   ```bash
   curl -X POST http://localhost:5555/api/chat \
     -H "Content-Type: application/json" \
     -d '{"question":"test"}' | head -50
   ```
5. **Container Status**:
   ```bash
   docker-compose ps
   docker ps | grep ollama
   ```

---

## ✅ Expected Working Behavior

### Page Load
1. Header shows "1,141 chunks"
2. Console: "✅ Marked.js configured successfully"
3. Console: "Stats loaded: {...}"

### Ask Question
1. Button: "Ask" → "⏳ Thinking..."
2. User message appears
3. Button: "🔍 Searching vault..."
4. AI avatar appears with loading dots
5. Button: "📝 Context retrieved..."
6. Button: "✍️ Writing..."
7. **Text streams in word by word!** ← This is the key!
8. Sources appear at bottom
9. Button: "✅ Done"
10. Button: "Ask" (ready)

---

**If Step 7 doesn't happen** (text streaming), that's the bug to focus on!

