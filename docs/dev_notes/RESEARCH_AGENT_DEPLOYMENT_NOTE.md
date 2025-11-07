# Research Agent Deployment Note
**Date:** November 7, 2025
**Version:** v1.1.0
**Status:** ✅ Ready for Deployment

---

## Changes Summary

### What Changed
Enhanced Research Agent from **2 sources** to **6 sources** for comprehensive AI content discovery.

### New Sources Added
1. ✅ **TechCrunch AI** - Tech news and startup coverage
2. ✅ **VentureBeat AI** - Enterprise AI and business coverage
3. ✅ **The Verge AI** - Consumer tech and AI trends
4. ⚠️ **OpenAI Blog** - Official OpenAI announcements (403 anti-scraping, needs user-agent)

### Existing Sources (Enhanced)
5. ✅ **arXiv AI/ML** - Academic papers (cs.AI, cs.LG, cs.CL, cs.CV)
6. ✅ **Hugging Face Papers** - Latest ML research

---

## Files Modified

### Primary Changes
- **`services/research-agent/app/service.py`** - Updated `initialize_default_sources()` function
  - Added 4 new source initializations
  - Each with appropriate config (max_results: 10-20)
  - All enabled by default

### Documentation Updates
- **`BUILD_INFO`** - Updated to v1.1.0, build 20251107.1
- **`CHANGELOG.md`** - Added [1.3.1] entry documenting enhancements

---

## Deployment Instructions

### For Docker Compose
The changes are **automatically included** via volume mount:
```yaml
volumes:
  - ./services/research-agent/app:/app  # ← service.py changes included
```

**Steps:**
1. Commit changes to `security` branch
2. Push to GitHub
3. On AWS instance:
   ```bash
   cd ~/rag_lab
   git pull origin security
   docker compose restart research-agent
   ```

### For New AWS Instances
Cloud-init automatically handles everything:
- Clones repo from security branch
- Builds and starts all services
- Research agent initializes all 6 sources on first run

**No additional configuration needed!**

---

## Testing Results (AWS Instance: 54.190.74.93)

### ✅ Verified Working
```json
{
  "stats": {
    "items_ingested": 80,
    "success_rate": 100.0,
    "active_sources": 6
  }
}
```

### Source Performance
| Source | Items | Status |
|--------|-------|--------|
| arXiv AI/ML | 20 | ✅ Working |
| Hugging Face Papers | 11 | ✅ Working |
| TechCrunch AI | 20 | ✅ Working |
| VentureBeat AI | 19 | ✅ Working |
| The Verge AI | 10 | ✅ Working |
| OpenAI Blog | 0 | ⚠️ 403 Forbidden |

### Content Verification
- ✅ Papers searchable: "diffusion models" returns 10 results
- ✅ News searchable: "AI funding" returns relevant articles
- ✅ Auto-ingestion confirmed via vector database
- ✅ Scheduler running (next: daily at 02:00 UTC)

---

## Manual Trigger Commands

### Check Status
```bash
curl http://localhost:8015/status | jq .
```

### Trigger Manual Fetch
```bash
# All sources
curl -X POST http://localhost:8015/trigger/all

# Specific source by ID
curl -X POST http://localhost:8015/trigger/1  # arXiv
curl -X POST http://localhost:8015/trigger/2  # Hugging Face
curl -X POST http://localhost:8015/trigger/3  # TechCrunch
curl -X POST http://localhost:8015/trigger/4  # VentureBeat
curl -X POST http://localhost:8015/trigger/5  # The Verge
curl -X POST http://localhost:8015/trigger/6  # OpenAI Blog
```

### View Ingested Items
```bash
curl http://localhost:8015/items?limit=10 | jq .
```

---

## Automatic Behavior

### On Service Start
- Checks database for existing sources
- Creates any missing default sources
- Does NOT re-create existing sources (idempotent)

### Scheduled Fetching
- **Frequency:** Daily at 02:00 UTC
- **Reason:** After arXiv daily update (typically 00:00 UTC)
- **Content:** Up to 80-90 items per cycle
- **Processing:** Fully automatic, no manual intervention

---

## Known Issues & Solutions

### Issue: OpenAI Blog 403 Forbidden
**Cause:** Anti-scraping protection on openai.com

**Solution Options:**
1. Add user-agent header in scraper
2. Use rotating user-agents
3. Add rate limiting delays
4. Consider disabling if not critical

**Current Status:** Source is created but returns 0 items. Does not affect other sources.

---

## Rollback Plan (If Needed)

### Option 1: Revert Service Only
```bash
cd ~/rag_lab/services/research-agent/app
git checkout HEAD~1 service.py
docker compose restart research-agent
```

### Option 2: Disable New Sources
```bash
# Via API
curl -X PUT http://localhost:8015/sources/3 -d '{"enabled": false}'  # TechCrunch
curl -X PUT http://localhost:8015/sources/4 -d '{"enabled": false}'  # VentureBeat
curl -X PUT http://localhost:8015/sources/5 -d '{"enabled": false}'  # The Verge
curl -X PUT http://localhost:8015/sources/6 -d '{"enabled": false}'  # OpenAI
```

### Option 3: Full Rollback
```bash
cd ~/rag_lab
git checkout <previous-commit>
docker compose down research-agent
docker compose up -d research-agent
```

---

## Monitoring & Validation

### Health Check
```bash
curl http://localhost:8015/health
# Expected: {"status": "healthy", "scheduler_running": true}
```

### Fetch History
```bash
curl http://localhost:8015/history?limit=10 | jq .
```

### Docker Logs
```bash
docker logs rag-research-agent --tail 100
# Look for: "✅ Ingested: <title>"
# Warnings: "Error discovering" (OK for OpenAI Blog)
```

### Database Check
```bash
docker exec rag-research-agent ls -lh /data/research_agent.db
# Should show growing file size after fetches
```

---

## Performance Impact

### Resource Usage
- **CPU:** Minimal increase (web scraping is IO-bound)
- **Memory:** ~50MB additional (4 new scrapers)
- **Network:** ~5-10MB per fetch cycle
- **Storage:** ~500KB per ingested item

### Time to Fetch
- **arXiv:** ~3-4 seconds (20 items)
- **Hugging Face:** ~7-8 seconds (10 items)
- **TechCrunch:** ~6 seconds (20 items)
- **VentureBeat:** ~4 seconds (19 items)
- **The Verge:** ~4 seconds (10 items)
- **Total:** ~25-30 seconds for full cycle

---

## Future Enhancements

### Potential Additions
- [ ] Fix OpenAI Blog scraper (user-agent)
- [ ] Add MIT News AI coverage
- [ ] Add Google AI Blog
- [ ] Add Microsoft Research blog
- [ ] Add arXiv cs.RO (Robotics) category
- [ ] Content deduplication (see RESEARCH_AGENT_DEDUPLICATION.md)
- [ ] UI dashboard for source management

### Configuration Options
- [ ] Per-source fetch frequencies
- [ ] Category filtering per source
- [ ] Max items per source (currently hardcoded)
- [ ] Quality scoring and filtering

---

## Contact & Support

**Developer:** RAG Lab Team
**Documentation:** `/docs/research-agent/`
**Service Port:** 8015
**GitHub Branch:** `security`

**Questions?** Check `/docs/research-agent/README.md` for detailed architecture and API documentation.

---

**Status:** ✅ **READY FOR PRODUCTION DEPLOYMENT**

This enhancement is backwards compatible, tested, and ready to roll out to any environment.

