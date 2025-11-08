"""
Recency gate for RAG pipeline - simplified for API service
"""
from datetime import datetime, timezone
from typing import Any
import logging

logger = logging.getLogger(__name__)


def is_temporal_query(query: str) -> bool:
    """Detect if query requires fresh sources"""
    temporal_keywords = [
        "today", "yesterday", "this week", "this month", "this year",
        "recently", "latest", "current", "now", "breaking",
        "last week", "past week", "last month", "update", "news"
    ]
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in temporal_keywords)


def compute_freshness_hours(published_at: datetime | None) -> float | None:
    """Calculate hours since publication"""
    if not published_at:
        return None
    now = datetime.now(timezone.utc)
    # Ensure published_at is timezone-aware
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)
    return (now - published_at).total_seconds() / 3600


def build_freshness_histogram(results: list) -> dict[str, int]:
    """Build histogram of source freshness"""
    histogram = {"<24h": 0, "24-48h": 0, "48h-1w": 0, "1w-1m": 0, ">1m": 0, "unknown": 0}

    for result in results:
        freshness = compute_freshness_hours(result.published_at)
        if freshness is None:
            histogram["unknown"] += 1
        elif freshness < 24:
            histogram["<24h"] += 1
        elif freshness < 48:
            histogram["24-48h"] += 1
        elif freshness < 7 * 24:
            histogram["48h-1w"] += 1
        elif freshness < 30 * 24:
            histogram["1w-1m"] += 1
        else:
            histogram[">1m"] += 1

    return histogram


def count_primary_sources_within_window(results: list, window_hours: int) -> int:
    """Count primary sources within freshness window"""
    count = 0
    for result in results:
        if result.is_primary:
            freshness = compute_freshness_hours(result.published_at)
            if freshness is not None and freshness <= window_hours:
                count += 1
    return count


def evaluate_recency_gate(
    evidence_list: list,
    query: str,
    policy_requires_recency: bool,
    policy_min_primary_sources: int,
    window_hours: int = 48
) -> dict[str, Any]:
    """
    Evaluate recency gate for a query.

    Returns dict with:
      - passed: bool
      - notes: str
      - freshness_histogram: dict
      - primary_sources_within_window: int
      - query_is_temporal: bool
    """
    query_is_temporal = is_temporal_query(query)
    freshness_histogram = build_freshness_histogram(evidence_list)
    primary_within_window = count_primary_sources_within_window(evidence_list, window_hours)

    passed = True
    notes = "Recency requirements met"

    if policy_requires_recency or query_is_temporal:
        if primary_within_window < policy_min_primary_sources:
            passed = False
            notes = (
                f"RECENCY_FAIL: Required {policy_min_primary_sources} primary sources "
                f"≤{window_hours}h, found {primary_within_window}. "
                f"Query appears temporal (requires fresh sources)."
            )

    return {
        "window_hours": window_hours,
        "passed": passed,
        "notes": notes,
        "freshness_histogram": freshness_histogram,
        "primary_sources_within_window": primary_within_window,
        "query_is_temporal": query_is_temporal
    }

