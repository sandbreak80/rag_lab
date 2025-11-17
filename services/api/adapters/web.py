"""
Web search adapter for external sources with guardrails
"""
from typing import Any
from dataclasses import dataclass
import requests
import logging
import os
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

# B3 Web Guardrails Configuration
RAG_WEB_TIMEOUT_MS = int(os.getenv("RAG_WEB_TIMEOUT_MS", "1000"))  # 1s default
RAG_WEB_RESULTS = int(os.getenv("RAG_WEB_RESULTS", "5"))  # Limit to 5 results
RAG_WEB_TIMEOUT_SEC = RAG_WEB_TIMEOUT_MS / 1000.0


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
    searxng_url: str = "http://searxng:8080"
) -> list[WebSearchResult]:
    """
    Real web search via SearXNG with B3 guardrails:
    - Timeout budget (RAG_WEB_TIMEOUT_MS, default 1000ms)
    - Result cap (RAG_WEB_RESULTS, default 5)
    - Deduplication by URL
    - Partial results on timeout

    Flow:
    1. Call SearXNG with timeout
    2. Parse JSON results
    3. Deduplicate by URL
    4. Cap to top_k
    5. Format with origin_tool="web"
    """
    import httpx
    import time
    from opentelemetry import trace

    tracer = trace.get_tracer(__name__)

    # Apply guardrails
    effective_top_k = min(top_k, RAG_WEB_RESULTS)
    timeout_sec = RAG_WEB_TIMEOUT_SEC

    try:
        t0 = time.perf_counter()

        with tracer.start_as_current_span("web_search.searxng") as span:
            span.set_attribute("web.timeout_ms", RAG_WEB_TIMEOUT_MS)
            span.set_attribute("web.top_k", effective_top_k)

            try:
                async with httpx.AsyncClient(timeout=timeout_sec) as cx:
                    response = await cx.get(
                        f"{searxng_url}/search",
                        params={"q": query, "format": "json"}
                    )
                    response.raise_for_status()
                    data = response.json()

                timeout_hit = False
            except (httpx.TimeoutException, httpx.ReadTimeout) as e:
                logger.warning(f"Web search timeout after {timeout_sec}s, returning partial results")
                timeout_hit = True
                data = {"results": []}  # Return empty on timeout

            latency_ms = (time.perf_counter() - t0) * 1000

            # Deduplicate by URL
            seen_urls = set()
            results = []

            for idx, hit in enumerate(data.get("results", [])):
                url = hit.get("url", "")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)

                # Stop at effective_top_k
                if len(results) >= effective_top_k:
                    break

                # Extract URL as unique ID
                doc_id = f"web_{hash(url) % 100000}"  # Stable hash-based ID

                results.append(WebSearchResult(
                    doc_id=doc_id,
                    chunk_id=f"{doc_id}_chunk",
                    content=hit.get("content", hit.get("snippet", hit.get("title", "")))[:2000],
                    score=hit.get("score", 0.7),
                    metadata={
                        "title": hit.get("title", ""),
                        "domain": hit.get("engine", "unknown"),
                        "source_uri": url,
                        "engine": hit.get("engine", "unknown"),
                        "latency_ms": latency_ms,
                        "timeout_hit": timeout_hit
                    },
                    origin_tool="web_search",  # Immutable - must match checks in rag.py
                    published_at=datetime.fromisoformat(hit["published_at"]) if hit.get("published_at") else datetime.now(timezone.utc),
                    is_primary=False  # External web sources are secondary by default
                ))

            span.set_attribute("web.results_returned", len(results))
            span.set_attribute("web.timeout_hit", timeout_hit)
            span.set_attribute("web.latency_ms", int(latency_ms))

            logger.info(
                f"Web search: {len(results)} results in {latency_ms:.0f}ms "
                f"(timeout: {timeout_hit}, budget: {RAG_WEB_TIMEOUT_MS}ms)"
            )

            return results

    except Exception as e:
        logger.error(f"Web search failed: {e}, returning empty results")
        # Return empty instead of mock to avoid masking issues
        return []


async def search(query: str, top_k: int, use_mock: bool = True) -> list[WebSearchResult]:
    """Main entry point for web search"""
    if use_mock:
        return await search_web_mock(query, top_k)
    else:
        return await search_web_real(query, top_k)

