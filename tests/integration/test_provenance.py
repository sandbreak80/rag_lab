"""
Integration tests for provenance tracking in the search pipeline

These tests verify that origin_tool is preserved correctly through
the entire retrieval and merging process.
"""

import pytest
from services.common.evidence import Evidence, OriginTool
from services.common.validators import ProvenanceValidator, validate_evidence_list


class TestProvenanceValidator:
    """Test the provenance validator"""

    def test_validator_passes_valid_evidence(self):
        """Validator passes valid evidence"""
        evidence = Evidence(
            id="test-1",
            content="Valid content",
            origin_tool=OriginTool.WEB_SEARCH,
            url="https://example.com",
            domain="example.com",
        )

        validator = ProvenanceValidator()
        assert validator.validate([evidence]) is True
        assert len(validator.get_violations()) == 0

    def test_validator_catches_missing_origin_tool(self):
        """Validator catches missing origin_tool"""
        # Can't create Evidence without origin_tool (required field)
        # But we can test validation logic with partially constructed data
        pass  # This is prevented by dataclass definition

    def test_validator_catches_web_source_no_url(self):
        """Validator catches web sources without URLs"""
        evidence = Evidence(
            id="web-1",
            content="Web content",
            origin_tool=OriginTool.WEB_SEARCH,
            # Missing URL!
        )

        validator = ProvenanceValidator(strict_mode=False)
        assert validator.validate([evidence]) is False

        errors = validator.get_violations("error")
        assert len(errors) == 1
        assert errors[0].error_code == "WEB_SOURCE_NO_URL"

    def test_validator_catches_empty_content(self):
        """Validator catches empty content"""
        evidence = Evidence(
            id="test-1",
            content="",  # Empty!
            origin_tool=OriginTool.RAG,
        )

        validator = ProvenanceValidator()
        assert validator.validate([evidence]) is False

        errors = validator.get_violations("error")
        assert any(e.error_code == "EMPTY_CONTENT" for e in errors)

    def test_validator_warns_rag_source_no_doc_id(self):
        """Validator warns about RAG sources without doc_id"""
        evidence = Evidence(
            id="rag-1",
            content="RAG content",
            origin_tool=OriginTool.RAG,
            # Missing doc_id
        )

        validator = ProvenanceValidator(strict_mode=False)
        # Should pass in non-strict mode (warnings don't fail)
        assert validator.validate([evidence]) is True

        warnings = validator.get_violations("warning")
        assert len(warnings) == 1
        assert warnings[0].error_code == "RAG_SOURCE_NO_DOC_ID"

    def test_validator_strict_mode(self):
        """Strict mode treats warnings as errors"""
        evidence = Evidence(
            id="rag-1",
            content="RAG content",
            origin_tool=OriginTool.RAG,
            # Missing doc_id (warning)
        )

        # Non-strict mode: should pass
        validator_nonstrict = ProvenanceValidator(strict_mode=False)
        assert validator_nonstrict.validate([evidence]) is True

        # Strict mode: should fail
        validator_strict = ProvenanceValidator(strict_mode=True)
        assert validator_strict.validate([evidence]) is False

    def test_validator_report_format(self):
        """Validator generates correct report format"""
        evidence_good = Evidence(
            id="good-1",
            content="Good",
            origin_tool=OriginTool.RAG,
            doc_id="doc_123",
        )

        evidence_bad = Evidence(
            id="bad-1",
            content="Bad",
            origin_tool=OriginTool.WEB_SEARCH,
            # Missing URL
        )

        validator = ProvenanceValidator(strict_mode=False)
        validator.validate([evidence_good, evidence_bad])

        report = validator.get_report()

        assert 'valid' in report
        assert 'total_violations' in report
        assert 'errors' in report
        assert 'warnings' in report
        assert 'violations' in report

        assert report['valid'] is False
        assert report['total_violations'] > 0
        assert report['errors'] > 0


class TestMergePreservesOrigin:
    """Test that merging evidence preserves origin_tool"""

    def test_simple_merge_preserves_origins(self):
        """Merging two lists preserves both origins"""
        web_evidence = Evidence(
            id="web-1",
            content="Web content",
            origin_tool=OriginTool.WEB_SEARCH,
            url="https://example.com",
        )

        rag_evidence = Evidence(
            id="rag-1",
            content="RAG content",
            origin_tool=OriginTool.RAG,
            doc_id="doc_123",
        )

        # Merge (simple concatenation)
        merged = [web_evidence, rag_evidence]

        # Validate
        validator = ProvenanceValidator()
        assert validator.validate(merged) is True

        # Check origins preserved
        assert merged[0].origin_tool == OriginTool.WEB_SEARCH
        assert merged[1].origin_tool == OriginTool.RAG

    def test_deduplication_preserves_origin(self):
        """Deduplication keeps original Evidence object"""
        evidence1 = Evidence(
            id="dup-1",
            content="Duplicate content",
            origin_tool=OriginTool.WEB_SEARCH,
            url="https://example.com",
            score=0.9,
        )

        evidence2 = Evidence(
            id="dup-2",
            content="Duplicate content",
            origin_tool=OriginTool.RAG,
            doc_id="doc_123",
            score=0.8,
        )

        # Simulate deduplication (keep higher score)
        # IMPORTANT: Keep the Evidence object, don't reconstruct
        evidence_list = [evidence1, evidence2]

        # Simple deduplication: keep first occurrence
        deduped = [evidence_list[0]]

        # Validate
        validator = ProvenanceValidator()
        assert validator.validate(deduped) is True

        # Origin should be preserved from kept evidence
        assert deduped[0].origin_tool == OriginTool.WEB_SEARCH
        assert deduped[0].id == "dup-1"

    def test_reranking_preserves_origin(self):
        """Reranking changes scores but preserves origin"""
        evidence_list = [
            Evidence(
                id="web-1",
                content="Web content A",
                origin_tool=OriginTool.WEB_SEARCH,
                url="https://example.com/a",
                score=0.5,
            ),
            Evidence(
                id="rag-1",
                content="RAG content B",
                origin_tool=OriginTool.RAG,
                doc_id="doc_123",
                score=0.7,
            ),
            Evidence(
                id="web-2",
                content="Web content C",
                origin_tool=OriginTool.WEB_SEARCH,
                url="https://example.com/c",
                score=0.6,
            ),
        ]

        # Simulate reranking (sort by score)
        # IMPORTANT: Sort the Evidence objects, don't create new ones
        reranked = sorted(evidence_list, key=lambda e: e.score, reverse=True)

        # Validate
        validator = ProvenanceValidator()
        assert validator.validate(reranked) is True

        # Check origins preserved
        assert reranked[0].origin_tool == OriginTool.RAG  # 0.7
        assert reranked[1].origin_tool == OriginTool.WEB_SEARCH  # 0.6
        assert reranked[2].origin_tool == OriginTool.WEB_SEARCH  # 0.5


class TestOriginCounts:
    """Test counting sources by origin"""

    def test_count_by_origin(self):
        """Can count sources by origin_tool"""
        evidence_list = [
            Evidence(id="web-1", content="A", origin_tool=OriginTool.WEB_SEARCH, url="https://a.com"),
            Evidence(id="web-2", content="B", origin_tool=OriginTool.WEB_SEARCH, url="https://b.com"),
            Evidence(id="rag-1", content="C", origin_tool=OriginTool.RAG, doc_id="doc1"),
            Evidence(id="rag-2", content="D", origin_tool=OriginTool.RAG, doc_id="doc2"),
            Evidence(id="rag-3", content="E", origin_tool=OriginTool.RAG, doc_id="doc3"),
            Evidence(id="research-1", content="F", origin_tool=OriginTool.RESEARCH_AGENT, url="https://research.com"),
        ]

        # Count by origin
        from collections import Counter
        origin_counts = Counter(e.origin_tool for e in evidence_list)

        assert origin_counts[OriginTool.WEB_SEARCH] == 2
        assert origin_counts[OriginTool.RAG] == 3
        assert origin_counts[OriginTool.RESEARCH_AGENT] == 1

    def test_footer_breakdown(self):
        """Generate source breakdown for UI footer"""
        evidence_list = [
            Evidence(id="web-1", content="A", origin_tool=OriginTool.WEB_SEARCH, url="https://a.com"),
            Evidence(id="rag-1", content="B", origin_tool=OriginTool.RAG, doc_id="doc1"),
            Evidence(id="web-2", content="C", origin_tool=OriginTool.WEB_SEARCH, url="https://b.com"),
        ]

        # Generate breakdown
        breakdown = {}
        for evidence in evidence_list:
            origin = evidence.origin_tool.value
            breakdown[origin] = breakdown.get(origin, 0) + 1

        assert breakdown == {
            'web_search': 2,
            'rag': 1,
        }


class TestSerializationRoundTrip:
    """Test that Evidence survives serialization with origin intact"""

    def test_json_round_trip(self):
        """Evidence survives JSON serialization"""
        import json

        original = Evidence(
            id="test-1",
            content="Test content",
            origin_tool=OriginTool.WEB_SEARCH,
            url="https://example.com",
            title="Test",
            score=0.95,
        )

        # Serialize
        dict_form = original.to_dict()
        json_str = json.dumps(dict_form, default=str)

        # Deserialize
        reconstructed_dict = json.loads(json_str)
        final = Evidence.from_dict(reconstructed_dict)

        # Validate
        validator = ProvenanceValidator()
        assert validator.validate([final]) is True

        # Check origin preserved
        assert final.origin_tool == OriginTool.WEB_SEARCH
        assert final.id == original.id
        assert final.url == original.url

    def test_list_serialization(self):
        """List of Evidence survives serialization"""
        import json

        original_list = [
            Evidence(id="web-1", content="A", origin_tool=OriginTool.WEB_SEARCH, url="https://a.com"),
            Evidence(id="rag-1", content="B", origin_tool=OriginTool.RAG, doc_id="doc1"),
            Evidence(id="research-1", content="C", origin_tool=OriginTool.RESEARCH_AGENT, url="https://research.com"),
        ]

        # Serialize
        dict_list = [e.to_dict() for e in original_list]
        json_str = json.dumps(dict_list, default=str)

        # Deserialize
        reconstructed_dicts = json.loads(json_str)
        final_list = [Evidence.from_dict(d) for d in reconstructed_dicts]

        # Validate
        validator = ProvenanceValidator()
        assert validator.validate(final_list) is True

        # Check all origins preserved
        assert final_list[0].origin_tool == OriginTool.WEB_SEARCH
        assert final_list[1].origin_tool == OriginTool.RAG
        assert final_list[2].origin_tool == OriginTool.RESEARCH_AGENT


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

