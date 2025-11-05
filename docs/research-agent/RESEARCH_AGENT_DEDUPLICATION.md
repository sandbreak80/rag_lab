# 🔄 Research Agent Deduplication System

**Date:** November 5, 2025
**Status:** 🎯 Design Complete - Ready for Implementation
**Priority:** Critical for production use

---

## 🎯 Problem Statement

The research agent discovers content from multiple sources and runs periodically. Without deduplication:

❌ **Problem 1: Re-ingesting Same Content**
- arXiv paper discovered twice → ingested twice
- Wastes storage, compute, and costs
- Pollutes search results with duplicates

❌ **Problem 2: Cross-Source Duplicates**
- Same AP article on 20 different news sites
- Same research paper on arXiv, ResearchGate, and author's website
- Same blog post republished on Medium, Dev.to, and personal site

❌ **Problem 3: Near-Duplicates**
- Paper v1 vs v2 vs v3 (minor revisions)
- Article with/without ads, different formatting
- Translation or paraphrasing

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                Discovery Phase                          │
│  - arXiv, Hugging Face, Tech Blogs, News Sites         │
└────────────────────┬────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│         Level 1: Database Deduplication                 │
│  - Check external_id (arXiv ID, DOI, URL)              │
│  - Check content_hash (SHA256 of normalized content)    │
│  - Check semantic_hash (simhash of content)             │
│  - Query: "Have we seen this exact content before?"     │
└────────────────────┬────────────────────────────────────┘
                     ↓
        ┌────────────┴────────────┐
        │ Found in DB?            │
        └─────┬──────────────┬────┘
             YES             NO
              ↓               ↓
      ┌───────────────┐  ┌──────────────────────┐
      │ Skip          │  │ Level 2: Semantic    │
      │ Already       │  │ Similarity Check     │
      │ Ingested      │  │ - Embed title/abstract│
      └───────────────┘  │ - Search vector DB   │
                         │ - Similarity > 0.95? │
                         └──────────┬───────────┘
                                   ↓
                        ┌─────────┴──────────┐
                        │ Similar exists?     │
                        └───┬──────────┬─────┘
                           YES        NO
                            ↓          ↓
                    ┌────────────┐  ┌──────────┐
                    │ Mark as    │  │ INGEST   │
                    │ Duplicate  │  │ Content  │
                    └────────────┘  └──────────┘
```

---

## 📋 Implementation Plan

### Phase 1: Database-Level Deduplication (FAST)

#### 1.1 Enhanced Schema

```sql
-- Add deduplication fields to research_items table
ALTER TABLE research_items ADD COLUMN content_hash TEXT;
ALTER TABLE research_items ADD COLUMN semantic_hash TEXT;
ALTER TABLE research_items ADD COLUMN canonical_url TEXT;
ALTER TABLE research_items ADD COLUMN duplicate_of INTEGER REFERENCES research_items(id);

-- Indexes for fast lookups
CREATE INDEX idx_content_hash ON research_items(content_hash);
CREATE INDEX idx_semantic_hash ON research_items(semantic_hash);
CREATE INDEX idx_canonical_url ON research_items(canonical_url);
CREATE INDEX idx_external_id ON research_items(external_id);

-- Canonical external IDs table (for cross-source matching)
CREATE TABLE canonical_identifiers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_id TEXT UNIQUE NOT NULL,  -- e.g., "arxiv:2311.12345", "doi:10.1234/..."
    id_type TEXT NOT NULL,  -- 'arxiv', 'doi', 'url', 'isbn'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_canonical_id ON canonical_identifiers(canonical_id);
```

#### 1.2 Content Hashing

```python
import hashlib
from simhash import Simhash

def normalize_content(text: str) -> str:
    """
    Normalize content for consistent hashing
    """
    import re

    # Convert to lowercase
    text = text.lower()

    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)

    # Remove common formatting
    text = re.sub(r'[^\w\s]', '', text)

    # Remove URLs
    text = re.sub(r'http[s]?://\S+', '', text)

    return text.strip()

def compute_content_hash(content: str) -> str:
    """
    Compute SHA256 hash of normalized content

    Fast, exact matching
    """
    normalized = normalize_content(content)
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

def compute_semantic_hash(content: str) -> str:
    """
    Compute SimHash for near-duplicate detection

    Allows fuzzy matching (95%+ similar = duplicate)
    """
    normalized = normalize_content(content)
    # SimHash converts text to 64-bit fingerprint
    # Similar documents have similar fingerprints
    return str(Simhash(normalized).value)

def hamming_distance(hash1: str, hash2: str) -> int:
    """
    Calculate hamming distance between two simhashes
    Distance < 3 = very similar (likely duplicate)
    """
    h1 = int(hash1)
    h2 = int(hash2)
    xor = h1 ^ h2
    return bin(xor).count('1')
```

#### 1.3 URL Canonicalization

```python
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

def canonicalize_url(url: str) -> str:
    """
    Convert URL to canonical form

    Examples:
    - http://example.com?utm_source=twitter → http://example.com
    - https://example.com/article#comments → https://example.com/article
    - http://www.example.com → http://example.com
    """
    parsed = urlparse(url.lower())

    # Remove tracking parameters
    tracking_params = {'utm_source', 'utm_medium', 'utm_campaign', 'utm_content',
                      'fbclid', 'gclid', 'ref', 'source'}
    query_params = parse_qs(parsed.query)
    clean_params = {k: v for k, v in query_params.items() if k not in tracking_params}

    # Rebuild URL without fragment and tracking
    canonical = urlunparse((
        parsed.scheme,
        parsed.netloc.replace('www.', ''),  # Remove www
        parsed.path.rstrip('/'),  # Remove trailing slash
        '',  # params
        urlencode(clean_params, doseq=True) if clean_params else '',
        ''  # fragment
    ))

    return canonical
```

#### 1.4 Deduplication Check

```python
class DeduplicationChecker:
    """
    Multi-level deduplication checker
    """

    def __init__(self, db):
        self.db = db

    def is_duplicate(self, item: Dict, content: str) -> tuple[bool, Optional[int]]:
        """
        Check if item is a duplicate

        Returns: (is_duplicate, duplicate_of_id)
        """

        # Level 1: Check external ID (exact match)
        external_id = item.get('external_id')
        if external_id:
            existing = self.db.find_by_external_id(external_id)
            if existing:
                return (True, existing['id'])

        # Level 2: Check canonical URL
        url = item.get('url')
        if url:
            canonical = canonicalize_url(url)
            existing = self.db.find_by_canonical_url(canonical)
            if existing:
                return (True, existing['id'])

        # Level 3: Check content hash (exact content match)
        content_hash = compute_content_hash(content)
        existing = self.db.find_by_content_hash(content_hash)
        if existing:
            return (True, existing['id'])

        # Level 4: Check semantic hash (near-duplicate)
        semantic_hash = compute_semantic_hash(content)
        similar = self.db.find_similar_semantic_hash(semantic_hash, threshold=3)
        if similar:
            # Verify with cosine similarity of title/abstract
            if self._verify_semantic_similarity(item, similar):
                return (True, similar['id'])

        # Not a duplicate!
        return (False, None)

    def _verify_semantic_similarity(self, item1: Dict, item2: Dict) -> bool:
        """
        Verify similarity using title and abstract comparison
        """
        from sklearn.metrics.pairwise import cosine_similarity
        from sklearn.feature_extraction.text import TfidfVectorizer

        text1 = f"{item1.get('title', '')} {item1.get('abstract', '')}"
        text2 = f"{item2.get('title', '')} {item2.get('abstract', '')}"

        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform([text1, text2])
        similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]

        return similarity > 0.95  # 95% similar = duplicate
```

### Phase 2: Vector DB Semantic Deduplication (ACCURATE)

```python
def semantic_duplicate_check(title: str, abstract: str, vector_db) -> Optional[str]:
    """
    Check if semantically similar content exists in vector DB

    This catches:
    - Same content, different formatting
    - Translations
    - Paraphrases
    - Updated versions
    """

    # Embed the query
    query_text = f"{title} {abstract}"

    # Search vector DB for similar content
    results = vector_db.search(
        query=query_text,
        top_k=5,
        filters={'source_type': ['arxiv', 'huggingface', 'news', 'blog']}
    )

    # Check if any result is highly similar
    for result in results:
        if result['score'] > 0.95:  # 95% semantic similarity
            # Found a near-duplicate!
            return result['metadata'].get('external_id')

    return None
```

---

## 📅 Optimal Fetch Frequency

### Recommended Schedule (Per Source Type)

```python
FETCH_SCHEDULES = {
    # Research Papers (slow-moving)
    'arxiv': {
        'frequency': 'daily',
        'time': '02:00 UTC',  # After arXiv daily update (00:00 EST)
        'lookback_days': 2,  # Catch any late submissions
        'reason': 'arXiv updates once per day (Sun-Thu)'
    },

    'huggingface': {
        'frequency': 'daily',
        'time': '06:00 UTC',
        'lookback_days': 2,
        'reason': 'Papers added throughout the day'
    },

    # News & Blogs (fast-moving)
    'tech_news': {
        'frequency': 'every_6_hours',  # 4x per day
        'times': ['00:00', '06:00', '12:00', '18:00'],
        'lookback_hours': 8,  # Slight overlap to catch updates
        'reason': 'Breaking AI news needs faster updates'
    },

    'tech_blogs': {
        'frequency': 'daily',
        'time': '12:00 UTC',
        'lookback_days': 1,
        'reason': 'Most blogs publish during business hours'
    },

    # AI Research Labs (medium-moving)
    'openai_blog': {
        'frequency': 'weekly',
        'day': 'Monday',
        'time': '08:00 UTC',
        'lookback_days': 8,
        'reason': 'Posts 1-2x per week'
    },

    'anthropic_blog': {
        'frequency': 'weekly',
        'day': 'Monday',
        'time': '09:00 UTC',
        'lookback_days': 8,
        'reason': 'Posts 1-2x per week'
    }
}
```

### Adaptive Scheduling

```python
class AdaptiveScheduler:
    """
    Automatically adjust fetch frequency based on source activity
    """

    def suggest_frequency(self, source_id: int) -> str:
        """
        Analyze fetch history to recommend optimal frequency
        """
        history = self.db.get_fetch_history(source_id, last_n=20)

        # Calculate average items per fetch
        avg_items = sum(h['items_discovered'] for h in history) / len(history)

        # Calculate days between significant updates
        significant_fetches = [h for h in history if h['items_discovered'] > 0]
        if len(significant_fetches) > 1:
            time_deltas = [
                (significant_fetches[i]['fetch_time'] - significant_fetches[i-1]['fetch_time']).days
                for i in range(1, len(significant_fetches))
            ]
            avg_days_between = sum(time_deltas) / len(time_deltas)
        else:
            avg_days_between = 7  # Default

        # Decision logic
        if avg_items > 10 and avg_days_between < 1:
            return 'every_6_hours'  # Very active
        elif avg_items > 5 and avg_days_between < 2:
            return 'daily'  # Active
        elif avg_days_between < 7:
            return 'twice_weekly'  # Moderate
        else:
            return 'weekly'  # Slow-moving
```

---

## 🔧 Integration with Research Agent

### Updated Fetch Flow

```python
def fetch_from_source(source_id: int, manual: bool = False):
    """
    Updated fetch flow with deduplication
    """
    source = db.get_source(source_id)
    scraper = get_scraper(source)
    dedup_checker = DeduplicationChecker(db)

    # Discover items
    discovered = scraper.discover(since=get_last_fetch_time(source))

    stats = {
        'discovered': len(discovered),
        'duplicates': 0,
        'ingested': 0,
        'failed': 0
    }

    for item in discovered:
        try:
            # Fetch content
            content = scraper.fetch_content(item)
            if not content:
                stats['failed'] += 1
                continue

            # ====== DEDUPLICATION CHECK ======
            is_dup, dup_id = dedup_checker.is_duplicate(item, content)

            if is_dup:
                logger.info(f"⏭️ Skipping duplicate: {item['title'][:50]}... (duplicate of item #{dup_id})")
                stats['duplicates'] += 1

                # Still create database record, but mark as duplicate
                item_id = db.create_item(
                    source_id=source_id,
                    external_id=item['external_id'],
                    data=item,
                    status='duplicate',
                    duplicate_of=dup_id
                )
                continue

            # ====== NEW CONTENT - INGEST ======

            # Compute hashes for future deduplication
            content_hash = compute_content_hash(content)
            semantic_hash = compute_semantic_hash(content)
            canonical_url = canonicalize_url(item['url']) if item.get('url') else None

            # Create database record
            item_id = db.create_item(
                source_id=source_id,
                external_id=item['external_id'],
                data=item,
                status='pending',
                content_hash=content_hash,
                semantic_hash=semantic_hash,
                canonical_url=canonical_url
            )

            # Ingest to RAG system
            success = ingest_content(item, content)

            if success:
                db.update_item_status(item_id, 'ingested')
                stats['ingested'] += 1
                logger.info(f"✅ Ingested: {item['title'][:50]}...")
            else:
                db.update_item_status(item_id, 'failed')
                stats['failed'] += 1
                logger.warning(f"❌ Failed: {item['title'][:50]}...")

        except Exception as e:
            logger.error(f"Error processing item: {e}")
            stats['failed'] += 1

    logger.info(f"""
    📊 Fetch Summary:
       Discovered: {stats['discovered']}
       Duplicates: {stats['duplicates']} (⏭️ skipped)
       Ingested:   {stats['ingested']} (✅ new)
       Failed:     {stats['failed']} (❌ errors)
    """)

    return stats
```

---

## 📊 Monitoring & Reporting

### Deduplication Dashboard

```python
@app.route('/dedup/stats', methods=['GET'])
def get_dedup_stats():
    """
    Get deduplication statistics
    """
    stats = db.execute("""
        SELECT
            source_id,
            COUNT(*) as total_items,
            SUM(CASE WHEN status = 'duplicate' THEN 1 ELSE 0 END) as duplicates,
            SUM(CASE WHEN status = 'ingested' THEN 1 ELSE 0 END) as ingested,
            ROUND(100.0 * SUM(CASE WHEN status = 'duplicate' THEN 1 ELSE 0 END) / COUNT(*), 1) as duplicate_rate
        FROM research_items
        WHERE discovered_at > datetime('now', '-30 days')
        GROUP BY source_id
    """).fetchall()

    return jsonify({
        'period': 'Last 30 days',
        'by_source': stats,
        'total_duplicates_prevented': sum(s['duplicates'] for s in stats),
        'storage_saved_mb': sum(s['duplicates'] for s in stats) * 0.5,  # Avg 500KB per paper
        'ingestion_time_saved_hours': sum(s['duplicates'] for s in stats) * 5 / 3600  # Avg 5s per ingest
    })
```

---

## ✅ Benefits

### Before Deduplication:
```
📊 Weekly Fetch Results:
   Discovered: 100 items
   Ingested:   100 items (50 duplicates!)
   Storage:    +50MB (25MB wasted)
   Compute:    +500 sec (250 sec wasted)
   Search:     Polluted with duplicates
```

### After Deduplication:
```
📊 Weekly Fetch Results:
   Discovered: 100 items
   Duplicates: 50 (⏭️ skipped)
   Ingested:   50 items (all new!)
   Storage:    +25MB (50% saved ✅)
   Compute:    +250 sec (50% saved ✅)
   Search:     Clean, no duplicates ✅
```

---

## 🚀 Next Steps

1. **Phase 1: Database Deduplication** (1-2 days)
   - [ ] Update database schema
   - [ ] Implement hashing functions
   - [ ] Add deduplication checks to fetch flow
   - [ ] Test with arXiv

2. **Phase 2: Semantic Deduplication** (1 day)
   - [ ] Integrate vector DB similarity search
   - [ ] Add verification logic
   - [ ] Test with cross-source duplicates

3. **Phase 3: Adaptive Scheduling** (1 day)
   - [ ] Implement adaptive scheduler
   - [ ] Add per-source frequency config
   - [ ] Test with multiple sources

4. **Phase 4: Monitoring** (0.5 days)
   - [ ] Add deduplication stats endpoints
   - [ ] Create UI dashboard
   - [ ] Set up alerts

**Total Estimated Time:** 3-4 days

---

**Status:** 📋 Design Complete - Ready for Implementation

