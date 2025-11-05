# Custom Crawler / "Skill" System Design

## 🎯 Vision

Build a **domain-specific knowledge crawler** (aka "Skill") that automatically researches, indexes, and maintains expertise in a focused subject area. Think of it as giving your RAG system a **PhD in a specific topic**.

---

## 💡 Core Concept: What is a "Skill"?

A **Skill** is a self-contained knowledge domain that:
1. **Crawls** specific sources (websites, APIs, RSS feeds)
2. **Ingests** new content automatically
3. **Indexes** documents for RAG retrieval
4. **Maintains** freshness (updates daily/weekly)
5. **Specializes** the RAG system for that domain

### **Example Skills:**

#### **Skill 1: "AI Research Papers"**
- **Sources:** arXiv, Hugging Face papers, Google Scholar
- **Update Frequency:** Daily
- **Content Types:** PDFs, abstracts, citations
- **Use Case:** Answer questions about latest AI research

#### **Skill 2: "Company News & Announcements"**
- **Sources:** Company blog, press releases, SEC filings
- **Update Frequency:** Hourly
- **Content Types:** HTML, PDFs, RSS feeds
- **Use Case:** Corporate knowledge base

#### **Skill 3: "AI Industry News"**
- **Sources:** TechCrunch, VentureBeat, The Verge, AI-focused blogs
- **Update Frequency:** Hourly
- **Content Types:** Articles, blog posts
- **Use Case:** Stay current on AI trends

#### **Skill 4: "Technical Documentation"**
- **Sources:** Official docs (PyTorch, TensorFlow, LangChain)
- **Update Frequency:** Weekly
- **Content Types:** Markdown, HTML, code examples
- **Use Case:** Developer Q&A

---

## 🏗️ Architecture

### **High-Level Design:**

```
┌─────────────────────────────────────────────────────────────┐
│                     SKILL MANAGER                            │
│  - Register skills                                           │
│  - Schedule crawls                                           │
│  - Monitor health                                            │
└─────────────────────────────────────────────────────────────┘
                              ↓
        ┌─────────────────────┼─────────────────────┐
        ↓                     ↓                     ↓
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  SKILL: AI    │    │ SKILL: Company│    │ SKILL: Tech   │
│  Research     │    │ News          │    │ Docs          │
├───────────────┤    ├───────────────┤    ├───────────────┤
│ Sources:      │    │ Sources:      │    │ Sources:      │
│ - arXiv       │    │ - Blog RSS    │    │ - PyTorch     │
│ - HF Papers   │    │ - Press API   │    │ - TensorFlow  │
│ - Scholar     │    │ - SEC EDGAR   │    │ - LangChain   │
├───────────────┤    ├───────────────┤    ├───────────────┤
│ Crawler:      │    │ Crawler:      │    │ Crawler:      │
│ - PDF fetch   │    │ - RSS parser  │    │ - HTML scrape │
│ - Extract     │    │ - API calls   │    │ - MD parse    │
│ - Dedupe      │    │ - Dedupe      │    │ - Code extract│
├───────────────┤    ├───────────────┤    ├───────────────┤
│ Schedule:     │    │ Schedule:     │    │ Schedule:     │
│ - Daily 2am   │    │ - Hourly      │    │ - Weekly      │
├───────────────┤    ├───────────────┤    ├───────────────┤
│ Storage:      │    │ Storage:      │    │ Storage:      │
│ /skills/ai/   │    │ /skills/news/ │    │ /skills/docs/ │
└───────────────┘    └───────────────┘    └───────────────┘
        ↓                     ↓                     ↓
┌─────────────────────────────────────────────────────────────┐
│                  INGESTION PIPELINE                          │
│  1. Docling (PDF → Markdown)                                │
│  2. Chunking (Agentic or Fixed)                             │
│  3. Embedding (nomic-embed-text)                            │
│  4. Vector DB (ChromaDB)                                    │
│  5. BM25 Index                                              │
│  6. Knowledge Graph                                         │
└─────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────┐
│                     RAG SYSTEM                               │
│  - Query with skill filter: "skill:ai_research"            │
│  - Multi-skill queries: "skill:ai_research,company_news"   │
│  - Skill-specific prompts                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Data Storage

### **Directory Structure:**

```
/data/skills/
├── ai_research/
│   ├── config.json              # Skill configuration
│   ├── sources.json             # Source URLs, APIs, RSS feeds
│   ├── schedule.json            # Cron schedule
│   ├── raw/                     # Raw downloaded files
│   │   ├── arxiv_2024_11_05/
│   │   │   ├── paper1.pdf
│   │   │   ├── paper2.pdf
│   │   └── huggingface_papers/
│   ├── processed/               # Processed markdown
│   │   ├── paper1.md
│   │   ├── paper2.md
│   ├── metadata.db              # SQLite: URLs, dates, hashes
│   └── stats.json               # Crawl statistics
│
├── company_news/
│   ├── config.json
│   ├── sources.json
│   ├── raw/
│   ├── processed/
│   ├── metadata.db
│   └── stats.json
│
└── tech_docs/
    ├── config.json
    ├── sources.json
    ├── raw/
    ├── processed/
    ├── metadata.db
    └── stats.json
```

### **Skill Configuration (`config.json`):**

```json
{
  "skill_id": "ai_research",
  "name": "AI Research Papers",
  "description": "Latest AI/ML research from arXiv, Hugging Face, and Google Scholar",
  "version": "1.0.0",
  "enabled": true,
  "schedule": {
    "frequency": "daily",
    "time": "02:00",
    "timezone": "UTC"
  },
  "sources": [
    {
      "type": "arxiv",
      "url": "http://export.arxiv.org/api/query",
      "query": "cat:cs.AI OR cat:cs.LG OR cat:cs.CL",
      "max_results": 50,
      "enabled": true
    },
    {
      "type": "rss",
      "url": "https://huggingface.co/papers/rss",
      "max_items": 20,
      "enabled": true
    },
    {
      "type": "web",
      "url": "https://scholar.google.com/scholar?q=large+language+models",
      "selector": ".gs_ri",
      "enabled": false
    }
  ],
  "processing": {
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "use_agentic_chunking": true,
    "extract_citations": true,
    "extract_code": false
  },
  "retention": {
    "keep_raw_files": true,
    "max_age_days": 365,
    "max_documents": 10000
  },
  "metadata": {
    "tags": ["ai", "research", "papers", "arxiv"],
    "priority": "high",
    "quality_threshold": 0.7
  }
}
```

### **Source Registry (`sources.json`):**

```json
{
  "sources": [
    {
      "id": "arxiv_cs_ai",
      "type": "arxiv",
      "url": "http://export.arxiv.org/api/query",
      "params": {
        "search_query": "cat:cs.AI",
        "max_results": 50,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
      },
      "last_crawl": "2025-11-05T02:00:00Z",
      "next_crawl": "2025-11-06T02:00:00Z",
      "documents_fetched": 47,
      "errors": 0,
      "enabled": true
    },
    {
      "id": "huggingface_papers",
      "type": "rss",
      "url": "https://huggingface.co/papers/rss",
      "last_crawl": "2025-11-05T02:00:00Z",
      "next_crawl": "2025-11-06T02:00:00Z",
      "documents_fetched": 18,
      "errors": 0,
      "enabled": true
    }
  ]
}
```

---

## 🔧 Implementation

### **Service: `skill-manager`**

```python
# services/skill-manager/app/service.py

from flask import Flask, request, jsonify
import schedule
import time
import threading
from pathlib import Path
import json

app = Flask(__name__)

class SkillManager:
    def __init__(self):
        self.skills_dir = Path("/data/skills")
        self.skills = {}
        self.load_skills()
        
    def load_skills(self):
        """Load all skill configurations"""
        for skill_dir in self.skills_dir.iterdir():
            if skill_dir.is_dir():
                config_path = skill_dir / "config.json"
                if config_path.exists():
                    with open(config_path) as f:
                        config = json.load(f)
                        self.skills[config['skill_id']] = Skill(config, skill_dir)
    
    def schedule_crawls(self):
        """Schedule crawls for all enabled skills"""
        for skill in self.skills.values():
            if skill.enabled:
                schedule.every().day.at(skill.schedule_time).do(skill.crawl)
    
    def crawl_all(self):
        """Manually trigger crawl for all skills"""
        results = {}
        for skill_id, skill in self.skills.items():
            if skill.enabled:
                results[skill_id] = skill.crawl()
        return results

class Skill:
    def __init__(self, config, skill_dir):
        self.config = config
        self.skill_dir = skill_dir
        self.skill_id = config['skill_id']
        self.name = config['name']
        self.enabled = config.get('enabled', True)
        self.schedule_time = config['schedule']['time']
        self.sources = config['sources']
        
    def crawl(self):
        """Execute crawl for this skill"""
        print(f"🕷️  Crawling skill: {self.name}")
        results = {
            'skill_id': self.skill_id,
            'started_at': time.time(),
            'sources': []
        }
        
        for source in self.sources:
            if source.get('enabled', True):
                source_result = self.crawl_source(source)
                results['sources'].append(source_result)
        
        results['completed_at'] = time.time()
        results['duration_seconds'] = results['completed_at'] - results['started_at']
        
        # Save results
        self.save_crawl_results(results)
        
        # Trigger ingestion
        self.ingest_new_documents()
        
        return results
    
    def crawl_source(self, source):
        """Crawl a specific source"""
        source_type = source['type']
        
        if source_type == 'arxiv':
            return self.crawl_arxiv(source)
        elif source_type == 'rss':
            return self.crawl_rss(source)
        elif source_type == 'web':
            return self.crawl_web(source)
        else:
            return {'error': f'Unknown source type: {source_type}'}
    
    def crawl_arxiv(self, source):
        """Crawl arXiv API"""
        import requests
        import xml.etree.ElementTree as ET
        
        url = source['url']
        params = {
            'search_query': source['query'],
            'max_results': source['max_results'],
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }
        
        response = requests.get(url, params=params)
        root = ET.fromstring(response.content)
        
        papers = []
        for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
            paper = {
                'id': entry.find('{http://www.w3.org/2005/Atom}id').text,
                'title': entry.find('{http://www.w3.org/2005/Atom}title').text,
                'summary': entry.find('{http://www.w3.org/2005/Atom}summary').text,
                'published': entry.find('{http://www.w3.org/2005/Atom}published').text,
                'pdf_url': entry.find('{http://www.w3.org/2005/Atom}link[@title="pdf"]').attrib['href']
            }
            
            # Download PDF
            pdf_path = self.download_pdf(paper['pdf_url'], paper['id'])
            paper['local_path'] = str(pdf_path)
            
            papers.append(paper)
        
        return {
            'source_type': 'arxiv',
            'papers_fetched': len(papers),
            'papers': papers
        }
    
    def crawl_rss(self, source):
        """Crawl RSS feed"""
        import feedparser
        
        feed = feedparser.parse(source['url'])
        
        items = []
        for entry in feed.entries[:source.get('max_items', 20)]:
            item = {
                'title': entry.title,
                'link': entry.link,
                'published': entry.get('published', ''),
                'summary': entry.get('summary', '')
            }
            
            # Download content
            content_path = self.download_html(entry.link, entry.title)
            item['local_path'] = str(content_path)
            
            items.append(item)
        
        return {
            'source_type': 'rss',
            'items_fetched': len(items),
            'items': items
        }
    
    def crawl_web(self, source):
        """Crawl web page with selector"""
        import requests
        from bs4 import BeautifulSoup
        
        response = requests.get(source['url'])
        soup = BeautifulSoup(response.content, 'html.parser')
        
        elements = soup.select(source['selector'])
        
        items = []
        for elem in elements:
            item = {
                'text': elem.get_text(strip=True),
                'html': str(elem)
            }
            items.append(item)
        
        return {
            'source_type': 'web',
            'items_fetched': len(items),
            'items': items
        }
    
    def download_pdf(self, url, paper_id):
        """Download PDF to raw directory"""
        import requests
        
        raw_dir = self.skill_dir / "raw" / "arxiv"
        raw_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{paper_id.replace('/', '_')}.pdf"
        filepath = raw_dir / filename
        
        if not filepath.exists():
            response = requests.get(url)
            with open(filepath, 'wb') as f:
                f.write(response.content)
        
        return filepath
    
    def download_html(self, url, title):
        """Download HTML to raw directory"""
        import requests
        import hashlib
        
        raw_dir = self.skill_dir / "raw" / "html"
        raw_dir.mkdir(parents=True, exist_ok=True)
        
        # Use hash of URL as filename
        url_hash = hashlib.md5(url.encode()).hexdigest()
        filename = f"{url_hash}.html"
        filepath = raw_dir / filename
        
        if not filepath.exists():
            response = requests.get(url)
            with open(filepath, 'wb') as f:
                f.write(response.content)
        
        return filepath
    
    def ingest_new_documents(self):
        """Trigger ingestion for new documents"""
        # Call ingest service
        import requests
        
        ingest_url = "http://ingest-service:8001/ingest_directory"
        
        response = requests.post(ingest_url, json={
            'directory': str(self.skill_dir / "raw"),
            'skill_id': self.skill_id,
            'metadata': {
                'skill': self.skill_id,
                'skill_name': self.name,
                'tags': self.config.get('metadata', {}).get('tags', [])
            }
        })
        
        return response.json()
    
    def save_crawl_results(self, results):
        """Save crawl results to stats file"""
        stats_file = self.skill_dir / "stats.json"
        
        # Load existing stats
        if stats_file.exists():
            with open(stats_file) as f:
                stats = json.load(f)
        else:
            stats = {'crawls': []}
        
        # Append new crawl
        stats['crawls'].append(results)
        
        # Keep only last 100 crawls
        stats['crawls'] = stats['crawls'][-100:]
        
        # Save
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)

# Flask routes
skill_manager = SkillManager()

@app.route('/skills', methods=['GET'])
def list_skills():
    """List all registered skills"""
    return jsonify({
        'skills': [
            {
                'skill_id': skill.skill_id,
                'name': skill.name,
                'enabled': skill.enabled,
                'sources': len(skill.sources)
            }
            for skill in skill_manager.skills.values()
        ]
    })

@app.route('/skills/<skill_id>/crawl', methods=['POST'])
def crawl_skill(skill_id):
    """Manually trigger crawl for a skill"""
    skill = skill_manager.skills.get(skill_id)
    if not skill:
        return jsonify({'error': 'Skill not found'}), 404
    
    results = skill.crawl()
    return jsonify(results)

@app.route('/skills/crawl_all', methods=['POST'])
def crawl_all_skills():
    """Manually trigger crawl for all skills"""
    results = skill_manager.crawl_all()
    return jsonify(results)

if __name__ == '__main__':
    # Start scheduler in background thread
    def run_scheduler():
        skill_manager.schedule_crawls()
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    # Start Flask app
    app.run(host='0.0.0.0', port=8012, debug=False)
```

---

## 🎯 Recommended First Skill: "AI Research Papers"

### **Why This is Perfect:**

1. **High Value:** Latest AI research is always relevant
2. **Well-Structured:** arXiv has clean APIs
3. **Educational:** Students learn about current research
4. **Manageable:** ~50 papers/day, mostly PDFs
5. **Verifiable:** Easy to check if crawl worked

### **Sources:**

1. **arXiv** (Primary)
   - API: `http://export.arxiv.org/api/query`
   - Categories: `cs.AI`, `cs.LG`, `cs.CL`
   - ~50 papers/day

2. **Hugging Face Papers** (Secondary)
   - RSS: `https://huggingface.co/papers/rss`
   - ~20 papers/day

3. **Papers with Code** (Tertiary)
   - API: `https://paperswithcode.com/api/v1/papers/`
   - Includes code implementations

### **Storage Estimate:**

- **Raw PDFs:** ~50 papers/day × 5MB/paper = 250MB/day
- **Processed Markdown:** ~50 papers/day × 100KB/paper = 5MB/day
- **Embeddings:** ~50 papers/day × 50 chunks/paper × 1KB/chunk = 2.5MB/day
- **Total:** ~260MB/day = ~7.8GB/month = ~95GB/year

**With 1-year retention:** ~100GB storage needed

---

## 🚀 Implementation Plan

### **Phase 1: Core Infrastructure (4-6 hours)**

1. **Skill Manager Service** (2 hours)
   - Create `services/skill-manager/`
   - Implement `SkillManager` class
   - Add Flask routes
   - Add to `docker-compose.yml`

2. **Skill Configuration** (1 hour)
   - Create `/data/skills/` directory structure
   - Write `config.json` for "AI Research Papers"
   - Write `sources.json` for arXiv + HF

3. **Crawler Implementation** (2 hours)
   - arXiv API crawler
   - RSS feed crawler
   - PDF download logic
   - Deduplication (by URL hash)

4. **Integration** (1 hour)
   - Connect to ingest service
   - Test end-to-end flow
   - Verify documents appear in RAG

### **Phase 2: UI & Monitoring (2-3 hours)**

5. **Skill Management UI** (2 hours)
   - New page: `/skills`
   - List all skills
   - Enable/disable skills
   - Trigger manual crawls
   - View crawl history

6. **Skill Filtering in Search** (1 hour)
   - Add `skill_id` filter to search
   - UI toggle: "Search only AI Research Papers"
   - Show skill badge on results

### **Phase 3: Additional Skills (1-2 hours each)**

7. **Skill: "Company News"**
   - RSS feeds from company blogs
   - Press release APIs
   - SEC EDGAR filings

8. **Skill: "Tech Documentation"**
   - PyTorch docs
   - TensorFlow docs
   - LangChain docs

---

## 🧪 Lab Exercise: "Build Your Own Skill"

### **Student Assignment:**

**Goal:** Create a custom skill for a domain of your choice

**Steps:**
1. Choose a domain (e.g., "Crypto News", "Sports Stats", "Weather Data")
2. Identify 2-3 sources (RSS feeds, APIs, websites)
3. Write `config.json` for your skill
4. Test crawler manually
5. Schedule daily crawls
6. Query your skill via RAG

**Deliverables:**
- `config.json` file
- Crawl statistics (documents fetched)
- 3 example queries answered by your skill
- Reflection: What worked? What didn't?

---

## 📊 Success Metrics

### **Technical:**
- ✅ Crawl success rate (> 95%)
- ✅ Deduplication rate (< 5% duplicates)
- ✅ Ingestion success rate (> 90%)
- ✅ Storage efficiency (< 1GB/month per skill)

### **Educational:**
- ✅ Student engagement (time spent with skills)
- ✅ Skill creation rate (students build own skills)
- ✅ Query quality (students ask better questions)
- ✅ Understanding (quiz scores on RAG concepts)

---

## 🔮 Future Enhancements

### **Advanced Features:**

1. **Incremental Crawling**
   - Only fetch new documents (since last crawl)
   - Use ETags, Last-Modified headers
   - Reduce bandwidth and storage

2. **Quality Scoring**
   - LLM rates document quality (1-5 stars)
   - Filter low-quality documents
   - Prioritize high-quality sources

3. **Automatic Source Discovery**
   - LLM suggests new sources for a skill
   - User approves/rejects suggestions
   - Continuously improve coverage

4. **Multi-Skill Queries**
   - Query across multiple skills
   - Weight results by skill relevance
   - Show skill distribution in results

5. **Skill Marketplace**
   - Share skills with community
   - Import skills from others
   - Rate and review skills

---

**Version:** 1.0.0 (Design)  
**Date:** November 5, 2025  
**Status:** 📋 Design Complete → 🚧 Ready to Implement  
**Estimated Effort:** 6-8 hours for Phase 1  
**Recommended First Skill:** AI Research Papers (arXiv + Hugging Face)

