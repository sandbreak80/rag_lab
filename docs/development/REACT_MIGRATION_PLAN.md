# React Migration Plan - Neural Vault Educational Lab

## 🎯 Goal
Transform monolithic HTML/JS UI into modern React + TypeScript application with component-based architecture.

## 📦 Tech Stack

### Frontend
- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool (fast HMR)
- **Shadcn/ui** - Beautiful component library (Tailwind-based)
- **Zustand** - Lightweight state management
- **React Router** - Tab navigation
- **Recharts** - Metrics visualization
- **React Query** - API data fetching
- **Axios** - HTTP client

### Backend
- **Flask** - Keep as-is (API only)
- **No templating** - Pure JSON API responses

## 📁 New Project Structure

```
/Users/bmstoner/code_projects/rag_lab/
├── frontend/                      # NEW: React app
│   ├── src/
│   │   ├── components/
│   │   │   ├── chat/
│   │   │   │   ├── ChatInterface.tsx
│   │   │   │   ├── MessageList.tsx
│   │   │   │   ├── MessageItem.tsx
│   │   │   │   ├── InputBar.tsx
│   │   │   │   └── SourceCard.tsx
│   │   │   ├── documents/
│   │   │   │   ├── DocumentList.tsx
│   │   │   │   ├── DocumentUpload.tsx
│   │   │   │   └── DocumentItem.tsx
│   │   │   ├── settings/
│   │   │   │   ├── SettingsPanel.tsx
│   │   │   │   ├── ModelSelector.tsx
│   │   │   │   ├── RAGToggles.tsx
│   │   │   │   ├── QuickPresets.tsx
│   │   │   │   └── MetadataFilters.tsx    # NEW FEATURE
│   │   │   ├── metrics/
│   │   │   │   ├── MetricsOverview.tsx
│   │   │   │   ├── QueryHistoryTable.tsx
│   │   │   │   ├── PerformanceChart.tsx
│   │   │   │   └── MetricCard.tsx
│   │   │   ├── lab/
│   │   │   │   ├── LabGuide.tsx
│   │   │   │   ├── LabSection.tsx
│   │   │   │   └── ProgressTracker.tsx
│   │   │   ├── qa/
│   │   │   │   └── QASection.tsx
│   │   │   ├── feedback/
│   │   │   │   └── FeedbackForm.tsx
│   │   │   ├── layout/
│   │   │   │   ├── AppLayout.tsx
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── TabNavigation.tsx
│   │   │   │   └── StatsBar.tsx
│   │   │   └── ui/                 # Shadcn components
│   │   │       ├── button.tsx
│   │   │       ├── card.tsx
│   │   │       ├── tabs.tsx
│   │   │       ├── table.tsx
│   │   │       ├── dialog.tsx
│   │   │       └── ...
│   │   ├── hooks/
│   │   │   ├── useRAGConfig.ts
│   │   │   ├── useMetrics.ts
│   │   │   ├── useChat.ts
│   │   │   ├── useDocuments.ts
│   │   │   └── useStats.ts
│   │   ├── stores/
│   │   │   ├── configStore.ts      # RAG configuration
│   │   │   ├── metricsStore.ts     # Query history
│   │   │   └── labStore.ts         # Lab progress
│   │   ├── services/
│   │   │   └── api.ts              # API client
│   │   ├── types/
│   │   │   ├── config.ts
│   │   │   ├── metrics.ts
│   │   │   ├── chat.ts
│   │   │   └── documents.ts
│   │   ├── utils/
│   │   │   ├── formatting.ts
│   │   │   └── localStorage.ts
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── tailwind.config.js
├── src/
│   ├── webapp.py                  # MODIFIED: API only, no templates
│   └── api/                       # NEW: API routes
│       ├── __init__.py
│       ├── chat.py
│       ├── documents.py
│       ├── settings.py
│       └── metrics.py
└── docker-compose.test.yml        # MODIFIED: Add frontend service
```

## 🔄 Migration Phases

### Phase 1: Setup (30 min)
- [ ] Initialize Vite + React + TypeScript project
- [ ] Install dependencies (Shadcn/ui, Zustand, React Query, etc.)
- [ ] Configure Tailwind CSS
- [ ] Setup Shadcn/ui components
- [ ] Create basic project structure

### Phase 2: Core Infrastructure (1 hour)
- [ ] Create API client (`services/api.ts`)
- [ ] Setup Zustand stores (config, metrics, lab)
- [ ] Define TypeScript types
- [ ] Create custom hooks
- [ ] Setup React Router for tabs

### Phase 3: Layout & Navigation (1 hour)
- [ ] Build AppLayout component
- [ ] Build Header with stats
- [ ] Build TabNavigation
- [ ] Implement tab routing
- [ ] Style with Tailwind

### Phase 4: Chat Tab (2 hours)
- [ ] ChatInterface component
- [ ] MessageList with streaming support
- [ ] InputBar with suggestions
- [ ] SourceCard for citations
- [ ] Markdown rendering
- [ ] Syntax highlighting

### Phase 5: Documents Tab (1 hour)
- [ ] DocumentList component
- [ ] File upload with drag & drop
- [ ] Upload progress indicators
- [ ] Document filtering (user vs system)

### Phase 6: Settings Tab (2 hours)
- [ ] SettingsPanel layout
- [ ] ModelSelector dropdown
- [ ] RAGToggles (switches for each feature)
- [ ] Sliders (temp, top-k, web search, etc.)
- [ ] QuickPresets buttons
- [ ] **NEW: MetadataFilters component**

### Phase 7: Metrics Tab (2 hours)
- [ ] MetricsOverview (summary cards)
- [ ] QueryHistoryTable
- [ ] PerformanceChart (Recharts)
- [ ] Export CSV functionality
- [ ] Query detail modal

### Phase 8: Lab Guide Tab (1 hour)
- [ ] LabGuide component
- [ ] Collapsible sections
- [ ] Progress tracking
- [ ] Exercise components

### Phase 9: Q&A & Feedback Tabs (30 min)
- [ ] QA accordion component
- [ ] Feedback form with validation

### Phase 10: Backend API Updates (1 hour)
- [ ] Remove template rendering from Flask
- [ ] Create dedicated API routes
- [ ] Add CORS support
- [ ] Test all endpoints

### Phase 11: Docker & Build (1 hour)
- [ ] Update Dockerfile for frontend
- [ ] Add frontend service to docker-compose
- [ ] Setup Nginx for production
- [ ] Configure API proxy

### Phase 12: Testing & Polish (2 hours)
- [ ] Test all features
- [ ] Fix bugs
- [ ] Add loading states
- [ ] Add error boundaries
- [ ] Polish animations
- [ ] Responsive design

**Total Time: 15-16 hours (2 full days)**

## 🎨 Design System (Shadcn/ui)

### Color Palette
```typescript
// Keep existing dark theme
const colors = {
  primary: '#6366f1',     // Indigo
  secondary: '#8b5cf6',   // Purple
  background: '#0a0e27',
  surface: '#151930',
  border: 'rgba(148, 163, 184, 0.1)',
}
```

### Key Components
- Button (primary, secondary, ghost)
- Card (elevated surfaces)
- Tabs (navigation)
- Table (metrics)
- Dialog/Modal (details, presets)
- Switch (RAG toggles)
- Slider (parameters)
- Select (dropdowns)
- Badge (status indicators)
- Alert (notifications)

## 🔌 API Endpoints (Flask)

All endpoints return JSON (no HTML):

```python
# Chat
POST   /api/chat          - Stream chat responses
POST   /api/search        - Search documents

# Documents
GET    /api/documents     - List documents
POST   /api/upload        - Upload files
GET    /api/stats         - Get system stats

# Settings
GET    /api/presets       - Get configuration presets
GET    /api/models        - Get available models (Ollama API)

# Metrics
GET    /api/metrics       - Get query history
POST   /api/metrics       - Log query metrics
DELETE /api/metrics       - Clear metrics

# Lab
GET    /api/lab/progress  - Get lab progress
POST   /api/lab/progress  - Update lab progress
```

## 📊 State Management (Zustand)

### configStore
```typescript
interface ConfigState {
  model: string;
  temperature: number;
  topK: number;
  useQueryExpansion: boolean;
  useBM25: boolean;
  useHybrid: boolean;
  useGraph: boolean;
  useReranking: boolean;
  useWebSearch: boolean;
  webSearchDocs: number;
  webSearchPages: number;
  rerankTopK: number;
  // Actions
  setModel: (model: string) => void;
  updateConfig: (config: Partial<ConfigState>) => void;
  loadPreset: (preset: string) => void;
}
```

### metricsStore
```typescript
interface MetricsState {
  queries: QueryMetric[];
  addQuery: (metric: QueryMetric) => void;
  clearMetrics: () => void;
  exportCSV: () => void;
}
```

## 🚀 Development Workflow

1. **Start backend**: `docker-compose -f docker-compose.test.yml up` (Flask API)
2. **Start frontend**: `cd frontend && npm run dev` (Vite dev server on :5173)
3. **Hot reload**: Changes reflect instantly
4. **API proxy**: Vite proxies `/api/*` to Flask backend

## 📦 Production Build

```bash
cd frontend
npm run build           # Creates frontend/dist/
```

Nginx serves:
- Static files from `frontend/dist/`
- API requests proxied to Flask backend

## ✅ Success Criteria

- [ ] All current features working
- [ ] Beautiful, modern UI
- [ ] Fast, responsive
- [ ] Type-safe (no runtime errors)
- [ ] Easy to add new features
- [ ] Component reusability
- [ ] Maintainable codebase

## 🎯 New Features Made Easy

With React, adding new features becomes trivial:

**Metadata Filtering (Feature 1):**
```tsx
// Just add a component!
<MetadataFilters
  onFilterChange={(filters) => setFilters(filters)}
/>
```

**Query Decomposition (Feature 2):**
```tsx
// Add to chat interface
{decomposedQueries.map(q => (
  <SubQueryCard key={q.id} query={q} />
))}
```

**Self-RAG (Feature 3):**
```tsx
// Show critique/refinement UI
<SelfRAGIndicator
  iterations={iterations}
  currentStep={step}
/>
```

---

**Let's build this! 🚀**

