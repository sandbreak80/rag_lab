"""
Test that all required dependencies are installed and importable.

This test suite catches missing dependencies that would cause runtime failures.
"""

import pytest
import sys
import subprocess


class TestDependencies:
    """Test all required dependencies are installed"""
    
    def test_core_dependencies(self):
        """Test core RAG dependencies are importable"""
        # Core MCP
        import mcp
        assert mcp is not None
        
        # Vector store
        import chromadb
        assert chromadb is not None
        
        # YAML parsing
        import yaml
        assert yaml is not None
        
        # HTTP requests
        import requests
        assert requests is not None
        
        # Async HTTP
        import aiohttp
        assert aiohttp is not None
    
    def test_advanced_rag_dependencies(self):
        """Test advanced RAG feature dependencies"""
        # BM25 for hybrid search
        from rank_bm25 import BM25Okapi
        assert BM25Okapi is not None
        
        # NetworkX for knowledge graph
        import networkx
        assert networkx is not None
    
    def test_web_ui_dependencies(self):
        """Test web UI dependencies"""
        # Flask
        from flask import Flask, jsonify, request
        assert Flask is not None
        assert jsonify is not None
        assert request is not None
    
    def test_testing_dependencies(self):
        """Test that testing dependencies are available"""
        # Pytest
        import pytest
        assert pytest is not None
        
        # Playwright
        import playwright
        assert playwright is not None
        
        from playwright.sync_api import sync_playwright
        assert sync_playwright is not None
    
    def test_project_modules_importable(self):
        """Test all project modules can be imported"""
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        
        # Core modules
        import config
        assert config is not None
        
        from parser import MarkdownParser
        assert MarkdownParser is not None
        
        from indexer import VaultIndexer
        assert VaultIndexer is not None
        
        from search import VaultSearcher
        assert VaultSearcher is not None
        
        # Advanced modules
        from hybrid_search import HybridSearcher
        assert HybridSearcher is not None
        
        from query_expansion import QueryExpander
        assert QueryExpander is not None
        
        from knowledge_graph import KnowledgeGraph
        assert KnowledgeGraph is not None
        
        from advanced_search import AdvancedSearcher
        assert AdvancedSearcher is not None
        
        from agentic_chunker import AgenticChunker
        assert AgenticChunker is not None
        
        # Web app
        import webapp
        assert webapp is not None
    
    def test_playwright_browser_available(self):
        """Test Playwright browser is installed"""
        try:
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as p:
                # Try to launch browser
                browser = p.chromium.launch(headless=True)
                assert browser is not None
                
                # Verify we can create a page
                page = browser.new_page()
                assert page is not None
                
                # Clean up
                browser.close()
                
        except Exception as e:
            pytest.fail(f"Playwright browser not available: {e}")
    
    def test_ollama_connectivity(self):
        """Test Ollama service is reachable"""
        import requests
        import config
        
        try:
            response = requests.get(f"{config.OLLAMA_URL}/api/tags", timeout=5)
            assert response.status_code == 200, "Ollama service not responding"
            
            data = response.json()
            assert 'models' in data, "Ollama response missing models"
            
        except requests.exceptions.ConnectionError:
            pytest.skip("Ollama service not available (expected in CI)")
        except requests.exceptions.Timeout:
            pytest.skip("Ollama service timeout (expected in CI)")
    
    def test_required_ollama_models(self):
        """Test required Ollama models are available"""
        import requests
        import config
        
        try:
            response = requests.get(f"{config.OLLAMA_URL}/api/tags", timeout=5)
            if response.status_code != 200:
                pytest.skip("Ollama service not available")
            
            data = response.json()
            model_names = [m['name'] for m in data.get('models', [])]
            
            # Check for embedding model
            embedding_model = config.EMBEDDING_MODEL
            assert any(embedding_model in name for name in model_names), \
                f"Embedding model {embedding_model} not found in Ollama"
            
            # Check for chat model
            chat_model = config.CHAT_MODEL
            assert any(chat_model in name for name in model_names), \
                f"Chat model {chat_model} not found in Ollama"
                
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            pytest.skip("Ollama service not available (expected in CI)")
    
    def test_chromadb_collection_accessible(self):
        """Test ChromaDB collection can be accessed"""
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        
        from search import VaultSearcher
        
        try:
            searcher = VaultSearcher()
            assert searcher.collection is not None
            
            # Verify collection has data
            count = searcher.collection.count()
            assert count >= 0, "Collection count should be non-negative"
            
        except Exception as e:
            pytest.fail(f"ChromaDB collection not accessible: {e}")
    
    def test_webapp_can_initialize(self):
        """Test webapp can initialize without errors"""
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        
        try:
            # Import webapp (this initializes the searcher)
            import webapp
            
            # Verify Flask app exists
            assert webapp.app is not None
            assert webapp.searcher is not None
            
            # Verify search mode is set
            assert webapp.search_mode in ['vector', 'advanced']
            
        except Exception as e:
            pytest.fail(f"Webapp initialization failed: {e}")
    
    def test_webapp_stats_endpoint_logic(self):
        """Test webapp stats endpoint logic works"""
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        
        import webapp
        import config
        
        try:
            # Try to get collection using the same logic as stats endpoint
            collection = None
            
            if hasattr(webapp.searcher, 'collection'):
                collection = webapp.searcher.collection
            elif hasattr(webapp.searcher, 'hybrid_searcher'):
                collection = webapp.searcher.hybrid_searcher.vector_searcher.collection
            elif hasattr(webapp.searcher, 'vector_searcher'):
                collection = webapp.searcher.vector_searcher.collection
            
            assert collection is not None, "Could not access collection from searcher"
            
            # Verify we can get count
            count = collection.count()
            assert isinstance(count, int), "Collection count should be an integer"
            
            # Verify config values are accessible
            assert config.EMBEDDING_MODEL is not None
            assert config.CHAT_MODEL is not None
            assert config.VAULT_PATH is not None
            
        except Exception as e:
            pytest.fail(f"Webapp stats logic failed: {e}")
    
    def test_all_test_files_runnable(self):
        """Test all test files can be imported without errors"""
        from pathlib import Path
        test_dir = Path(__file__).parent
        
        test_files = [
            'test_parser.py',
            'test_indexer.py',
            'test_search.py',
            'test_e2e.py',
            'test_rag_performance.py',
        ]
        
        for test_file in test_files:
            test_path = test_dir / test_file
            if test_path.exists():
                # Try to import the test module
                module_name = test_file.replace('.py', '')
                try:
                    __import__(f'tests.{module_name}')
                except Exception as e:
                    pytest.fail(f"Failed to import {test_file}: {e}")


class TestEnvironmentSetup:
    """Test environment is properly configured"""
    
    def test_python_version(self):
        """Test Python version is 3.11+"""
        assert sys.version_info >= (3, 11), \
            f"Python 3.11+ required, got {sys.version_info.major}.{sys.version_info.minor}"
    
    def test_workspace_structure(self):
        """Test workspace has expected directory structure"""
        from pathlib import Path
        
        workspace = Path(__file__).parent.parent
        
        # Check key directories exist
        assert (workspace / "src").exists(), "src/ directory missing"
        assert (workspace / "tests").exists(), "tests/ directory missing"
        assert (workspace / "indices").exists(), "indices/ directory missing"
        
        # Check key files exist
        assert (workspace / "requirements.txt").exists(), "requirements.txt missing"
        assert (workspace / "Dockerfile").exists(), "Dockerfile missing"
        assert (workspace / "docker-compose.yml").exists(), "docker-compose.yml missing"
        assert (workspace / "Makefile").exists(), "Makefile missing"
    
    def test_src_modules_exist(self):
        """Test all expected source modules exist"""
        from pathlib import Path
        
        src_dir = Path(__file__).parent.parent / "src"
        
        required_modules = [
            'config.py',
            'parser.py',
            'indexer.py',
            'search.py',
            'server.py',
            'webapp.py',
            'hybrid_search.py',
            'query_expansion.py',
            'knowledge_graph.py',
            'advanced_search.py',
            'agentic_chunker.py',
        ]
        
        for module in required_modules:
            module_path = src_dir / module
            assert module_path.exists(), f"Required module {module} missing"
    
    def test_indices_directory_writable(self):
        """Test indices directory is writable"""
        from pathlib import Path
        import tempfile
        
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        import config
        
        indices_path = Path(config.INDICES_PATH)
        
        # Try to create a temp file
        try:
            test_file = indices_path / ".test_write"
            test_file.write_text("test")
            test_file.unlink()
        except Exception as e:
            pytest.fail(f"Indices directory not writable: {e}")
    
    def test_vault_path_readable(self):
        """Test vault path is readable"""
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        import config
        
        vault_path = Path(config.VAULT_PATH)
        
        # Check vault exists and is readable
        assert vault_path.exists(), f"Vault path {vault_path} does not exist"
        assert vault_path.is_dir(), f"Vault path {vault_path} is not a directory"
        
        # Try to list directory
        try:
            list(vault_path.iterdir())
        except Exception as e:
            pytest.fail(f"Vault path not readable: {e}")


class TestDockerEnvironment:
    """Test Docker-specific environment"""
    
    def test_running_in_docker(self):
        """Test if running in Docker container"""
        from pathlib import Path
        
        # Check for Docker indicators
        is_docker = (
            Path('/.dockerenv').exists() or
            Path('/workspace').exists() or
            Path('/proc/1/cgroup').exists()
        )
        
        # This test documents the environment but doesn't fail
        if is_docker:
            print("✅ Running in Docker container")
        else:
            print("ℹ️  Running outside Docker (local development)")
    
    def test_docker_networking(self):
        """Test Docker can reach host services"""
        import requests
        import config
        
        # Check if we can reach Ollama through Docker networking
        if 'host.docker.internal' in config.OLLAMA_URL:
            try:
                response = requests.get(config.OLLAMA_URL, timeout=2)
                assert response.status_code in [200, 404], \
                    "Docker host networking not working"
            except requests.exceptions.ConnectionError:
                pytest.skip("Ollama not running on host (expected in some environments)")
            except requests.exceptions.Timeout:
                pytest.skip("Ollama timeout (expected in some environments)")


if __name__ == '__main__':
    pytest.main([__file__, "-v", "-s"])

