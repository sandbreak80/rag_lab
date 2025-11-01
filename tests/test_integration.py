"""
Integration Tests for Educational RAG Lab
NO MOCKS - Real service calls only

Tests the entire system end-to-end with actual service interactions.
"""

import pytest
import requests
import time
import json

# Service URLs
BASE_URL = "http://localhost:5555"
SEARCH_URL = "http://localhost:8002"
VECTOR_DB_URL = "http://localhost:8005"
INGEST_URL = "http://localhost:8001"
WEB_SEARCH_URL = "http://localhost:8009"
KNOWLEDGE_GRAPH_URL = "http://localhost:8007"
RERANKER_URL = "http://localhost:8008"

class TestServiceHealth:
    """Test all services are running and healthy"""

    def test_web_ui_health(self):
        """Web UI should respond"""
        response = requests.get(f"{BASE_URL}/api/stats", timeout=5)
        assert response.status_code == 200

    def test_search_service_health(self):
        """Search service should be healthy"""
        response = requests.get(f"{SEARCH_URL}/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'

    def test_vector_db_health(self):
        """Vector DB should be healthy"""
        response = requests.get(f"{VECTOR_DB_URL}/health", timeout=5)
        assert response.status_code == 200

    def test_web_search_health(self):
        """Web search service should be healthy"""
        response = requests.get(f"{WEB_SEARCH_URL}/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data['searxng_accessible'] == True

    def test_knowledge_graph_health(self):
        """Knowledge graph service should be healthy"""
        response = requests.get(f"{KNOWLEDGE_GRAPH_URL}/health", timeout=5)
        assert response.status_code == 200

    def test_reranker_health(self):
        """Reranker service should be healthy"""
        response = requests.get(f"{RERANKER_URL}/health", timeout=5)
        assert response.status_code == 200


class TestConfigurableSearch:
    """Test the search_with_config endpoint with various configurations"""

    def test_minimal_config(self):
        """Test minimal configuration (vector only)"""
        config = {
            "query": "test query",
            "config": {
                "use_query_expansion": False,
                "use_bm25": False,
                "use_hybrid": False,
                "use_graph": False,
                "use_reranking": False,
                "top_k": 5
            }
        }

        response = requests.post(
            f"{SEARCH_URL}/search_with_config",
            json=config,
            timeout=30
        )

        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert 'results' in data
        assert 'metrics' in data
        assert 'config_used' in data

        # Verify metrics
        metrics = data['metrics']
        assert 'total_latency_ms' in metrics
        assert metrics['total_latency_ms'] > 0
        assert metrics['query_expansion_ms'] == 0  # Should be disabled
        assert metrics['bm25_search_ms'] == 0  # Should be disabled

    def test_balanced_config(self):
        """Test balanced configuration (hybrid search)"""
        config = {
            "query": "explain embeddings",
            "config": {
                "use_query_expansion": True,
                "use_bm25": True,
                "use_hybrid": True,
                "use_graph": False,
                "use_reranking": False,
                "top_k": 10
            }
        }

        response = requests.post(
            f"{SEARCH_URL}/search_with_config",
            json=config,
            timeout=30
        )

        assert response.status_code == 200
        data = response.json()

        metrics = data['metrics']
        # Should have hybrid method
        assert metrics['method'] == 'hybrid'
        # Query expansion should have taken time
        assert metrics['query_expansion_ms'] > 0
        # BM25 should have taken time
        assert metrics['bm25_search_ms'] > 0
        # Should have breakdown percentages
        assert 'breakdown_percent' in metrics

    def test_maximum_config(self):
        """Test maximum quality configuration (all features)"""
        config = {
            "query": "vector search",
            "config": {
                "use_query_expansion": True,
                "use_bm25": True,
                "use_hybrid": True,
                "use_graph": True,
                "use_reranking": True,
                "top_k": 20
            }
        }

        response = requests.post(
            f"{SEARCH_URL}/search_with_config",
            json=config,
            timeout=90  # Longer timeout for re-ranking
        )

        assert response.status_code == 200
        data = response.json()

        metrics = data['metrics']
        # All components should be active
        assert metrics['query_expansion_ms'] > 0
        assert metrics['vector_search_ms'] > 0
        assert metrics['bm25_search_ms'] > 0
        # Total latency should be higher
        assert metrics['total_latency_ms'] > 1000  # At least 1 second with re-ranking


class TestWebSearch:
    """Test web search integration"""

    def test_web_search_basic(self):
        """Test basic web search functionality"""
        payload = {
            "query": "RAG retrieval augmented generation",
            "limit": 3
        }

        response = requests.post(
            f"{WEB_SEARCH_URL}/search",
            json=payload,
            timeout=30
        )

        assert response.status_code == 200
        data = response.json()

        # Verify results
        assert 'results' in data
        assert data['count'] >= 1
        assert data['web_docs_returned'] >= 1
        assert data['latency_ms'] > 0

        # Verify result structure
        if data['results']:
            result = data['results'][0]
            assert 'title' in result
            assert 'url' in result
            assert 'content' in result
            assert 'engine' in result

    def test_web_search_metrics(self):
        """Test web search returns proper metrics"""
        payload = {
            "query": "machine learning",
            "limit": 5
        }

        response = requests.post(
            f"{WEB_SEARCH_URL}/search",
            json=payload,
            timeout=30
        )

        assert response.status_code == 200
        data = response.json()

        # Check metrics
        assert 'web_docs_returned' in data
        assert 'avg_pages_per_doc' in data
        assert 'latency_ms' in data
        assert 'engines_used' in data

        # Latency should be reasonable (< 20 seconds)
        assert data['latency_ms'] < 20000


class TestPresets:
    """Test configuration presets"""

    def test_get_presets(self):
        """Test retrieving all presets"""
        response = requests.get(f"{BASE_URL}/api/presets", timeout=5)

        assert response.status_code == 200
        data = response.json()

        assert 'presets' in data
        presets = data['presets']

        # Should have all 6 presets
        assert 'minimal' in presets
        assert 'fast' in presets
        assert 'balanced' in presets
        assert 'quality' in presets
        assert 'maximum' in presets
        assert 'production' in presets

        # Check preset structure
        for preset_name, preset in presets.items():
            assert 'name' in preset
            assert 'config' in preset
            assert 'llm_config' in preset
            assert 'expected_metrics' in preset


class TestKnowledgeGraph:
    """Test knowledge graph functionality"""

    def test_build_graph(self):
        """Test building knowledge graph"""
        # First get all documents
        docs_response = requests.post(
            f"{VECTOR_DB_URL}/get_all",
            json={},
            timeout=30
        )

        if docs_response.status_code == 200:
            docs_data = docs_response.json()

            if docs_data.get('count', 0) > 0:
                # Build graph
                response = requests.post(
                    f"{KNOWLEDGE_GRAPH_URL}/build",
                    timeout=30
                )

                assert response.status_code == 200
                data = response.json()
                assert data['success'] == True
                assert data['nodes'] >= 0
                assert data['edges'] >= 0


class TestReranker:
    """Test LLM re-ranking functionality"""

    def test_rerank_results(self):
        """Test re-ranking search results"""
        # First get some results
        search_response = requests.post(
            f"{SEARCH_URL}/search_with_config",
            json={
                "query": "neural networks",
                "config": {
                    "use_query_expansion": False,
                    "use_bm25": False,
                    "use_hybrid": False,
                    "use_graph": False,
                    "use_reranking": False,
                    "top_k": 5
                }
            },
            timeout=30
        )

        if search_response.status_code == 200:
            search_data = search_response.json()
            results = search_data.get('results', [])

            if results:
                # Rerank them
                rerank_response = requests.post(
                    f"{RERANKER_URL}/rerank",
                    json={
                        "query": "neural networks",
                        "results": results,
                        "limit": 5
                    },
                    timeout=90
                )

                assert rerank_response.status_code == 200
                rerank_data = rerank_response.json()

                assert 'results' in rerank_data
                assert 'latency_ms' in rerank_data
                # Re-ranking should take significant time
                assert rerank_data['latency_ms'] > 100


class TestEndToEndFlow:
    """Test complete end-to-end workflows"""

    def test_complete_rag_flow(self):
        """Test complete RAG flow: search -> context -> answer"""
        # Step 1: Configure and search
        search_response = requests.post(
            f"{SEARCH_URL}/search_with_config",
            json={
                "query": "What is an embedding?",
                "config": {
                    "use_query_expansion": True,
                    "use_bm25": True,
                    "use_hybrid": True,
                    "use_graph": False,
                    "use_reranking": False,
                    "top_k": 5
                }
            },
            timeout=30
        )

        assert search_response.status_code == 200
        search_data = search_response.json()

        # Verify we got results
        assert 'results' in search_data
        assert len(search_data['results']) > 0

        # Verify metrics are complete
        metrics = search_data['metrics']
        assert metrics['total_latency_ms'] > 0
        assert 'breakdown_percent' in metrics

        # Step 2: These results would go to LLM for answer generation
        # (We don't test LLM here as it's external Ollama service)

    def test_performance_comparison_flow(self):
        """Test flow for comparing two configurations"""
        configs = [
            {
                "name": "minimal",
                "config": {
                    "use_query_expansion": False,
                    "use_bm25": False,
                    "use_hybrid": False,
                    "use_graph": False,
                    "use_reranking": False,
                    "top_k": 5
                }
            },
            {
                "name": "balanced",
                "config": {
                    "use_query_expansion": True,
                    "use_bm25": True,
                    "use_hybrid": True,
                    "use_graph": False,
                    "use_reranking": False,
                    "top_k": 10
                }
            }
        ]

        results = []
        query = "explain vector search"

        for cfg in configs:
            response = requests.post(
                f"{SEARCH_URL}/search_with_config",
                json={"query": query, "config": cfg['config']},
                timeout=30
            )

            assert response.status_code == 200
            data = response.json()
            results.append({
                'name': cfg['name'],
                'latency': data['metrics']['total_latency_ms'],
                'method': data['metrics']['method']
            })

        # Balanced should be slower but hybrid
        assert results[1]['latency'] > results[0]['latency']
        assert results[1]['method'] == 'hybrid'
        assert results[0]['method'] == 'vector_only'


class TestMetricsAccuracy:
    """Test that metrics are accurate and consistent"""

    def test_latency_breakdown_sum(self):
        """Test that component latencies sum to total"""
        response = requests.post(
            f"{SEARCH_URL}/search_with_config",
            json={
                "query": "test",
                "config": {
                    "use_query_expansion": True,
                    "use_bm25": True,
                    "use_hybrid": True,
                    "use_graph": False,
                    "use_reranking": False,
                    "top_k": 5
                }
            },
            timeout=30
        )

        assert response.status_code == 200
        data = response.json()

        metrics = data['metrics']
        total = metrics['total_latency_ms']

        # Sum of components should be close to total (within 10% for overhead)
        component_sum = (
            metrics.get('query_expansion_ms', 0) +
            metrics.get('vector_search_ms', 0) +
            metrics.get('bm25_search_ms', 0) +
            metrics.get('fusion_ms', 0) +
            metrics.get('graph_enhancement_ms', 0) +
            metrics.get('reranking_ms', 0)
        )

        # Allow 10% variance for overhead
        assert abs(total - component_sum) < total * 0.1

    def test_percentage_breakdown(self):
        """Test that percentages sum to ~100%"""
        response = requests.post(
            f"{SEARCH_URL}/search_with_config",
            json={
                "query": "test",
                "config": {
                    "use_query_expansion": True,
                    "use_bm25": True,
                    "use_hybrid": True,
                    "use_graph": False,
                    "use_reranking": False,
                    "top_k": 5
                }
            },
            timeout=30
        )

        assert response.status_code == 200
        data = response.json()

        breakdown = data['metrics']['breakdown_percent']
        total_percent = sum(breakdown.values())

        # Should sum to approximately 100%
        assert 95 <= total_percent <= 105


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

