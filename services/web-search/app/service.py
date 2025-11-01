"""
Web Search Service - SearXNG Integration
Provides web search capabilities for RAG enhancement
"""
from flask import Flask, request, jsonify
import requests
import os
import sys
import time

# Add common to path
sys.path.insert(0, '/workspace/services/common')

from metrics import ServiceMetrics, timed
from health import HealthCheck

app = Flask(__name__)

# Configuration
SERVICE_PORT = int(os.getenv('SERVICE_PORT', 8009))
SEARXNG_URL = os.getenv('SEARXNG_URL', 'http://searxng:8080')

# Initialize metrics and health
metrics = ServiceMetrics("web-search-service")
health = HealthCheck("web-search-service")

@app.route('/health')
def health_check():
    """Health check endpoint"""
    # Check if SearXNG is accessible
    try:
        response = requests.get(f"{SEARXNG_URL}/", timeout=2)
        searxng_healthy = response.status_code == 200
    except:
        searxng_healthy = False
    
    return jsonify({
        'status': 'healthy' if searxng_healthy else 'degraded',
        'service': 'web-search-service',
        'searxng_accessible': searxng_healthy,
        'searxng_url': SEARXNG_URL
    })

@app.route('/metrics')
def get_metrics():
    """Metrics endpoint"""
    return jsonify(metrics.get_metrics())

@app.route('/search', methods=['POST'])
@timed(metrics, 'web_search')
def web_search():
    """
    Perform web search using SearXNG
    
    Body:
    {
        "query": "search query",
        "limit": 5,
        "categories": ["general", "science", "news"]
    }
    
    Returns:
    {
        "results": [
            {
                "title": "...",
                "url": "...",
                "content": "...",
                "engine": "google",
                "score": 0.95
            }
        ],
        "count": 5,
        "web_docs_returned": 5,
        "avg_pages_per_doc": 1.2,
        "latency_ms": 850
    }
    """
    try:
        data = request.json
        query = data.get('query', '')
        limit = data.get('limit', 5)
        categories = data.get('categories', 'general')
        
        if not query:
            return jsonify({'error': 'query required'}), 400
        
        metrics.increment('search_requests')
        start_time = time.time()
        
        # Query SearXNG
        search_url = f"{SEARXNG_URL}/search"
        params = {
            'q': query,
            'format': 'json',
            'categories': categories,
            'pageno': 1
        }
        
        print(f"🌐 Searching web for: '{query}'")
        
        response = requests.get(search_url, params=params, timeout=15)
        response.raise_for_status()
        
        search_data = response.json()
        raw_results = search_data.get('results', [])
        
        # Process and format results
        results = []
        total_pages = 0
        
        for item in raw_results[:limit]:
            # Estimate pages from content length
            content = item.get('content', '')
            estimated_pages = max(1, len(content) // 3000)
            total_pages += estimated_pages
            
            result = {
                'title': item.get('title', ''),
                'url': item.get('url', ''),
                'content': content,
                'engine': item.get('engine', 'unknown'),
                'score': item.get('score', 0.5),
                'estimated_pages': estimated_pages,
                'category': item.get('category', 'general')
            }
            results.append(result)
        
        latency_ms = round((time.time() - start_time) * 1000, 2)
        avg_pages = round(total_pages / len(results), 2) if results else 0
        
        metrics.increment('successful_searches')
        metrics.set_gauge('last_search_latency_ms', latency_ms)
        
        print(f"✅ Found {len(results)} web results in {latency_ms}ms")
        
        return jsonify({
            'results': results,
            'count': len(results),
            'web_docs_returned': len(results),
            'avg_pages_per_doc': avg_pages,
            'latency_ms': latency_ms,
            'query': query,
            'engines_used': list(set(r['engine'] for r in results))
        })
        
    except requests.exceptions.Timeout:
        metrics.increment('search_timeouts')
        return jsonify({'error': 'Web search timeout'}), 504
    except requests.exceptions.RequestException as e:
        metrics.increment('search_errors')
        print(f"❌ Web search error: {e}")
        return jsonify({'error': f'Web search failed: {str(e)}'}), 500
    except Exception as e:
        metrics.increment('search_errors')
        print(f"❌ Unexpected error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Web Search Service starting...")
    print(f"🌐 SearXNG URL: {SEARXNG_URL}")
    print(f"📡 Listening on port {SERVICE_PORT}")
    
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=False)

