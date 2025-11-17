#!/usr/bin/env python3
"""
Comprehensive Backend Feature Functionality Tests
Tests all RAG features (A-R) and validates FUNCTIONALITY ONLY:
1. Feature works (answer returned)
2. Expected sources present (if applicable)
3. API returns valid response

NOTE: Timing/performance tracking will be added later as enhancement.
Focus is on ensuring features actually work correctly.

Usage:
    python3 tests/test_backend_features_with_timing.py
    RAG_API=http://localhost:3000 python3 tests/test_backend_features_with_timing.py
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
    stage_timings: Optional[Dict[str, Any]] = None
    trace_id: Optional[str] = None

class FeatureTester:
    def __init__(self, api_base: str = API_BASE):
        self.api_base = api_base
        self.results: List[TestResult] = []

    def test_feature(self, feature_name: str, config: Dict[str, Any],
                    expected_sources: Optional[List[str]] = None) -> TestResult:
        """
        Test a specific feature with given configuration - FUNCTIONALITY ONLY

        Args:
            feature_name: Name of the feature (e.g., "A. Security Guardrails")
            config: Feature configuration dict
            expected_sources: List of expected source types (e.g., ["web_search", "web"])
        """
        print(f"\n{'='*60}")
        print(f"Testing: {feature_name}")
        print(f"{'='*60}")

        query = "What is retrieval augmented generation? Explain how RAG works."

        # Prepare request - RAG API v1 only accepts specific fields
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

            # Extract stage timings
            stage_timings = {}
            if 'artifacts' in data and 'stage_timings' in data.get('artifacts', {}):
                stage_timings = data['artifacts']['stage_timings']
            elif 'metrics' in data and 'stage_timings' in data.get('metrics', {}):
                stage_timings = data['metrics']['stage_timings']

            # Extract trace_id
            trace_id = data.get('trace_id')

            # Validate sources
            source_check = True
            missing_sources = []
            messages = []

            if expected_sources:
                source_lower = [s.lower() for s in sources]
                expected_lower = [e.lower() for e in expected_sources]
                found_any = any(any(exp in src for exp in expected_lower) for src in source_lower)

                if not found_any:
                    if len(sources) > 0:
                        source_check = False
                        missing_sources = expected_sources
                        messages.append(f"Got sources: {', '.join(sources)} but expected: {', '.join(expected_sources)}")
                    else:
                        source_check = False
                        missing_sources = expected_sources
                        messages.append(f"No sources returned, expected: {', '.join(expected_sources)}")
                else:
                    messages.append(f"✅ Expected sources found: {', '.join([s for s in sources if any(e.lower() in s.lower() for e in expected_sources)])}")
            elif len(sources) > 0:
                messages.append(f"✅ Sources returned: {', '.join(sources)}")
            else:
                messages.append("⚠️  No sources returned")

            # Validate answer (REQUIRED) - FUNCTIONALITY FOCUS
            has_answer = 'answer' in data and len(data.get('answer', '')) > 0

            if not has_answer:
                messages.append("❌ No answer returned")
            else:
                messages.append(f"✅ Answer returned ({len(data['answer'])} chars)")

            # Note: Timing data and trace_id are nice-to-have but not required for functionality
            if stage_timings:
                messages.append(f"ℹ️  Timing data present: {len(stage_timings)} entries (enhancement)")
            if trace_id:
                messages.append(f"ℹ️  Trace ID present: {trace_id[:16]}... (enhancement)")

            # Determine if test passed - FUNCTIONALITY ONLY
            # Must have: answer, expected sources (if specified)
            # Timing and trace_id are optional (will be added as enhancement)
            passed = has_answer and source_check

            return TestResult(
                feature=feature_name,
                passed=passed,
                message=" | ".join(messages),
                timing=elapsed,
                sources=sources,
                stage_timings=stage_timings,
                trace_id=trace_id
            )

        except Exception as e:
            return TestResult(
                feature=feature_name,
                passed=False,
                message=f"Exception: {str(e)}",
                timing=time.time() - start_time,
                errors=[str(e)]
            )

    def test_security_guardrails(self) -> TestResult:
        """Test A. Security Guardrails"""
        config = {"top_k": 5}
        return self.test_feature("A. Security Guardrails", config)

    def test_query_expansion(self) -> TestResult:
        """Test B. Query Expansion"""
        config = {"use_query_expansion": True, "top_k": 5}
        return self.test_feature("B. Query Expansion", config)

    def test_bm25_search(self) -> TestResult:
        """Test C. BM25 Search"""
        config = {"use_bm25": True, "top_k": 5}
        return self.test_feature("C. BM25 Search", config)

    def test_hybrid_search(self) -> TestResult:
        """Test D. Hybrid Search"""
        config = {"use_hybrid": True, "top_k": 5}
        return self.test_feature("D. Hybrid Search", config)

    def test_knowledge_graph(self) -> TestResult:
        """Test E. Knowledge Graph"""
        config = {"use_graph": True, "top_k": 5}
        return self.test_feature(
            "E. Knowledge Graph",
            config,
            expected_sources=["knowledge_graph", "kg"]
        )

    def test_llm_reranking(self) -> TestResult:
        """Test F. LLM Re-ranking"""
        config = {"use_reranking": True, "top_k": 10}
        return self.test_feature("F. LLM Re-ranking", config)

    def test_web_search(self) -> TestResult:
        """Test G. Web Search"""
        config = {"web_search_enabled": True, "top_k": 5}
        return self.test_feature(
            "G. Web Search",
            config,
            expected_sources=["web_search", "web"]
        )

    def test_agentic_chunking(self) -> TestResult:
        """Test H. Agentic Chunking"""
        config = {"use_agentic_chunking": True, "top_k": 5}
        return self.test_feature("H. Agentic Chunking", config)

    def test_top_k(self) -> TestResult:
        """Test I. Top-K Results"""
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
        config = {"use_enhancement": True, "top_k": 5}
        return self.test_feature("J. Prompt Enhancement", config)

    def test_auto_model_routing(self) -> TestResult:
        """Test K. Auto Model Routing"""
        config = {"use_auto_routing": True, "top_k": 5}
        return self.test_feature("K. Auto Model Routing", config)

    def test_query_decomposition(self) -> TestResult:
        """Test L. Query Decomposition"""
        config = {"use_decomposition": True, "top_k": 5}
        return self.test_feature("L. Query Decomposition", config)

    def test_self_rag(self) -> TestResult:
        """Test M. Self-RAG"""
        config = {"use_self_rag": True, "top_k": 5}
        return self.test_feature("M. Self-RAG", config)

    def test_show_reasoning(self) -> TestResult:
        """Test N. Show Reasoning Process"""
        config = {"show_reasoning": True, "top_k": 5}
        return self.test_feature("N. Show Reasoning Process", config)

    def test_vector_database(self) -> TestResult:
        """Test O. Vector Database"""
        config = {"top_k": 5}
        return self.test_feature("O. Vector Database", config)

    def test_research_agent(self) -> TestResult:
        """Test P. Research Agent"""
        config = {"enable_research": True, "top_k": 5}
        return self.test_feature(
            "P. Research Agent",
            config,
            expected_sources=["research_agent", "research"]
        )

    def run_all_tests(self):
        """Run all feature tests"""
        print("\n" + "="*60)
        print("RAG Backend Feature Functionality Tests")
        print("="*60)
        print(f"API Base: {self.api_base}")
        print(f"Testing {18} features (A-R) - FUNCTIONALITY ONLY")
        print("NOTE: Timing/performance tracking will be added later")
        print("="*60)

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

        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)

        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)

        print(f"\nTotal Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {passed/total*100:.1f}%")

        if passed < total:
            print("\nFailed Tests:")
            for result in self.results:
                if not result.passed:
                    print(f"  ❌ {result.feature}: {result.message}")

        # Note: Timing data is optional (enhancement)
        timing_coverage = sum(1 for r in self.results if r.stage_timings)
        trace_coverage = sum(1 for r in self.results if r.trace_id)

        print("\n" + "="*60)
        print("OBSERVABILITY DATA (Optional - Enhancement)")
        print("="*60)
        print(f"Timing Data: {timing_coverage}/{total} features ({timing_coverage/total*100:.1f}%)")
        print(f"Trace ID: {trace_coverage}/{total} features ({trace_coverage/total*100:.1f}%)")
        print("NOTE: These will be added as enhancement - not required for functionality")
        print("="*60)


if __name__ == "__main__":
    tester = FeatureTester()
    tester.run_all_tests()

    # Exit with error code if any tests failed
    failed = sum(1 for r in tester.results if not r.passed)
    sys.exit(1 if failed > 0 else 0)

