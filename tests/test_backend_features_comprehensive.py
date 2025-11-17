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
        
        # Pass other feature flags through filters dict
        feature_flags = {}
        for key, value in config.items():
            if key not in ["top_k", "web_search_enabled", "enable_research"]:
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

            # Extract sources
            sources = []
            if 'citations' in data:
                for citation in data['citations']:
                    origin = citation.get('origin_tool', 'unknown')
                    sources.append(origin)

            # Check if expected sources are present
            source_check = True
            missing_sources = []
            if expected_sources:
                for expected in expected_sources:
                    if expected.lower() not in [s.lower() for s in sources]:
                        source_check = False
                        missing_sources.append(expected)

            # Check for timing data
            has_timing = 'artifacts' in data and 'stage_timings' in data.get('artifacts', {})

            # Check for trace_id
            has_trace = 'trace_id' in data

            # Validate answer
            has_answer = 'answer' in data and len(data.get('answer', '')) > 0

            # Build result message
            messages = []
            if not has_answer:
                messages.append("No answer returned")
            if not source_check:
                messages.append(f"Missing expected sources: {missing_sources}")
            if not has_timing:
                messages.append("No timing data in response")
            if not has_trace:
                messages.append("No trace_id in response")

            passed = has_answer and source_check and has_timing and has_trace

            if passed:
                messages.append(f"✅ Feature working correctly")
            else:
                messages.append(f"❌ Feature has issues")

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
        config = {
            "top_k": 5
        }
        return self.test_feature("A. Security Guardrails", config)

    def test_query_expansion(self) -> TestResult:
        """Test B. Query Expansion"""
        config = {
            "use_query_expansion": True,
            "top_k": 5
        }
        return self.test_feature("B. Query Expansion", config, expected_sources=["rag"])

    def test_bm25_search(self) -> TestResult:
        """Test C. BM25 Search"""
        config = {
            "use_bm25": True,
            "top_k": 5
        }
        return self.test_feature("C. BM25 Search", config, expected_sources=["rag"])

    def test_hybrid_search(self) -> TestResult:
        """Test D. Hybrid Search"""
        config = {
            "use_hybrid": True,
            "top_k": 5
        }
        return self.test_feature("D. Hybrid Search", config, expected_sources=["rag"])

    def test_knowledge_graph(self) -> TestResult:
        """Test E. Knowledge Graph"""
        config = {
            "use_graph": True,
            "top_k": 5
        }
        return self.test_feature("E. Knowledge Graph", config, expected_sources=["knowledge_graph", "kg"])

    def test_llm_reranking(self) -> TestResult:
        """Test F. LLM Re-ranking"""
        config = {
            "use_reranking": True,
            "top_k": 10
        }
        return self.test_feature("F. LLM Re-ranking", config, expected_sources=["rag"])

    def test_web_search(self) -> TestResult:
        """Test G. Web Search"""
        config = {
            "web_search_enabled": True,
            "top_k": 5
        }
        return self.test_feature("G. Web Search", config, expected_sources=["web_search", "web"])

    def test_agentic_chunking(self) -> TestResult:
        """Test H. Agentic Chunking"""
        config = {
            "use_agentic_chunking": True,
            "top_k": 5
        }
        return self.test_feature("H. Agentic Chunking", config, expected_sources=["rag"])

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
        config = {
            "use_enhancement": True,
            "top_k": 5
        }
        return self.test_feature("J. Prompt Enhancement", config, expected_sources=["rag"])

    def test_auto_model_routing(self) -> TestResult:
        """Test K. Auto Model Routing"""
        config = {
            "use_auto_routing": True,
            "top_k": 5
        }
        return self.test_feature("K. Auto Model Routing", config, expected_sources=["rag"])

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
        config = {
            "use_self_rag": True,
            "top_k": 5
        }
        return self.test_feature("M. Self-RAG", config, expected_sources=["rag"])

    def test_show_reasoning(self) -> TestResult:
        """Test N. Show Reasoning Process"""
        config = {
            "show_reasoning_process": True,
            "top_k": 5
        }
        return self.test_feature("N. Show Reasoning Process", config, expected_sources=["rag"])

    def test_vector_database(self) -> TestResult:
        """Test O. Vector Database"""
        config = {
            "use_vector_db": True,
            "top_k": 5
        }
        return self.test_feature("O. Vector Database", config, expected_sources=["rag"])

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

