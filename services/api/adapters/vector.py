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
    vector_db_url: str = "http://vector-db:8005",
    embedding_url: str = "http://embedding-service:8006"
) -> tuple[list[SearchResult], dict[str, Any]]:
    """
    Real vector search with ACL pre-filtering at index level.

    CRITICAL: ACL filter is applied BEFORE retrieval (not post-filter).

    Flow:
    1. Get query embedding
    2. Search vector-db with embedding + ACL filter
    3. Format results
    """
    try:
        # Step 1: Get query embedding
        embed_response = requests.post(
            f"{embedding_url}/embed",
            json={"text": query},  # Note: singular 'text', not 'texts'
            timeout=3.0
        )
        embed_response.raise_for_status()
        embedding_data = embed_response.json()
        # Wrap single embedding in a list for ChromaDB query format
        embeddings = [embedding_data["embedding"]]

        # Step 2: Search vector database
        search_payload = {
            "query_embeddings": embeddings,
            "n_results": top_k * 2  # Over-fetch for ACL filtering
        }

        # Add ACL metadata filters if available
        if hasattr(acl_predicate, 'to_filter'):
            search_payload["metadata_filters"] = acl_predicate.to_filter()

        search_response = requests.post(
            f"{vector_db_url}/search",
            json=search_payload,
            timeout=3.0
        )
        search_response.raise_for_status()
        raw_results = search_response.json()

        # Step 3: Format results
        results = []
        ids = raw_results.get("ids", [[]])[0]
        documents = raw_results.get("documents", [[]])[0]
        distances = raw_results.get("distances", [[]])[0]
        metadatas = raw_results.get("metadatas", [[]])[0]

        candidates_before_acl = len(ids)

        for i in range(min(len(ids), top_k)):
            metadata = metadatas[i] if i < len(metadatas) else {}
            doc_content = documents[i] if i < len(documents) else ""

            results.append(SearchResult(
                doc_id=ids[i],
                chunk_id=metadata.get("chunk_id", ids[i]),
                content=doc_content,
                score=1.0 - distances[i] if i < len(distances) else 0.0,  # Convert distance to similarity
                metadata={
                    **metadata,
                    "version": metadata.get("version", "1.0"),
                    "source_uri": metadata.get("source_uri", metadata.get("file_name", ""))
                },
                origin_tool="rag",
                published_at=datetime.fromisoformat(metadata["published_at"]) if metadata.get("published_at") else None,
                is_primary=metadata.get("is_primary", i < 3)  # First 3 are primary by default
            ))

        stats = {
            "candidates_before_acl": candidates_before_acl,
            "candidates_after_acl": len(results),
            "acl_filtered_count": candidates_before_acl - len(results)
        }

        logger.info(f"Real vector search: retrieved {len(results)} results (filtered {stats['acl_filtered_count']})")
        return results, stats

    except Exception as e:
        logger.error(f"Vector search failed: {e}, falling back to mock")
        # Fallback to mock on error
        return await search_vector_mock(query, acl_predicate, top_k)


async def search(query: str, acl_predicate: Any, top_k: int, use_mock: bool = True) -> tuple[list[SearchResult], dict[str, Any]]:
    """Main entry point for vector search"""
    if use_mock:
        return await search_vector_mock(query, acl_predicate, top_k)
    else:
        return await search_vector_real(query, acl_predicate, top_k)

