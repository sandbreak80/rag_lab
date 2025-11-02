#!/usr/bin/env python3
"""
Integration tests for React UI + Backend
Tests the full stack end-to-end
"""
import requests
import time
import json
from typing import Dict, Any

BASE_URL = "http://localhost:5173"
API_URL = "http://localhost:5555"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def test_result(name: str, success: bool, details: str = ""):
    """Print test result"""
    icon = f"{Colors.GREEN}✅{Colors.RESET}" if success else f"{Colors.RED}❌{Colors.RESET}"
    print(f"{icon} {name}")
    if details:
        print(f"   {details}")
    return success

def test_ui_loads():
    """Test 1: React UI loads"""
    try:
        response = requests.get(BASE_URL, timeout=5)
        success = response.status_code == 200 and "Neural Vault" in response.text
        return test_result("React UI loads", success, f"Status: {response.status_code}")
    except Exception as e:
        return test_result("React UI loads", False, str(e))

def test_api_health():
    """Test 2: API health check"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        data = response.json()
        success = response.status_code == 200 and data.get("status") == "ok"
        return test_result("API health check", success, json.dumps(data))
    except Exception as e:
        return test_result("API health check", False, str(e))

def test_stats_endpoint():
    """Test 3: Stats endpoint returns data"""
    try:
        response = requests.get(f"{API_URL}/api/stats", timeout=5)
        data = response.json()
        success = (response.status_code == 200 and 
                  "chunks" in data and 
                  "documents" in data and
                  "knowledge_graph_nodes" in data)
        details = f"Chunks: {data.get('chunks')}, Docs: {data.get('documents')}, Nodes: {data.get('knowledge_graph_nodes')}"
        return test_result("Stats endpoint", success, details)
    except Exception as e:
        return test_result("Stats endpoint", False, str(e))

def test_ui_proxy():
    """Test 4: UI proxy to backend"""
    try:
        # Test through Vite proxy
        response = requests.get(f"{BASE_URL}/api/stats", timeout=5)
        data = response.json()
        success = response.status_code == 200 and "chunks" in data
        return test_result("UI → API proxy", success, "Proxy working correctly")
    except Exception as e:
        return test_result("UI → API proxy", False, str(e))

def test_documents_list():
    """Test 5: Documents list endpoint"""
    try:
        response = requests.get(f"{API_URL}/api/documents", timeout=5)
        success = response.status_code == 200
        if success:
            data = response.json()
            doc_count = len(data.get("documents", []))
            return test_result("Documents list", success, f"{doc_count} documents found")
        return test_result("Documents list", success)
    except Exception as e:
        return test_result("Documents list", False, str(e))

def test_settings_models():
    """Test 6: Models list endpoint"""
    try:
        response = requests.get(f"{API_URL}/api/models", timeout=5)
        success = response.status_code == 200
        if success:
            data = response.json()
            models = data.get("models", [])
            model_names = [m.get("name", m.get("model")) for m in models]
            return test_result("Models endpoint", success, f"Models: {', '.join(model_names[:3])}")
        return test_result("Models endpoint", success)
    except Exception as e:
        return test_result("Models endpoint", False, str(e))

def test_settings_presets():
    """Test 7: Presets endpoint"""
    try:
        response = requests.get(f"{API_URL}/api/presets", timeout=5)
        success = response.status_code == 200
        if success:
            data = response.json()
            preset_names = [p.get("name") for p in data]
            return test_result("Presets endpoint", success, f"Presets: {', '.join(preset_names)}")
        return test_result("Presets endpoint", success)
    except Exception as e:
        return test_result("Presets endpoint", False, str(e))

def test_vector_db_connection():
    """Test 8: Vector DB health"""
    try:
        response = requests.get("http://localhost:8005/health", timeout=5)
        data = response.json()
        success = response.status_code == 200 and data.get("status") == "healthy"
        return test_result("Vector DB connection", success, f"Chunks: {data.get('stats', {}).get('chunks', 0)}")
    except Exception as e:
        return test_result("Vector DB connection", False, str(e))

def test_knowledge_graph():
    """Test 9: Knowledge Graph health"""
    try:
        response = requests.get("http://localhost:8007/health", timeout=5)
        data = response.json()
        success = response.status_code == 200 and data.get("status") == "healthy"
        return test_result("Knowledge Graph service", success)
    except Exception as e:
        return test_result("Knowledge Graph service", False, str(e))

def test_search_service():
    """Test 10: Search Service health"""
    try:
        response = requests.get("http://localhost:8002/health", timeout=5)
        data = response.json()
        success = response.status_code == 200
        return test_result("Search service", success, f"Status: {data.get('status')}")
    except Exception as e:
        return test_result("Search service", False, str(e))

def main():
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}React UI + Backend Integration Tests{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}")
    print()
    
    tests = [
        test_ui_loads,
        test_api_health,
        test_stats_endpoint,
        test_ui_proxy,
        test_documents_list,
        test_settings_models,
        test_settings_presets,
        test_vector_db_connection,
        test_knowledge_graph,
        test_search_service,
    ]
    
    results = []
    for i, test in enumerate(tests, 1):
        print(f"\n{Colors.YELLOW}[{i}/{len(tests)}]{Colors.RESET} ", end="")
        results.append(test())
    
    print()
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}")
    passed = sum(results)
    total = len(results)
    percentage = (passed / total) * 100
    
    color = Colors.GREEN if percentage == 100 else Colors.YELLOW if percentage >= 70 else Colors.RED
    print(f"{color}Results: {passed}/{total} tests passed ({percentage:.0f}%){Colors.RESET}")
    
    if percentage == 100:
        print(f"{Colors.GREEN}🎉 All tests passed! Full stack is working!{Colors.RESET}")
    elif percentage >= 70:
        print(f"{Colors.YELLOW}⚠️  Most tests passed. Check failures above.{Colors.RESET}")
    else:
        print(f"{Colors.RED}❌ Multiple failures. Check services are running.{Colors.RESET}")
    
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}")
    print()
    print(f"📱 React UI: {BASE_URL}")
    print(f"🔧 Flask API: {API_URL}")
    print()
    
    return 0 if percentage == 100 else 1

if __name__ == "__main__":
    exit(main())
