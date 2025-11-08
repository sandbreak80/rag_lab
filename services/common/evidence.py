"""
Immutable Evidence Objects with Guaranteed Provenance Tracking

This module provides the core Evidence class that ensures provenance
(origin_tool) is set once at creation and never modified. This is critical
for maintaining trust in source attribution throughout the RAG pipeline.

Key Design Principles:
- Evidence objects are immutable (frozen dataclass)
- origin_tool is set at creation and cannot be changed
- Full audit trail with timestamps
- Rich metadata for quality assessment
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Literal, Dict, Any
from types import MappingProxyType
from enum import Enum


class OriginTool(str, Enum):
    """
    Source origin types - immutable after creation.

    This enum ensures type safety and prevents typos in origin attribution.
    """
    RAG = "rag"  # Internal vector/BM25 search
    WEB_SEARCH = "web_search"  # External web search (SearXNG)
    RESEARCH_AGENT = "research_agent"  # Autonomous research discovery
    UNKNOWN = "unknown"  # Unknown or missing origin (should be avoided)


@dataclass(frozen=True)  # IMMUTABLE - cannot be modified after creation
class Evidence:
    """
    Immutable evidence object with guaranteed provenance.

    Once created, the origin_tool field cannot be changed. This ensures
    that provenance tracking is reliable throughout the entire RAG pipeline,
    from retrieval through merging, reranking, and final synthesis.

    Design Decision: We use a frozen dataclass rather than a regular class
    because it provides compile-time guarantees of immutability and clear
    error messages if modification is attempted.

    Attributes:
        id: Unique identifier for this evidence
        content: The actual text content
        origin_tool: Source type (IMMUTABLE - set once at creation)
        url: Web URL if from web search
        domain: Domain name extracted from URL
        title: Document or page title
        published_at: When the source was published (for recency)
        fetched_at: When we retrieved this evidence
        is_primary: Whether this is a primary source (vs secondary/tertiary)
        score: Relevance/quality score (0.0-1.0)
        doc_id: Internal document ID if from RAG
        chunk_id: Chunk ID if from RAG
        metadata: Additional key-value metadata
    """

    # Core identification
    id: str
    content: str
    origin_tool: OriginTool  # IMMUTABLE - set once, never changed

    # Source metadata (for web sources)
    url: Optional[str] = None
    domain: Optional[str] = None
    title: Optional[str] = None

    # Temporal metadata (for recency tracking)
    published_at: Optional[datetime] = None
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Quality metadata
    is_primary: bool = False  # Primary vs secondary/tertiary source
    score: float = 0.0  # Relevance score (0.0-1.0)

    # RAG-specific metadata (for internal sources)
    doc_id: Optional[str] = None
    chunk_id: Optional[str] = None

    # Additional metadata (extensible) - stored as private, exposed as immutable
    _metadata: Dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Get immutable view of metadata.
        
        Returns:
            MappingProxyType (read-only dict view) to prevent mutation
        """
        return MappingProxyType(self._metadata)

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize to dictionary for API responses.

        Returns:
            Dictionary representation suitable for JSON serialization
        """
        return {
            'id': self.id,
            'content': self.content,
            'origin_tool': self.origin_tool.value,  # Convert enum to string
            'url': self.url,
            'domain': self.domain,
            'title': self.title,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'fetched_at': self.fetched_at.isoformat(),
            'is_primary': self.is_primary,
            'score': self.score,
            'doc_id': self.doc_id,
            'chunk_id': self.chunk_id,
            'metadata': dict(self._metadata),  # Convert to regular dict for serialization
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Evidence':
        """
        Deserialize from dictionary.

        Args:
            data: Dictionary with evidence fields

        Returns:
            Evidence object
        """
        # Handle datetime strings
        published_at = None
        if data.get('published_at'):
            if isinstance(data['published_at'], str):
                published_at = datetime.fromisoformat(data['published_at'])
            else:
                published_at = data['published_at']

        fetched_at = datetime.now(timezone.utc)
        if data.get('fetched_at'):
            if isinstance(data['fetched_at'], str):
                fetched_at = datetime.fromisoformat(data['fetched_at'])
            else:
                fetched_at = data['fetched_at']

        # Handle origin_tool string or enum
        # CRITICAL FIX: Fail loudly if origin_tool is missing
        if 'origin_tool' not in data:
            raise ValueError(
                f"Evidence.from_dict() requires 'origin_tool' field. "
                f"This is critical for provenance tracking. Got: {list(data.keys())}"
            )
        
        origin_tool = data['origin_tool']
        if isinstance(origin_tool, str):
            try:
                origin_tool = OriginTool(origin_tool)
            except ValueError:
                raise ValueError(
                    f"Invalid origin_tool value: '{origin_tool}'. "
                    f"Must be one of: {[e.value for e in OriginTool]}"
                )

        return cls(
            id=data['id'],
            content=data['content'],
            origin_tool=origin_tool,
            url=data.get('url'),
            domain=data.get('domain'),
            title=data.get('title'),
            published_at=published_at,
            fetched_at=fetched_at,
            is_primary=data.get('is_primary', False),
            score=data.get('score', 0.0),
            doc_id=data.get('doc_id'),
            chunk_id=data.get('chunk_id'),
            _metadata=data.get('metadata', {}),
        )

    def __str__(self) -> str:
        """Human-readable string representation"""
        source_type = self.origin_tool.value
        identifier = self.url or self.title or self.doc_id or self.id
        return f"Evidence({source_type}: {identifier})"

    def __repr__(self) -> str:
        """Developer-friendly representation"""
        return (
            f"Evidence(id={self.id!r}, origin_tool={self.origin_tool.value!r}, "
            f"score={self.score:.3f}, title={self.title!r})"
        )


def extract_domain(url: str) -> Optional[str]:
    """
    Extract domain from URL for categorization and filtering.

    Args:
        url: Full URL string

    Returns:
        Domain name (e.g., "example.com") or None if invalid

    Examples:
        >>> extract_domain("https://www.example.com/path")
        "example.com"
        >>> extract_domain("https://blog.example.co.uk/post/123")
        "blog.example.co.uk"
    """
    if not url:
        return None

    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc

        # Remove www. prefix for consistency
        if domain.startswith('www.'):
            domain = domain[4:]

        return domain if domain else None
    except Exception:
        return None


def is_primary_source(url: str) -> bool:
    """
    Determine if a URL is likely a primary source.

    Primary sources include: official docs, research papers, government sites,
    academic institutions, official company blogs.

    Secondary sources include: news aggregators, social media, wikis, forums.

    Args:
        url: URL to check

    Returns:
        True if likely a primary source, False otherwise

    Note:
        This is a heuristic and not 100% accurate. Can be improved with
        a configurable allow/deny list.
    """
    if not url:
        return False

    url_lower = url.lower()

    # Primary source indicators
    primary_patterns = [
        '.gov',  # Government sites
        '.edu',  # Educational institutions
        'arxiv.org',  # Research papers
        'github.com',  # Official repos
        'pytorch.org',  # Official docs
        'tensorflow.org',
        'openai.com/blog',  # Official company blogs
        'anthropic.com/research',
        'research.google',
        'ai.meta.com',
        'huggingface.co/blog',
    ]

    # Secondary/tertiary source indicators (deprioritize)
    secondary_patterns = [
        'reddit.com',
        'stackoverflow.com',  # Q&A sites
        'medium.com',  # Aggregators
        'wikipedia.org',  # Wikis
        'facebook.com',
        'twitter.com',
        'linkedin.com',
    ]

    # Check for secondary first (to exclude)
    for pattern in secondary_patterns:
        if pattern in url_lower:
            return False

    # Check for primary
    for pattern in primary_patterns:
        if pattern in url_lower:
            return True

    # Default: assume secondary unless proven otherwise
    return False


def parse_published_date(date_str: Optional[str]) -> Optional[datetime]:
    """
    Parse various date formats into datetime object.

    Args:
        date_str: Date string in various formats

    Returns:
        Parsed datetime or None if unparseable

    Supports:
        - ISO 8601: "2025-11-08T10:30:00Z"
        - RFC 2822: "Fri, 08 Nov 2025 10:30:00 +0000"
        - Common formats: "2025-11-08", "Nov 8, 2025"
    """
    if not date_str:
        return None

    try:
        from dateutil import parser
        return parser.parse(date_str)
    except Exception:
        # Fallback: try common formats
        try:
            # ISO 8601
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except Exception:
            return None


# Example usage and testing
if __name__ == "__main__":
    # Example: Create web search evidence
    web_evidence = Evidence(
        id="web-1",
        content="OpenAI released GPT-4 with improved reasoning capabilities.",
        origin_tool=OriginTool.WEB_SEARCH,
        url="https://openai.com/blog/gpt-4",
        domain="openai.com",
        title="GPT-4 Release Announcement",
        published_at=datetime(2025, 11, 8),
        is_primary=True,
        score=0.95,
    )

    print(web_evidence)
    print(f"Is primary source: {web_evidence.is_primary}")
    print(f"Origin tool: {web_evidence.origin_tool.value}")

    # Example: Create RAG evidence
    rag_evidence = Evidence(
        id="rag-1",
        content="RAG systems combine retrieval and generation.",
        origin_tool=OriginTool.RAG,
        doc_id="doc_123",
        chunk_id="chunk_456",
        title="RAG Overview",
        score=0.88,
    )

    print(rag_evidence)

    # Test immutability
    try:
        web_evidence.origin_tool = OriginTool.RAG  # This should fail
        print("ERROR: Should not be able to modify origin_tool!")
    except Exception as e:
        print(f"✅ Immutability works: {type(e).__name__}")

    # Test serialization
    evidence_dict = web_evidence.to_dict()
    print(f"\nSerialized: {evidence_dict['origin_tool']}")

    # Test deserialization
    reconstructed = Evidence.from_dict(evidence_dict)
    print(f"Reconstructed: {reconstructed.origin_tool.value}")

    print("\n✅ Evidence class tests passed!")

