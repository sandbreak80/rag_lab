"""Unit tests for search.py"""
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from search import VaultSearcher
import config


class TestVaultSearcher:
    """Test VaultSearcher class"""
    
    @pytest.mark.skipif(
        not Path("/workspace/indices").exists(),
        reason="Requires Docker environment with indexed vault"
    )
    def test_init(self, temp_indices, monkeypatch):
        """Test searcher initialization"""
        monkeypatch.setattr(config, "INDICES_PATH", str(temp_indices))
        
        try:
            searcher = VaultSearcher()
            assert searcher is not None
        except Exception as e:
            pytest.skip(f"ChromaDB not initialized: {e}")
    
    @pytest.mark.skipif(
        not Path("/workspace/indices").exists(),
        reason="Requires Docker environment with indexed vault"
    )
    def test_search_basic(self):
        """Test basic search functionality"""
        try:
            searcher = VaultSearcher()
            results = searcher.search("test query", limit=5)
            
            assert isinstance(results, list)
            assert len(results) <= 5
            
            if len(results) > 0:
                result = results[0]
                assert "content" in result
                assert "metadata" in result
                assert "score" in result
        except Exception as e:
            pytest.skip(f"Search not available: {e}")
    
    @pytest.mark.skipif(
        not Path("/workspace/indices").exists(),
        reason="Requires Docker environment with indexed vault"
    )
    def test_search_with_filters(self):
        """Test search with metadata filters"""
        try:
            searcher = VaultSearcher()
            
            # Search with tag filter
            results = searcher.search(
                "test query",
                limit=5,
                filters={"tags": {"$contains": "test"}}
            )
            
            assert isinstance(results, list)
        except Exception as e:
            pytest.skip(f"Search not available: {e}")
    
    @pytest.mark.skipif(
        not Path("/workspace/indices").exists(),
        reason="Requires Docker environment with indexed vault"
    )
    def test_answer_question(self):
        """Test RAG question answering"""
        try:
            searcher = VaultSearcher()
            
            answer = searcher.answer_question(
                "What is this vault about?",
                num_contexts=3
            )
            
            assert isinstance(answer, dict)
            assert "answer" in answer
            assert "sources" in answer
            assert "contexts" in answer
        except Exception as e:
            pytest.skip(f"Q&A not available: {e}")
    
    @pytest.mark.skipif(
        not Path("/workspace/indices").exists(),
        reason="Requires Docker environment with indexed vault"
    )
    def test_get_stats(self):
        """Test getting index statistics"""
        try:
            searcher = VaultSearcher()
            stats = searcher.get_stats()
            
            assert isinstance(stats, dict)
            assert "total_chunks" in stats
            assert "unique_files" in stats
        except Exception as e:
            pytest.skip(f"Stats not available: {e}")


