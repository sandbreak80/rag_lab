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
    Real web search via SearXNG or similar.
    """
    try:
        response = requests.post(
            f"{web_search_url}/search",
            json={"query": query, "top_k": top_k},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        results = []
        for hit in data.get("results", []):
            results.append(WebSearchResult(
                doc_id=hit.get("id", f"web_{hit['url']}"),
                chunk_id=f"web_chunk_{hit.get('id', 0)}",
                content=hit.get("content", hit.get("snippet", "")),
                score=hit.get("score", 0.5),
                metadata={
                    "domain": hit.get("domain", "unknown"),
                    "source_uri": hit["url"]
                },
                origin_tool="web_search",
                published_at=datetime.fromisoformat(hit["published_at"]) if hit.get("published_at") else None,
                is_primary=False  # External sources are secondary by default
            ))
        
        return results
        
    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return []


async def search(query: str, top_k: int, use_mock: bool = True) -> list[WebSearchResult]:
    """Main entry point for web search"""
    if use_mock:
        return await search_web_mock(query, top_k)
    else:
        return await search_web_real(query, top_k)

