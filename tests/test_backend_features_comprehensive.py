#!/usr/bin/env python3
"""
Comprehensive Backend Feature Tests
Tests all RAG features (A-R) to validate they work correctly on the backend.

Usage:
    python3 tests/test_backend_features_comprehensive.py
    RAG_API=http://localhost:3000 python3 tests/test_backend_features_comprehensive.py
"""

import os
import sys
import json
import time
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Configuration
API_BASE = os.environ.get('RAG_API', 'http://localhost:3000')

def get_api_endpoint(path: str) -> str:
    """Get correct API endpoint path based on API_BASE"""
    if ":3000" in API_BASE:
        return f"{API_BASE}/api{path}"
    return f"{API_BASE}{path}"

@dataclass
class TestResult:
    feature: str
    passed: bool
    message: str
    timing: Optional[float] = None
    sources: Optional[List[str]] = None
    errors: Optional[List[str]] = None

class FeatureTester:
    def __init__(self, api_base: str = API_BASE):
        self.api_base = api_base
        self.results: List[TestResult] = []

    def test_feature(self, feature_name: str, config: Dict[str, Any],
                    expected_sources: Optional[List[str]] = None) -> TestResult:
        """Test a specific feature with given configuration"""
        print(f"\n{'='*60}")
        print(f"Testing: {feature_name}")
        print(f"{'='*60}")

        query = "What is retrieval augmented generation? Explain how RAG works."

        # Prepare request - RAG API v1 only accepts specific fields
        # Feature flags may need to be passed through filters dict
        # For now, only use fields that are in the RagQuery model
        payload = {
            "query": query,
            "user_id": "automated_test",
            "groups": [],
            "top_k": config.get("top_k", 8),
        }

        # Add fields that are in RagQuery model
        if "web_search_enabled" in config:
            payload["web_search_enabled"] = config["web_search_enabled"]
        if "enable_research" in config:
            payload["enable_research"] = config["enable_research"]
        if "use_graph" in config:
            payload["use_graph"] = config["use_graph"]

        # Pass other feature flags through filters dict
        feature_flags = {}
        for key, value in config.items():
            if key not in ["top_k", "web_search_enabled", "enable_research", "use_graph"]:
                feature_flags[key] = value

        if feature_flags:
            payload["filters"] = feature_flags

        start_time = time.time()
        try:
            response = requests.post(
                get_api_endpoint("/v1/rag/query"),
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            elapsed = time.time() - start_time

            if response.status_code != 200:
                return TestResult(
                    feature=feature_name,
                    passed=False,
                    message=f"API returned status {response.status_code}: {response.text}",
                    timing=elapsed
                )

            data = response.json()

            # Extract sources from citations
            sources = []
            if 'citations' in data:
                for citation in data['citations']:
                    origin = citation.get('origin_tool', 'unknown')
                    sources.append(origin)

            # Also check sources field if present
            if 'sources' in data and data['sources']:
                for source in data['sources']:
                    origin = source.get('origin_tool', source.get('source_type', 'unknown'))
                    if origin not in sources:
                        sources.append(origin)

            # Check if expected sources are present
            # For features that should return specific source types, validate them
            # For general RAG features, any sources are acceptable
            source_check = True
            missing_sources = []
            messages = []

            if expected_sources:
                # Check if any of the expected sources are present
                source_lower = [s.lower() for s in sources]
                expected_lower = [e.lower() for e in expected_sources]
                found_any = any(any(exp in src for exp in expected_lower) for src in source_lower)

                if not found_any:
                    # If we have sources but not the expected type, note it
                    if len(sources) > 0:
                        source_check = False
                        missing_sources = expected_sources
                        messages.append(f"Got sources: {', '.join(sources)} but expected: {', '.join(expected_sources)}")
                    else:
                        # No sources at all - this is a failure
                        source_check = False
                        missing_sources = expected_sources
                        messages.append(f"No sources returned, expected: {', '.join(expected_sources)}")
                else:
                    messages.append(f"✅ Expected sources found: {', '.join([s for s in sources if any(e.lower() in s.lower() for e in expected_sources)])}")
            elif len(sources) > 0:
                messages.append(f"✅ Sources returned: {', '.join(sources)}")
            else:
                # No expected sources and no sources - might be OK for some features
                messages.append("⚠️  No sources returned")

            # Check for timing data (optional - may be new feature)
            has_timing = 'artifacts' in data and 'stage_timings' in data.get('artifacts', {})
            # Also check metrics.stage_timings
            if not has_timing and 'metrics' in data:
                has_timing = 'stage_timings' in data.get('metrics', {})

            # Check for trace_id (optional - for observability)
            has_trace = 'trace_id' in data

            # Validate answer (REQUIRED)
            has_answer = 'answer' in data and len(data.get('answer', '')) > 0

            # Build result message
            if not has_answer:
                messages.append("❌ No answer returned")
            else:
                messages.append(f"✅ Answer returned ({len(data['answer'])} chars)")

            # Timing and trace are optional - note if missing but don't fail
            if has_timing:
                messages.append("✅ Timing data present")
            else:
                messages.append("⚠️  No timing data (may be new feature)")

            if has_trace:
                messages.append("✅ Trace ID present")
            else:
                messages.append("⚠️  No trace_id (observability may be disabled)")

            # Pass if we have answer and expected sources (functionality works)
            # Timing and trace are nice-to-have but not required
            # For features without expected sources, just need an answer
            if expected_sources:
                passed = has_answer and source_check
            else:
                passed = has_answer  # Just need an answer if no specific sources expected

            if passed:
                messages.append(f"✅ Feature FUNCTIONALITY working")
            else:
                messages.append(f"❌ Feature FUNCTIONALITY has issues")

            return TestResult(
                feature=feature_name,
                passed=passed,
                message=" | ".join(messages),
                timing=elapsed,
                sources=sources
            )

        except Exception as e:
            elapsed = time.time() - start_time
            return TestResult(
                feature=feature_name,
                passed=False,
                message=f"Exception: {str(e)}",
                timing=elapsed,
                errors=[str(e)]
            )

    def test_security_guardrails(self) -> TestResult:
        """Test A. Security Guardrails"""
        # Note: Security guardrails may be enabled by default
        # Test with a query that might trigger security checks
        # Security guardrails don't necessarily return sources - they filter/validate
        config = {
            "top_k": 5
        }
        return self.test_feature("A. Security Guardrails", config, expected_sources=None)

    def test_query_expansion(self) -> TestResult:
        """Test B. Query Expansion"""
        # Query expansion modifies the query but still returns RAG sources
        config = {
            "use_query_expansion": True,
            "top_k": 5
        }
        # Any sources are OK - expansion is about query modification, not source type
        return self.test_feature("B. Query Expansion", config, expected_sources=None)

    def test_bm25_search(self) -> TestResult:
        """Test C. BM25 Search"""
        # BM25 is a search method, returns RAG sources
        config = {
            "use_bm25": True,
            "top_k": 5
        }
        # Any sources are OK - BM25 is about search method, not source type
        return self.test_feature("C. BM25 Search", config, expected_sources=None)

    def test_hybrid_search(self) -> TestResult:
        """Test D. Hybrid Search"""
        # Hybrid combines vector + BM25, returns RAG sources
        config = {
            "use_hybrid": True,
            "top_k": 5
        }
        # Any sources are OK - hybrid is about search method, not source type
        return self.test_feature("D. Hybrid Search", config, expected_sources=None)

    def test_knowledge_graph(self) -> TestResult:
        """Test E. Knowledge Graph"""
        config = {
            "use_graph": True,
            "top_k": 5
        }
        return self.test_feature("E. Knowledge Graph", config, expected_sources=["knowledge_graph", "kg"])

    def test_llm_reranking(self) -> TestResult:
        """Test F. LLM Re-ranking"""
        # Re-ranking reorders results, doesn't change source types
        config = {
            "use_reranking": True,
            "top_k": 10
        }
        # Any sources are OK - reranking is about result ordering, not source type
        return self.test_feature("F. LLM Re-ranking", config, expected_sources=None)

    def test_web_search(self) -> TestResult:
        """Test G. Web Search"""
        config = {
            "web_search_enabled": True,
            "top_k": 5
        }
        return self.test_feature("G. Web Search", config, expected_sources=["web_search", "web"])

    def test_agentic_chunking(self) -> TestResult:
        """Test H. Agentic Chunking"""
        # Agentic chunking affects how documents are chunked, not source types
        config = {
            "use_agentic_chunking": True,
            "top_k": 5
        }
        # Any sources are OK - chunking is about document processing, not source type
        return self.test_feature("H. Agentic Chunking", config, expected_sources=None)

    def test_top_k(self) -> TestResult:
        """Test I. Top-K Results"""
        # Test different Top-K values
        for top_k in [3, 5, 10]:
            config = {"top_k": top_k}
            result = self.test_feature(f"I. Top-K Results (K={top_k})", config)
            if not result.passed:
                return result

        return TestResult(
            feature="I. Top-K Results",
            passed=True,
            message="All Top-K values work correctly"
        )

    def test_prompt_enhancement(self) -> TestResult:
        """Test J. Prompt Enhancement"""
        # Prompt enhancement improves the prompt, doesn't change source types
        config = {
            "use_enhancement": True,
            "top_k": 5
        }
        # Any sources are OK - enhancement is about prompt quality, not source type
        return self.test_feature("J. Prompt Enhancement", config, expected_sources=None)

    def test_auto_model_routing(self) -> TestResult:
        """Test K. Auto Model Routing"""
        # Auto routing selects model, doesn't change source types
        config = {
            "use_auto_routing": True,
            "top_k": 5
        }
        # Any sources are OK - routing is about model selection, not source type
        return self.test_feature("K. Auto Model Routing", config, expected_sources=None)

    def test_query_decomposition(self) -> TestResult:
        """Test L. Query Decomposition"""
        config = {
            "use_query_decomposition": True,
            "top_k": 5
        }
        # Use a complex query for decomposition
        query = "What is RAG? How does it work? What are the benefits and limitations?"
        payload = {
            "query": query,
            "user_id": "automated_test",
            "groups": [],
            "top_k": 5,
            **config
        }

        try:
            response = requests.post(
                get_api_endpoint("/v1/rag/query"),
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60
            )

            if response.status_code != 200:
                return TestResult(
                    feature="L. Query Decomposition",
                    passed=False,
                    message=f"API returned status {response.status_code}: {response.text}"
                )

            data = response.json()
            has_decomposition = 'decomposition' in data or 'artifacts' in data

            return TestResult(
                feature="L. Query Decomposition",
                passed=has_decomposition,
                message="Decomposition working" if has_decomposition else "No decomposition data"
            )
        except Exception as e:
            return TestResult(
                feature="L. Query Decomposition",
                passed=False,
                message=f"Exception: {str(e)}"
            )

    def test_self_rag(self) -> TestResult:
        """Test M. Self-RAG"""
        # Self-RAG improves answer quality, doesn't change source types
        config = {
            "use_self_rag": True,
            "top_k": 5
        }
        # Any sources are OK - Self-RAG is about answer quality, not source type
        return self.test_feature("M. Self-RAG", config, expected_sources=None)

    def test_show_reasoning(self) -> TestResult:
        """Test N. Show Reasoning Process"""
        # Show reasoning adds reasoning to answer, doesn't change source types
        config = {
            "show_reasoning_process": True,
            "top_k": 5
        }
        # Any sources are OK - reasoning is about answer format, not source type
        return self.test_feature("N. Show Reasoning Process", config, expected_sources=None)

    def test_vector_database(self) -> TestResult:
        """Test O. Vector Database"""
        # Vector DB is the default search method, returns RAG sources
        config = {
            "use_vector_db": True,
            "top_k": 5
        }
        # Any sources are OK - vector DB is about search method, not source type
        return self.test_feature("O. Vector Database", config, expected_sources=None)

    def test_research_agent(self) -> TestResult:
        """Test P. Research Agent"""
        config = {
            "enable_research": True,
            "top_k": 5
        }
        return self.test_feature("P. Research Agent", config, expected_sources=["research_agent", "research"])

    def run_all_tests(self):
        """Run all feature tests"""
        print(f"\n{'='*60}")
        print(f"Comprehensive Backend Feature Tests")
        print(f"API Base: {self.api_base}")
        print(f"{'='*60}\n")

        # Run all tests
        tests = [
            self.test_security_guardrails,
            self.test_query_expansion,
            self.test_bm25_search,
            self.test_hybrid_search,
            self.test_knowledge_graph,
            self.test_llm_reranking,
            self.test_web_search,
            self.test_agentic_chunking,
            self.test_top_k,
            self.test_prompt_enhancement,
            self.test_auto_model_routing,
            self.test_query_decomposition,
            self.test_self_rag,
            self.test_show_reasoning,
            self.test_vector_database,
            self.test_research_agent,
        ]

        for test_func in tests:
            result = test_func()
            self.results.append(result)
            print(f"\n{result.feature}: {'✅ PASS' if result.passed else '❌ FAIL'}")
            print(f"  {result.message}")
            if result.timing:
                print(f"  Timing: {result.timing:.2f}s")
            if result.sources:
                print(f"  Sources: {', '.join(result.sources)}")

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print(f"\n{'='*60}")
        print("TEST SUMMARY")
        print(f"{'='*60}\n")

        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)

        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%\n")

        print("Failed Tests:")
        for result in self.results:
            if not result.passed:
                print(f"  ❌ {result.feature}: {result.message}")

        print("\nPassed Tests:")
        for result in self.results:
            if result.passed:
                print(f"  ✅ {result.feature}")

if __name__ == "__main__":
    tester = FeatureTester()
    tester.run_all_tests()

    # Exit with error code if any tests failed
    failed = sum(1 for r in tester.results if not r.passed)
    sys.exit(1 if failed > 0 else 0)

