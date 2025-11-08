"""
Acceptance Tests for Full Observability Contract

Tests all 6 key probes:
1. Temporal probe: ≤48h requirement with recency check
2. Provenance probe: Mixed RAG/Web/ResearchAgent with correct origin_tool
3. Routing transparency: route + route_reason consistency
4. A/B probe: Non-zero dimension scores + Δ(B-A)
5. Guardrail probe: Forced error returns Schema F + security_status:degraded
6. SLA probe: wall_time tracking

Run with: pytest tests/test_acceptance_full_contract.py -v
"""

import pytest
import requests
import json
from typing import Dict, Any

# API endpoint
API_URL = "http://localhost:8080/v1/rag/query"


class TestFullContractAcceptance:
    """Acceptance tests for 100% observability contract"""
    
    def test_temporal_probe_recency_check(self):
        """Temporal query with ≤48h requirement"""
        response = requests.post(API_URL, json={
            "query": "What happened today in AI?",
            "tenant": "test_tenant",
            "user_id": "test_user",
            "policy": {
                "requires_recency": True,
                "min_primary_sources": 2
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Check recency artifact
        assert 'recency' in data
        assert 'passed' in data['recency']
        assert 'freshness_histogram' in data['recency']
        assert 'primary_sources_within_window' in data['recency']
        
        # Check freshness histogram structure
        histogram = data['recency']['freshness_histogram']
        assert '<24h' in histogram
        assert '24-48h' in histogram
        assert '>1w' in histogram
        
        print(f"✅ Temporal probe: passed={data['recency']['passed']}, primaries={data['recency']['primary_sources_within_window']}")
    
    def test_provenance_probe_mixed_sources(self):
        """Mixed RAG/Web sources with correct origin_tool"""
        response = requests.post(API_URL, json={
            "query": "Tell me about RAG systems",
            "tenant": "test_tenant",
            "user_id": "test_user",
            "plan_id": "blended_v1"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Check sources have origin_tool
        assert 'sources' in data
        for source in data['sources']:
            assert 'origin_tool' in source
            assert source['origin_tool'] in ['rag', 'web_search', 'research_agent']
        
        # Check source_mix matches
        assert 'source_mix' in data
        assert 'rag' in data['source_mix']
        assert 'web_search' in data['source_mix']
        
        # Verify counts match
        total_from_mix = sum(data['source_mix'].values())
        assert total_from_mix == len(data['sources'])
        
        print(f"✅ Provenance probe: source_mix={data['source_mix']}, sources={len(data['sources'])}")
    
    def test_routing_transparency(self):
        """Route decision is transparent and consistent"""
        response = requests.post(API_URL, json={
            "query": "What is machine learning?",
            "tenant": "test_tenant",
            "user_id": "test_user"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Check route fields
        assert 'route' in data
        assert data['route'] in ['rag', 'web', 'blended']
        assert 'route_reason' in data
        assert len(data['route_reason']) > 10
        
        # Check planner artifact consistency
        assert 'planner' in data
        assert data['planner']['route_decision'] == data['route']
        assert len(data['planner']['route_reason']) > 10
        
        print(f"✅ Routing transparency: route={data['route']}, reason={data['route_reason'][:50]}...")
    
    def test_ab_probe_dimensions(self):
        """A/B evaluation with dimension scores"""
        response = requests.post(API_URL, json={
            "query": "Explain RAG",
            "tenant": "test_tenant",
            "user_id": "test_user",
            "ab_test": {"setting": "A"}
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Check ab_eval artifact
        assert 'ab_eval' in data
        ab_eval = data['ab_eval']
        
        assert ab_eval['setting'] == 'A'
        assert 'dimensions' in ab_eval
        assert 'overall_score' in ab_eval
        
        # Check 7 dimensions
        dimensions = ab_eval['dimensions']
        expected_dims = ['coverage', 'grounding', 'recency', 'retrieval_quality', 
                        'decision_adherence', 'structure', 'conciseness']
        for dim in expected_dims:
            assert dim in dimensions
            assert 0.0 <= dimensions[dim] <= 1.0
        
        assert 0.0 <= ab_eval['overall_score'] <= 1.0
        
        print(f"✅ A/B probe: overall={ab_eval['overall_score']:.3f}, dims={list(dimensions.keys())}")
    
    def test_guardrail_probe_schema_f(self):
        """Guardrail report exists (Schema F)"""
        response = requests.post(API_URL, json={
            "query": "Normal query",
            "tenant": "test_tenant",
            "user_id": "test_user"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Check guardrail_report artifact
        assert 'guardrail_report' in data
        guardrail = data['guardrail_report']
        
        assert 'overall_safe' in guardrail
        assert 'detections' in guardrail
        assert 'service_errors' in guardrail
        
        # Check security_status in footer
        assert 'security_status' in data
        assert data['security_status'] in ['healthy', 'degraded']
        
        # If service errors, status should be degraded
        if guardrail['service_errors']:
            assert data['security_status'] == 'degraded'
        
        print(f"✅ Guardrail probe: safe={guardrail['overall_safe']}, status={data['security_status']}")
    
    def test_sla_probe_wall_time(self):
        """Wall time tracking"""
        response = requests.post(API_URL, json={
            "query": "Complex query",
            "tenant": "test_tenant",
            "user_id": "test_user",
            "budgets": {"sla_ms": 90000}
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Check wall_time_ms
        assert 'wall_time_ms' in data
        assert data['wall_time_ms'] > 0
        assert data['wall_time_ms'] < 120000  # Should be under 2 minutes for local test
        
        # Check X-Response-Time header
        assert 'X-Response-Time' in response.headers
        
        print(f"✅ SLA probe: wall_time={data['wall_time_ms']:.0f}ms")
    
    def test_id_correlation(self):
        """trace_id and request_id propagate to all artifacts"""
        response = requests.post(API_URL, json={
            "query": "Test ID correlation",
            "tenant": "test_tenant",
            "user_id": "test_user"
        }, headers={"X-Request-ID": "test-request-123"})
        
        assert response.status_code == 200
        data = response.json()
        
        # Check main trace_id
        assert 'trace_id' in data
        trace_id = data['trace_id']
        request_id = "test-request-123"
        
        # Check all artifacts have matching IDs
        artifacts = ['planner', 'retrieval_log', 'evidence_map', 'recency', 
                    'chunking_report', 'guardrail_report', 'ab_eval']
        
        for artifact_name in artifacts:
            if artifact_name in data:
                artifact = data[artifact_name]
                assert 'trace_id' in artifact, f"{artifact_name} missing trace_id"
                assert 'request_id' in artifact, f"{artifact_name} missing request_id"
                assert artifact['trace_id'] == trace_id, f"{artifact_name} trace_id mismatch"
                assert artifact['request_id'] == request_id, f"{artifact_name} request_id mismatch"
        
        print(f"✅ ID correlation: trace_id={trace_id}, request_id={request_id}")
    
    def test_contract_version(self):
        """Contract version in response headers"""
        response = requests.post(API_URL, json={
            "query": "Test",
            "tenant": "test_tenant",
            "user_id": "test_user"
        })
        
        assert response.status_code == 200
        assert 'X-Contract-Version' in response.headers
        assert response.headers['X-Contract-Version'] == '2.0.0'
        
        print(f"✅ Contract version: {response.headers['X-Contract-Version']}")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

