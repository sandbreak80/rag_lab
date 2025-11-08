"""
Tests for Deduplication and Domain Filtering

Ensures:
1. Deduplication preserves highest-scored duplicate
2. Deduplication audit trail is complete
3. Domain filtering applies rules correctly
4. Audit trails are machine-readable for Schema B
5. CRITICAL: origin_tool is NEVER modified (immutability test)
"""

import pytest
from datetime import datetime, timezone

from services.common.evidence import Evidence, OriginTool
from services.common.deduplicator import deduplicate_evidence, DedupAction
from services.common.domain_filter import DomainFilter, DomainFilterAction, create_default_filter


class TestDeduplication:
    """Test deduplication with audit trail"""

    def test_deduplicate_preserves_highest_score(self):
        """Dedup keeps highest-scored duplicate"""
        evidence = [
            Evidence(
                id="doc1",
                content="This is duplicate content.",
                origin_tool=OriginTool.RAG,
                _metadata={'score': 0.7}
            ),
            Evidence(
                id="doc2",
                content="This is duplicate content.",  # Same content
                origin_tool=OriginTool.WEB_SEARCH,
                _metadata={'score': 0.95}  # Higher score
            ),
            Evidence(
                id="doc3",
                content="This is unique content.",
                origin_tool=OriginTool.RAG,
                _metadata={'score': 0.8}
            )
        ]

        deduplicated, audit = deduplicate_evidence(evidence)

        # Should keep doc2 (higher score) and doc3 (unique)
        assert len(deduplicated) == 2
        assert deduplicated[0].id == "doc2"
        assert deduplicated[1].id == "doc3"

        # Check audit trail
        assert len(audit) == 3

        # doc1 should be dropped
        dropped = [a for a in audit if a.doc_id == "doc1" and a.action == DedupAction.DROPPED]
        assert len(dropped) == 1
        assert dropped[0].duplicate_of == "doc2"
        assert "duplicate_content_hash" in dropped[0].reason

        # doc2 should be kept
        kept = [a for a in audit if a.doc_id == "doc2" and a.action == DedupAction.KEPT]
        assert len(kept) == 1

        # doc3 should be kept
        kept = [a for a in audit if a.doc_id == "doc3" and a.action == DedupAction.KEPT]
        assert len(kept) == 1
        assert kept[0].reason == "unique_content"

    def test_deduplicate_never_modifies_origin_tool(self):
        """CRITICAL: Dedup NEVER modifies origin_tool (immutability)"""
        evidence = [
            Evidence(
                id="doc1",
                content="Duplicate",
                origin_tool=OriginTool.RAG,
                _metadata={'score': 0.7}
            ),
            Evidence(
                id="doc2",
                content="Duplicate",
                origin_tool=OriginTool.WEB_SEARCH,
                _metadata={'score': 0.9}
            )
        ]

        # Store original origin_tools
        original_origins = {e.id: e.origin_tool for e in evidence}

        deduplicated, audit = deduplicate_evidence(evidence)

        # Check that kept evidence has ORIGINAL origin_tool
        for ev in deduplicated:
            assert ev.origin_tool == original_origins[ev.id]

        # Check that dropped evidence still has ORIGINAL origin_tool
        for ev in evidence:
            assert ev.origin_tool == original_origins[ev.id]

    def test_deduplicate_with_no_duplicates(self):
        """Dedup with all unique content keeps everything"""
        evidence = [
            Evidence(id="doc1", content="Content A", origin_tool=OriginTool.RAG),
            Evidence(id="doc2", content="Content B", origin_tool=OriginTool.WEB_SEARCH),
            Evidence(id="doc3", content="Content C", origin_tool=OriginTool.RESEARCH_AGENT)
        ]

        deduplicated, audit = deduplicate_evidence(evidence)

        assert len(deduplicated) == 3
        assert all(a.action == DedupAction.KEPT for a in audit)

    def test_deduplicate_audit_trail_serializable(self):
        """Audit trail can be serialized to dict (for Schema B)"""
        evidence = [
            Evidence(
                id="doc1",
                content="Test",
                origin_tool=OriginTool.RAG,
                _metadata={'score': 0.8}
            )
        ]

        deduplicated, audit = deduplicate_evidence(evidence)

        # Serialize to dict
        audit_dicts = [a.to_dict() for a in audit]

        assert len(audit_dicts) == 1
        assert audit_dicts[0]['action'] == 'kept'
        assert audit_dicts[0]['doc_id'] == 'doc1'
        assert audit_dicts[0]['reason'] == 'unique_content'


class TestDomainFiltering:
    """Test domain filtering with audit trail"""

    def test_denylist_blocks_domains(self):
        """Denylist blocks specified domains"""
        filter = DomainFilter(denylist=["asana.com", "jira.com"])

        evidence = [
            Evidence(
                id="doc1",
                content="Good source",
                origin_tool=OriginTool.WEB_SEARCH,
                url="https://example.com/page",
                _metadata={'domain': 'example.com'}
            ),
            Evidence(
                id="doc2",
                content="Blocked source",
                origin_tool=OriginTool.WEB_SEARCH,
                url="https://asana.com/task/123",
                _metadata={'domain': 'asana.com'}
            ),
            Evidence(
                id="doc3",
                content="Another blocked source",
                origin_tool=OriginTool.WEB_SEARCH,
                url="https://jira.com/issue/456",
                _metadata={'domain': 'jira.com'}
            )
        ]

        filtered, audit = filter.filter_evidence(evidence)

        # Should only keep doc1
        assert len(filtered) == 1
        assert filtered[0].id == "doc1"

        # Check audit trail
        allowed = [a for a in audit if a.action == DomainFilterAction.ALLOWED]
        dropped = [a for a in audit if a.action == DomainFilterAction.DROPPED]

        assert len(allowed) == 1
        assert allowed[0].doc_id == "doc1"

        assert len(dropped) == 2
        assert any("denylist: asana.com" in a.reason for a in dropped)
        assert any("denylist: jira.com" in a.reason for a in dropped)

    def test_allowlist_only_allows_specified_domains(self):
        """Allowlist only allows specified domains (blocks all others)"""
        filter = DomainFilter(allowlist=["example.com", "trusted.com"])

        evidence = [
            Evidence(
                id="doc1",
                content="Allowed",
                origin_tool=OriginTool.WEB_SEARCH,
                url="https://example.com/page",
                _metadata={'domain': 'example.com'}
            ),
            Evidence(
                id="doc2",
                content="Not on allowlist",
                origin_tool=OriginTool.WEB_SEARCH,
                url="https://random.com/page",
                _metadata={'domain': 'random.com'}
            )
        ]

        filtered, audit = filter.filter_evidence(evidence)

        assert len(filtered) == 1
        assert filtered[0].id == "doc1"

        dropped = [a for a in audit if a.action == DomainFilterAction.DROPPED]
        assert len(dropped) == 1
        assert "not_on_allowlist" in dropped[0].reason

    def test_wildcard_subdomain_matching(self):
        """Wildcard patterns match subdomains"""
        filter = DomainFilter(denylist=["*.asana.com"])

        evidence = [
            Evidence(
                id="doc1",
                content="Subdomain blocked",
                origin_tool=OriginTool.WEB_SEARCH,
                url="https://app.asana.com/task/123",
                _metadata={'domain': 'app.asana.com'}
            ),
            Evidence(
                id="doc2",
                content="Deep subdomain blocked",
                origin_tool=OriginTool.WEB_SEARCH,
                url="https://team.app.asana.com/task/456",
                _metadata={'domain': 'team.app.asana.com'}
            ),
            Evidence(
                id="doc3",
                content="Base domain NOT blocked by wildcard",
                origin_tool=OriginTool.WEB_SEARCH,
                url="https://asana.com/",
                _metadata={'domain': 'asana.com'}
            )
        ]

        filtered, audit = filter.filter_evidence(evidence)

        # Wildcard should block app.asana.com and team.app.asana.com
        # but NOT asana.com itself
        assert len(filtered) == 1
        assert filtered[0].id == "doc3"

    def test_domain_filter_never_modifies_origin_tool(self):
        """CRITICAL: Domain filter NEVER modifies origin_tool (immutability)"""
        filter = DomainFilter(denylist=["blocked.com"])

        evidence = [
            Evidence(
                id="doc1",
                content="Allowed",
                origin_tool=OriginTool.WEB_SEARCH,
                url="https://example.com/page",
                _metadata={'domain': 'example.com'}
            ),
            Evidence(
                id="doc2",
                content="Blocked",
                origin_tool=OriginTool.RAG,
                url="https://blocked.com/page",
                _metadata={'domain': 'blocked.com'}
            )
        ]

        # Store original origin_tools
        original_origins = {e.id: e.origin_tool for e in evidence}

        filtered, audit = filter.filter_evidence(evidence)

        # Check that filtered evidence has ORIGINAL origin_tool
        for ev in filtered:
            assert ev.origin_tool == original_origins[ev.id]

        # Check that dropped evidence still has ORIGINAL origin_tool
        for ev in evidence:
            assert ev.origin_tool == original_origins[ev.id]

    def test_domain_filter_audit_trail_serializable(self):
        """Audit trail can be serialized to dict (for Schema B)"""
        filter = DomainFilter(denylist=["blocked.com"])

        evidence = [
            Evidence(
                id="doc1",
                content="Test",
                origin_tool=OriginTool.WEB_SEARCH,
                url="https://blocked.com/page",
                _metadata={'domain': 'blocked.com'}
            )
        ]

        filtered, audit = filter.filter_evidence(evidence)

        # Serialize to dict
        audit_dicts = [a.to_dict() for a in audit]

        assert len(audit_dicts) == 1
        assert audit_dicts[0]['action'] == 'dropped'
        assert audit_dicts[0]['doc_id'] == 'doc1'
        assert audit_dicts[0]['domain'] == 'blocked.com'
        assert 'denylist' in audit_dicts[0]['reason']

    def test_get_filtered_domains(self):
        """Extract unique list of filtered domains"""
        filter = DomainFilter(denylist=["asana.com", "jira.com"])

        evidence = [
            Evidence(id="doc1", content="A", origin_tool=OriginTool.WEB_SEARCH, url="https://asana.com/1", _metadata={'domain': 'asana.com'}),
            Evidence(id="doc2", content="B", origin_tool=OriginTool.WEB_SEARCH, url="https://asana.com/2", _metadata={'domain': 'asana.com'}),
            Evidence(id="doc3", content="C", origin_tool=OriginTool.WEB_SEARCH, url="https://jira.com/3", _metadata={'domain': 'jira.com'}),
        ]

        filtered, audit = filter.filter_evidence(evidence)

        filtered_domains = filter.get_filtered_domains(audit)

        assert set(filtered_domains) == {"asana.com", "jira.com"}


class TestProvenanceImmutability:
    """Test that origin_tool is NEVER modified during pipeline operations"""

    def test_origin_tool_immutable_through_dedup_and_filter(self):
        """CRITICAL: origin_tool survives dedup + filter unchanged"""
        # Create evidence with different origin_tools
        evidence = [
            Evidence(
                id="doc1",
                content="Duplicate",
                origin_tool=OriginTool.RAG,
                url="https://internal.com/1",
                _metadata={'score': 0.7, 'domain': 'internal.com'}
            ),
            Evidence(
                id="doc2",
                content="Duplicate",  # Will be kept (higher score)
                origin_tool=OriginTool.WEB_SEARCH,
                url="https://example.com/2",
                _metadata={'score': 0.9, 'domain': 'example.com'}
            ),
            Evidence(
                id="doc3",
                content="Unique",
                origin_tool=OriginTool.RESEARCH_AGENT,
                url="https://blocked.com/3",
                _metadata={'score': 0.8, 'domain': 'blocked.com'}
            )
        ]

        # Store original origin_tools
        original_origins = {e.id: e.origin_tool for e in evidence}

        # Step 1: Dedup
        deduped, dedup_audit = deduplicate_evidence(evidence)

        for ev in deduped:
            assert ev.origin_tool == original_origins[ev.id], f"Dedup changed origin_tool for {ev.id}"

        # Step 2: Domain filter
        filter = DomainFilter(denylist=["blocked.com"])
        filtered, filter_audit = filter.filter_evidence(deduped)

        for ev in filtered:
            assert ev.origin_tool == original_origins[ev.id], f"Filter changed origin_tool for {ev.id}"

        # Final check: doc2 should be the only one kept
        assert len(filtered) == 1
        assert filtered[0].id == "doc2"
        assert filtered[0].origin_tool == OriginTool.WEB_SEARCH

