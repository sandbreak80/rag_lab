#!/usr/bin/env python3
"""
Validate RAG Feature Toggles

Tests that each RAG feature can be enabled/disabled and has a measurable impact.
This is critical for the educational lab where students toggle features to see their effect.

Tests:
1. Query Expansion (synonym/related terms)
2. BM25 Keyword Search (exact term matching)
3. Hybrid Search (RRF fusion of vector + BM25)
4. Knowledge Graph (entity/relationship expansion)
5. LLM Re-ranking (precision improvement)
6. Web Search (SearXNG integration)

Each test runs the same query with feature ON and OFF, comparing results.
"""

import requests
import json
import time
from typing import Dict, List, Any
from datetime import datetime

API_BASE = "http://localhost:8000/api"
API_ENDPOINT = f"{API_BASE}/ask"  # Use the /ask endpoint which returns metrics
TEST_QUERY = "What are the key features of RAG?"

class RAGToggleValidator:
    def __init__(self):
        self.results = []

    def test_feature(self, feature_name: str, config_on: Dict, config_off: Dict) -> Dict[str, Any]:
        """Test a feature by running query with feature ON and OFF"""
        print(f"\n{'='*60}")
        print(f"Testing: {feature_name}")
        print(f"{'='*60}")

        result = {
            'feature': feature_name,
            'timestamp': datetime.now().isoformat(),
            'query': TEST_QUERY,
            'status': 'PENDING'
        }

        # Test with feature OFF
        print(f"\n📴 Testing with {feature_name} OFF...")
        try:
            response_off = self._send_query(config_off)
            result['off'] = {
                'success': True,
                'latency_ms': response_off.get('metrics', {}).get('total_latency_ms', 0),
                'sources': len(response_off.get('sources', [])),
                'answer_length': len(response_off.get('answer', '')),
            }
            print(f"   ✅ OFF: {result['off']['latency_ms']:.0f}ms, {result['off']['sources']} sources")
        except Exception as e:
            result['off'] = {'success': False, 'error': str(e)}
            print(f"   ❌ OFF: {e}")

        # Test with feature ON
        print(f"\n✅ Testing with {feature_name} ON...")
        try:
            response_on = self._send_query(config_on)
            result['on'] = {
                'success': True,
                'latency_ms': response_on.get('metrics', {}).get('total_latency_ms', 0),
                'sources': len(response_on.get('sources', [])),
                'answer_length': len(response_on.get('answer', '')),
            }
            print(f"   ✅ ON:  {result['on']['latency_ms']:.0f}ms, {result['on']['sources']} sources")
        except Exception as e:
            result['on'] = {'success': False, 'error': str(e)}
            print(f"   ❌ ON: {e}")

        # Compare results
        if result['off']['success'] and result['on']['success']:
            latency_diff = result['on']['latency_ms'] - result['off']['latency_ms']
            source_diff = result['on']['sources'] - result['off']['sources']

            print(f"\n📊 Impact:")

            # Calculate percentage change (avoid division by zero)
            if result['off']['latency_ms'] > 0:
                latency_pct = latency_diff / result['off']['latency_ms'] * 100
                print(f"   Latency: {latency_diff:+.0f}ms ({latency_pct:+.1f}%)")
            else:
                latency_pct = 0
                print(f"   Latency: {latency_diff:+.0f}ms (no baseline)")

            print(f"   Sources: {source_diff:+d} documents")

            result['impact'] = {
                'latency_delta_ms': latency_diff,
                'latency_pct': latency_pct,
                'sources_delta': source_diff,
            }

            # Feature should have some measurable impact
            has_impact = abs(latency_diff) > 10 or abs(source_diff) > 0
            result['status'] = 'PASS' if has_impact else 'WARNING'

            if not has_impact:
                print(f"   ⚠️  WARNING: No measurable impact detected!")
        else:
            result['status'] = 'FAIL'
            print(f"\n❌ Test FAILED: One or both requests failed")

        self.results.append(result)
        return result

    def _send_query(self, config: Dict) -> Dict:
        """Send chat query with specified config - using camelCase for React API format"""
        response = requests.post(
            API_ENDPOINT,
            json={
                'query': TEST_QUERY,
                'model': config.get('model', 'llama3.1:8b'),
                'temperature': config.get('temperature', 0.7),
                'topK': config.get('top_k', 5),
                'contextWindow': config.get('context_window', 2048),
                'useQueryExpansion': config.get('use_query_expansion', False),
                'useBM25': config.get('use_bm25', False),
                'useHybrid': config.get('use_hybrid', False),
                'useGraph': config.get('use_graph', False),
                'useReranking': config.get('use_reranking', False),
                'useWebSearch': config.get('use_web_search', False),
                'useAgenticChunking': config.get('use_agentic_chunking', True),
                'webSearchDocs': config.get('web_search_docs', 3),
                'webSearchPages': config.get('web_search_pages', 2),
                'rerankTopK': config.get('rerank_top_k', 5),
            },
            timeout=180
        )
        response.raise_for_status()
        return response.json()

    def run_all_tests(self):
        """Run all feature toggle tests"""
        print(f"\n🧪 RAG Feature Toggle Validation")
        print(f"Query: '{TEST_QUERY}'")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Base config (all features OFF)
        base_config = {
            'model': 'llama3.1:8b',
            'temperature': 0.7,
            'top_k': 5,
            'context_window': 2048,
            'use_query_expansion': False,
            'use_bm25': False,
            'use_hybrid': False,
            'use_graph': False,
            'use_reranking': False,
            'use_web_search': False,
            'use_agentic_chunking': True,  # Keep this on (document processing)
            'web_search_docs': 3,
            'web_search_pages': 2,
            'rerank_top_k': 5,
        }

        # Test 1: Query Expansion
        self.test_feature(
            "Query Expansion",
            {**base_config, 'use_query_expansion': True},
            base_config
        )

        time.sleep(2)  # Brief pause between tests

        # Test 2: BM25 Keyword Search
        self.test_feature(
            "BM25 Keyword Search",
            {**base_config, 'use_bm25': True},
            base_config
        )

        time.sleep(2)

        # Test 3: Hybrid Search (requires BM25)
        self.test_feature(
            "Hybrid Search (Vector + BM25)",
            {**base_config, 'use_bm25': True, 'use_hybrid': True},
            {**base_config, 'use_bm25': True, 'use_hybrid': False}
        )

        time.sleep(2)

        # Test 4: Knowledge Graph
        self.test_feature(
            "Knowledge Graph",
            {**base_config, 'use_graph': True},
            base_config
        )

        time.sleep(2)

        # Test 5: LLM Re-ranking
        self.test_feature(
            "LLM Re-ranking",
            {**base_config, 'use_reranking': True, 'rerank_top_k': 3},
            base_config
        )

        time.sleep(2)

        # Test 6: Web Search
        self.test_feature(
            "Web Search",
            {**base_config, 'use_web_search': True, 'web_search_docs': 2, 'web_search_pages': 1},
            base_config
        )

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print(f"\n\n{'='*60}")
        print(f"📊 TEST SUMMARY")
        print(f"{'='*60}")

        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        warned = sum(1 for r in self.results if r['status'] == 'WARNING')
        failed = sum(1 for r in self.results if r['status'] == 'FAIL')

        print(f"\nTotal Tests: {len(self.results)}")
        print(f"✅ Passed:   {passed}")
        print(f"⚠️  Warnings: {warned}")
        print(f"❌ Failed:   {failed}")

        print(f"\n{'Feature':<30} {'Status':<10} {'Latency Impact':<20}")
        print(f"{'-'*60}")

        for r in self.results:
            status_icon = {
                'PASS': '✅',
                'WARNING': '⚠️',
                'FAIL': '❌',
                'PENDING': '⏳'
            }.get(r['status'], '?')

            latency_str = ''
            if r.get('impact'):
                latency_str = f"{r['impact']['latency_delta_ms']:+.0f}ms ({r['impact']['latency_pct']:+.1f}%)"

            print(f"{r['feature']:<30} {status_icon} {r['status']:<8} {latency_str:<20}")

        # Save detailed results to JSON
        output_file = '/Users/bmstoner/code_projects/rag_lab/tests/toggle_validation_results.json'
        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'total': len(self.results),
                    'passed': passed,
                    'warnings': warned,
                    'failed': failed
                },
                'results': self.results
            }, f, indent=2)

        print(f"\n📄 Detailed results saved to: {output_file}")

        # Overall result
        if failed == 0 and warned == 0:
            print(f"\n🎉 ALL TESTS PASSED! All RAG toggles working correctly.")
            return 0
        elif failed == 0:
            print(f"\n⚠️  WARNINGS DETECTED: Some features show no measurable impact.")
            return 1
        else:
            print(f"\n❌ TESTS FAILED: {failed} feature(s) not working correctly.")
            return 2

def main():
    """Main entry point"""
    # Check if services are running
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        response.raise_for_status()
        print(f"✅ API Gateway healthy: {response.json()}")
    except Exception as e:
        print(f"❌ ERROR: Cannot reach API Gateway at http://localhost:8000")
        print(f"   {e}")
        print(f"\n💡 Make sure Docker containers are running:")
        print(f"   cd /Users/bmstoner/code_projects/rag_lab")
        print(f"   ./scripts/start-lab.sh")
        return 1

    # Run tests
    validator = RAGToggleValidator()
    return validator.run_all_tests()

if __name__ == '__main__':
    exit(main())

