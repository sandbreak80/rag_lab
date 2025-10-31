"""End-to-end tests for the full pipeline"""
import pytest
from pathlib import Path
import sys
import tempfile
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from indexer import VaultIndexer
from search import VaultSearcher
import config


class TestEndToEnd:
    """End-to-end integration tests"""
    
    def test_full_pipeline_index_and_search(self):
        """Test complete pipeline: create vault -> index -> search"""
        # Create temporary vault
        vault_dir = tempfile.mkdtemp()
        vault_path = Path(vault_dir)
        
        # Create test files
        (vault_path / "ai_note.md").write_text("""---
title: AI and Machine Learning
tags: [ai, ml, technology]
---

# Artificial Intelligence

Machine learning is a subset of artificial intelligence.
Deep learning uses neural networks.
""")
        
        (vault_path / "python_note.md").write_text("""# Python Programming

Python is a high-level programming language.
It's great for data science and machine learning.
""")
        
        (vault_path / "docker_note.md").write_text("""# Docker Containers

Docker provides containerization for applications.
It's useful for development and deployment.
""")
        
        # Create temporary indices
        indices_dir = tempfile.mkdtemp()
        
        try:
            # Backup original config
            original_vault = config.VAULT_PATH
            original_indices = config.INDICES_PATH
            
            # Set temporary paths
            config.VAULT_PATH = str(vault_path)
            config.INDICES_PATH = str(indices_dir)
            
            # INDEX: Index the vault
            indexer = VaultIndexer()
            stats = indexer.index_vault(force_reindex=True)
            
            assert stats["files_processed"] == 3
            assert stats["chunks_created"] > 0
            assert stats["errors"] == 0
            
            # SEARCH: Search for content
            searcher = VaultSearcher()
            
            # Test 1: Search for AI content
            results = searcher.search("machine learning artificial intelligence", limit=3)
            assert len(results) > 0
            assert any("ai_note" in r["metadata"]["file_name"] for r in results)
            
            # Test 2: Search for Python
            results = searcher.search("python programming language", limit=3)
            assert len(results) > 0
            assert any("python_note" in r["metadata"]["file_name"] for r in results)
            
            # Test 3: Search for Docker
            results = searcher.search("docker containerization", limit=3)
            assert len(results) > 0
            assert any("docker_note" in r["metadata"]["file_name"] for r in results)
            
            # RAG Context: Generate context for a question
            context = searcher.generate_rag_context("What is Python used for?", max_length=1000)
            assert len(context) > 0
            assert "python" in context.lower() or "programming" in context.lower()
            
            # Verify collection stats
            assert searcher.collection.count() > 0
        
        finally:
            # Restore original config
            config.VAULT_PATH = original_vault
            config.INDICES_PATH = original_indices
            
            # Cleanup
            shutil.rmtree(vault_dir)
            shutil.rmtree(indices_dir)
    
    def test_force_reindex(self):
        """Test force re-indexing"""
        vault_dir = tempfile.mkdtemp()
        vault_path = Path(vault_dir)
        indices_dir = tempfile.mkdtemp()
        
        (vault_path / "test.md").write_text("# Test\n\nContent for testing")
        (vault_path / "test2.md").write_text("# Another Test\n\nMore content")
        
        try:
            original_vault = config.VAULT_PATH
            original_indices = config.INDICES_PATH
            original_collection = config.COLLECTION_NAME
            
            config.VAULT_PATH = str(vault_path)
            config.INDICES_PATH = str(indices_dir)
            config.COLLECTION_NAME = "test_force_reindex"  # Use unique collection
            
            # First index
            indexer = VaultIndexer()
            stats1 = indexer.index_vault(force_reindex=True)
            
            assert stats1["files_processed"] == 2
            assert stats1["chunks_created"] > 0
            
            # Get initial count
            initial_count = indexer.collection.count()
            assert initial_count > 0
            
            # Force re-index (should delete and rebuild)
            stats2 = indexer.index_vault(force_reindex=True)
            
            assert stats2["files_processed"] == 2
            assert stats2["chunks_created"] > 0
            
            # Count should be the same (rebuilt from scratch)
            final_count = indexer.collection.count()
            assert final_count == initial_count
        
        finally:
            config.VAULT_PATH = original_vault
            config.INDICES_PATH = original_indices
            shutil.rmtree(vault_dir)
            shutil.rmtree(indices_dir)
    
    def test_error_handling_corrupt_file(self):
        """Test handling of corrupt/invalid markdown files"""
        vault_dir = tempfile.mkdtemp()
        vault_path = Path(vault_dir)
        indices_dir = tempfile.mkdtemp()
        
        # Create a valid file
        (vault_path / "valid.md").write_text("# Valid\n\nContent")
        
        # Create a binary file with .md extension (should be handled gracefully)
        (vault_path / "binary.md").write_bytes(b'\x00\x01\x02\x03\x04')
        
        try:
            original_vault = config.VAULT_PATH
            original_indices = config.INDICES_PATH
            
            config.VAULT_PATH = str(vault_path)
            config.INDICES_PATH = str(indices_dir)
            
            indexer = VaultIndexer()
            stats = indexer.index_vault(force_reindex=True)
            
            # Should handle errors gracefully
            assert stats["files_processed"] >= 1  # At least the valid file
        
        finally:
            config.VAULT_PATH = original_vault
            config.INDICES_PATH = original_indices
            shutil.rmtree(vault_dir)
            shutil.rmtree(indices_dir)


