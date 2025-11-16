#!/usr/bin/env python3
"""
Automated Backend API Tests
Tests the RAG API v1 directly (bypassing nginx for now)
"""

import os
import sys
import json
import time
import requests
from typing import Dict, Any

# Configuration
# Note: rag-api-v1 is on port 8080 internally, or accessible via nginx on port 3000
# Default to port 3000 (via nginx) for same-origin routing
API_BASE = os.environ.get('RAG_API', 'http://16.146.148.184:3000')

# Helper to get correct endpoint path
def get_api_endpoint(path: str) -> str:
    """Get correct API endpoint path based on API_BASE"""
    # If accessing via nginx (port 3000), use /api prefix
    if ":3000" in API_BASE:
        return f"{API_BASE}/api{path}"
    # Direct access (port 8080) uses path as-is
    return f"{API_BASE}{path}"
RESULTS = {
    'passed': 0,
    'failed': 0,
    'tests': []
}

def test_result(name: str, passed: bool, message: str = ''):
    """Record test result"""
    RESULTS['tests'].append({
        'name': name,
        'passed': passed,
        'message': message
    })
    if passed:
        RESULTS['passed'] += 1
        print(f"✅ {name}: PASS")
    else:
        RESULTS['failed'] += 1
        print(f"❌ {name}: FAIL - {message}")
    if message and passed:
        print(f"   {message}")

def test_health_endpoints():
    """Test health endpoints"""
    print("\n" + "="*50)
    print("TEST 1: Health Endpoints")
    print("="*50)

    # Test /live
    try:
        resp = requests.get(f"{API_BASE}/live", timeout=5)
        if resp.status_code == 200 and 'status' in resp.json():
            test_result("Health /live", True, f"Status: {resp.json().get('status')}")
        else:
            test_result("Health /live", False, f"HTTP {resp.status_code}")
    except Exception as e:
        test_result("Health /live", False, str(e))

    # Test /ready
    try:
        resp = requests.get(f"{API_BASE}/ready", timeout=5)
        if resp.status_code == 200 and 'status' in resp.json():
            test_result("Health /ready", True, f"Status: {resp.json().get('status')}")
        else:
            test_result("Health /ready", False, f"HTTP {resp.status_code}")
    except Exception as e:
        test_result("Health /ready", False, str(e))

    # Test /health
    try:
        resp = requests.get(f"{API_BASE}/health", timeout=5)
        if resp.status_code == 200 and 'status' in resp.json():
            test_result("Health /health", True, f"Status: {resp.json().get('status')}")
        else:
            test_result("Health /health", False, f"HTTP {resp.status_code}")
    except Exception as e:
        test_result("Health /health", False, str(e))

def test_api_query():
    """Test RAG query endpoint"""
    print("\n" + "="*50)
    print("TEST 2: RAG Query API")
    print("="*50)

    payload = {
        "query": "What is RAG?",
        "user_id": "automated_test",
        "groups": [],
        "top_k": 8
    }

    try:
        resp = requests.post(
            get_api_endpoint("/v1/rag/query"),
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=15
        )

        if resp.status_code != 200:
            test_result("API Query", False, f"HTTP {resp.status_code}")
            return

        data = resp.json()

        # Check response structure
        required_fields = ['answer', 'citations', 'artifacts', 'trace_id', 'request_id', 'security_status', 'contract_version']
        missing = [f for f in required_fields if f not in data]

        if missing:
            test_result("API Query", False, f"Missing fields: {missing}")
            return

        test_result("API Query", True, f"Response contains all required fields")

        # Check answer
        if data.get('answer'):
            test_result("API Query - Answer", True, f"Length: {len(data['answer'])} chars")
        else:
            test_result("API Query - Answer", False, "Empty answer")

        # Check citations
        citations = data.get('citations', [])
        test_result("API Query - Citations", len(citations) > 0, f"Count: {len(citations)}")

        # Check trace_id
        trace_id = data.get('trace_id')
        test_result("API Query - Trace ID", bool(trace_id), f"Trace: {trace_id}")

        # Check security_status
        security = data.get('security_status')
        test_result("API Query - Security", security in ['ok', 'degraded', 'blocked'], f"Status: {security}")

        # Check contract_version
        version = data.get('contract_version')
        test_result("API Query - Contract", bool(version), f"Version: {version}")

    except Exception as e:
        test_result("API Query", False, str(e))

def test_golden_queries():
    """Test three golden queries"""
    print("\n" + "="*50)
    print("TEST 3: Golden Queries")
    print("="*50)

    queries = [
        ("Navigational", "Where is the Phase 2 quickstart?"),
        ("Policy", "How to run acceptance probes?"),
        ("Temporal", "What changed in Phase B today?")
    ]

    for name, query in queries:
        try:
            resp = requests.post(
                get_api_endpoint("/v1/rag/query"),
                json={"query": query, "user_id": "test", "groups": []},
                timeout=15
            )

            if resp.status_code == 200:
                data = resp.json()
                answer = data.get('answer', '')
                citations = len(data.get('citations', []))

                if answer and citations > 0:
                    test_result(f"Golden Query - {name}", True, f"Answer: {len(answer)} chars, Citations: {citations}")
                else:
                    test_result(f"Golden Query - {name}", False, "Empty answer or no citations")
            else:
                test_result(f"Golden Query - {name}", False, f"HTTP {resp.status_code}")
        except Exception as e:
            test_result(f"Golden Query - {name}", False, str(e))

def test_metrics():
    """Test Prometheus metrics endpoint"""
    print("\n" + "="*50)
    print("TEST 4: Prometheus Metrics")
    print("="*50)

    try:
        resp = requests.get(f"{API_BASE}/metrics", timeout=5)
        if resp.status_code == 200:
            lines = resp.text.split('\n')
            metric_lines = [l for l in lines if l and not l.startswith('#')]
            test_result("Metrics Endpoint", True, f"Exposed ~{len(metric_lines)} metrics")
        else:
            test_result("Metrics Endpoint", False, f"HTTP {resp.status_code}")
    except Exception as e:
        test_result("Metrics Endpoint", False, str(e))

def test_performance():
    """Test performance"""
    print("\n" + "="*50)
    print("TEST 5: Performance")
    print("="*50)

    # Test API response time
    try:
        start = time.time()
        resp = requests.post(
            get_api_endpoint("/v1/rag/query"),
            json={"query": "Quick test", "user_id": "perf", "groups": []},
            timeout=15
        )
        elapsed = time.time() - start

        if resp.status_code == 200:
            if elapsed < 10:
                test_result("API Response Time", True, f"{elapsed:.2f}s < 10s")
            else:
                test_result("API Response Time", False, f"{elapsed:.2f}s >= 10s (slow)")
        else:
            test_result("API Response Time", False, f"HTTP {resp.status_code}")
    except Exception as e:
        test_result("API Response Time", False, str(e))

def test_opentelemetry():
    """Test OpenTelemetry header forwarding"""
    print("\n" + "="*50)
    print("TEST 6: OpenTelemetry")
    print("="*50)

    try:
        resp = requests.post(
            get_api_endpoint("/v1/rag/query"),
            json={"query": "Test trace", "user_id": "trace_test", "groups": []},
            headers={
                'Content-Type': 'application/json',
                'traceparent': '00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01'
            },
            timeout=15
        )

        if resp.status_code == 200:
            data = resp.json()
            trace_id = data.get('trace_id')
            if trace_id:
                test_result("OpenTelemetry Tracing", True, f"Trace ID: {trace_id}")
            else:
                test_result("OpenTelemetry Tracing", False, "No trace_id in response")
        else:
            test_result("OpenTelemetry Tracing", False, f"HTTP {resp.status_code}")
    except Exception as e:
        test_result("OpenTelemetry Tracing", False, str(e))

def print_summary():
    """Print test summary"""
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)

    total = RESULTS['passed'] + RESULTS['failed']
    passed_pct = (RESULTS['passed'] / total * 100) if total > 0 else 0

    print(f"\nTotal Tests: {total}")
    print(f"✅ Passed: {RESULTS['passed']} ({passed_pct:.1f}%)")
    print(f"❌ Failed: {RESULTS['failed']}")
    print("")

    if RESULTS['failed'] == 0:
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("⚠️  SOME TESTS FAILED")
        print("\nFailed tests:")
        for test in RESULTS['tests']:
            if not test['passed']:
                print(f"  - {test['name']}: {test['message']}")
        return 1

def main():
    """Run all tests"""
    print("="*50)
    print("RAG Lab - Automated Backend Tests")
    print(f"Target: {API_BASE}")
    print("="*50)

    # Run tests
    test_health_endpoints()
    test_api_query()
    test_golden_queries()
    test_metrics()
    test_performance()
    test_opentelemetry()

    # Print summary and exit
    exit_code = print_summary()
    sys.exit(exit_code)

if __name__ == '__main__':
    main()

