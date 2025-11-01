"""
Backend Service Validation Tests
Tests all RAG pipeline services to determine what's working vs broken
"""
import requests
import json
import time

# Service URLs (correct internal Docker network names and ports)
SERVICES = {
    'ingest': 'http://ingest-service:8001',
    'search': 'http://search-service:8002',
    'chat': 'http://chat-service:8003',
    'docling': 'http://docling-service:8004',
    'vector_db': 'http://vector-db:8005',
    'embedding': 'http://embedding-service:8006',
    'knowledge_graph': 'http://knowledge-graph:8007',
    'reranker': 'http://reranker:8008',
    'web_search': 'http://web-search:8009',
    'api_gateway': 'http://api-gateway:8000',
}

def test_service_health(service_name, url):
    """Test if service is up and responding"""
    print(f"\n{'='*60}")
    print(f"🏥 Testing {service_name.upper()} Health")
    print(f"{'='*60}")
    
    try:
        response = requests.get(f"{url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Service is UP")
            print(f"   Status: {data.get('status', 'unknown')}")
            print(f"   Service: {data.get('service', 'unknown')}")
            return True, data
        else:
            print(f"❌ Service returned {response.status_code}")
            return False, None
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to service")
        return False, None
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, None

def test_vector_db():
    """Test Vector DB (ChromaDB) connection"""
    print(f"\n{'='*60}")
    print(f"🗄️  Testing Vector DB (ChromaDB)")
    print(f"{'='*60}")
    
    try:
        # Test health endpoint
        response = requests.get(f"{SERVICES['vector_db']}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ Vector DB is UP")
            data = response.json()
            print(f"   Status: {data.get('status', 'unknown')}")
            return True, data
        else:
            print(f"❌ Vector DB returned {response.status_code}")
            return False, None
            
    except Exception as e:
        print(f"❌ Vector DB Error: {e}")
        return False, None

def test_search_service():
    """Test search service vector and BM25 functionality"""
    print(f"\n{'='*60}")
    print(f"🔍 Testing Search Service")
    print(f"{'='*60}")
    
    results = {}
    
    # Test vector search
    try:
        response = requests.post(
            f"{SERVICES['search']}/search",
            json={"query": "What is RAG?", "top_k": 5},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Vector Search: {len(data.get('results', []))} results")
            results['vector'] = True
        else:
            print(f"❌ Vector Search failed: {response.status_code}")
            results['vector'] = False
    except Exception as e:
        print(f"❌ Vector Search error: {e}")
        results['vector'] = False
    
    # Test BM25 search
    try:
        response = requests.post(
            f"{SERVICES['search']}/search",
            json={"query": "RAG pipeline", "top_k": 5, "use_bm25": True},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ BM25 Search: {len(data.get('results', []))} results")
            results['bm25'] = True
        else:
            print(f"❌ BM25 Search failed: {response.status_code}")
            results['bm25'] = False
    except Exception as e:
        print(f"❌ BM25 Search error: {e}")
        results['bm25'] = False
    
    # Test hybrid search
    try:
        response = requests.post(
            f"{SERVICES['search']}/search",
            json={"query": "embeddings", "top_k": 5, "use_hybrid": True},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Hybrid Search: {len(data.get('results', []))} results")
            results['hybrid'] = True
        else:
            print(f"❌ Hybrid Search failed: {response.status_code}")
            results['hybrid'] = False
    except Exception as e:
        print(f"❌ Hybrid Search error: {e}")
        results['hybrid'] = False
    
    # Test query expansion
    try:
        response = requests.post(
            f"{SERVICES['search']}/search",
            json={"query": "LLM", "top_k": 5, "use_query_expansion": True},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Query Expansion: {len(data.get('results', []))} results")
            results['query_expansion'] = True
        else:
            print(f"❌ Query Expansion failed: {response.status_code}")
            results['query_expansion'] = False
    except Exception as e:
        print(f"❌ Query Expansion error: {e}")
        results['query_expansion'] = False
    
    return results

def test_knowledge_graph():
    """Test knowledge graph service"""
    print(f"\n{'='*60}")
    print(f"🕸️  Testing Knowledge Graph")
    print(f"{'='*60}")
    
    try:
        # Get graph stats
        response = requests.get(f"{SERVICES['knowledge_graph']}/metrics", timeout=5)
        if response.status_code == 200:
            metrics = response.json()
            print(f"✅ Knowledge Graph Metrics:")
            print(f"   Nodes: {metrics.get('nodes', 0)}")
            print(f"   Edges: {metrics.get('edges', 0)}")
            return True, metrics
        else:
            print(f"❌ Failed to get metrics: {response.status_code}")
            return False, None
    except Exception as e:
        print(f"❌ Knowledge Graph error: {e}")
        return False, None

def test_web_search():
    """Test web search service"""
    print(f"\n{'='*60}")
    print(f"🌐 Testing Web Search")
    print(f"{'='*60}")
    
    try:
        response = requests.post(
            f"{SERVICES['web_search']}/search",
            json={"query": "RAG system architecture", "max_results": 3},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Web Search Working")
            print(f"   Results: {len(data.get('results', []))}")
            for result in data.get('results', [])[:2]:
                print(f"   - {result.get('title', 'No title')}")
            return True, data
        else:
            print(f"❌ Web Search failed: {response.status_code}")
            return False, None
    except Exception as e:
        print(f"❌ Web Search error: {e}")
        return False, None

def main():
    print("\n" + "="*60)
    print("🚀 RAG BACKEND VALIDATION SUITE")
    print("="*60)
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        'services_up': {},
        'functionality': {}
    }
    
    # Test all service health
    for service_name, url in SERVICES.items():
        is_up, data = test_service_health(service_name, url)
        results['services_up'][service_name] = is_up
    
    # Test specific functionality
    results['functionality']['vector_db'] = test_vector_db()[0]
    results['functionality']['search'] = test_search_service()
    results['functionality']['knowledge_graph'] = test_knowledge_graph()[0]
    results['functionality']['web_search'] = test_web_search()[0]
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 VALIDATION SUMMARY")
    print(f"{'='*60}")
    
    services_up = sum(1 for v in results['services_up'].values() if v)
    print(f"\n🏥 Services Health: {services_up}/{len(SERVICES)} UP")
    for service, is_up in results['services_up'].items():
        status = "✅" if is_up else "❌"
        print(f"   {status} {service}")
    
    print(f"\n🔧 Functionality Tests:")
    for feature, result in results['functionality'].items():
        if isinstance(result, dict):
            for sub_feature, sub_result in result.items():
                status = "✅" if sub_result else "❌"
                print(f"   {status} {feature}.{sub_feature}")
        else:
            status = "✅" if result else "❌"
            print(f"   {status} {feature}")
    
    print(f"\n{'='*60}")
    
    return results

if __name__ == "__main__":
    results = main()

