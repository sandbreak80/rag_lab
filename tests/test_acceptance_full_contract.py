"""
Acceptance Tests for Full Observability Contract (v1 API)

Tests 8 key probes:
1. Liveness probe: /live always returns 200
2. Readiness probe: /ready checks dependencies
3. Basic RAG query: Returns answer + citations
4. Temporal probe: Recency gate evaluation
5. Provenance probe: origin_tool immutability
6. A/B probe: Dimension scores (when enabled)
7. Guardrail probe: Schema F on degradation
8. Metrics probe: Prometheus endpoint

Run with: export RAG_API=http://localhost:8080 && pytest tests/test_acceptance_full_contract.py -v
"""

import pytest
import requests
import json
import os
from typing import Dict, Any

# API endpoint - read from environment or default to localhost
API_BASE_URL = os.getenv("RAG_API", "http://localhost:8080")


class TestFullContractAcceptance:
    """Acceptance tests for /v1/rag/query endpoint"""

    def test_1_liveness_probe(self):
        """Liveness probe always returns 200"""
        response = requests.get(f"{API_BASE_URL}/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
        assert "service" in data
        print(f"✅ Probe 1/8: Liveness - service={data['service']}")

    def test_2_readiness_probe(self):
        """Readiness probe checks dependencies"""
        response = requests.get(f"{API_BASE_URL}/ready")
        # Should return 200 or 503
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        print(f"✅ Probe 2/8: Readiness - status={data['status']}")

    def test_3_basic_rag_query(self):
        """Basic RAG query returns answer + citations"""
        response = requests.post(f"{API_BASE_URL}/v1/rag/query", json={
            "query": "What is RAG?",
            "user_id": "test_user",
            "groups": []
        })

        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert "answer" in data
        assert "citations" in data
        assert "artifacts" in data
        assert "metrics" in data
        assert "security_status" in data
        assert "request_id" in data
        assert "trace_id" in data
        assert "contract_version" in data

        print(f"✅ Probe 3/8: Basic query - citations={len(data['citations'])}, status={data['security_status']}")

    def test_4_temporal_probe_recency(self):
        """Temporal query with recency evaluation"""
        response = requests.post(f"{API_BASE_URL}/v1/rag/query", json={
            "query": "What happened today in AI?",
            "user_id": "test_user",
            "groups": []
        })

        assert response.status_code == 200
        data = response.json()

        # Check recency artifact in artifacts
        assert "artifacts" in data
        assert "recency" in data["artifacts"]

        recency = data["artifacts"]["recency"]
        assert "passed" in recency
        assert "freshness_histogram" in recency
        assert "primary_sources_within_window" in recency
        assert "query_is_temporal" in recency

        histogram = recency["freshness_histogram"]
        assert "<24h" in histogram
        assert "24-48h" in histogram

        print(f"✅ Probe 4/8: Temporal - passed={recency['passed']}, temporal={recency['query_is_temporal']}, primaries={recency['primary_sources_within_window']}")

    def test_5_provenance_probe_origin_tool(self):
        """Provenance: origin_tool in citations"""
        response = requests.post(f"{API_BASE_URL}/v1/rag/query", json={
            "query": "Tell me about retrieval augmented generation",
            "user_id": "test_user",
            "groups": []
        })

        assert response.status_code == 200
        data = response.json()

        # Check citations have origin_tool
        assert "citations" in data
        for citation in data["citations"]:
            assert "origin_tool" in citation
            assert citation["origin_tool"] in ["rag", "web_search", "research_agent"]
            assert "doc_id" in citation
            assert "chunk_id" in citation

        # Check evidence_map artifact
        assert "evidence_map" in data["artifacts"]
        evidence_map = data["artifacts"]["evidence_map"]
        assert "provenance_immutable" in evidence_map

        print(f"✅ Probe 5/8: Provenance - citations={len(data['citations'])}, immutable={evidence_map['provenance_immutable']}")

    def test_6_ab_probe_dimensions(self):
        """A/B evaluation with dimension scores"""
        response = requests.post(f"{API_BASE_URL}/v1/rag/query", json={
            "query": "Explain machine learning",
            "user_id": "test_user",
            "groups": [],
            "ab_bucket": "A"
        })

        assert response.status_code == 200
        data = response.json()

        # With AB_TEST enabled or ab_bucket set, we should get ab_eval
        # For now with mocks, it may not be present
        # Check if present and validate structure
        if "ab_eval" in data["artifacts"]:
            ab_eval = data["artifacts"]["ab_eval"]
            assert "dimensions" in ab_eval
            assert "overall_score" in ab_eval
            assert "passed_dimensions" in ab_eval
            assert "failed_dimensions" in ab_eval

            # Check 7 dimensions
            expected_dims = ["coverage", "grounding", "recency", "retrieval_quality",
                           "decision_adherence", "structure", "conciseness"]
            for dim in expected_dims:
                assert dim in ab_eval["dimensions"]

            print(f"✅ Probe 6/8: A/B - overall={ab_eval['overall_score']:.3f}, passed={len(ab_eval['passed_dimensions'])}/7")
        else:
            print(f"⚠️  Probe 6/8: A/B - Skipped (RAG_AB_TEST=0)")

    def test_7_guardrail_probe_degradation(self):
        """Guardrail handling on degradation"""
        response = requests.post(f"{API_BASE_URL}/v1/rag/query", json={
            "query": "Test query",
            "user_id": "test_user",
            "groups": []
        })

        assert response.status_code == 200
        data = response.json()

        # Check security_status
        assert "security_status" in data
        assert data["security_status"] in ["ok", "degraded", "blocked"]

        # If guardrail_report exists, check structure
        if "guardrail_report" in data["artifacts"]:
            guardrail = data["artifacts"]["guardrail_report"]
            assert "detections" in guardrail
            assert "service_errors" in guardrail
            assert "overall_safe" in guardrail

        print(f"✅ Probe 7/8: Guardrails - status={data['security_status']}")

    def test_8_metrics_probe(self):
        """Prometheus metrics endpoint"""
        response = requests.get(f"{API_BASE_URL}/metrics")
        assert response.status_code == 200

        # Check for our key metrics
        metrics_text = response.text
        assert "rag_requests_total" in metrics_text
        assert "rag_request_duration_seconds" in metrics_text

        print(f"✅ Probe 8/8: Metrics - endpoint active, {len(metrics_text.splitlines())} lines")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
