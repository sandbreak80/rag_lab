# 🚀 Quick Start - React Frontend

## What's New?

The RAG Lab now has a **modern React + TypeScript frontend** with:
- 🎨 Beautiful, professional UI
- ⚡ Lightning-fast performance
- 🧩 Component-based architecture
- 🔒 Type-safe with TypeScript
- 📦 Production-ready Docker setup

---

## Start the Application

### Option 1: Development Mode (Recommended for testing)

```bash
# Terminal 1: Start all backend services
cd /Users/bmstoner/code_projects/rag_lab
docker-compose -f docker-compose.test.yml up

# Terminal 2: Start React dev server (hot reload)
cd /Users/bmstoner/code_projects/rag_lab/frontend
npm install  # First time only
npm run dev

# Open browser to http://localhost:5173
```

**Why dev mode?**
- Instant hot reload on code changes
- Better error messages
- React DevTools support
- Faster iteration

### Option 2: Production Mode (Full Docker)

```bash
cd /Users/bmstoner/code_projects/rag_lab

# Build and start everything
docker-compose -f docker-compose.test.yml up --build frontend web-api

# Open browser to http://localhost:3000
```

**Why production mode?**
- Tests the full deployment
- Nginx reverse proxy
- Optimized build
- Production-like environment

---

## What to Test

### 1. Chat Tab (Main Feature) 💬
- Ask questions about your documents
- See sources with citations
- Watch metrics being tracked
- Try different RAG configurations

### 2. Documents Tab 📁
- Upload PDF, Word, Excel, PowerPoint, Text files
- Drag & drop support
- See upload progress
- View your uploaded documents

### 3. Settings Tab ⚙️
- Change LLM model
- Toggle RAG features (Query Expansion, BM25, Hybrid, etc.)
- Adjust temperature, top-K, context window
- Configure web search and reranker
- **NEW**: Filter by metadata (type, date, tags, author)
- Load quick presets (minimal, production, etc.)

### 4. Metrics Tab 📊
- See all your queries
- View performance breakdowns
- Track latency, tokens, results
- Export to CSV
- Compare different configurations

### 5. Lab Guide Tab 🎓
- Learn about RAG systems
- Complete exercises
- Track your progress
- Understand each feature's impact

### 6. Q&A Tab ❓
- Browse frequently asked questions
- Learn about search methods
- Understand advanced features

### 7. Feedback Tab 💭
- Rate your experience
- Submit comments
- Help improve the lab

---

## Architecture Overview

```
Browser → Nginx (port 3000 or 5173)
    ↓
    ├─ React Frontend (static files)
    └─ /api/* → Flask Backend
          ↓
          └─ Microservices
              ├─ Vector DB (ChromaDB)
              ├─ Search Service
              ├─ Ingest Service
              ├─ Knowledge Graph
              ├─ Reranker
              ├─ Web Search
              └─ Ollama (LLM)
```

---

## Key Files

```
frontend/
├── src/
│   ├── components/       # React components
│   │   ├── chat/        # Chat interface
│   │   ├── documents/   # File upload
│   │   ├── settings/    # Configuration
│   │   ├── metrics/     # Analytics
│   │   ├── lab/         # Lab guide
│   │   ├── qa/          # Q&A
│   │   ├── feedback/    # Feedback form
│   │   ├── layout/      # Header, nav
│   │   └── ui/          # Reusable components
│   ├── stores/          # State management
│   ├── services/        # API client
│   ├── types/           # TypeScript types
│   └── utils/           # Helper functions
├── Dockerfile           # Production build
├── nginx.conf           # Reverse proxy config
└── package.json         # Dependencies
```

---

## Troubleshooting

### Port Already in Use
```bash
# Kill process on port 5173
lsof -ti:5173 | xargs kill -9

# Kill process on port 3000
lsof -ti:3000 | xargs kill -9
```

### Frontend Not Connecting to Backend
- Make sure all backend services are running: `docker-compose -f docker-compose.test.yml ps`
- Check API proxy in browser DevTools → Network tab
- Verify CORS is working (should see Access-Control-Allow-Origin header)

### Ollama Not Found
```bash
# Make sure Ollama is running on your Mac
ollama serve

# Test it
curl http://localhost:11434/api/tags
```

### Hot Reload Not Working
```bash
# Restart Vite dev server
cd frontend
npm run dev
```

---

## Next Steps

1. **Test the UI** - Click through all tabs
2. **Upload Documents** - Try PDF, Word, Excel
3. **Run Queries** - Ask questions and see sources
4. **Toggle Features** - See how they impact quality
5. **Check Metrics** - View performance data
6. **Complete Lab** - Follow the lab guide exercises

---

## Development Tips

### Add a New Component
```bash
cd frontend/src/components/chat
touch NewComponent.tsx
```

```tsx
import React from 'react';

export function NewComponent() {
  return <div>Hello World!</div>;
}
```

### Add a New API Endpoint
```bash
# Edit src/api/chat.py or other route file
# Add new @bp.route() function
# Restart web-api service
docker-compose -f docker-compose.test.yml restart web-api
```

### Update Styling
- Tailwind classes in JSX
- Global styles in `frontend/src/index.css`
- Component-specific in `frontend/src/components/**/*.tsx`

---

## Build for Production

```bash
cd frontend
npm run build
# Output in dist/

# Test production build locally
npm run preview
```

---

## Questions?

- See `/docs/development/REACT_MIGRATION_COMPLETE.md` for full details
- Check `/frontend/README.md` for deployment info
- Review component code in `/frontend/src/components/`

---

**Enjoy the new React frontend! 🎉**

