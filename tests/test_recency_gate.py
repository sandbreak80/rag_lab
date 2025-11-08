"""
Tests for Recency Gate

Ensures:
1. Server-side freshness_hours calculation
2. Temporal query detection
3. Freshness histogram generation
4. Primary source counting within window
5. Pass/fail logic based on policy
6. Graceful failure with partial refusal
"""

import pytest
from datetime import datetime, timezone, timedelta

from services.common.evidence import Evidence, OriginTool
from services.common.recency_gate import (
    is_temporal_query,
    compute_freshness_hours_server_side,
    build_freshness_histogram,
    count_primary_sources_within_window,
    evaluate_recency_gate
)


class TestTemporalQueryDetection:
    """Test temporal query detection"""

    def test_detects_explicit_temporal_keywords(self):
        """Detect queries with explicit time references"""
        assert is_temporal_query("What happened today in AI?") is True
        assert is_temporal_query("Tell me the latest news") is True
        assert is_temporal_query("Current events in technology") is True
        assert is_temporal_query("What's trending now?") is True
        assert is_temporal_query("Recent updates on GPT") is True

    def test_does_not_detect_non_temporal_queries(self):
        """Do not flag timeless queries"""
        assert is_temporal_query("What is machine learning?") is False
        assert is_temporal_query("Explain neural networks") is False
        assert is_temporal_query("How does attention work?") is False

    def test_detects_year_references(self):
        """Detect queries with current/recent year"""
        current_year = datetime.now(timezone.utc).year
        assert is_temporal_query(f"AI developments in {current_year}") is True
        assert is_temporal_query(f"Events during {current_year - 1}") is True
        # Old year should not trigger
        assert is_temporal_query("Events in 2010") is False


class TestFreshnessCalculation:
    """Test server-side freshness calculation"""

    def test_compute_freshness_hours_server_side(self):
        """Compute freshness_hours from published_at"""
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

        # Evidence published 6 hours ago
        evidence = Evidence(
            id="doc1",
            content="Test",
            origin_tool=OriginTool.WEB_SEARCH,
            published_at=datetime(2024, 1, 15, 6, 0, 0, tzinfo=timezone.utc)
        )

        freshness = compute_freshness_hours_server_side(evidence, now)
        assert freshness == 6

    def test_freshness_with_no_published_at(self):
        """Return None for evidence without published_at"""
        evidence = Evidence(
            id="doc1",
            content="Test",
            origin_tool=OriginTool.RAG,
            published_at=None
        )

        freshness = compute_freshness_hours_server_side(evidence)
        assert freshness is None

    def test_freshness_with_days_old(self):
        """Calculate freshness for multi-day old content"""
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

        # Evidence published 3 days ago
        evidence = Evidence(
            id="doc1",
            content="Test",
            origin_tool=OriginTool.WEB_SEARCH,
            published_at=datetime(2024, 1, 12, 12, 0, 0, tzinfo=timezone.utc)
        )

        freshness = compute_freshness_hours_server_side(evidence, now)
        assert freshness == 72  # 3 days * 24 hours


class TestFreshnessHistogram:
    """Test freshness histogram generation"""

    def test_build_freshness_histogram(self):
        """Build histogram with multiple evidence"""
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

        evidence_list = [
            # <24h
            Evidence(
                id="doc1", content="Fresh", origin_tool=OriginTool.WEB_SEARCH,
                published_at=datetime(2024, 1, 15, 6, 0, 0, tzinfo=timezone.utc)
            ),
            # 24-48h
            Evidence(
                id="doc2", content="Recent", origin_tool=OriginTool.WEB_SEARCH,
                published_at=datetime(2024, 1, 14, 6, 0, 0, tzinfo=timezone.utc)
            ),
            # 48h-1w
            Evidence(
                id="doc3", content="Week old", origin_tool=OriginTool.WEB_SEARCH,
                published_at=datetime(2024, 1, 10, 12, 0, 0, tzinfo=timezone.utc)
            ),
            # >1m
            Evidence(
                id="doc4", content="Old", origin_tool=OriginTool.WEB_SEARCH,
                published_at=datetime(2023, 12, 1, 12, 0, 0, tzinfo=timezone.utc)
            ),
            # unknown
            Evidence(
                id="doc5", content="No date", origin_tool=OriginTool.RAG,
                published_at=None
            )
        ]

        histogram = build_freshness_histogram(evidence_list, now)

        assert histogram["<24h"] == 1
        assert histogram["24-48h"] == 1
        assert histogram["48h-1w"] == 1
        assert histogram[">1m"] == 1
        assert histogram["unknown"] == 1


class TestPrimarySourceCounting:
    """Test primary source counting within window"""

    def test_count_primary_sources_within_window(self):
        """Count only primary sources within 48h window"""
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

        evidence_list = [
            # Primary, within 48h
            Evidence(
                id="doc1", content="Primary fresh", origin_tool=OriginTool.WEB_SEARCH,
                published_at=datetime(2024, 1, 15, 6, 0, 0, tzinfo=timezone.utc),
                is_primary=True
            ),
            # Primary, within 48h
            Evidence(
                id="doc2", content="Primary recent", origin_tool=OriginTool.WEB_SEARCH,
                published_at=datetime(2024, 1, 14, 6, 0, 0, tzinfo=timezone.utc),
                is_primary=True
            ),
            # Primary, outside 48h
            Evidence(
                id="doc3", content="Primary old", origin_tool=OriginTool.WEB_SEARCH,
                published_at=datetime(2024, 1, 10, 12, 0, 0, tzinfo=timezone.utc),
                is_primary=True
            ),
            # Secondary, within 48h (should not count)
            Evidence(
                id="doc4", content="Secondary fresh", origin_tool=OriginTool.WEB_SEARCH,
                published_at=datetime(2024, 1, 15, 6, 0, 0, tzinfo=timezone.utc),
                is_primary=False
            )
        ]

        count = count_primary_sources_within_window(evidence_list, window_hours=48, now=now)
        assert count == 2  # Only doc1 and doc2


class TestRecencyGateEvaluation:
    """Test full recency gate evaluation"""

    def test_recency_gate_passes_with_sufficient_primary_sources(self):
        """Pass when ≥2 primary sources ≤48h"""
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

        evidence_list = [
            Evidence(
                id="doc1", content="Primary 1", origin_tool=OriginTool.WEB_SEARCH,
                published_at=datetime(2024, 1, 15, 6, 0, 0, tzinfo=timezone.utc),
                is_primary=True
            ),
            Evidence(
                id="doc2", content="Primary 2", origin_tool=OriginTool.WEB_SEARCH,
                published_at=datetime(2024, 1, 14, 18, 0, 0, tzinfo=timezone.utc),
                is_primary=True
            )
        ]

        result = evaluate_recency_gate(
            evidence_list,
            query="What happened today?",  # Temporal query
            policy_requires_recency=False,
            policy_min_primary_sources=2,
            now=now
        )

        assert result['passed'] is True
        assert result['query_is_temporal'] is True
        assert result['primary_sources_within_window'] == 2

    def test_recency_gate_fails_with_insufficient_primary_sources(self):
        """Fail when <2 primary sources ≤48h"""
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

        evidence_list = [
            Evidence(
                id="doc1", content="Primary 1", origin_tool=OriginTool.WEB_SEARCH,
                published_at=datetime(2024, 1, 15, 6, 0, 0, tzinfo=timezone.utc),
                is_primary=True
            ),
            # Only 1 primary within 48h
            Evidence(
                id="doc2", content="Primary old", origin_tool=OriginTool.WEB_SEARCH,
                published_at=datetime(2024, 1, 10, 12, 0, 0, tzinfo=timezone.utc),
                is_primary=True
            )
        ]

        result = evaluate_recency_gate(
            evidence_list,
            query="What's the latest news?",
            policy_requires_recency=False,
            policy_min_primary_sources=2,
            now=now
        )

        assert result['passed'] is False
        assert result['query_is_temporal'] is True
        assert result['primary_sources_within_window'] == 1
        assert "RECENCY_FAIL" in result['notes']

    def test_recency_gate_skips_for_non_temporal_query(self):
        """Skip recency check for non-temporal query"""
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

        evidence_list = [
            # Old sources, but query is not temporal
            Evidence(
                id="doc1", content="Old", origin_tool=OriginTool.RAG,
                published_at=datetime(2023, 12, 1, 12, 0, 0, tzinfo=timezone.utc),
                is_primary=True
            )
        ]

        result = evaluate_recency_gate(
            evidence_list,
            query="What is machine learning?",  # Not temporal
            policy_requires_recency=False,
            policy_min_primary_sources=2,
            now=now
        )

        assert result['passed'] is True
        assert result['query_is_temporal'] is False
        assert "No recency requirements" in result['notes']

    def test_recency_gate_enforced_by_policy(self):
        """Enforce recency when policy requires it"""
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

        evidence_list = [
            Evidence(
                id="doc1", content="Old", origin_tool=OriginTool.RAG,
                published_at=datetime(2023, 12, 1, 12, 0, 0, tzinfo=timezone.utc),
                is_primary=True
            )
        ]

        result = evaluate_recency_gate(
            evidence_list,
            query="What is AI?",  # Not temporal
            policy_requires_recency=True,  # But policy enforces it
            policy_min_primary_sources=2,
            now=now
        )

        assert result['passed'] is False
        assert "RECENCY_FAIL" in result['notes']

