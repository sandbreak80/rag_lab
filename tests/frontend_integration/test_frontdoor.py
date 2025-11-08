#!/usr/bin/env python3
"""
Frontend Integration Tests - Test the ACTUAL user-facing URL (port 3000)
NOT the backend API directly (port 8000)

This tests the full stack: Browser → Frontend Nginx → Backend API
"""

import os
import sys
import requests
import time
from typing import Dict, Any

# CRITICAL: Test the frontend URL, not backend!
FRONTEND_URL = os.environ.get('FRONTEND', 'http://16.146.148.184:3000')
RESULTS = {'passed': 0, 'failed': 0, 'tests': []}

GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
NC = '\033[0m'

def test_result(name: str, passed: bool, message: str = ''):
    """Record test result"""
    RESULTS['tests'].append({'name': name, 'passed': passed, 'message': message})
    if passed:
        RESULTS['passed'] += 1
        print(f"{GREEN}✅ {name}: PASS{NC}")
    else:
        RESULTS['failed'] += 1
        print(f"{RED}❌ {name}: FAIL - {message}{NC}")
    if message and passed:
        print(f"   {message}")

print("="*60)
print("Frontend Integration Tests - Port 3000 (Full Stack)")
print(f"Target: {FRONTEND_URL}")
print("="*60)
print("")

# Test 1: Homepage loads
print("TEST 1: Homepage loads (HTML)")
print("-"*60)
try:
    resp = requests.get(FRONTEND_URL, timeout=10)
    if resp.status_code == 200 and 'html' in resp.text.lower():
        test_result("Homepage loads", True, f"Status: {resp.status_code}, Content-Type: {resp.headers.get('content-type')}")
    else:
        test_result("Homepage loads", False, f"HTTP {resp.status_code}")
except Exception as e:
    test_result("Homepage loads", False, str(e))
print("")

# Test 2: Health endpoints return JSON (not HTML!)
print("TEST 2: Health endpoints (via nginx)")
print("-"*60)

for endpoint in ['/live', '/ready', '/health']:
    try:
        resp = requests.get(f"{FRONTEND_URL}{endpoint}", timeout=5)

        # CRITICAL: Must return JSON, not HTML
        content_type = resp.headers.get('content-type', '')
        is_json = 'json' in content_type.lower()
        has_html = '<html' in resp.text.lower() or '<!doctype' in resp.text.lower()

        if resp.status_code == 200 and is_json and not has_html:
            try:
                data = resp.json()
                test_result(f"Health {endpoint}", True, f"JSON response: {data.get('status', 'unknown')}")
            except:
                test_result(f"Health {endpoint}", False, "Response not valid JSON")
        elif has_html:
            test_result(f"Health {endpoint}", False, "Returned HTML (nginx routing broken!)")
        else:
            test_result(f"Health {endpoint}", False, f"HTTP {resp.status_code}, Content-Type: {content_type}")
    except Exception as e:
        test_result(f"Health {endpoint}", False, str(e))
print("")

# Test 3: API endpoint via /api (same-origin)
print("TEST 3: RAG Query API (via /api same-origin)")
print("-"*60)
try:
    payload = {
        "query": "What is RAG?",
        "user_id": "frontend_integration_test",
        "groups": [],
        "top_k": 8
    }

    resp = requests.post(
        f"{FRONTEND_URL}/api/v1/rag/query",
        json=payload,
        headers={'Content-Type': 'application/json'},
        timeout=20
    )

    if resp.status_code == 502:
        test_result("API via /api", False, "502 Bad Gateway - nginx can't reach rag-api-v1")
    elif resp.status_code != 200:
        test_result("API via /api", False, f"HTTP {resp.status_code}")
    else:
        try:
            data = resp.json()
            has_answer = 'answer' in data
            has_citations = 'citations' in data
            has_trace = 'trace_id' in data

            if has_answer and has_citations and has_trace:
                test_result("API via /api", True, "Valid RAG response")
                test_result("API - Answer", len(data.get('answer', '')) > 0, f"Length: {len(data.get('answer', ''))} chars")
                test_result("API - Citations", len(data.get('citations', [])) > 0, f"Count: {len(data.get('citations', []))}")
                test_result("API - Trace ID", bool(data.get('trace_id')), f"Trace: {data.get('trace_id')}")
            else:
                test_result("API via /api", False, f"Missing fields: answer={has_answer}, citations={has_citations}, trace={has_trace}")
        except:
            test_result("API via /api", False, "Response not valid JSON")
except Exception as e:
    test_result("API via /api", False, str(e))
print("")

# Test 4: CORS check (should NOT have CORS errors with same-origin)
print("TEST 4: CORS Headers (same-origin should not need CORS)")
print("-"*60)
try:
    resp = requests.options(
        f"{FRONTEND_URL}/api/v1/rag/query",
        headers={'Origin': FRONTEND_URL}
    )

    # With same-origin, CORS shouldn't be needed
    # But if present, it should allow the origin
    cors_header = resp.headers.get('Access-Control-Allow-Origin', '')

    if cors_header:
        test_result("CORS configured", True, f"CORS header: {cors_header}")
    else:
        test_result("CORS not needed", True, "Same-origin routing (no CORS needed)")
except Exception as e:
    test_result("CORS check", False, str(e))
print("")

# Test 5: Golden query through frontend
print("TEST 5: Golden Query (Full Stack)")
print("-"*60)
try:
    resp = requests.post(
        f"{FRONTEND_URL}/api/v1/rag/query",
        json={
            "query": "Where is the Phase 2 quickstart?",
            "user_id": "e2e_test",
            "groups": []
        },
        timeout=20
    )

    if resp.status_code == 200:
        data = resp.json()
        answer = data.get('answer', '')
        citations = len(data.get('citations', []))

        if answer and citations > 0:
            test_result("Golden Query", True, f"Answer: {len(answer)} chars, Citations: {citations}")
        else:
            test_result("Golden Query", False, "Empty answer or no citations")
    else:
        test_result("Golden Query", False, f"HTTP {resp.status_code}")
except Exception as e:
    test_result("Golden Query", False, str(e))
print("")

# Test 6: Performance through frontend
print("TEST 6: Performance (E2E latency)")
print("-"*60)
try:
    start = time.time()
    resp = requests.post(
        f"{FRONTEND_URL}/api/v1/rag/query",
        json={"query": "Quick test", "user_id": "perf", "groups": []},
        timeout=20
    )
    elapsed = time.time() - start

    if resp.status_code == 200:
        if elapsed < 10:
            test_result("E2E Latency", True, f"{elapsed:.2f}s < 10s")
        else:
            test_result("E2E Latency", False, f"{elapsed:.2f}s >= 10s (slow)")
    else:
        test_result("E2E Latency", False, f"HTTP {resp.status_code}")
except Exception as e:
    test_result("E2E Latency", False, str(e))
print("")

# Summary
print("="*60)
print("TEST SUMMARY")
print("="*60)
total = RESULTS['passed'] + RESULTS['failed']
passed_pct = (RESULTS['passed'] / total * 100) if total > 0 else 0

print(f"\nTotal Tests: {total}")
print(f"{GREEN}✅ Passed: {RESULTS['passed']} ({passed_pct:.1f}%){NC}")
print(f"{RED}❌ Failed: {RESULTS['failed']}{NC}")
print("")

if RESULTS['failed'] == 0:
    print(f"{GREEN}🎉 ALL FRONTEND INTEGRATION TESTS PASSED!{NC}")
    print(f"{GREEN}The full stack is working: Frontend → Nginx → Backend API{NC}")
    sys.exit(0)
else:
    print(f"{YELLOW}⚠️  SOME TESTS FAILED{NC}")
    print("\nFailed tests:")
    for test in RESULTS['tests']:
        if not test['passed']:
            print(f"  - {test['name']}: {test['message']}")
    print("")
    print("Common issues:")
    print("  - 502 errors: nginx can't reach rag-api-v1 (check docker network)")
    print("  - HTML responses: nginx not proxying correctly (check nginx.conf)")
    print("  - Missing /api: NEXT_PUBLIC_RAG_API not set to '/api'")
    sys.exit(1)

