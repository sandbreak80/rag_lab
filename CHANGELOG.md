# Changelog

All notable changes to RAG Lab will be documented in this file.

## [1.3.1] - 2025-11-07

### Enhanced
- **Research Agent**: Expanded to 6 content sources (was 2)
  - arXiv AI/ML papers (cs.AI, cs.LG, cs.CL, cs.CV)
  - Hugging Face Papers
  - TechCrunch AI news
  - VentureBeat AI coverage
  - The Verge AI articles
  - OpenAI Blog (prepared, needs user-agent config)
- **Auto-Discovery**: Daily scheduled fetching at 02:00 UTC
- **Content Coverage**: Up to 80+ items per fetch cycle
- **Metadata Tracking**: Per-source statistics and fetch history

### Technical Details
- Added 4 new scrapers (TechCrunch, VentureBeat, TheVerge, OpenAI)
- Enhanced `initialize_default_sources()` in research-agent service
- 100% success rate on active sources
- All content automatically ingested and searchable

## [1.3.0] - 2025-11-06

### Added
- **Metadata Filtering UI**: User-controlled document filtering by type, date, source, tags, and authors
  - Collapsible filter panel with active filter badge
  - Pill-style filter buttons with real-time updates
  - Persistent state saved to localStorage
  - Backend support in search and vector-db services
- **Self-RAG Service**: New microservice (port 8020) for quality assessment
  - Multi-dimensional critique (relevance, accuracy, completeness, grounding)
  - Quality scoring (0-1 scale) with weighted dimensions
  - Suggestion generation for improvement
  - Optional auto-improvement of responses
  - Re-retrieval detection for low-quality answers
- **Enhanced Markdown Rendering**: Professional chat message formatting
  - Code blocks with copy buttons and line numbers
  - Math equation support (KaTeX: inline $...$ and display $$...$$)
  - Improved styling for headings, lists, tables, blockquotes
  - Interactive hover effects on code blocks
  - Syntax highlighting for 50+ languages
- **Query Decomposition UI**: Complete implementation from Phase 1
  - Settings toggle for complex query handling
  - Sub-query display in chat interface
  - Metrics integration in waterfall chart

### Changed
- **Frontend Build**: Switched from `npm ci` to `npm install` in Dockerfile for easier updates
- **CSS Import Order**: Fixed KaTeX import to prevent PostCSS warnings
- **Project Organization**: Moved 40+ status/session docs to `docs/archive/` for cleaner structure

### Technical Details
- FilterPanel component with MetadataFilters state management
- ChromaDB where clause generation for vector search
- BM25 post-scoring filters for keyword search
- Self-RAG Flask service with gunicorn (2 workers)
- KaTeX, remark-math, rehype-katex dependencies added
- Enhanced ReactMarkdown with custom component renderers

### Documentation
- METADATA_FILTERING_COMPLETE.md - Feature documentation
- PHASE_2_COMPLETE_SUMMARY.md - Session summary
- MARKDOWN_IMPROVEMENTS_COMPLETE.md - Rendering improvements
- SESSION_COMPLETE_NOV_6_2025.md - Full session report

## [1.2.4] - 2025-11-06

### Added
- **Baseline Prompts**: 3 pre-built prompts for performance testing (low/medium/high complexity)
- **Authentication Proxy**: API Gateway now properly routes `/api/auth/*` requests to auth service
- **Reasoning Process Toggle**: UI control to show/hide LLM step-by-step reasoning
- **Playwright Tests**: Automated browser testing for login and UI validation

### Fixed
- **Login Issue**: Frontend authentication now works correctly through API Gateway proxy
- **Waterfall Chart**: Simplified rendering from stacked to simple bar chart for better visibility
- **Source Score Display**: Added null check for undefined score values preventing crashes
- **Chat Window Height**: Increased from 200px to 40px margin for better content visibility

### Changed
- **API Gateway**: Added auth service to service registry
- **Frontend Container**: Rebuilt with latest baseline prompt changes

### Technical Details
- Auth proxy routes forward requests to `auth-service:8014`
- JWT tokens work correctly for login/register/validation
- All 3 baseline prompts render and function properly
- Playwright integration tests confirm UI functionality

## [1.2.3] - 2025-11-05

### Added
- **Citation Hallucination Detection**: Validates citations against retrieved sources
- **Rich Source Metadata**: Enhanced source cards with authors, dates, DOIs, external IDs
- **Strict Citation Controls**: Prompt engineering to prevent fabricated citations
- **Source Metadata Enrichment**: Backend enrichment of source information

### Fixed
- **BM25 Index Path**: Corrected from directory to file path (`/indices/bm25_index.pkl`)
- **Query Expansion**: Fixed "Partial" status by ensuring BM25 index loads correctly
- **Metric Naming**: Standardized performance metric names across services

### Changed
- **Prompt Enhancement**: Injected citation control instructions
- **API Gateway**: Added hallucination detection and metadata enrichment functions

## [1.2.2] - 2025-11-05

### Added
- **Performance Waterfall Chart**: Visualize RAG pipeline latency breakdown by stage
- **Query Decomposer Service**: New microservice for breaking complex queries into sub-queries
- **Auto Model Routing**: Intelligent LLM selection based on query characteristics
- **Prompt Categorization**: Classification by intent, domain, and complexity

### Changed
- **Chat Interface**: Enhanced with performance metrics display
- **Frontend Types**: Added comprehensive performance metrics interface
- **Search Service**: Integrated query decomposition logic

## [1.2.1] - 2025-11-04

### Added
- **Security Guardrails**: PII detection, prompt injection prevention, content filtering
- **Rate Limiting**: Redis-based rate limiting (100/min, 1000/hour)
- **Authentication Service**: JWT-based user auth with bcrypt password hashing
- **Input Sanitization**: Unicode normalization and pattern detection

### Fixed
- **CORS Configuration**: Proper headers for frontend-backend communication
- **Token Refresh**: Automatic token refresh on 401 responses

## [1.2.0] - 2025-11-03

### Added
- **React Frontend**: Complete rewrite from Flask to React + TypeScript
- **Configuration Toggles**: UI controls for all RAG features
- **Zustand State Management**: Efficient state handling with localStorage persistence
- **Responsive Design**: Mobile-friendly Tailwind CSS implementation
- **Real-time Streaming**: Token-by-token response streaming

### Changed
- **Frontend Architecture**: Migrated from server-side rendering to SPA
- **Build System**: Vite for fast development and optimized production builds
- **Nginx Serving**: Static file serving with reverse proxy

## [1.1.0] - 2025-11-02

### Added
- **Knowledge Graph**: NetworkX-based entity relationship mapping
- **Hybrid Search**: Combined vector + BM25 with RRF fusion
- **Reranking Service**: Cross-encoder for result reranking
- **Web Search Integration**: SearXNG for external source retrieval
- **Research Agent**: Autonomous AI paper discovery and ingestion

### Changed
- **Search Pipeline**: Multi-stage retrieval with graph enhancement
- **Document Processing**: Improved chunking strategies

## [1.0.0] - 2025-11-01

### Added
- **Initial Release**: Core RAG system with vector database
- **Microservices Architecture**: 14 independent services
- **Docker Compose**: Complete service orchestration
- **Qdrant Integration**: Vector database for semantic search
- **Docling Processing**: Advanced PDF parsing
- **Ollama LLM**: Local language model inference
- **Basic UI**: Flask-based web interface

### Technical Foundation
- Python 3.11 backend services
- REST API architecture
- Health check endpoints
- Service metrics collection
- Comprehensive logging

---

## Version Numbering

- **Major.Minor.Patch** (Semantic Versioning)
- **Major**: Breaking changes or major feature additions
- **Minor**: New features, backward compatible
- **Patch**: Bug fixes and minor improvements

