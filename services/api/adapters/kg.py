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
    """
    logger.info(f"KG search: query_len={len(query)}, top_k={top_k}, kg_url={kg_url}")
    
    results = []
    related_docs = set()
    
    try:
        # Get related documents for top 5 vector results
        for result in vector_results[:5]:
            doc_id = getattr(result, 'doc_id', None) or result.get('doc_id', '') if isinstance(result, dict) else ''
            if doc_id:
                try:
                    response = requests.get(
                        f"{kg_url}/related/{doc_id}",
                        params={'limit': 5},
                        timeout=5
                    )
                    if response.status_code == 200:
                        related = response.json().get('related', [])
                        related_docs.update(related)
                except Exception as e:
                    logger.warning(f"Failed to get KG related docs for {doc_id}: {e}")
        
        # Convert related doc IDs to SearchResult format
        # In a real implementation, we'd fetch the actual content from vector DB
        # For now, create results from the doc IDs
        for idx, doc_id in enumerate(list(related_docs)[:top_k]):
            results.append(KGSearchResult(
                doc_id=doc_id,
                chunk_id=f"kg_{doc_id}",
                content=f"Knowledge graph related document: {doc_id} (connected via graph relationships)",
                score=0.7 - (idx * 0.05),  # Lower score than direct matches
                metadata={
                    "source_uri": f"kg://related/{doc_id}",
                    "relationship_type": "related_to",
                    "kg_score": 0.7 - (idx * 0.05)
                },
                origin_tool="knowledge_graph"
            ))
        
        logger.info(f"KG search found {len(results)} related documents")
        
    except Exception as e:
        logger.error(f"KG search error: {e}")
        # Return empty list on error
    
    return results


async def search(
    query: str,
    vector_results: list,
    top_k: int = 5,
    use_mock: bool = True
) -> list[KGSearchResult]:
    """
    Knowledge graph search entry point.
    
    Args:
        query: Search query
        vector_results: Top vector search results to find relationships for
        top_k: Maximum number of KG results to return
        use_mock: Use mock implementation
    
    Returns:
        List of KG search results
    """
    if use_mock:
        return await search_kg_mock(query, top_k)
    else:
        return await search_kg_real(query, vector_results, top_k)

