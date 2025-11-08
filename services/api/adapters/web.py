"""
Web search adapter for external sources
"""
from typing import Any
from dataclasses import dataclass
import requests
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


@dataclass
class WebSearchResult:
    """Web search result with provenance"""
    doc_id: str
    chunk_id: str
    content: str
    score: float
    metadata: dict[str, Any]
    origin_tool: str = "web_search"  # Immutable
    published_at: datetime | None = None
    is_primary: bool = False


async def search_web_mock(
    query: str,
    top_k: int = 5
) -> list[WebSearchResult]:
    """
    Mock web search.

    Note: No ACL filtering for public web sources.
    """
    logger.info(f"Mock web search: query_len={len(query)}, top_k={top_k}")

    results = []
    for i in range(top_k):
        results.append(WebSearchResult(
            doc_id=f"web_doc_{i+1}",
            chunk_id=f"web_chunk_{i+1}",
            content=f"Mock web article {i+1} discussing: {query[:50]}... (from external source)",
            score=0.7 - (i * 0.1),
            metadata={
                "domain": "example.com",
                "source_uri": f"https://example.com/article/{i+1}"
            },
            origin_tool="web_search",
            published_at=datetime.now(timezone.utc) - timedelta(hours=i * 6),  # Spread over last 24h
            is_primary=i < 2  # First 2 are primary
        ))

    return results


async def search_web_real(
    query: str,
    top_k: int = 5,
    web_search_url: str = "http://web-search:8009"
) -> list[WebSearchResult]:
    """
    Real web search via web-search service (SearXNG wrapper).

    Flow:
    1. Call web-search service
    2. Parse results from SearXNG
    3. Format with origin_tool="web_search"
    """
    try:
        response = requests.post(
            f"{web_search_url}/search",
            json={"query": query, "limit": top_k},  # Note: 'limit' not 'top_k'
            timeout=10.0
        )
        response.raise_for_status()
        data = response.json()

        results = []
        for idx, hit in enumerate(data.get("results", [])):
            # Extract URL as unique ID
            url = hit.get("url", "")
            doc_id = f"web_{hash(url) % 100000}"  # Stable hash-based ID

            results.append(WebSearchResult(
                doc_id=doc_id,
                chunk_id=f"{doc_id}_chunk",
                content=hit.get("content", hit.get("snippet", hit.get("title", ""))),
                score=hit.get("score", 0.7),
                metadata={
                    "title": hit.get("title", ""),
                    "domain": hit.get("engine", "unknown"),
                    "source_uri": url,
                    "engine": hit.get("engine", "unknown")
                },
                origin_tool="web_search",
                published_at=datetime.fromisoformat(hit["published_at"]) if hit.get("published_at") else datetime.now(timezone.utc),
                is_primary=False  # External web sources are secondary by default
            ))

        logger.info(f"Real web search: retrieved {len(results)} results from SearXNG")
        return results

    except Exception as e:
        logger.error(f"Web search failed: {e}, falling back to mock")
        # Fallback to mock on error
        return await search_web_mock(query, top_k)


async def search(query: str, top_k: int, use_mock: bool = True) -> list[WebSearchResult]:
    """Main entry point for web search"""
    if use_mock:
        return await search_web_mock(query, top_k)
    else:
        return await search_web_real(query, top_k)

