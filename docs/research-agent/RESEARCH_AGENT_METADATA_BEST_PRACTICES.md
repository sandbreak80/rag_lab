# 📋 Research Agent Metadata Best Practices

**Date:** November 5, 2025
**Topic:** Optimal metadata structure and storage architecture

---

## 🎯 Goals

1. **Rich Attribution**: Who wrote it, when, where
2. **Discoverability**: Filter by date, topic, source
3. **Quality Signals**: Citation counts, community scores
4. **Provenance**: Track origin and processing
5. **Time-Aware**: Prioritize recent content

---

## 📊 Comprehensive Metadata Schema

### Tier 1: Essential Metadata (Always Include)

```json
{
  "source_type": "arxiv | blog | github | huggingface | web",
  "external_id": "unique-id-from-source",
  "url": "https://...",
  "title": "Paper/Article Title",
  "authors": "Author 1, Author 2, et al.",
  "published_date": "2025-11-05T00:00:00Z",
  "discovered_date": "2025-11-05T10:30:00Z",
  "abstract": "Brief summary...",
  "language": "en"
}
```

### Tier 2: Enhanced Metadata (When Available)

```json
{
  "doi": "10.1234/example",
  "author_affiliations": ["Google Research", "Stanford"],
  "keywords": ["transformer", "attention", "nlp"],
  "subject_categories": ["cs.LG", "cs.CL", "cs.AI"],
  "page_count": 15,
  "has_code": true,
  "github_repo": "https://github.com/...",
  "citation_count": 1500,
  "version": "v2",
  "last_updated": "2025-11-03T00:00:00Z"
}
```

### Tier 3: Processing Metadata (Auto-Generated)

```json
{
  "ingestion_method": "research-agent-arxiv",
  "processing_date": "2025-11-05T10:35:00Z",
  "content_hash": "sha256...",
  "chunk_count": 45,
  "chunk_strategy": "semantic | fixed | paragraph",
  "embedding_model": "nomic-embed-text",
  "docling_processed": true,
  "quality_score": 0.85
}
```

---

## 🏗️ Storage Architecture

### RECOMMENDED: Hybrid Approach

#### 1. Research Agent Database (SQLite)

**Purpose:** Track discovery & fetch status ONLY

**Schema:**
```sql
CREATE TABLE items (
    id INTEGER PRIMARY KEY,
    source_id INTEGER,
    external_id TEXT UNIQUE,     -- e.g., "2311.12345"
    title TEXT,
    url TEXT,
    authors TEXT,
    discovered_at TIMESTAMP,
    ingested_at TIMESTAMP,       -- When added to vector DB
    status TEXT,                 -- 'discovered', 'ingested', 'failed'
    metadata_json TEXT           -- Full metadata for reference
);
```

**What It Stores:**
- ✅ What was discovered
- ✅ When it was found
- ✅ Fetch/ingest status
- ✅ Error tracking
- ❌ NOT the actual content
- ❌ NOT the embeddings

#### 2. Vector Database (ChromaDB)

**Purpose:** Store ALL searchable content with embeddings

**What Goes Here:**
- ✅ Research papers (from agent)
- ✅ User uploads
- ✅ Blog articles
- ✅ GitHub READMEs
- ✅ All with full metadata
- ✅ All searchable together

**Collection Structure:**
```python
collection.add(
    documents=["chunk 1 text", "chunk 2 text", ...],
    metadatas=[
        {
            "filename": "research_2311.12345.md",
            "chunk_index": 0,
            "source_type": "arxiv",
            "external_id": "2311.12345",
            "title": "Attention Is All You Need",
            "authors": "Vaswani, Shazeer, et al.",
            "published_date": "2017-06-12",
            "discovered_date": "2025-11-05",
            "subject_categories": "cs.LG,cs.CL",
            "tags": "research,transformer,attention,auto-discovered",
            "ingestion_source": "research-agent",
            "page_number": 3,
            "section": "Methods"
        },
        ...
    ],
    ids=["research_2311.12345_chunk_0", ...],
    embeddings=[[0.1, 0.2, ...], ...]  # Auto-generated
)
```

---

## 🔄 Processing Pipeline

### Step 1: Discovery (Research Agent)

```python
discovered_item = {
    'external_id': '2311.12345',
    'title': 'Paper Title',
    'url': 'https://arxiv.org/abs/2311.12345',
    'authors': 'Authors',
    'abstract': '...',
    'published_date': datetime(...),
    'metadata': {
        'categories': ['cs.AI', 'cs.LG'],
        'doi': '10.1234/...',
        # ... more metadata
    }
}

# Save to research agent DB
db.create_item(...)
```

### Step 2: Content Fetching

**For PDFs (arXiv, research papers):**
```python
# Use Docling for structure-aware extraction
def fetch_pdf_content(url):
    # 1. Download PDF
    pdf_file = download(url)

    # 2. Process with Docling
    result = docling_service.convert(pdf_file)

    # 3. Get structured markdown
    markdown = result.markdown

    # 4. Preserve structure metadata
    sections = result.sections  # ["Introduction", "Methods", ...]
    tables = result.tables      # Extracted tables
    figures = result.figures    # Figure captions

    return {
        'content': markdown,
        'sections': sections,
        'page_count': result.page_count
    }
```

**For Web Content (blogs, articles):**
```python
def fetch_web_content(url):
    # 1. Fetch HTML
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # 2. Extract main content (remove nav, ads, etc.)
    article = extract_article_content(soup)

    # 3. Convert to markdown
    markdown = html_to_markdown(article)

    # 4. Extract metadata
    metadata = {
        'title': soup.find('title').text,
        'author': extract_author(soup),
        'published_date': extract_date(soup),
        'description': soup.find('meta', {'name': 'description'})['content']
    }

    return {'content': markdown, 'metadata': metadata}
```

### Step 3: Ingestion (Via Ingest Service)

```python
# Send to ingest service with rich metadata
ingest_request = {
    'content': markdown_content,
    'filename': f"research_{external_id}.md",
    'metadata': {
        # Source identification
        'source_type': 'arxiv',
        'external_id': '2311.12345',
        'url': 'https://arxiv.org/abs/2311.12345',

        # Content metadata
        'title': 'Paper Title',
        'authors': 'Author 1, Author 2',
        'published_date': '2017-06-12',
        'subject_categories': 'cs.LG,cs.CL',
        'abstract': '...',

        # Processing metadata
        'discovered_date': '2025-11-05T10:30:00Z',
        'ingestion_source': 'research-agent',
        'docling_processed': True,
        'page_count': 15,

        # Tags for filtering
        'tags': 'research,ai,transformer,auto-discovered'
    }
}

response = requests.post(
    f"{INGEST_SERVICE_URL}/ingest",
    json=ingest_request
)
```

### Step 4: Storage (Ingest Service → Vector DB)

```python
# Ingest service processes and stores
def process_research_content(content, metadata):
    # 1. Chunk semantically
    chunks = semantic_chunker.chunk(content)

    # 2. For each chunk, create metadata
    chunk_metadatas = []
    for i, chunk in enumerate(chunks):
        chunk_meta = {
            **metadata,  # All document-level metadata
            'chunk_index': i,
            'chunk_total': len(chunks),
            'filename': metadata['filename'],
            # Add chunk-specific metadata
            'section': detect_section(chunk),
            'page_number': estimate_page(chunk, i, len(chunks))
        }
        chunk_metadatas.append(chunk_meta)

    # 3. Store in vector DB
    vector_db.add(
        documents=chunks,
        metadatas=chunk_metadatas,
        ids=[f"{metadata['external_id']}_chunk_{i}" for i in range(len(chunks))]
    )
```

---

## 🔍 Querying with Metadata

### Example 1: Recent Papers on Transformers

```python
results = vector_db.query(
    query_texts=["transformer architectures"],
    where={
        "source_type": "arxiv",
        "published_date": {"$gte": "2024-01-01"},
        "$or": [
            {"subject_categories": {"$contains": "cs.LG"}},
            {"keywords": {"$contains": "transformer"}}
        ]
    },
    n_results=10
)
```

### Example 2: Highly-Cited Papers

```python
results = vector_db.query(
    query_texts=["attention mechanisms"],
    where={
        "citation_count": {"$gte": 100}
    },
    n_results=5
)
```

### Example 3: Multi-Source Search

```python
# Search both user docs and research content
results = vector_db.query(
    query_texts=["RAG best practices"],
    where={
        "$or": [
            {"source_type": "user_upload"},
            {"source_type": {"$in": ["arxiv", "blog", "github"]}}
        ]
    },
    n_results=20
)
```

---

## 📊 Metadata in UI

### Display in Search Results

```markdown
📄 **Attention Is All You Need**
👤 Vaswani, Shazeer, et al. | Google Research
📅 Published: 2017-06-12 | Discovered: 2025-11-05
🏷️ cs.LG, cs.CL | 📚 75,000 citations
🔗 https://arxiv.org/abs/1706.03762
💬 "The dominant sequence transduction models..."
```

### Filter Panel

```
Source Type:
☑ Research Papers (arXiv)
☑ Blog Articles
☐ GitHub READMEs
☑ User Uploads

Date Range:
● Last 7 days
○ Last 30 days
○ Last year
○ Custom

Categories:
☑ Machine Learning (cs.LG)
☑ NLP (cs.CL)
☐ Computer Vision (cs.CV)
```

---

## ⚡ Performance Considerations

### 1. Metadata Indexing

ChromaDB automatically indexes metadata fields for fast filtering:
- String fields: Exact match, contains
- Numeric fields: Range queries ($gt, $lt, $gte, $lte)
- Date fields: Time range queries

### 2. Metadata Size

- Keep metadata < 5KB per chunk
- Use codes/IDs instead of full text where possible
- Example: Store `"category_ids": [1, 5, 8]` instead of full category names

### 3. Query Optimization

```python
# ✅ GOOD: Filter first, then semantic search
results = query(
    where={"published_date": {"$gte": "2024-01-01"}},  # Narrow search space
    query_texts=["transformers"],
    n_results=10
)

# ❌ BAD: Search all, filter after
all_results = query(query_texts=["transformers"], n_results=1000)
filtered = [r for r in all_results if r.published_date >= "2024-01-01"]
```

---

## 🎯 Best Practices Summary

### ✅ DO:

1. **Capture comprehensive metadata** at discovery time
2. **Use the shared vector DB** for all searchable content
3. **Preserve source attribution** (author, date, URL)
4. **Include processing metadata** for debugging
5. **Tag content** for easy filtering
6. **Use Docling for PDFs** (structure-aware)
7. **Standardize date formats** (ISO 8601)
8. **Track provenance** (where did it come from?)

### ❌ DON'T:

1. **Don't create separate vector DBs** per source
2. **Don't skip metadata** - it's crucial for filtering
3. **Don't lose attribution** - always track authors/sources
4. **Don't ignore timestamps** - time-aware search is powerful
5. **Don't store full content in research agent DB** - that's for vector DB
6. **Don't forget to clean/sanitize** before ingestion

---

## 🚀 Implementation Checklist

- [ ] Update `arxiv_scraper.py` to capture all available metadata
- [ ] Add Docling integration for PDF processing
- [ ] Enhance `ingest_content()` to pass rich metadata
- [ ] Update ingest service to accept extended metadata
- [ ] Add metadata display to UI search results
- [ ] Create metadata filter panel in frontend
- [ ] Add time-based relevance scoring
- [ ] Implement citation count tracking (if available)

---

**Result:** A world-class research agent with professional-grade metadata management! 🌟

