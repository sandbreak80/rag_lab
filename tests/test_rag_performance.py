"""
RAG Performance Evaluation - Real metrics, no mocks

Tests actual vs theoretical performance with real queries
"""

import pytest
import time
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from search import VaultSearcher
from hybrid_search import HybridSearcher
from advanced_search import AdvancedSearcher
from query_expansion import QueryExpander
from knowledge_graph import KnowledgeGraph


class TestRAGPerformance:
    """Measure actual RAG performance with real queries"""
    
    # Real test queries from your domain
    TEST_QUERIES = [
        {
            "query": "Help me study for AI bluebelt",
            "expected_keywords": ["blue belt", "certification", "training", "ai"],
            "expected_files": ["blue-belt", "study", "training"],
            "category": "study"
        },
        {
            "query": "What is prompt engineering?",
            "expected_keywords": ["prompt", "engineering", "llm"],
            "expected_files": ["prompt", "engineering"],
            "category": "technical"
        },
        {
            "query": "AppDynamics observability best practices",
            "expected_keywords": ["appdynamics", "observability", "monitoring"],
            "expected_files": ["appdynamics", "observability"],
            "category": "product"
        },
        {
            "query": "transformer architecture attention mechanism",
            "expected_keywords": ["transformer", "attention", "neural"],
            "expected_files": ["transformer", "attention"],
            "category": "technical"
        },
        {
            "query": "RAG retrieval augmented generation",
            "expected_keywords": ["rag", "retrieval", "generation"],
            "expected_files": ["rag"],
            "category": "technical"
        }
    ]
    
    def test_vector_search_baseline(self):
        """Test baseline vector search performance"""
        searcher = VaultSearcher()
        
        results = {}
        for test in self.TEST_QUERIES:
            start = time.time()
            search_results = searcher.search(test["query"], limit=10)
            elapsed = time.time() - start
            
            # Calculate recall (how many expected keywords found)
            recall = self._calculate_recall(search_results, test["expected_keywords"])
            
            # Calculate precision (relevance of top results)
            precision = self._calculate_precision(search_results, test["expected_files"])
            
            results[test["query"]] = {
                "recall": recall,
                "precision": precision,
                "latency_ms": elapsed * 1000,
                "num_results": len(search_results)
            }
        
        # Assert baseline performance
        avg_recall = sum(r["recall"] for r in results.values()) / len(results)
        avg_precision = sum(r["precision"] for r in results.values()) / len(results)
        avg_latency = sum(r["latency_ms"] for r in results.values()) / len(results)
        
        print(f"\n📊 Vector Search Baseline:")
        print(f"  Recall: {avg_recall:.2%}")
        print(f"  Precision: {avg_precision:.2%}")
        print(f"  Latency: {avg_latency:.0f}ms")
        
        assert avg_recall > 0.3, "Baseline recall should be > 30%"
        assert avg_latency < 2000, "Latency should be < 2s"
    
    def test_hybrid_search_improvement(self):
        """Test hybrid search vs vector baseline"""
        vector_searcher = VaultSearcher()
        hybrid_searcher = HybridSearcher()
        
        improvements = []
        
        for test in self.TEST_QUERIES:
            # Vector baseline
            vector_results = vector_searcher.search(test["query"], limit=10)
            vector_recall = self._calculate_recall(vector_results, test["expected_keywords"])
            
            # Hybrid search
            hybrid_results = hybrid_searcher.hybrid_search(test["query"], limit=10)
            hybrid_recall = self._calculate_recall(hybrid_results, test["expected_keywords"])
            
            improvement = hybrid_recall - vector_recall
            improvements.append(improvement)
            
            print(f"\n  {test['query'][:50]}...")
            print(f"    Vector: {vector_recall:.2%} | Hybrid: {hybrid_recall:.2%} | Δ: {improvement:+.2%}")
        
        avg_improvement = sum(improvements) / len(improvements)
        print(f"\n📈 Hybrid Search Improvement: {avg_improvement:+.2%}")
        
        assert avg_improvement >= 0, "Hybrid should not degrade performance"
    
    def test_query_expansion_effectiveness(self):
        """Test query expansion impact"""
        expander = QueryExpander()
        searcher = VaultSearcher()
        
        improvements = []
        
        for test in self.TEST_QUERIES:
            # Original query
            original_results = searcher.search(test["query"], limit=10)
            original_recall = self._calculate_recall(original_results, test["expected_keywords"])
            
            # Expanded query
            expanded_query = expander.expand_with_context(test["query"])
            expanded_results = searcher.search(expanded_query, limit=10)
            expanded_recall = self._calculate_recall(expanded_results, test["expected_keywords"])
            
            improvement = expanded_recall - original_recall
            improvements.append(improvement)
            
            print(f"\n  Original: {test['query']}")
            print(f"  Expanded: {expanded_query}")
            print(f"  Recall: {original_recall:.2%} → {expanded_recall:.2%} (Δ: {improvement:+.2%})")
        
        avg_improvement = sum(improvements) / len(improvements)
        print(f"\n📝 Query Expansion Improvement: {avg_improvement:+.2%}")
        
        assert avg_improvement >= 0, "Expansion should not hurt recall"
    
    def test_advanced_search_complete(self):
        """Test complete advanced search system"""
        advanced_searcher = AdvancedSearcher()
        
        results = {}
        
        for test in self.TEST_QUERIES:
            start = time.time()
            search_results = advanced_searcher.search(
                test["query"],
                limit=10,
                expand_query=True,
                use_graph=True,
                rerank=False  # Skip LLM re-ranking for speed
            )
            elapsed = time.time() - start
            
            recall = self._calculate_recall(search_results, test["expected_keywords"])
            precision = self._calculate_precision(search_results, test["expected_files"])
            
            results[test["query"]] = {
                "recall": recall,
                "precision": precision,
                "latency_ms": elapsed * 1000,
                "num_results": len(search_results)
            }
        
        # Calculate metrics
        avg_recall = sum(r["recall"] for r in results.values()) / len(results)
        avg_precision = sum(r["precision"] for r in results.values()) / len(results)
        avg_latency = sum(r["latency_ms"] for r in results.values()) / len(results)
        
        print(f"\n🚀 Advanced Search Performance:")
        print(f"  Recall: {avg_recall:.2%}")
        print(f"  Precision: {avg_precision:.2%}")
        print(f"  Latency: {avg_latency:.0f}ms")
        
        # Assert performance targets
        assert avg_recall > 0.5, f"Advanced recall should be > 50%, got {avg_recall:.2%}"
        assert avg_precision > 0.4, f"Advanced precision should be > 40%, got {avg_precision:.2%}"
        assert avg_latency < 3000, f"Latency should be < 3s, got {avg_latency:.0f}ms"
    
    def test_knowledge_graph_coverage(self):
        """Test knowledge graph relationship discovery"""
        kg = KnowledgeGraph()
        
        # Test graph has nodes
        assert kg.graph.number_of_nodes() > 0, "Graph should have nodes"
        assert kg.graph.number_of_edges() > 0, "Graph should have edges"
        
        # Test relationship discovery
        # Get a random document node
        doc_nodes = [n for n in kg.graph.nodes() if kg.graph.nodes[n].get('type') == 'document']
        
        if doc_nodes:
            test_doc = doc_nodes[0]
            related = kg.find_related(test_doc, max_hops=2, limit=5)
            
            print(f"\n🕸️  Knowledge Graph Test:")
            print(f"  Total nodes: {kg.graph.number_of_nodes()}")
            print(f"  Total edges: {kg.graph.number_of_edges()}")
            print(f"  Document nodes: {len(doc_nodes)}")
            print(f"  Related to '{test_doc}': {len(related)}")
            
            assert isinstance(related, list), "Should return list of related docs"
    
    def test_end_to_end_latency(self):
        """Test complete end-to-end query latency"""
        advanced_searcher = AdvancedSearcher()
        
        latencies = []
        
        for test in self.TEST_QUERIES:
            start = time.time()
            results = advanced_searcher.search(
                test["query"],
                limit=5,
                expand_query=True,
                use_graph=True,
                rerank=False
            )
            elapsed = time.time() - start
            latencies.append(elapsed * 1000)
        
        avg_latency = sum(latencies) / len(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
        
        print(f"\n⚡ Latency Metrics:")
        print(f"  Average: {avg_latency:.0f}ms")
        print(f"  P95: {p95_latency:.0f}ms")
        print(f"  Min: {min(latencies):.0f}ms")
        print(f"  Max: {max(latencies):.0f}ms")
        
        assert avg_latency < 3000, f"Average latency should be < 3s, got {avg_latency:.0f}ms"
        assert p95_latency < 5000, f"P95 latency should be < 5s, got {p95_latency:.0f}ms"
    
    def _calculate_recall(self, results, expected_keywords):
        """Calculate recall: % of expected keywords found in results"""
        if not results or not expected_keywords:
            return 0.0
        
        # Combine all result content
        all_content = " ".join(r.get("content", "") for r in results).lower()
        all_metadata = " ".join(str(r.get("metadata", {})) for r in results).lower()
        combined = all_content + " " + all_metadata
        
        # Count how many expected keywords are found
        found = sum(1 for keyword in expected_keywords if keyword.lower() in combined)
        
        return found / len(expected_keywords)
    
    def _calculate_precision(self, results, expected_files):
        """Calculate precision: % of results that are relevant"""
        if not results or not expected_files:
            return 0.0
        
        # Check top 5 results
        top_results = results[:5]
        
        relevant = 0
        for result in top_results:
            file_name = result.get("metadata", {}).get("file_name", "").lower()
            file_path = result.get("metadata", {}).get("file_path", "").lower()
            combined = file_name + " " + file_path
            
            if any(expected.lower() in combined for expected in expected_files):
                relevant += 1
        
        return relevant / len(top_results)


if __name__ == '__main__':
    pytest.main([__file__, "-v", "-s"])

