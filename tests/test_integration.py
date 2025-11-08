"""
Integration Tests for Days 1-3 Implementations

Tests the complete flow of:
1. Provenance tracking (immutable Evidence)
2. Thread-safe timing collection
3. URL sanitization
4. End-to-end search with all components

Run with: pytest tests/test_integration.py -v
"""

import pytest
import time
import threading
import sys
import os

# Add services directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services'))

from common.evidence import Evidence, OriginTool, validate_url
from common.timing import TimingCollector
from common.validators import ProvenanceValidator


class TestProvenanceEndToEnd:
    """Test provenance tracking through complete pipeline"""

    def test_provenance_preserved_through_merge(self):
        """Evidence origin_tool preserved when merging RAG and web results"""
        # Simulate RAG results
        rag_results = [
            Evidence(
                id="rag-1",
                content="RAG content 1",
                origin_tool=OriginTool.RAG,
                doc_id="doc_123",
                score=0.9
            ),
            Evidence(
                id="rag-2",
                content="RAG content 2",
                origin_tool=OriginTool.RAG,
                doc_id="doc_456",
                score=0.8
            )
        ]

        # Simulate web search results
        web_results = [
            Evidence(
                id="web-1",
                content="Web content 1",
                origin_tool=OriginTool.WEB_SEARCH,
                url="https://example.com",
                domain="example.com",
                score=0.95
            ),
            Evidence(
                id="web-2",
                content="Web content 2",
                origin_tool=OriginTool.WEB_SEARCH,
                url="https://test.com",
                domain="test.com",
                score=0.85
            )
        ]

        # Merge results (simple concatenation)
        merged = rag_results + web_results

        # Sort by score
        sorted_results = sorted(merged, key=lambda e: e.score, reverse=True)

        # Verify origins preserved
        assert sorted_results[0].origin_tool == OriginTool.WEB_SEARCH  # 0.95
        assert sorted_results[1].origin_tool == OriginTool.RAG        # 0.9
        assert sorted_results[2].origin_tool == OriginTool.WEB_SEARCH # 0.85
        assert sorted_results[3].origin_tool == OriginTool.RAG        # 0.8

        # Verify no mutation occurred
        assert rag_results[0].origin_tool == OriginTool.RAG
        assert web_results[0].origin_tool == OriginTool.WEB_SEARCH

    def test_provenance_validation_catches_issues(self):
        """ProvenanceValidator catches evidence without proper metadata"""
        validator = ProvenanceValidator(strict_mode=False)

        # Good evidence
        good_evidence = Evidence(
            id="good-1",
            content="Test",
            origin_tool=OriginTool.WEB_SEARCH,
            url="https://example.com",
            domain="example.com"
        )

        # Bad evidence (web search without URL)
        bad_evidence = Evidence(
            id="bad-1",
            content="Test",
            origin_tool=OriginTool.WEB_SEARCH
            # Missing URL!
        )

        # Validate
        is_valid = validator.validate([good_evidence, bad_evidence])

        # Should have violations
        assert not is_valid
        violations = validator.get_violations("error")
        assert len(violations) > 0
        assert any("url" in v.message.lower() for v in violations)

    def test_source_breakdown_calculation(self):
        """Source breakdown correctly counts origins"""
        evidence_list = [
            Evidence(id="1", content="A", origin_tool=OriginTool.RAG, score=0.9),
            Evidence(id="2", content="B", origin_tool=OriginTool.RAG, score=0.8),
            Evidence(id="3", content="C", origin_tool=OriginTool.WEB_SEARCH, url="https://a.com", score=0.7),
            Evidence(id="4", content="D", origin_tool=OriginTool.WEB_SEARCH, url="https://b.com", score=0.6),
            Evidence(id="5", content="E", origin_tool=OriginTool.WEB_SEARCH, url="https://c.com", score=0.5),
        ]

        # Calculate breakdown
        source_breakdown = {}
        for evidence in evidence_list:
            origin = evidence.origin_tool.value
            source_breakdown[origin] = source_breakdown.get(origin, 0) + 1

        assert source_breakdown['rag'] == 2
        assert source_breakdown['web_search'] == 3


class TestTimingIntegration:
    """Test timing collector in realistic scenarios"""

    def test_timing_realistic_search_pipeline(self):
        """Time a realistic search pipeline"""
        timer = TimingCollector()

        # Simulate search pipeline
        with timer.measure('query_expansion'):
            time.sleep(0.01)  # 10ms

        with timer.measure('vector_search'):
            time.sleep(0.045)  # 45ms

        with timer.measure('bm25_search'):
            time.sleep(0.023)  # 23ms

        with timer.measure('hybrid_fusion'):
            time.sleep(0.008)  # 8ms

        with timer.measure('web_search'):
            time.sleep(0.1)  # 100ms (slowest)

        # Get results
        timings = timer.get_timings()

        # Verify all stages recorded
        assert 'query_expansion' in timings
        assert 'vector_search' in timings
        assert 'bm25_search' in timings
        assert 'hybrid_fusion' in timings
        assert 'web_search' in timings
        assert 'total' in timings

        # Verify web search is slowest
        assert timings['web_search'] > timings['vector_search']
        assert timings['web_search'] > timings['bm25_search']

        # Verify breakdown percentages
        breakdown = timer.get_breakdown_percent()
        assert breakdown['web_search'] > 50  # Should be majority of time

    def test_timing_under_concurrent_load(self):
        """Timer works correctly under concurrent requests"""
        results = []

        def simulate_request(request_id):
            timer = TimingCollector()

            with timer.measure('operation'):
                time.sleep(0.01)

            timings = timer.get_timings()
            results.append({
                'request_id': request_id,
                'operation_ms': timings['operation'],
                'total_ms': timings['total']
            })

        # Run 10 concurrent requests
        threads = []
        for i in range(10):
            t = threading.Thread(target=simulate_request, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # All requests should complete
        assert len(results) == 10

        # All timings should be reasonable
        for result in results:
            assert 9 <= result['operation_ms'] <= 15
            assert 9 <= result['total_ms'] <= 15


class TestSecurityIntegration:
    """Test security measures in realistic scenarios"""

    def test_url_validation_blocks_attacks(self):
        """URL validation blocks common XSS vectors"""
        attack_vectors = [
            'javascript:alert("XSS")',
            'data:text/html,<script>alert("XSS")</script>',
            'file:///etc/passwd',
            'vbscript:msgbox("XSS")',
            'https://evil.com/<script>alert(1)</script>',
            'https://evil.com/page?param=onerror=alert(1)',
        ]

        for attack_url in attack_vectors:
            assert validate_url(attack_url) is False, f"Failed to block: {attack_url}"

    def test_evidence_from_dict_rejects_attacks(self):
        """from_dict() rejects evidence with malicious URLs"""
        attack_data = {
            'id': 'attack-1',
            'content': 'Malicious content',
            'origin_tool': 'web_search',
            'url': 'javascript:alert("XSS")'
        }

        with pytest.raises(ValueError) as exc_info:
            Evidence.from_dict(attack_data)

        assert 'unsafe' in str(exc_info.value).lower() or 'invalid' in str(exc_info.value).lower()

    def test_safe_urls_accepted(self):
        """Legitimate URLs are accepted"""
        safe_urls = [
            'https://example.com',
            'http://test.com/path',
            'https://blog.example.co.uk/post/123?id=456',
            'https://github.com/user/repo',
            'https://arxiv.org/abs/2301.00001',
        ]

        for safe_url in safe_urls:
            assert validate_url(safe_url) is True, f"Incorrectly blocked safe URL: {safe_url}"


class TestFullPipelineSimulation:
    """Simulate complete end-to-end search pipeline"""

    def test_complete_search_with_provenance_and_timing(self):
        """Full search pipeline with provenance tracking and timing"""
        timer = TimingCollector()

        # Step 1: Query expansion
        with timer.measure('query_expansion'):
            original_query = "What is RAG?"
            expanded_query = f"{original_query} retrieval augmented generation"
            time.sleep(0.01)

        # Step 2: Vector search (RAG)
        with timer.measure('vector_search'):
            rag_results = [
                Evidence(
                    id="rag-1",
                    content="RAG combines retrieval and generation",
                    origin_tool=OriginTool.RAG,
                    doc_id="doc_rag_overview",
                    score=0.88
                )
            ]
            time.sleep(0.045)

        # Step 3: Web search
        with timer.measure('web_search'):
            web_results = [
                Evidence(
                    id="web-1",
                    content="RAG is a technique for improving LLMs",
                    origin_tool=OriginTool.WEB_SEARCH,
                    url="https://example.com/rag",
                    domain="example.com",
                    score=0.92
                )
            ]
            time.sleep(0.1)

        # Step 4: Merge and validate
        with timer.measure('merge_and_validate'):
            all_results = rag_results + web_results
            sorted_results = sorted(all_results, key=lambda e: e.score, reverse=True)

            # Validate provenance
            validator = ProvenanceValidator(strict_mode=False)
            is_valid = validator.validate(sorted_results)
            time.sleep(0.005)

        # Get final metrics
        timings = timer.get_timings()

        # Assertions
        assert is_valid or len(validator.get_violations("error")) == 0
        assert len(sorted_results) == 2
        assert sorted_results[0].origin_tool == OriginTool.WEB_SEARCH  # Higher score
        assert sorted_results[1].origin_tool == OriginTool.RAG

        # Verify timing metrics
        assert 'query_expansion' in timings
        assert 'vector_search' in timings
        assert 'web_search' in timings
        assert 'merge_and_validate' in timings
        assert 'total' in timings

        # Calculate source breakdown
        source_breakdown = {}
        for evidence in sorted_results:
            origin = evidence.origin_tool.value
            source_breakdown[origin] = source_breakdown.get(origin, 0) + 1

        assert source_breakdown == {'web_search': 1, 'rag': 1}

        print(f"\n✅ Full pipeline test passed!")
        print(f"   Timings: {timings}")
        print(f"   Source breakdown: {source_breakdown}")
        print(f"   Provenance valid: {is_valid}")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
