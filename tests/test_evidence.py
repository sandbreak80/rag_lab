"""
Tests for Evidence class immutability and provenance tracking

These tests ensure that the Evidence class provides strong guarantees
about provenance immutability, which is critical for maintaining trust
in source attribution throughout the RAG pipeline.
"""

import pytest
from datetime import datetime
from services.common.evidence import (
    Evidence,
    OriginTool,
    extract_domain,
    is_primary_source,
    parse_published_date,
)


class TestEvidenceImmutability:
    """Test that Evidence objects are truly immutable"""
    
    def test_evidence_is_frozen(self):
        """Evidence objects should be frozen (immutable)"""
        evidence = Evidence(
            id="test-1",
            content="Test content",
            origin_tool=OriginTool.WEB_SEARCH,
            url="https://example.com"
        )
        
        # Attempting to modify should raise FrozenInstanceError
        with pytest.raises(Exception):  # dataclasses.FrozenInstanceError
            evidence.origin_tool = OriginTool.RAG
    
    def test_origin_tool_cannot_be_changed(self):
        """origin_tool field must remain immutable after creation"""
        evidence = Evidence(
            id="test-2",
            content="Web content",
            origin_tool=OriginTool.WEB_SEARCH,
        )
        
        # Verify it's set correctly
        assert evidence.origin_tool == OriginTool.WEB_SEARCH
        
        # Try to change it (should fail)
        with pytest.raises(Exception):
            evidence.origin_tool = OriginTool.RAG
        
        # Verify it's still the original value
        assert evidence.origin_tool == OriginTool.WEB_SEARCH
    
    def test_all_fields_immutable(self):
        """All Evidence fields should be immutable"""
        evidence = Evidence(
            id="test-3",
            content="Test",
            origin_tool=OriginTool.RAG,
            score=0.8,
        )
        
        # Try to modify various fields
        with pytest.raises(Exception):
            evidence.score = 0.9
        
        with pytest.raises(Exception):
            evidence.content = "Modified"
        
        with pytest.raises(Exception):
            evidence.id = "new-id"


class TestEvidenceOriginPreservation:
    """Test that origin_tool is preserved through serialization"""
    
    def test_web_search_origin_preserved(self):
        """Web search evidence maintains origin through serialization"""
        evidence = Evidence(
            id="web-1",
            content="Web content",
            origin_tool=OriginTool.WEB_SEARCH,
            url="https://example.com",
        )
        
        # Serialize to dict
        data = evidence.to_dict()
        assert data['origin_tool'] == 'web_search'
        
        # Deserialize from dict
        reconstructed = Evidence.from_dict(data)
        assert reconstructed.origin_tool == OriginTool.WEB_SEARCH
    
    def test_rag_origin_preserved(self):
        """RAG evidence maintains origin through serialization"""
        evidence = Evidence(
            id="rag-1",
            content="RAG content",
            origin_tool=OriginTool.RAG,
            doc_id="doc_123",
        )
        
        data = evidence.to_dict()
        assert data['origin_tool'] == 'rag'
        
        reconstructed = Evidence.from_dict(data)
        assert reconstructed.origin_tool == OriginTool.RAG
    
    def test_research_agent_origin_preserved(self):
        """Research agent evidence maintains origin"""
        evidence = Evidence(
            id="research-1",
            content="Research content",
            origin_tool=OriginTool.RESEARCH_AGENT,
        )
        
        data = evidence.to_dict()
        assert data['origin_tool'] == 'research_agent'
        
        reconstructed = Evidence.from_dict(data)
        assert reconstructed.origin_tool == OriginTool.RESEARCH_AGENT


class TestEvidenceCreation:
    """Test creating Evidence objects with different configurations"""
    
    def test_create_web_evidence(self):
        """Can create web search evidence with all metadata"""
        evidence = Evidence(
            id="web-1",
            content="Content from web",
            origin_tool=OriginTool.WEB_SEARCH,
            url="https://example.com/article",
            domain="example.com",
            title="Example Article",
            published_at=datetime(2025, 11, 8),
            is_primary=True,
            score=0.95,
        )
        
        assert evidence.origin_tool == OriginTool.WEB_SEARCH
        assert evidence.url == "https://example.com/article"
        assert evidence.domain == "example.com"
        assert evidence.is_primary is True
        assert evidence.score == 0.95
    
    def test_create_rag_evidence(self):
        """Can create RAG evidence with doc metadata"""
        evidence = Evidence(
            id="rag-1",
            content="Content from internal docs",
            origin_tool=OriginTool.RAG,
            doc_id="doc_123",
            chunk_id="chunk_456",
            title="Internal Document",
            score=0.88,
        )
        
        assert evidence.origin_tool == OriginTool.RAG
        assert evidence.doc_id == "doc_123"
        assert evidence.chunk_id == "chunk_456"
        assert evidence.url is None  # RAG evidence has no URL
    
    def test_create_minimal_evidence(self):
        """Can create evidence with minimal required fields"""
        evidence = Evidence(
            id="min-1",
            content="Minimal content",
            origin_tool=OriginTool.RAG,
        )
        
        assert evidence.id == "min-1"
        assert evidence.content == "Minimal content"
        assert evidence.origin_tool == OriginTool.RAG
        assert evidence.score == 0.0
        assert evidence.is_primary is False


class TestEvidenceSerialization:
    """Test serialization and deserialization"""
    
    def test_to_dict_includes_all_fields(self):
        """to_dict() includes all evidence fields"""
        evidence = Evidence(
            id="test-1",
            content="Test",
            origin_tool=OriginTool.WEB_SEARCH,
            url="https://example.com",
            title="Test Title",
            score=0.9,
        )
        
        data = evidence.to_dict()
        
        assert 'id' in data
        assert 'content' in data
        assert 'origin_tool' in data
        assert 'url' in data
        assert 'title' in data
        assert 'score' in data
        assert 'fetched_at' in data
    
    def test_from_dict_reconstructs_evidence(self):
        """from_dict() correctly reconstructs Evidence"""
        original = Evidence(
            id="test-1",
            content="Test content",
            origin_tool=OriginTool.WEB_SEARCH,
            url="https://example.com",
            score=0.85,
        )
        
        data = original.to_dict()
        reconstructed = Evidence.from_dict(data)
        
        assert reconstructed.id == original.id
        assert reconstructed.content == original.content
        assert reconstructed.origin_tool == original.origin_tool
        assert reconstructed.url == original.url
        assert reconstructed.score == original.score
    
    def test_datetime_serialization(self):
        """Datetime fields serialize to ISO format"""
        evidence = Evidence(
            id="test-1",
            content="Test",
            origin_tool=OriginTool.WEB_SEARCH,
            published_at=datetime(2025, 11, 8, 10, 30, 0),
        )
        
        data = evidence.to_dict()
        
        # Should be ISO format string
        assert isinstance(data['published_at'], str)
        assert '2025-11-08' in data['published_at']
        
        # Should deserialize back to datetime
        reconstructed = Evidence.from_dict(data)
        assert isinstance(reconstructed.published_at, datetime)


class TestDomainExtraction:
    """Test domain extraction utility"""
    
    def test_extract_domain_simple(self):
        """Extract domain from simple URL"""
        assert extract_domain("https://example.com/path") == "example.com"
    
    def test_extract_domain_with_www(self):
        """Remove www. prefix"""
        assert extract_domain("https://www.example.com/path") == "example.com"
    
    def test_extract_domain_subdomain(self):
        """Preserve subdomains (except www)"""
        assert extract_domain("https://blog.example.com/post") == "blog.example.com"
    
    def test_extract_domain_complex_url(self):
        """Extract domain from complex URL"""
        url = "https://blog.example.co.uk/2025/11/article?id=123#section"
        assert extract_domain(url) == "blog.example.co.uk"
    
    def test_extract_domain_invalid_url(self):
        """Handle invalid URLs gracefully"""
        assert extract_domain("not-a-url") is None
        assert extract_domain("") is None
        assert extract_domain(None) is None


class TestPrimarySourceDetection:
    """Test primary source detection heuristic"""
    
    def test_primary_source_gov(self):
        """Government sites are primary sources"""
        assert is_primary_source("https://www.whitehouse.gov/policy") is True
        assert is_primary_source("https://data.gov/dataset") is True
    
    def test_primary_source_edu(self):
        """Educational institutions are primary sources"""
        assert is_primary_source("https://www.stanford.edu/research") is True
        assert is_primary_source("https://mit.edu/paper") is True
    
    def test_primary_source_research(self):
        """Research sites are primary sources"""
        assert is_primary_source("https://arxiv.org/abs/2301.00001") is True
        assert is_primary_source("https://research.google/pubs/pub12345") is True
    
    def test_primary_source_official_docs(self):
        """Official documentation sites are primary"""
        assert is_primary_source("https://pytorch.org/docs/stable") is True
        assert is_primary_source("https://openai.com/blog/gpt-4") is True
    
    def test_secondary_source_social_media(self):
        """Social media sites are not primary"""
        assert is_primary_source("https://twitter.com/user/status") is False
        assert is_primary_source("https://reddit.com/r/machinelearning") is False
    
    def test_secondary_source_aggregators(self):
        """News aggregators are not primary"""
        assert is_primary_source("https://medium.com/@user/article") is False
        assert is_primary_source("https://stackoverflow.com/questions/123") is False
    
    def test_secondary_source_wiki(self):
        """Wikipedia is not a primary source"""
        assert is_primary_source("https://en.wikipedia.org/wiki/AI") is False


class TestStringRepresentations:
    """Test __str__ and __repr__ methods"""
    
    def test_str_representation(self):
        """__str__ provides human-readable output"""
        evidence = Evidence(
            id="test-1",
            content="Test",
            origin_tool=OriginTool.WEB_SEARCH,
            url="https://example.com",
        )
        
        str_repr = str(evidence)
        assert "web_search" in str_repr
        assert "example.com" in str_repr
    
    def test_repr_representation(self):
        """__repr__ provides developer-friendly output"""
        evidence = Evidence(
            id="test-1",
            content="Test",
            origin_tool=OriginTool.RAG,
            title="Test Title",
            score=0.85,
        )
        
        repr_str = repr(evidence)
        assert "Evidence" in repr_str
        assert "test-1" in repr_str
        assert "rag" in repr_str
        assert "0.850" in repr_str


# Integration-style tests
class TestEvidenceInPipeline:
    """Test Evidence behavior in realistic pipeline scenarios"""
    
    def test_merge_preserves_origin(self):
        """Merging evidence lists preserves origin_tool"""
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
        
        # Simulate merging (just combining lists)
        merged = [web_evidence, rag_evidence]
        
        # Verify origins preserved
        assert merged[0].origin_tool == OriginTool.WEB_SEARCH
        assert merged[1].origin_tool == OriginTool.RAG
    
    def test_deduplication_preserves_origin(self):
        """Deduplication should keep original Evidence objects"""
        evidence1 = Evidence(
            id="web-1",
            content="Same content",
            origin_tool=OriginTool.WEB_SEARCH,
            score=0.9,
        )
        
        evidence2 = Evidence(
            id="rag-1",
            content="Same content",
            origin_tool=OriginTool.RAG,
            score=0.8,
        )
        
        # Simulate deduplication (keep higher score)
        evidence_list = [evidence1, evidence2]
        deduped = [max(evidence_list, key=lambda e: e.score)]
        
        # Should keep web_search (higher score)
        assert len(deduped) == 1
        assert deduped[0].origin_tool == OriginTool.WEB_SEARCH
    
    def test_serialization_round_trip(self):
        """Evidence survives serialization round trip"""
        original = Evidence(
            id="test-1",
            content="Test content",
            origin_tool=OriginTool.WEB_SEARCH,
            url="https://example.com",
            title="Test",
            published_at=datetime(2025, 11, 8),
            score=0.95,
        )
        
        # Serialize
        dict_form = original.to_dict()
        
        # Simulate JSON round trip
        import json
        json_str = json.dumps(dict_form, default=str)
        reconstructed_dict = json.loads(json_str)
        
        # Deserialize
        final = Evidence.from_dict(reconstructed_dict)
        
        # Verify all key fields preserved
        assert final.id == original.id
        assert final.content == original.content
        assert final.origin_tool == original.origin_tool
        assert final.url == original.url
        assert final.score == original.score


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])

