# Research Agent UI Implementation
**Date:** November 7, 2025
**Status:** ✅ Backend Complete, Frontend Ready for Integration

---

## 🎯 What Was Built

### Backend API (✅ Complete)
**File:** `services/research-agent/app/service.py`

Added new endpoint: `POST /trigger/custom`

**Features:**
- Configurable source limit (1-31 sources)
- Configurable lookback period (1-90 days)
- Automatic knowledge graph rebuild after fetch
- Background processing (non-blocking)
- Progress tracking via status endpoint

**API Spec:**
```json
POST /api/research-agent/trigger/custom
{
  "source_limit": 10,      // 1-31
  "days_back": 7,          // 1-90
  "rebuild_kg": true       // boolean
}

Response:
{
  "success": true,
  "message": "Fetch started for 10 sources (7 days)",
  "source_limit": 10,
  "days_back": 7,
  "sources_selected": 10,
  "rebuild_kg": true,
  "status": "running"
}
```

### API Gateway Proxy (✅ Complete)
**File:** `services/api-gateway/app/service.py`

Added routes:
- `GET /api/research-agent/status` - Get current stats
- `POST /api/research-agent/trigger/custom` - Trigger custom fetch
- `GET /api/research-agent/sources` - List all sources

### Frontend Component (✅ Complete)
**File:** `frontend/src/components/research/ResearchAgentPage.tsx`

**Features:**
- ✅ Dual sliders (sources & days)
- ✅ Real-time status display
- ✅ Estimated impact calculation
- ✅ Progress tracking
- ✅ Toast notifications
- ✅ Auto-refresh (10s interval)
- ✅ Beautiful UI with cards
- ✅ How It Works section
- ✅ Source list display

---

## 📋 Remaining Integration Steps

### Step 1: Add to App Routing

**File:** `frontend/src/App.tsx`

```typescript
// Add import
import { ResearchAgentPage } from './components/research/ResearchAgentPage';

// Add route in switch/case or router
case 'research':
  return <ResearchAgentPage />;
```

### Step 2: Add to Tab Navigation

**File:** `frontend/src/components/layout/TabNavigation.tsx`

```typescript
const tabs = [
  { id: 'chat', label: 'Chat', icon: <MessageSquare className="h-5 w-5" /> },
  { id: 'documents', label: 'Documents', icon: <FileText className="h-5 w-5" /> },
  { id: 'research', label: 'Research Agent', icon: <RefreshCw className="h-5 w-5" /> }, // NEW!
  { id: 'metrics', label: 'Metrics', icon: <BarChart3 className="h-5 w-5" /> },
  { id: 'settings', label: 'Settings', icon: <Settings className="h-5 w-5" /> },
  { id: 'lab', label: 'Lab', icon: <Flask className="h-5 w-5" /> },
];
```

### Step 3: Create Slider Component (if not exists)

**File:** `frontend/src/components/ui/slider.tsx`

If you don't have a slider component yet, create one using Radix UI or shadcn/ui:

```bash
# If using shadcn/ui
npx shadcn-ui@latest add slider
```

Or create a simple one:
```typescript
// frontend/src/components/ui/slider.tsx
import * as React from 'react';

export function Slider({ value, onValueChange, min, max, step, className }: any) {
  return (
    <input
      type="range"
      value={value[0]}
      onChange={(e) => onValueChange([parseInt(e.target.value)])}
      min={min}
      max={max}
      step={step}
      className={`w-full ${className}`}
    />
  );
}
```

### Step 4: Deploy Updated Services

```bash
# Copy updated files to AWS
scp services/research-agent/app/service.py ubuntu@aws:~/rag_lab/services/research-agent/app/
scp services/api-gateway/app/service.py ubuntu@aws:~/rag_lab/services/api-gateway/app/

# Restart services
ssh ubuntu@aws "cd rag_lab && docker compose restart research-agent api-gateway"

# Build and deploy frontend
cd frontend && npm run build
docker compose build frontend
docker compose up -d frontend
```

---

## 🎨 UI Features

### Sliders
1. **Number of Sources (1-31)**
   - Visual badge showing selection
   - Displays "(All)" when max selected
   - Real-time update

2. **Lookback Period (1-90 days)**
   - Visual badge showing days
   - Helpful tip about trade-offs
   - Real-time update

### Status Dashboard
- Active sources count
- Items ingested total
- Success rate percentage
- Last fetch timestamp

### Estimated Impact
- Sources selected
- Days configured
- Max articles estimate
- Estimated time (based on batching)

### Auto Knowledge Graph Rebuild
- Happens automatically after successful fetch
- User is informed via UI
- No manual intervention needed

---

## 🔄 How It Works

### User Flow
1. User opens "Research Agent" tab
2. Adjusts sliders:
   - Sources: 10 (out of 31)
   - Days: 7
3. Clicks "Start Research Agent"
4. UI shows "Fetching in Progress..."
5. Status auto-refreshes every 10 seconds
6. Toast notification on completion
7. Knowledge graph rebuilds automatically
8. New content ready for search!

### Backend Flow
```
1. UI → POST /api/research-agent/trigger/custom
2. API Gateway → Forward to research-agent:8015
3. Research Agent → Start background thread
4. Thread → Fetch from N sources (M days lookback)
5. Thread → Ingest articles to vector DB
6. Thread → POST /knowledge-graph/build
7. Knowledge Graph → Rebuild from vector DB
8. Done! → Status updated
```

---

## 🧪 Testing

### Test Locally First

```bash
# 1. Start services
docker compose up -d

# 2. Test backend endpoint
curl -X POST http://localhost:8000/api/research-agent/trigger/custom \
  -H "Content-Type: application/json" \
  -d '{"source_limit": 5, "days_back": 3, "rebuild_kg": true}'

# Should return:
# {"success": true, "message": "Fetch started for 5 sources (3 days)", ...}

# 3. Check status
curl http://localhost:8000/api/research-agent/status | jq .

# 4. Check logs
docker logs rag-research-agent -f

# Look for:
# - "Custom fetch triggered: 5 sources, 3 days"
# - "Fetch complete: 5/5 sources"
# - "Triggering knowledge graph rebuild..."
# - "✅ Knowledge graph rebuilt successfully"
```

### Test Frontend

1. Open http://localhost:3000
2. Click "Research Agent" tab
3. Move sliders
4. Click "Start Research Agent"
5. Watch status update
6. Check toast notifications
7. Verify KG was rebuilt (check Documents tab)

---

## 📊 Expected Results

### Small Fetch (5 sources, 7 days)
- Time: ~30 seconds
- Articles: 20-50
- KG Rebuild: 5-10 seconds
- Total: ~40 seconds

### Medium Fetch (15 sources, 14 days)
- Time: ~2 minutes
- Articles: 50-150
- KG Rebuild: 15-20 seconds
- Total: ~2.5 minutes

### Large Fetch (31 sources, 30 days)
- Time: ~5 minutes
- Articles: 100-300
- KG Rebuild: 30-45 seconds
- Total: ~6 minutes

---

## 🐛 Troubleshooting

### Issue: Slider component not found
**Solution:** Install or create slider component (see Step 3 above)

### Issue: API returns 503
**Solution:** Check research-agent service is running
```bash
docker logs rag-research-agent
curl http://localhost:8015/health
```

### Issue: KG not rebuilding
**Solution:** Check knowledge-graph service
```bash
docker logs rag-knowledge-graph
curl http://localhost:8007/health
```

### Issue: Fetch takes too long
**Solution:** Use smaller source_limit and days_back values

### Issue: Frontend not showing status
**Solution:** Check API gateway routes
```bash
curl http://localhost:8000/api/research-agent/status
```

---

## ✅ Checklist Before Deployment

- [ ] Slider component exists in frontend/src/components/ui/
- [ ] ResearchAgentPage imported in App.tsx
- [ ] Route added for 'research' tab
- [ ] Tab added to TabNavigation.tsx
- [ ] Backend endpoint tested locally
- [ ] Frontend tested locally
- [ ] API Gateway proxy routes tested
- [ ] Knowledge graph rebuild verified
- [ ] Error handling tested
- [ ] Toast notifications working
- [ ] Status polling working

---

## 🎉 Benefits

### For Users
- ✅ Easy UI control (no CLI needed)
- ✅ Visual feedback on progress
- ✅ Configurable fetch parameters
- ✅ Automatic KG updates
- ✅ No technical knowledge required

### For System
- ✅ Controlled resource usage
- ✅ Non-blocking operations
- ✅ Automatic optimization (KG rebuild)
- ✅ Progress tracking
- ✅ Error handling

---

## 📝 Future Enhancements

- [ ] Real-time progress bar (% complete)
- [ ] Pause/cancel button
- [ ] Source selection (choose specific sources)
- [ ] Schedule automatic fetches
- [ ] Email notifications on completion
- [ ] Fetch history log
- [ ] Performance metrics graph
- [ ] Estimated article count prediction

---

**Next Action:** Complete Steps 1-4 above to integrate the UI! 🚀

All the hard work is done - just needs final wiring in the frontend routing!

