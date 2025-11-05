"""
arXiv.org scraper for AI/ML research papers
Fetches papers from cs.AI, cs.LG, cs.CL, cs.CV categories
"""
import arxiv
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import requests
from .base import BaseScraper
import logging

logger = logging.getLogger(__name__)

class ArxivScraper(BaseScraper):
    """Scraper for arXiv.org AI/ML papers"""

    # arXiv categories to monitor
    DEFAULT_CATEGORIES = [
        'cs.AI',  # Artificial Intelligence
        'cs.LG',  # Machine Learning
        'cs.CL',  # Computation and Language (NLP)
        'cs.CV',  # Computer Vision
        'cs.NE',  # Neural and Evolutionary Computing
    ]

    def __init__(self, source_name: str, source_id: int, config: Dict = None):
        super().__init__(source_name, source_id, config)
        self.categories = config.get('categories', self.DEFAULT_CATEGORIES) if config else self.DEFAULT_CATEGORIES
        self.max_results = config.get('max_results', 20) if config else 20

    def discover(self, since: Optional[datetime] = None, max_items: int = 20) -> List[Dict]:
        """
        Discover new papers from arXiv

        Query arXiv API for papers in AI categories published since given date
        """
        if since is None:
            since = datetime.now() - timedelta(days=1)  # Last 24 hours by default

        # Make timezone-aware if it isn't (arXiv returns timezone-aware datetimes)
        if since.tzinfo is None:
            from datetime import timezone
            since = since.replace(tzinfo=timezone.utc)

        self.logger.info(f"Discovering arXiv papers since {since.strftime('%Y-%m-%d')}")

        # Build search query for all categories
        category_query = ' OR '.join([f'cat:{cat}' for cat in self.categories])

        discovered_items = []

        try:
            # Query arXiv API
            search = arxiv.Search(
                query=category_query,
                max_results=max_items,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )

            for result in search.results():
                # Filter by date
                if result.published < since:
                    continue

                # Extract comprehensive metadata (Best Practices!)
                item = {
                    # Core Identification
                    'external_id': result.entry_id.split('/')[-1],  # arXiv ID (e.g., "2311.12345")
                    'source_type': 'arxiv',
                    'url': result.entry_id,
                    'pdf_url': result.pdf_url,

                    # Content Metadata
                    'title': self.clean_text(result.title),
                    'authors': self.format_authors([author.name for author in result.authors]),
                    'author_list': [author.name for author in result.authors],  # Full list
                    'abstract': self.clean_text(result.summary),  # Full abstract
                    'keywords': result.categories,  # Categories as keywords

                    # Publication Info
                    'published_date': result.published,
                    'updated_date': result.updated,
                    'version': 'v1',  # Could parse from entry_id if available

                    # Categories & Classification
                    'categories': ', '.join(result.categories),
                    'primary_category': result.primary_category,
                    'subject_categories': result.categories,

                    # Additional Metadata
                    'doi': result.doi,
                    'journal_ref': result.journal_ref,
                    'comment': result.comment,
                    'language': 'en',  # arXiv is primarily English

                    # Enriched Metadata (for storage)
                    'metadata': {
                        'primary_category': result.primary_category,
                        'all_categories': result.categories,
                        'comment': result.comment,
                        'journal_ref': result.journal_ref,
                        'doi': result.doi,
                        'source_api': 'arxiv',
                        'content_type': 'research_paper',
                        'has_pdf': True,
                        'language': 'en'
                    }
                }

                discovered_items.append(item)
                self.logger.debug(f"Discovered: {item['title'][:50]}...")

            self.logger.info(f"Discovered {len(discovered_items)} papers from arXiv")
            return discovered_items

        except Exception as e:
            self.logger.error(f"Error discovering arXiv papers: {e}")
            return []

    def fetch_content(self, item: Dict) -> Optional[str]:
        """
        Fetch full paper content

        For arXiv, we use abstract + metadata by default.
        If USE_DOCLING_FOR_PDFS=true, we also fetch and process the full PDF.
        """
        import os

        try:
            self.logger.info(f"Fetching content for: {item['title'][:50]}...")

            # Check if we should process full PDFs
            use_docling = os.getenv('USE_DOCLING_FOR_PDFS', 'false').lower() == 'true'

            full_text = None
            if use_docling:
                pdf_url = item.get('pdf_url')
                if pdf_url:
                    self.logger.info(f"🔄 Processing full PDF with Docling...")
                    full_text = self._fetch_pdf_with_docling(pdf_url)
                    if full_text:
                        self.logger.info(f"✅ PDF processed: {len(full_text)} characters")
                    else:
                        self.logger.warning(f"⚠️ PDF processing failed, using abstract only")
            else:
                self.logger.debug("Using abstract only (USE_DOCLING_FOR_PDFS=false)")

            # Format as markdown (with or without full text)
            content = self._format_as_markdown(item, full_text=full_text)

            return content

        except Exception as e:
            self.logger.error(f"Error fetching content for {item['title']}: {e}")
            return None

    def _fetch_pdf_with_docling(self, pdf_url: str) -> Optional[str]:
        """
        Download PDF and process with Docling service
        Returns extracted markdown text
        """
        import requests
        import tempfile
        import os

        try:
            # Download PDF
            self.logger.info(f"Downloading PDF: {pdf_url}")
            response = requests.get(pdf_url, timeout=30)
            response.raise_for_status()

            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                tmp.write(response.content)
                tmp_path = tmp.name

            try:
                # Send to Docling service
                docling_url = os.getenv('DOCLING_SERVICE_URL', 'http://docling-service:8004')

                with open(tmp_path, 'rb') as f:
                    files = {'file': ('paper.pdf', f, 'application/pdf')}
                    docling_response = requests.post(
                        f"{docling_url}/convert",
                        files=files,
                        timeout=120
                    )

                if docling_response.status_code == 200:
                    result = docling_response.json()
                    markdown_text = result.get('markdown', '')
                    self.logger.info(f"Docling processed PDF: {len(markdown_text)} chars")
                    return markdown_text
                else:
                    self.logger.warning(f"Docling returned {docling_response.status_code}")
                    return None

            finally:
                # Clean up temp file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except Exception as e:
            self.logger.error(f"Error processing PDF with Docling: {e}")
            return None

    def _format_as_markdown(self, item: Dict, full_text: Optional[str] = None) -> str:
        """
        Format paper metadata as rich markdown document
        Includes comprehensive metadata for RAG system
        """
        # Extract all metadata fields
        title = item.get('title', 'Untitled')
        authors = item.get('authors', 'Unknown')
        author_list = item.get('author_list', [])
        abstract = item.get('abstract', '')
        categories = item.get('categories', '')
        primary_category = item.get('primary_category', 'N/A')
        published = item.get('published_date')
        updated = item.get('updated_date')
        url = item.get('url', '')
        pdf_url = item.get('pdf_url', '')
        doi = item.get('doi', '')
        journal_ref = item.get('journal_ref', '')
        comment = item.get('comment', '')
        external_id = item.get('external_id', 'unknown')

        # Format dates
        published_str = published.strftime('%Y-%m-%d') if published else 'Unknown'
        updated_str = updated.strftime('%Y-%m-%d') if updated else None
        discovered_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Build comprehensive markdown document
        markdown = f"""# {title}

## Paper Metadata

**📄 Paper ID:** {external_id}
**👤 Authors:** {authors}
**📅 Published:** {published_str}"""

        if updated_str and updated_str != published_str:
            markdown += f"""
**🔄 Updated:** {updated_str}"""

        markdown += f"""
**🏷️ Primary Category:** {primary_category}
**🔖 All Categories:** {categories}
**🌐 arXiv URL:** {url}
**📥 PDF:** {pdf_url}"""

        if doi:
            markdown += f"""
**🔗 DOI:** {doi}"""

        if journal_ref:
            markdown += f"""
**📚 Journal Reference:** {journal_ref}"""

        if comment:
            markdown += f"""
**💬 Comment:** {comment}"""

        markdown += f"""

## Abstract

{abstract}
"""

        # If full PDF text was processed with Docling, include it
        if full_text:
            markdown += f"""

## Full Paper Content

{full_text}
"""

        # Provenance information
        markdown += f"""

---

## Research Agent Metadata

**🤖 Discovered By:** Research Agent (arXiv Scraper)
**📅 Discovery Date:** {discovered_str}
**🔍 Source Type:** Research Paper (arXiv)
**🌍 Language:** English
**📊 Content Type:** Academic Research Paper

**All Authors:** {', '.join(author_list) if author_list else authors}

**Keywords:** {', '.join(item.get('keywords', [])) if isinstance(item.get('keywords'), list) else categories}

---

*This content was automatically discovered and ingested by the Research Agent. The abstract and metadata provide a comprehensive overview of the research. For the complete paper with figures, equations, and detailed methodology, please visit the arXiv URL above.*
"""

        return markdown

    def should_fetch_item(self, item: Dict) -> bool:
        """Filter items based on relevance"""
        # You can add custom logic here, e.g.:
        # - Check if title contains certain keywords
        # - Filter by primary category
        # - Check citation count (if available)

        title_lower = item['title'].lower()

        # Example: Skip papers with certain terms
        skip_terms = ['survey', 'review article']  # Could be configurable
        if any(term in title_lower for term in skip_terms):
            return False

        return True

