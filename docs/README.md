# RAG Lab Documentation

**Last Updated:** November 5, 2025
**Status:** ✅ Production Ready (needs security hardening for internet)

---

## 🚀 Quick Start

**New to RAG Lab?** Start here:
1. [Quick Reference](QUICK_REFERENCE.md) - Commands, endpoints, troubleshooting
2. [Quick Start Guide](QUICK_START.md) - Get up and running in 5 minutes
3. [Project Status](PROJECT_STATUS.md) - What's built, what's working

---

## 📂 Documentation Structure

### Essential Guides (Start Here)
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - All commands, endpoints, and common operations
- **[QUICK_START.md](QUICK_START.md)** - Get started in minutes
- **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Current system status
- **[PROJECT_COMPLETE.md](PROJECT_COMPLETE.md)** - Feature completeness
- **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** - Detailed documentation index

---

### Architecture & Design
📁 **[architecture/](architecture/)**
- `ARCHITECTURE.md` - System architecture overview
- `FRAMEWORK_DECISION.md` - Why custom stack vs LangChain
- `LLM_INFERENCE_COMPARISON.md` - Ollama vs vLLM vs llama.cpp
- `VLLM_HARDWARE_REQUIREMENTS.md` - GPU requirements, A4000 upgrade path
- `PERPLEXITY_LAYER_COMPARISON.md` - Web search processing design
- `CUSTOM_CRAWLER_DESIGN.md` - Custom scraper architecture

---

### Features & Capabilities
📁 **[features/](features/)**
- `RAG_FEATURES.md` - All RAG features explained
- `RAG_DEEP_DIVE.md` - Technical deep dive
- `WEB_SEARCH_ENHANCEMENTS.md` - SearXNG integration
- `WEB_SEARCH_PROCESSING_PIPELINE.md` - Perplexity-style processing
- `MODEL_RECOMMENDATIONS.md` - Model selection guide
- `MODEL_SELECTION_GUIDE.md` - Detailed model comparison

---

### Planning & Roadmap
📁 **[planning/](planning/)**
- `NEXT_FEATURES_QUEUE.md` - Upcoming features (Query Decomposition, Self-RAG, Metadata Filtering)
- `ROADMAP.md` - Long-term development plan
- `IMPLEMENTATION_PLAN.md` - Implementation strategy
- `next_steps.md` - Immediate next steps
- `FUTURE_ENHANCEMENTS_ROADMAP.md` - Future vision

---

### Security
📁 **[security/](security/)**
- `SECURITY_HARDENING_INTERNET_FACING.md` - Production security checklist
- `SECURITY_README.md` - Security overview
- `SECURITY_QUICKSTART.md` - Quick security setup
- `SECURITY_DEEP_DIVE.md` - Comprehensive security guide
- `SECURITY_ENHANCEMENT_PLAN.md` - Security roadmap
- `SECURITY_GAP_ANALYSIS.md` - Current gaps
- `SECURITY_INTEGRATION.md` - Security service integration

---

### Operations & Deployment
📁 **[operations/](operations/)**
- `CLEAN_REBUILD_GUIDE.md` - How to rebuild from scratch
- `DB_RESET_GUIDE.md` - Reset databases
- `PERFORMANCE.md` - Performance tuning

📁 **[deployment/](deployment/)**
- `UBUNTU_DEPLOYMENT.md` - Complete deployment guide
- `GPU_SETUP.md` - NVIDIA GPU setup

---

### Research Agent
📁 **[research-agent/](research-agent/)**
- `README.md` - Research agent overview
- Auto-discovery system for AI research content
- 6 data sources (arXiv, Hugging Face, tech news)
- 91 items ingested, 94.4% success rate

---

### Development
📁 **[development/](development/)**
- `DEV_PRACTICES.md` - Coding standards
- `DEPENDENCIES.md` - Python dependencies
- `TESTING_GUIDE.md` - How to test
- `BUG_TRACKER.md` - Known issues
- Bug fix sessions and progress reports

📁 **[dev_notes/](dev_notes/)**
- `SESSION_COMPLETE_NOV_5_2025.md` - **TODAY'S PROGRESS** ⭐
- `prompts.txt` - Prompt engineering notes
- Daily session summaries

---

### Field Guides & Tutorials
📁 **[field_guides/](field_guides/)**
- Step-by-step tutorials for specific tasks
- Educational content for learning RAG concepts

📁 **[lab/](lab/)**
- Experimental features
- Lab exercises

---

### Archive
📁 **[archive/](archive/)**
- Historical documentation
- Old status reports
- Migration guides
- Legacy implementations

---

## 🎯 Today's Key Documents (Nov 5, 2025)

### New Today ⭐
1. **[dev_notes/SESSION_COMPLETE_NOV_5_2025.md](dev_notes/SESSION_COMPLETE_NOV_5_2025.md)**
   - Complete session summary
   - All achievements, technical decisions
   - 3 new services built (classifier, enhancer, router)
   - Research agent fully functional (91 items ingested)

2. **[planning/NEXT_FEATURES_QUEUE.md](planning/NEXT_FEATURES_QUEUE.md)**
   - Query Decomposition (4-6 hours)
   - Metadata Filtering UI (2 hours)
   - Self-RAG (8-10 hours)

3. **[architecture/VLLM_HARDWARE_REQUIREMENTS.md](architecture/VLLM_HARDWARE_REQUIREMENTS.md)**
   - Why vLLM doesn't work on T4
   - A4000 upgrade recommendation
   - Performance comparison

---

## 🏗️ System Overview

### Current Status
- **18 services** running
- **7 LLM models** available via Ollama
- **6 research data sources** auto-ingesting
- **91 documents** from research agent
- **3 new intelligence services** (classifier, enhancer, router)

### What's Built
✅ Core RAG pipeline (ingest → embed → search → generate)
✅ Hybrid search (vector + keyword + reranking)
✅ Web search integration (SearXNG)
✅ Research agent (autonomous discovery)
✅ Prompt classification (intent, complexity)
✅ Prompt enhancement (CoT, ReAct, Few-Shot)
✅ Model routing (dynamic LLM selection)
✅ Security layer (validation, rate limiting)
✅ Authentication & authorization
✅ Performance metrics

### What's Next
🔜 API Gateway integration (classifier → enhancer → router)
🔜 UI toggles for new features
🔜 Research agent dashboard
🔜 Query decomposition
🔜 Metadata filtering UI
🔜 Self-RAG

---

## 🔍 Finding What You Need

### I want to...

**...understand the system**
- Start: [ARCHITECTURE.md](architecture/ARCHITECTURE.md)
- Then: [PROJECT_STATUS.md](PROJECT_STATUS.md)
- Deep dive: [RAG_DEEP_DIVE.md](features/RAG_DEEP_DIVE.md)

**...deploy the system**
- Start: [QUICK_START.md](QUICK_START.md)
- Full guide: [deployment/UBUNTU_DEPLOYMENT.md](deployment/UBUNTU_DEPLOYMENT.md)
- GPU setup: [deployment/GPU_SETUP.md](deployment/GPU_SETUP.md)

**...use the system**
- Start: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- All endpoints, commands, troubleshooting

**...develop new features**
- Start: [development/DEV_PRACTICES.md](development/DEV_PRACTICES.md)
- Next: [planning/NEXT_FEATURES_QUEUE.md](planning/NEXT_FEATURES_QUEUE.md)
- Testing: [development/TESTING_GUIDE.md](development/TESTING_GUIDE.md)

**...secure for production**
- Start: [security/SECURITY_HARDENING_INTERNET_FACING.md](security/SECURITY_HARDENING_INTERNET_FACING.md)
- Overview: [security/SECURITY_README.md](security/SECURITY_README.md)

**...understand today's progress**
- Read: [dev_notes/SESSION_COMPLETE_NOV_5_2025.md](dev_notes/SESSION_COMPLETE_NOV_5_2025.md)

**...upgrade to vLLM**
- Read: [architecture/VLLM_HARDWARE_REQUIREMENTS.md](architecture/VLLM_HARDWARE_REQUIREMENTS.md)
- Comparison: [architecture/LLM_INFERENCE_COMPARISON.md](architecture/LLM_INFERENCE_COMPARISON.md)

**...add new data sources to research agent**
- Guide: [research-agent/README.md](research-agent/README.md)
- View: `services/research-agent/app/scrapers/`

---

## 📊 Quick Stats

### Documentation
- **100+** markdown files
- **18** service configurations
- **6** major subsystems documented
- **3** deployment guides

### System
- **18** microservices
- **7** LLM models
- **6** research data sources
- **91** auto-ingested documents
- **94.4%** research agent success rate

### Code
- **Python 3.11** backend
- **React/TypeScript** frontend
- **Docker Compose** orchestration
- **ChromaDB** vector storage
- **Ollama** LLM serving

---

## 🤝 Contributing

### Adding Documentation
1. Choose appropriate folder based on category
2. Use clear, descriptive filenames
3. Update this README if adding new sections
4. Keep `QUICK_REFERENCE.md` updated for operations

### Documentation Standards
- **Use markdown** for all documentation
- **Include timestamps** in session summaries
- **Link between documents** for easy navigation
- **Keep status current** - mark outdated docs as archived

---

## 📞 Quick Links

### Most Used Docs
1. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Daily operations
2. [PROJECT_STATUS.md](PROJECT_STATUS.md) - Current state
3. [dev_notes/SESSION_COMPLETE_NOV_5_2025.md](dev_notes/SESSION_COMPLETE_NOV_5_2025.md) - Latest session

### For Demos
1. [PROJECT_COMPLETE.md](PROJECT_COMPLETE.md) - Feature showcase
2. [RAG_FEATURES.md](features/RAG_FEATURES.md) - Capabilities overview
3. [QUICK_START.md](QUICK_START.md) - Live demo setup

### For Learning
1. [RAG_DEEP_DIVE.md](features/RAG_DEEP_DIVE.md) - Technical concepts
2. [field_guides/](field_guides/) - Step-by-step tutorials
3. [architecture/FRAMEWORK_DECISION.md](architecture/FRAMEWORK_DECISION.md) - Design rationale

---

**Last Major Update:** November 5, 2025 - Added prompt classification, enhancement, model routing, and completed research agent with 6 data sources.

**Next Session:** Integrate new intelligence services, add UI controls, build research agent dashboard.
