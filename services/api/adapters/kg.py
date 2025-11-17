"""
Knowledge Graph search adapter for relationship discovery
"""
from typing import Any
from dataclasses import dataclass
import requests
import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

KNOWLEDGE_GRAPH_URL = os.getenv("KNOWLEDGE_GRAPH_URL", "http://knowledge-graph:8007")


@dataclass
class KGSearchResult:
    """Knowledge Graph search result with provenance"""
    doc_id: str
    chunk_id: str
    content: str
    score: float
    metadata: dict[str, Any]
    origin_tool: str = "knowledge_graph"  # Immutable
    published_at: datetime | None = None
    is_primary: bool = False


async def search_kg_mock(
    query: str,
    top_k: int = 5
) -> list[KGSearchResult]:
    """
    Mock knowledge graph search.

    Returns related documents based on graph relationships.
    """
    logger.info(f"Mock KG search: query_len={len(query)}, top_k={top_k}")

    results = []
    for i in range(top_k):
        results.append(KGSearchResult(
            doc_id=f"kg_doc_{i+1}",
            chunk_id=f"kg_chunk_{i+1}",
            content=f"Mock knowledge graph related document {i+1} connected to: {query[:50]}... (from KG relationships)",
            score=0.75 - (i * 0.05),
            metadata={
                "source_uri": f"kg://related/{i+1}",
                "relationship_type": "related_to",
                "kg_score": 0.75 - (i * 0.05)
            },
            origin_tool="knowledge_graph"
        ))

    return results


async def search_kg_real(
    query: str,
    vector_results: list,
    top_k: int = 5,
    kg_url: str = KNOWLEDGE_GRAPH_URL
) -> list[KGSearchResult]:
    """
    Real knowledge graph search using KG service.

    Finds related documents based on graph relationships from top vector results.
    Fetches actual content from vector DB for related doc IDs.
    """
    logger.info(f"KG search: query_len={len(query)}, top_k={top_k}, kg_url={kg_url}")

    results = []
    related_doc_ids = set()
    vector_db_url = os.getenv("VECTOR_DB_URL", "http://vector-db:8005")

    try:
        # Step 1: Get related document IDs from KG service for top vector results
        for result in vector_results[:5]:
            doc_id = getattr(result, 'doc_id', None) or result.get('doc_id', '') if isinstance(result, dict) else ''
            if doc_id:
                try:
                    response = requests.get(
                        f"{kg_url}/related/{doc_id}",
                        params={'limit': 5, 'max_hops': 2},
                        timeout=5
                    )
                    if response.status_code == 200:
                        related = response.json().get('related', [])
                        related_doc_ids.update(related)
                        logger.info(f"KG found {len(related)} related docs for {doc_id}")
                    elif response.status_code == 503:
                        logger.warning(f"KG service unavailable (503) for {doc_id}")
                    else:
                        logger.warning(f"KG service returned {response.status_code} for {doc_id}")
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Failed to get KG related docs for {doc_id}: {e}")
                    # Continue with other doc_ids even if one fails

        if not related_doc_ids:
            logger.info("KG search: No related documents found")
            return []

        # Step 2: Fetch actual content from vector DB for related doc IDs
        # Use vector DB /get endpoint with where filter on doc_id
        try:
            # Fetch documents by doc_id from vector DB
            get_response = requests.post(
                f"{vector_db_url}/get",
                json={
                    "where": {"doc_id": {"$in": list(related_doc_ids)[:top_k * 2]}}  # Get more to have options
                },
                timeout=10
            )

            if get_response.status_code == 200:
                data = get_response.json()
                documents = data.get('documents', [])
                metadatas = data.get('metadatas', [])
                ids = data.get('ids', [])

                # Create KG results from vector DB content
                for idx, (doc_id, content, metadata) in enumerate(zip(ids[:top_k], documents[:top_k], metadatas[:top_k])):
                    results.append(KGSearchResult(
                        doc_id=metadata.get('doc_id', doc_id),
                        chunk_id=doc_id,  # Use vector DB chunk ID
                        content=content or f"Knowledge graph related document: {doc_id}",
                        score=0.7 - (idx * 0.05),  # Lower score than direct vector matches
                        metadata={
                            **metadata,
                            "source_uri": metadata.get("source_uri", f"kg://related/{doc_id}"),
                            "relationship_type": "related_to",
                            "kg_score": 0.7 - (idx * 0.05)
                        },
                        origin_tool="knowledge_graph",
                        published_at=datetime.fromisoformat(metadata["published_at"].replace("Z", "+00:00")) if metadata.get("published_at") else None
                    ))

                logger.info(f"KG search: Fetched {len(results)} documents from vector DB")
            else:
                logger.warning(f"Vector DB /get returned {get_response.status_code}, creating placeholder results")
                # Fallback: create results with doc IDs only
                for idx, doc_id in enumerate(list(related_doc_ids)[:top_k]):
                    results.append(KGSearchResult(
                        doc_id=doc_id,
                        chunk_id=f"kg_{doc_id}",
                        content=f"Knowledge graph related document: {doc_id} (content unavailable)",
                        score=0.7 - (idx * 0.05),
                        metadata={
                            "source_uri": f"kg://related/{doc_id}",
                            "relationship_type": "related_to",
                            "kg_score": 0.7 - (idx * 0.05)
                        },
                        origin_tool="knowledge_graph"
                    ))
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch content from vector DB: {e}")
            # Return empty list if we can't get content

        logger.info(f"KG search found {len(results)} related documents with content")

    except Exception as e:
        logger.error(f"KG search error: {e}")
        # Return empty list on error

    return results


async def search(
    query: str,
    vector_results: list,
    top_k: int = 5,
    use_mock: bool = False  # Always use real service - no mocks
) -> list[KGSearchResult]:
    """
    Knowledge graph search entry point.
    
    ALWAYS uses real KG service - no mock fallback.

    Args:
        query: Search query
        vector_results: Top vector search results to find relationships for
        top_k: Maximum number of KG results to return
        use_mock: Ignored - always uses real service

    Returns:
        List of KG search results (empty list if graph not built or no results)
    """
    # Always use real KG service - return empty list if no results (expected when graph not built)
    return await search_kg_real(query, vector_results, top_k)

