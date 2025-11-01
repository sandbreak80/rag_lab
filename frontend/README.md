# React Frontend Deployment

## Development

```bash
cd frontend
npm install
npm run dev
```

Access at http://localhost:5173

## Production Build

```bash
cd frontend
npm run build
```

Output in `frontend/dist/`

## Docker Production Deployment

The frontend is built into a Docker image with Nginx:

```bash
# Build and start all services
docker-compose -f docker-compose.test.yml up --build frontend web-api

# Access the application
open http://localhost:3000
```

## Architecture

```
Browser → Nginx (port 3000)
    ↓
    ├─ /         → React SPA (static files)
    └─ /api/*    → Flask API (port 5555)
          ↓
          └─ Microservices (vector-db, search, ingest, etc.)
```

## Environment Variables

The frontend proxies API requests to the backend. No environment variables needed for production.

## Features

- **Modern UI**: React 18 + TypeScript + Tailwind CSS
- **Component Library**: Custom Shadcn-style components
- **State Management**: Zustand for global state
- **API Layer**: React Query for data fetching
- **Routing**: React Router for navigation
- **7 Main Tabs**:
  1. Chat - RAG Q&A with sources
  2. Documents - Upload and manage files
  3. Settings - Configure RAG features
  4. Metrics - Performance analytics
  5. Lab Guide - Educational content
  6. Q&A - Frequently asked questions
  7. Feedback - User feedback form

## Performance

- Gzip compression enabled
- Static assets cached for 1 year
- Code splitting via Vite
- Lazy loading for routes
- Optimized bundle size
