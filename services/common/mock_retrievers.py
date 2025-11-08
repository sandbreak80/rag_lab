"""
Mock Retrievers with Provenance (for testing until real services wired)

These mock retrievers demonstrate the correct pattern:
1. Set origin_tool at Evidence creation
2. Add published_at, is_primary, domain metadata
3. Return Evidence list with scores

Real retrievers (vector-db, web-search, research-agent services) should follow
this same pattern.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid

from services.common.evidence import Evidence, OriginTool
from services.common.artifact_base import OrchestrationContext

logger = logging.getLogger(__name__)


def mock_vector_search(
    query: str,
    k: int,
    ctx: OrchestrationContext
) -> List[Evidence]:
    """
    Mock vector search retriever.

    DEMONSTRATES: How to set origin_tool at Evidence creation.

    Real implementation would:
    1. Query ChromaDB/Qdrant with embedding
    2. Retrieve top-k results
    3. Create Evidence with origin_tool=OriginTool.RAG
    4. Add metadata (score, published_at, is_primary, domain)

    Args:
        query: Search query
        k: Number of results
        ctx: Orchestration context

    Returns:
        List of Evidence with origin_tool=RAG
    """
    logger.info(f"Mock vector search: query='{query}', k={k}")

    # Mock results
    mock_results = [
        {
            'id': f'internal_doc_{i}',
            'content': f'Internal documentation about {query} (result {i+1}). This is a mock result from the vector database.',
            'title': f'Internal Doc: {query} - Part {i+1}',
            'score': 0.9 - (i * 0.05),  # Decreasing scores
            'published_at': datetime.now(timezone.utc) - timedelta(days=i*10),
            'is_primary': i == 0,  # First result is primary
            'url': f'https://internal.example.com/docs/{uuid.uuid4()}',
            'domain': 'internal.example.com'
        }
        for i in range(min(k, 5))  # Return up to 5 mock results
    ]

    # Create Evidence with origin_tool=RAG
    evidence_list = []
    for result in mock_results:
        evidence = Evidence(
            id=result['id'],
            content=result['content'],
            origin_tool=OriginTool.RAG,  # SET HERE - IMMUTABLE
            url=result['url'],
            title=result['title'],
            published_at=result['published_at'],
            is_primary=result['is_primary'],
            _metadata={
                'score': result['score'],
                'domain': result['domain'],
                'source': 'chromadb'
            }
        )
        evidence_list.append(evidence)

    logger.info(f"Vector search returned {len(evidence_list)} results")

    # Update budget tracking
    ctx.budget_use['internal_queries'] = ctx.budget_use.get('internal_queries', 0) + 1

    return evidence_list


def mock_web_search(
    query: str,
    k: int,
    ctx: OrchestrationContext
) -> List[Evidence]:
    """
    Mock web search retriever.

    DEMONSTRATES: How to set origin_tool at Evidence creation.

    Real implementation would:
    1. Query SearXNG with search terms
    2. Parse results
    3. Create Evidence with origin_tool=OriginTool.WEB_SEARCH
    4. Add metadata (score, published_at, is_primary, domain)

    Args:
        query: Search query
        k: Number of results
        ctx: Orchestration context

    Returns:
        List of Evidence with origin_tool=WEB_SEARCH
    """
    logger.info(f"Mock web search: query='{query}', k={k}")

    # Mock results from different domains
    mock_domains = [
        'example.com',
        'wikipedia.org',
        'github.com',
        'stackoverflow.com',
        'medium.com'
    ]

    mock_results = [
        {
            'id': f'web_{uuid.uuid4()}',
            'content': f'Web article about {query} from {mock_domains[i % len(mock_domains)]}. This is a mock web search result.',
            'title': f'{query} - {mock_domains[i % len(mock_domains)].title()} Article',
            'score': 0.85 - (i * 0.08),
            'published_at': datetime.now(timezone.utc) - timedelta(hours=i*6),
            'is_primary': mock_domains[i % len(mock_domains)] in ['wikipedia.org', 'github.com'],
            'url': f'https://{mock_domains[i % len(mock_domains)]}/article/{uuid.uuid4()}',
            'domain': mock_domains[i % len(mock_domains)]
        }
        for i in range(min(k, 5))
    ]

    # Create Evidence with origin_tool=WEB_SEARCH
    evidence_list = []
    for result in mock_results:
        evidence = Evidence(
            id=result['id'],
            content=result['content'],
            origin_tool=OriginTool.WEB_SEARCH,  # SET HERE - IMMUTABLE
            url=result['url'],
            title=result['title'],
            published_at=result['published_at'],
            is_primary=result['is_primary'],
            _metadata={
                'score': result['score'],
                'domain': result['domain'],
                'source': 'searxng'
            }
        )
        evidence_list.append(evidence)

    logger.info(f"Web search returned {len(evidence_list)} results")

    # Update budget tracking
    ctx.budget_use['web_queries'] = ctx.budget_use.get('web_queries', 0) + 1

    return evidence_list


def mock_research_agent_retrieve(
    query: str,
    ctx: OrchestrationContext
) -> List[Evidence]:
    """
    Mock research agent retriever.

    DEMONSTRATES: How to set origin_tool at Evidence creation.

    Real implementation would:
    1. Decompose query into sub-questions
    2. Autonomously search and synthesize
    3. Create Evidence with origin_tool=OriginTool.RESEARCH_AGENT
    4. Add metadata (confidence, published_at, is_primary)

    Args:
        query: Research query
        ctx: Orchestration context

    Returns:
        List of Evidence with origin_tool=RESEARCH_AGENT
    """
    logger.info(f"Mock research agent: query='{query}'")

    # Research agent returns fewer but higher-quality results
    mock_results = [
        {
            'id': f'research_{uuid.uuid4()}',
            'content': f'Research synthesis: {query}. This is a synthesized result from the autonomous research agent, combining multiple sources.',
            'title': f'Research Brief: {query}',
            'confidence': 0.92,
            'published_at': datetime.now(timezone.utc),
            'is_primary': True,
            'url': f'https://research.internal.example.com/brief/{uuid.uuid4()}',
            'domain': 'research.internal.example.com'
        }
    ]

    # Create Evidence with origin_tool=RESEARCH_AGENT
    evidence_list = []
    for result in mock_results:
        evidence = Evidence(
            id=result['id'],
            content=result['content'],
            origin_tool=OriginTool.RESEARCH_AGENT,  # SET HERE - IMMUTABLE
            url=result['url'],
            title=result['title'],
            published_at=result['published_at'],
            is_primary=result['is_primary'],
            _metadata={
                'confidence': result['confidence'],
                'domain': result['domain'],
                'source': 'research_agent',
                'synthesis': True
            }
        )
        evidence_list.append(evidence)

    logger.info(f"Research agent returned {len(evidence_list)} results")

    return evidence_list

