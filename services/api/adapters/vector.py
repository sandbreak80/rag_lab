"""
Vector search adapter with ACL pre-filtering
"""
from typing import Any
from dataclasses import dataclass
import requests
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Single search result with provenance"""
    doc_id: str
    chunk_id: str
    content: str
    score: float
    metadata: dict[str, Any]
    origin_tool: str = "rag"  # Immutable
    published_at: datetime | None = None
    is_primary: bool = False


async def search_vector_mock(
    query: str,
    acl_predicate: Any,
    top_k: int = 20
) -> tuple[list[SearchResult], dict[str, Any]]:
    """
    Mock vector search with ACL pre-filtering.
    
    Returns:
        (results, stats) where stats includes candidate counts
    """
    logger.info(f"Mock vector search: query_len={len(query)}, top_k={top_k}, acl_tag={acl_predicate.tag}")
    
    # Simulate ACL filtering
    candidates_before_acl = min(top_k * 5, 100)  # Mock: retrieve 5x, then filter
    candidates_after_acl = top_k  # Mock: ACL filters some out
    
    results = []
    for i in range(top_k):
        results.append(SearchResult(
            doc_id=f"doc_{i+1}",
            chunk_id=f"chunk_{i+1}",
            content=f"Mock internal document content {i+1} related to: {query[:50]}...",
            score=0.9 - (i * 0.05),
            metadata={
                "access_control": ["public"],  # Mock: all public
                "version": "1.0",
                "source_uri": f"https://internal.example.com/docs/doc_{i+1}"
            },
            origin_tool="rag",
            published_at=datetime.now(timezone.utc),
            is_primary=i < 3  # First 3 are primary
        ))
    
    stats = {
        "candidates_before_acl": candidates_before_acl,
        "candidates_after_acl": candidates_after_acl,
        "acl_filtered_count": candidates_before_acl - candidates_after_acl
    }
    
    return results, stats


async def search_vector_real(
    query: str,
    acl_predicate: Any,
    top_k: int = 20,
    vector_db_url: str = "http://vector-db:8001"
) -> tuple[list[SearchResult], dict[str, Any]]:
    """
    Real vector search with ACL pre-filtering at index level.
    
    CRITICAL: ACL filter is applied BEFORE retrieval (not post-filter).
    """
    try:
        # Build query with ACL pre-filter
        payload = {
            "query": query,
            "top_k": top_k * 2,  # Over-fetch to account for ACL filtering
            "filter": acl_predicate.to_filter()
        }
        
        response = requests.post(
            f"{vector_db_url}/search",
            json=payload,
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
        
        results = []
        for hit in data.get("results", [])[:top_k]:
            results.append(SearchResult(
                doc_id=hit["doc_id"],
                chunk_id=hit["chunk_id"],
                content=hit["content"],
                score=hit["score"],
                metadata=hit.get("metadata", {}),
                origin_tool="rag",
                published_at=datetime.fromisoformat(hit["published_at"]) if hit.get("published_at") else None,
                is_primary=hit.get("is_primary", False)
            ))
        
        stats = {
            "candidates_before_acl": data.get("total_candidates", len(results) * 2),
            "candidates_after_acl": len(results),
            "acl_filtered_count": data.get("acl_filtered_count", 0)
        }
        
        return results, stats
        
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        # Fallback to empty results
        return [], {"candidates_before_acl": 0, "candidates_after_acl": 0, "acl_filtered_count": 0, "error": str(e)}


async def search(query: str, acl_predicate: Any, top_k: int, use_mock: bool = True) -> tuple[list[SearchResult], dict[str, Any]]:
    """Main entry point for vector search"""
    if use_mock:
        return await search_vector_mock(query, acl_predicate, top_k)
    else:
        return await search_vector_real(query, acl_predicate, top_k)

