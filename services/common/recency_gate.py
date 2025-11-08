"""
Recency Enforcement with Server-Side Freshness Calculation

This module implements the recency gate that:
1. Detects temporal queries (queries requiring fresh sources)
2. Computes freshness_hours SERVER-SIDE (no client clock skew)
3. Validates ≥2 primary sources ≤48h for temporal claims
4. Generates freshness histogram
5. Fails gracefully with partial refusal if recency unmet
"""

import logging
import re
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from services.common.evidence import Evidence
from services.common.artifact_base import OrchestrationContext

logger = logging.getLogger(__name__)


# Temporal keywords that indicate a query requires fresh sources
TEMPORAL_KEYWORDS = [
    # Explicit time references
    "today", "yesterday", "this week", "this month", "this year",
    "recently", "latest", "current", "now", "just", "breaking",
    
    # Temporal constraints
    "≤48h", "within 48 hours", "last 48 hours",
    "last week", "past week", "last month", "past month",
    
    # Trending/live
    "trending", "live", "happening", "ongoing",
    
    # Updates
    "update", "news", "announcement", "release",
]


def is_temporal_query(query: str) -> bool:
    """
    Detect if query requires fresh sources.
    
    Uses keyword matching and pattern detection to identify queries
    that need recent information.
    
    Args:
        query: User query string
    
    Returns:
        True if query appears temporal
    
    Examples:
        is_temporal_query("What happened today in AI?") -> True
        is_temporal_query("Tell me about the latest GPT model") -> True
        is_temporal_query("What is machine learning?") -> False
    """
    query_lower = query.lower()
    
    # Check for temporal keywords
    for keyword in TEMPORAL_KEYWORDS:
        if keyword in query_lower:
            logger.debug(f"Temporal query detected: found keyword '{keyword}'")
            return True
    
    # Pattern: "in [year]" where year is current or recent
    current_year = datetime.now(timezone.utc).year
    year_pattern = r'\b(in|for|during)\s+(\d{4})\b'
    year_matches = re.findall(year_pattern, query_lower)
    for _, year_str in year_matches:
        year = int(year_str)
        if year >= current_year - 1:  # Current or last year
            logger.debug(f"Temporal query detected: recent year reference '{year}'")
            return True
    
    return False


def compute_freshness_hours_server_side(
    evidence: Evidence,
    now: Optional[datetime] = None
) -> Optional[int]:
    """
    Compute freshness_hours SERVER-SIDE to avoid client clock skew.
    
    This is critical: we cannot trust client-side time calculations
    because clients may have incorrect clocks.
    
    Args:
        evidence: Evidence object with published_at
        now: Current time (defaults to UTC now, mockable for testing)
    
    Returns:
        Hours since publication, or None if no published_at
    """
    if not evidence.published_at:
        return None
    
    if now is None:
        now = datetime.now(timezone.utc)
    
    # Ensure both datetimes are timezone-aware
    pub_date = evidence.published_at
    if pub_date.tzinfo is None:
        pub_date = pub_date.replace(tzinfo=timezone.utc)
    
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    
    # Calculate hours difference
    hours_old = (now - pub_date).total_seconds() / 3600
    
    return int(hours_old)


def build_freshness_histogram(
    evidence_list: List[Evidence],
    now: Optional[datetime] = None
) -> Dict[str, int]:
    """
    Build freshness histogram showing distribution of source ages.
    
    Buckets:
    - <24h: Fresh (published within last day)
    - 24-48h: Recent (published 1-2 days ago)
    - 48h-1w: Week-old (published 2-7 days ago)
    - 1w-1m: Month-old (published 1 week - 1 month ago)
    - >1m: Old (published over a month ago)
    - unknown: No published_at date
    
    Args:
        evidence_list: List of Evidence objects
        now: Current time (defaults to UTC now)
    
    Returns:
        Dict with bucket counts
    """
    if now is None:
        now = datetime.now(timezone.utc)
    
    histogram = {
        "<24h": 0,
        "24-48h": 0,
        "48h-1w": 0,
        "1w-1m": 0,
        ">1m": 0,
        "unknown": 0
    }
    
    for evidence in evidence_list:
        freshness_hours = compute_freshness_hours_server_side(evidence, now)
        
        if freshness_hours is None:
            histogram["unknown"] += 1
        elif freshness_hours < 24:
            histogram["<24h"] += 1
        elif freshness_hours < 48:
            histogram["24-48h"] += 1
        elif freshness_hours < 168:  # 1 week
            histogram["48h-1w"] += 1
        elif freshness_hours < 720:  # ~1 month (30 days)
            histogram["1w-1m"] += 1
        else:
            histogram[">1m"] += 1
    
    return histogram


def count_primary_sources_within_window(
    evidence_list: List[Evidence],
    window_hours: int = 48,
    now: Optional[datetime] = None
) -> int:
    """
    Count primary sources within recency window.
    
    Args:
        evidence_list: List of Evidence objects
        window_hours: Recency window in hours (default 48)
        now: Current time (defaults to UTC now)
    
    Returns:
        Count of primary sources within window
    """
    if now is None:
        now = datetime.now(timezone.utc)
    
    count = 0
    for evidence in evidence_list:
        if not evidence.is_primary:
            continue
        
        freshness_hours = compute_freshness_hours_server_side(evidence, now)
        if freshness_hours is not None and freshness_hours <= window_hours:
            count += 1
    
    return count


def evaluate_recency_gate(
    evidence_list: List[Evidence],
    query: str,
    policy_requires_recency: bool,
    policy_min_primary_sources: int = 2,
    window_hours: int = 48,
    now: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Evaluate recency gate with full details.
    
    This is the core recency enforcement logic. It:
    1. Detects if query is temporal
    2. Computes freshness for all sources (server-side)
    3. Builds freshness histogram
    4. Counts primary sources within window
    5. Determines pass/fail based on policy
    
    Args:
        evidence_list: List of Evidence objects
        query: User query
        policy_requires_recency: Policy flag forcing recency check
        policy_min_primary_sources: Minimum primary sources required
        window_hours: Recency window in hours
        now: Current time (for testing)
    
    Returns:
        Dict with:
        - passed: bool
        - notes: str (reason for pass/fail)
        - freshness_histogram: Dict[str, int]
        - primary_sources_within_window: int
        - window_hours: int
        - query_is_temporal: bool
    """
    if now is None:
        now = datetime.now(timezone.utc)
    
    # Step 1: Compute freshness for all evidence (SERVER-SIDE)
    # This mutates evidence metadata but only to ADD freshness_hours
    for evidence in evidence_list:
        freshness_hours = compute_freshness_hours_server_side(evidence, now)
        if freshness_hours is not None:
            # Note: This requires evidence._metadata to be mutable during this phase
            # which is fine because we're ADDING data, not modifying origin_tool
            evidence._metadata['freshness_hours'] = freshness_hours
    
    # Step 2: Build histogram
    histogram = build_freshness_histogram(evidence_list, now)
    
    # Step 3: Count primary sources within window
    primary_within_window = count_primary_sources_within_window(
        evidence_list,
        window_hours=window_hours,
        now=now
    )
    
    # Step 4: Detect if query is temporal
    query_is_temporal = is_temporal_query(query)
    
    # Step 5: Evaluate pass/fail
    requires_recency = policy_requires_recency or query_is_temporal
    passed = True
    notes = []
    
    if requires_recency:
        if primary_within_window < policy_min_primary_sources:
            passed = False
            notes.append(
                f"RECENCY_FAIL: Required {policy_min_primary_sources} primary sources "
                f"≤{window_hours}h, found {primary_within_window}."
            )
            if query_is_temporal:
                notes.append("Query appears temporal (requires fresh sources).")
            notes.append(f"Freshness histogram: {histogram}")
        else:
            notes.append(
                f"Recency requirements met: {primary_within_window} primary sources "
                f"≤{window_hours}h (required: {policy_min_primary_sources})"
            )
    else:
        notes.append("No recency requirements for this query.")
    
    result = {
        'passed': passed,
        'notes': ' '.join(notes),
        'freshness_histogram': histogram,
        'primary_sources_within_window': primary_within_window,
        'window_hours': window_hours,
        'query_is_temporal': query_is_temporal
    }
    
    logger.info(
        f"Recency gate: passed={passed}, temporal={query_is_temporal}, "
        f"primary_within_window={primary_within_window}/{policy_min_primary_sources}"
    )
    
    return result

