"""
Schema B Population Helper

Builds RetrievalLog (Schema B) from retrieval results and audit trails.
Integrates dedup and domain filter audit trails into a complete Schema B artifact.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import asdict

from services.common.artifact_base import OrchestrationContext
from services.api.app import RetrievalLog, RetrievalLogEntry
from services.common.evidence import Evidence
from services.common.deduplicator import DedupAuditEntry
from services.common.domain_filter import DomainFilterAuditEntry

logger = logging.getLogger(__name__)


def build_retrieval_log(
    internal_results: List[Evidence],
    web_results: List[Evidence],
    dedup_audit: List[DedupAuditEntry],
    filter_audit: List[DomainFilterAuditEntry],
    timings: Dict[str, float],
    ctx: OrchestrationContext
) -> RetrievalLog:
    """
    Build Schema B (RetrievalLog) from retrieval results and audit trails.

    This function integrates:
    - Internal (RAG) retrieval results
    - Web search results
    - Deduplication audit trail
    - Domain filter audit trail
    - Per-stage timing breakdown

    Args:
        internal_results: Evidence from vector/BM25 search
        web_results: Evidence from web search
        dedup_audit: Deduplication audit trail
        filter_audit: Domain filtering audit trail
        timings: Dict of stage timings in ms
        ctx: Orchestration context (for trace_id/request_id)

    Returns:
        RetrievalLog artifact (Schema B) with full audit trail
    """

    # Count dedup and filter actions
    dedup_dropped = sum(1 for a in dedup_audit if a.action.value == "dropped")
    filter_dropped = sum(1 for a in filter_audit if a.action.value == "dropped")

    # Extract filtered domains
    filtered_domains = sorted(list(set(
        a.domain for a in filter_audit if a.action.value == "dropped"
    )))

    # Build internal query entry
    internal_entries = []
    if internal_results or timings.get('vector_search') or timings.get('bm25_search'):
        internal_entry = RetrievalLogEntry(
            source_type="internal",
            query=ctx.query,
            results_count=len(internal_results),
            dedup_removed=sum(
                1 for a in dedup_audit
                if a.action.value == "dropped"
                and any(ir.id == a.doc_id for ir in internal_results)
            ),
            domain_filtered=sum(
                1 for a in filter_audit
                if a.action.value == "dropped"
                and any(ir.id == a.doc_id for ir in internal_results)
            ),
            timing_ms=timings.get('vector_search', 0) + timings.get('bm25_search', 0),
            rank_list=[
                {
                    'doc_id': ev.id,
                    'score': ev.metadata.get('score', 0.0),
                    'origin': ev.origin_tool.value,
                    'title': ev.title or ev.content[:50] + '...'
                }
                for ev in internal_results[:5]  # Top 5
            ]
        )
        internal_entries.append(internal_entry)

    # Build web query entry
    web_entries = []
    if web_results or timings.get('web_search'):
        web_entry = RetrievalLogEntry(
            source_type="web",
            query=ctx.query,
            results_count=len(web_results),
            dedup_removed=sum(
                1 for a in dedup_audit
                if a.action.value == "dropped"
                and any(wr.id == a.doc_id for wr in web_results)
            ),
            domain_filtered=sum(
                1 for a in filter_audit
                if a.action.value == "dropped"
                and any(wr.id == a.doc_id for wr in web_results)
            ),
            timing_ms=timings.get('web_search', 0),
            rank_list=[
                {
                    'doc_id': ev.id,
                    'score': ev.metadata.get('score', 0.0),
                    'origin': ev.origin_tool.value,
                    'title': ev.title or ev.content[:50] + '...',
                    'domain': ev.metadata.get('domain', 'unknown')
                }
                for ev in web_results[:5]  # Top 5
            ]
        )
        web_entries.append(web_entry)

    # Build complete RetrievalLog
    retrieval_log = RetrievalLog(
        trace_id=ctx.trace_id,
        request_id=ctx.request_id,
        internal_queries=internal_entries,
        web_queries=web_entries,
        total_retrieved=len(internal_results) + len(web_results),
        total_deduped=dedup_dropped,
        domains_filtered=filtered_domains,
        timing_breakdown_ms=timings
    )

    logger.info(
        f"Schema B built: {retrieval_log.total_retrieved} retrieved, "
        f"{retrieval_log.total_deduped} deduped, "
        f"{len(retrieval_log.domains_filtered)} domains filtered"
    )

    return retrieval_log


def add_detailed_audit_to_retrieval_log(
    retrieval_log: RetrievalLog,
    dedup_audit: List[DedupAuditEntry],
    filter_audit: List[DomainFilterAuditEntry]
) -> Dict[str, Any]:
    """
    Add detailed audit trails to RetrievalLog for debug mode.

    This is useful for debugging but can be large, so only include
    when debug=True in the request.

    Args:
        retrieval_log: Base RetrievalLog
        dedup_audit: Deduplication audit trail
        filter_audit: Domain filtering audit trail

    Returns:
        Enhanced retrieval_log dict with detailed_audit section
    """
    log_dict = retrieval_log.to_dict()

    log_dict['detailed_audit'] = {
        'dedup_actions': [a.to_dict() for a in dedup_audit],
        'filter_actions': [a.to_dict() for a in filter_audit]
    }

    return log_dict

