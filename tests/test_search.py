"""Unit tests for search.py"""
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from search import VaultSearcher
import config


class TestVaultSearcher:
    """Test VaultSearcher class"""
    
    def test_init(self):
        """Test searcher initialization"""
        searcher = VaultSearcher()
        assert searcher is not None
        assert searcher.collection is not None
    
    def test_search_basic(self):
        """Test basic search functionality"""
        searcher = VaultSearcher()
        results = searcher.search("AI machine learning neural networks", limit=5)
        
        assert isinstance(results, list)
        assert len(results) > 0, "Search should return results from indexed vault"
        assert len(results) <= 5
        
        result = results[0]
        assert "content" in result
        assert "metadata" in result
        assert "score" in result
    
    def test_search_with_folder_filter(self):
        """Test search with folder filter"""
        searcher = VaultSearcher()
        
        # Test folder filter (may return empty if folder doesn't exist)
        results = searcher.search(
            "AI",
            limit=5,
            folder="Generative Artificial Intelligence - Blue Belt"
        )
        
        assert isinstance(results, list)
        # If results exist, verify they're from the correct folder
        for r in results:
            assert "Generative Artificial Intelligence - Blue Belt" in r["metadata"]["file_path"]
    
    def test_generate_rag_context(self):
        """Test RAG context generation"""
        searcher = VaultSearcher()
        
        context = searcher.generate_rag_context(
            "What is artificial intelligence?",
            max_length=1000
        )
        
        assert isinstance(context, str)
        assert len(context) > 0
        assert len(context) <= 1000
    
    def test_collection_stats(self):
        """Test getting collection statistics"""
        searcher = VaultSearcher()
        
        # Verify collection has data
        count = searcher.collection.count()
        assert count > 0, "Collection should have indexed documents"
        
        # Peek at some data
        sample = searcher.collection.peek(limit=1)
        assert len(sample['ids']) > 0
        assert len(sample['documents']) > 0
        assert len(sample['metadatas']) > 0


