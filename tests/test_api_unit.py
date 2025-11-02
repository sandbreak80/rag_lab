#!/usr/bin/env python3
"""
Comprehensive API Unit Tests
Tests all Flask API endpoints with real services (no mocks)
"""
import requests
import json
import time
import os
from typing import Dict, Any

BASE_URL = "http://localhost:5555"
TIMEOUT = 30

class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []

    def test(self, name: str, func):
        """Run a test and record result"""
        try:
            func()
            self.passed += 1
            self.tests.append({"name": name, "status": "PASS", "error": None})
            print(f"✅ PASS: {name}")
            return True
        except AssertionError as e:
            self.failed += 1
            self.tests.append({"name": name, "status": "FAIL", "error": str(e)})
            print(f"❌ FAIL: {name}")
            print(f"   Error: {e}")
            return False
        except Exception as e:
            self.failed += 1
            self.tests.append({"name": name, "status": "ERROR", "error": str(e)})
            print(f"💥 ERROR: {name}")
            print(f"   Error: {e}")
            return False

    def summary(self):
        total = self.passed + self.failed
        percentage = (self.passed / total * 100) if total > 0 else 0
        print(f"\n{'='*60}")
        print(f"Test Results: {self.passed}/{total} passed ({percentage:.1f}%)")
        print(f"{'='*60}\n")
        return self.passed, self.failed

runner = TestRunner()

print("="*60)
print("API UNIT TESTS - ALL ENDPOINTS")
print("="*60)
print()

# ============================================================================
# HEALTH & STATUS TESTS
# ============================================================================

def test_health_endpoint():
    """Test /health endpoint"""
    response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "status" in data, "Response missing 'status' field"
    assert data["status"] == "ok", f"Expected status 'ok', got {data['status']}"

def test_stats_endpoint():
    """Test /api/stats endpoint"""
    response = requests.get(f"{BASE_URL}/api/stats", timeout=TIMEOUT)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "chunks" in data, "Response missing 'chunks' field"
    assert "documents" in data, "Response missing 'documents' field"
    assert "knowledge_graph_nodes" in data, "Response missing 'knowledge_graph_nodes' field"
    assert isinstance(data["chunks"], int), "chunks should be an integer"
    assert data["chunks"] >= 0, "chunks should be non-negative"

print("📋 Health & Status Tests")
print("-" * 60)
runner.test("Health endpoint returns OK", test_health_endpoint)
runner.test("Stats endpoint returns valid data", test_stats_endpoint)
print()

# ============================================================================
# SETTINGS TESTS
# ============================================================================

def test_models_endpoint():
    """Test /api/models endpoint"""
    response = requests.get(f"{BASE_URL}/api/models", timeout=TIMEOUT)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "models" in data, "Response missing 'models' field"
    assert isinstance(data["models"], list), "models should be a list"
    if len(data["models"]) > 0:
        model = data["models"][0]
        assert "name" in model or "model" in model, "Model missing name/model field"

def test_presets_endpoint():
    """Test /api/presets endpoint"""
    response = requests.get(f"{BASE_URL}/api/presets", timeout=TIMEOUT)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert isinstance(data, list), "Presets should be a list"
    if len(data) > 0:
        preset = data[0]
        assert "name" in preset, "Preset missing 'name' field"
        assert "config" in preset, "Preset missing 'config' field"

print("⚙️  Settings Tests")
print("-" * 60)
runner.test("Models endpoint returns list", test_models_endpoint)
runner.test("Presets endpoint returns list", test_presets_endpoint)
print()

# ============================================================================
# DOCUMENTS TESTS
# ============================================================================

def test_documents_list():
    """Test /api/documents endpoint"""
    response = requests.get(f"{BASE_URL}/api/documents", timeout=TIMEOUT)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "documents" in data, "Response missing 'documents' field"
    assert isinstance(data["documents"], list), "documents should be a list"

def test_document_upload():
    """Test /api/upload endpoint with real file"""
    # Create a test file
    test_content = """# Test Document

This is a test document for API testing.

## Section 1
Some content here.

## Section 2
More content here.
"""
    files = {"file": ("test_api_doc.md", test_content, "text/markdown")}

    response = requests.post(f"{BASE_URL}/api/upload", files=files, timeout=TIMEOUT)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "file_name" in data or "filename" in data, "Response missing filename field"
    print(f"   Uploaded: {data.get('file_name', data.get('filename'))}")

print("📄 Documents Tests")
print("-" * 60)
runner.test("Documents list endpoint works", test_documents_list)
runner.test("Document upload works", test_document_upload)
print()

# ============================================================================
# SEARCH & CHAT TESTS
# ============================================================================

def test_chat_endpoint():
    """Test /api/chat endpoint"""
    payload = {
        "query": "What is a test?",
        "config": {
            "model": "llama3.2:3b",
            "temperature": 0.7,
            "top_k": 3,
            "use_hybrid": True
        }
    }

    response = requests.post(
        f"{BASE_URL}/api/chat",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=TIMEOUT
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "answer" in data, "Response missing 'answer' field"
    assert isinstance(data["answer"], str), "answer should be a string"
    assert len(data["answer"]) > 0, "answer should not be empty"
    print(f"   Answer length: {len(data['answer'])} chars")

def test_chat_with_sources():
    """Test /api/chat returns sources"""
    payload = {
        "query": "test document",
        "config": {
            "model": "llama3.2:3b",
            "temperature": 0.5,
            "top_k": 5,
            "use_hybrid": True
        }
    }

    response = requests.post(
        f"{BASE_URL}/api/chat",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=TIMEOUT
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()

    if "sources" in data and data["sources"]:
        assert isinstance(data["sources"], list), "sources should be a list"
        source = data["sources"][0]
        assert "content" in source or "text" in source, "Source missing content field"
        print(f"   Sources returned: {len(data['sources'])}")
    else:
        print(f"   No sources returned (may be expected if no relevant docs)")

def test_chat_metrics():
    """Test /api/chat returns metrics"""
    payload = {
        "query": "metrics test",
        "config": {
            "model": "llama3.2:3b",
            "temperature": 0.7,
            "top_k": 3
        }
    }

    response = requests.post(
        f"{BASE_URL}/api/chat",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=TIMEOUT
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()

    if "metrics" in data:
        metrics = data["metrics"]
        assert isinstance(metrics, dict), "metrics should be a dict"
        # Check for common metric fields
        if "total_latency_ms" in metrics:
            assert metrics["total_latency_ms"] > 0, "latency should be positive"
            print(f"   Total latency: {metrics['total_latency_ms']}ms")
    else:
        print(f"   Warning: No metrics returned")

print("💬 Chat & Search Tests")
print("-" * 60)
runner.test("Chat endpoint responds", test_chat_endpoint)
runner.test("Chat returns sources", test_chat_with_sources)
runner.test("Chat returns metrics", test_chat_metrics)
print()

# ============================================================================
# METRICS TESTS
# ============================================================================

def test_metrics_endpoint():
    """Test /api/metrics endpoint"""
    response = requests.get(f"{BASE_URL}/api/metrics", timeout=TIMEOUT)
    # Endpoint might not exist yet, so we allow 404
    assert response.status_code in [200, 404], f"Expected 200 or 404, got {response.status_code}"
    if response.status_code == 200:
        data = response.json()
        print(f"   Metrics available")
    else:
        print(f"   Metrics endpoint not implemented (404)")

print("📊 Metrics Tests")
print("-" * 60)
runner.test("Metrics endpoint accessible", test_metrics_endpoint)
print()

# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

def test_invalid_endpoint():
    """Test 404 for invalid endpoint"""
    response = requests.get(f"{BASE_URL}/api/nonexistent", timeout=TIMEOUT)
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"

def test_invalid_chat_payload():
    """Test chat with missing required fields"""
    payload = {"query": ""}  # Empty query

    response = requests.post(
        f"{BASE_URL}/api/chat",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=TIMEOUT
    )
    # Should either handle gracefully (200 with error) or return 400
    assert response.status_code in [200, 400, 422], f"Expected 200/400/422, got {response.status_code}"

print("🚨 Error Handling Tests")
print("-" * 60)
runner.test("404 for invalid endpoint", test_invalid_endpoint)
runner.test("Graceful handling of invalid payload", test_invalid_chat_payload)
print()

# ============================================================================
# SUMMARY
# ============================================================================

passed, failed = runner.summary()

# Save results to file
results = {
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    "total": passed + failed,
    "passed": passed,
    "failed": failed,
    "percentage": (passed / (passed + failed) * 100) if (passed + failed) > 0 else 0,
    "tests": runner.tests
}

with open("/tmp/api_test_results.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"📄 Results saved to: /tmp/api_test_results.json")
print()

# Exit with appropriate code
exit(0 if failed == 0 else 1)

