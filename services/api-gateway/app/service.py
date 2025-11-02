"""
API Gateway - Request routing and orchestration
Central entry point for all client requests
"""
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests
import sys

# Add common to path
sys.path.insert(0, '/workspace/services/common')

from config import *
from metrics import ServiceMetrics, timed
from health import HealthCheck

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Initialize metrics
metrics = ServiceMetrics("api-gateway")

# Initialize health checks
health = HealthCheck("api-gateway")

# Service registry
SERVICES = {
    'ingest': INGEST_SERVICE_URL,
    'search': SEARCH_SERVICE_URL,
    'chat': CHAT_SERVICE_URL,
    'vector_db': VECTOR_DB_URL,
    'embedding': EMBEDDING_SERVICE_URL,
    'docling': DOCLING_SERVICE_URL,
}

def check_services():
    """Check if core services are available"""
    core_services = ['ingest', 'search', 'chat', 'vector_db']
    for service in core_services:
        try:
            url = SERVICES[service]
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code != 200:
                print(f"⚠️  {service} unhealthy")
                return False
        except:
            print(f"❌ {service} unreachable")
            return False
    return True

# Health checks
health.add_check("core_services", check_services)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify(health.get_health())

@app.route('/metrics', methods=['GET'])
def get_metrics():
    """Metrics endpoint - aggregates metrics from all services"""
    try:
        all_metrics = {
            'gateway': metrics.get_stats(),
            'services': {}
        }

        # Collect metrics from all services
        for name, url in SERVICES.items():
            try:
                response = requests.get(f"{url}/metrics", timeout=5)
                if response.status_code == 200:
                    all_metrics['services'][name] = response.json()
            except:
                all_metrics['services'][name] = {'status': 'unavailable'}

        return jsonify(all_metrics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/services', methods=['GET'])
def list_services():
    """List all services and their status"""
    services_status = {}

    for name, url in SERVICES.items():
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                services_status[name] = {
                    'url': url,
                    'status': health_data.get('status', 'unknown'),
                    'healthy': True
                }
            else:
                services_status[name] = {
                    'url': url,
                    'status': 'unhealthy',
                    'healthy': False
                }
        except:
            services_status[name] = {
                'url': url,
                'status': 'unreachable',
                'healthy': False
            }

    return jsonify(services_status)

# === Stats Endpoints ===

@app.route('/api/stats', methods=['GET'])
@timed(metrics, 'stats_request')
def get_stats():
    """Get system statistics"""
    try:
        metrics.increment('stats_requests')

        # Get stats from vector DB
        response = requests.get(f"{VECTOR_DB_URL}/stats", timeout=10)
        response.raise_for_status()

        stats = response.json()
        stats['chat_model'] = CHAT_MODEL
        stats['search_mode'] = 'hybrid'

        return jsonify(stats)
    except Exception as e:
        metrics.increment('stats_errors')
        return jsonify({'error': str(e)}), 500

# === Upload Endpoints ===

@app.route('/api/upload', methods=['POST'])
@timed(metrics, 'upload_request')
def upload_file():
    """Upload file to ingest service"""
    try:
        metrics.increment('upload_requests')

        # Forward to ingest service
        files = {'file': request.files['file']}
        response = requests.post(
            f"{INGEST_SERVICE_URL}/upload",
            files=files,
            timeout=300  # Long timeout for large files
        )

        if response.status_code == 200:
            metrics.increment('upload_success')
        else:
            metrics.increment('upload_errors')

        return (response.json(), response.status_code)
    except Exception as e:
        metrics.increment('upload_errors')
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload/url', methods=['POST'])
@timed(metrics, 'upload_url_request')
def upload_from_url():
    """Upload file from URL"""
    try:
        metrics.increment('upload_url_requests')

        # Forward to ingest service
        response = requests.post(
            f"{INGEST_SERVICE_URL}/upload/url",
            json=request.json,
            timeout=300
        )

        if response.status_code == 200:
            metrics.increment('upload_url_success')
        else:
            metrics.increment('upload_url_errors')

        return (response.json(), response.status_code)
    except Exception as e:
        metrics.increment('upload_url_errors')
        return jsonify({'error': str(e)}), 500

# === Search Endpoints ===

@app.route('/api/search', methods=['POST'])
@timed(metrics, 'search_request')
def search():
    """Search the knowledge base"""
    try:
        metrics.increment('search_requests')

        # Forward to search service
        response = requests.post(
            f"{SEARCH_SERVICE_URL}/search",
            json=request.json,
            timeout=30
        )
        response.raise_for_status()

        metrics.increment('search_success')

        # Format results for UI
        results = response.json()['results']
        formatted_results = []

        for r in results:
            formatted_results.append({
                'title': r['metadata'].get('title', 'Unknown'),
                'file': r['metadata'].get('file_name', 'Unknown'),
                'score': round(r['score'], 3),
                'content': r['content'][:300] + '...' if len(r['content']) > 300 else r['content']
            })

        return jsonify({'results': formatted_results})
    except Exception as e:
        metrics.increment('search_errors')
        return jsonify({'error': str(e)}), 500

# === Chat Endpoints ===

@app.route('/api/chat', methods=['POST'])
@timed(metrics, 'chat_request')
def chat():
    """Chat with RAG (streaming)"""
    try:
        metrics.increment('chat_requests')

        # Forward to chat service (streaming)
        response = requests.post(
            f"{CHAT_SERVICE_URL}/stream",
            json=request.json,
            stream=True,
            timeout=120
        )

        def generate():
            try:
                for line in response.iter_lines():
                    if line:
                        yield line + b'\n'
                metrics.increment('chat_success')
            except Exception as e:
                metrics.increment('chat_errors')
                import json
                yield json.dumps({'type': 'error', 'message': str(e)}).encode() + b'\n'

        return Response(generate(), mimetype='application/json')
    except Exception as e:
        metrics.increment('chat_errors')
        return jsonify({'error': str(e)}), 500

@app.route('/api/ask', methods=['POST'])
@timed(metrics, 'ask_request')
def ask():
    """Ask question (non-streaming) - Transform React UI format to chat service format"""
    try:
        metrics.increment('ask_requests')

        # Get React UI format
        data = request.json

        # Transform to chat service format
        chat_request = {
            'question': data.get('query', data.get('question', '')),
            'num_contexts': data.get('topK', data.get('num_contexts', 5)),
            # Add other config as needed
            'use_query_expansion': data.get('useQueryExpansion', False),
            'use_bm25': data.get('useBM25', False),
            'use_hybrid': data.get('useHybrid', False),
            'use_graph': data.get('useGraph', False),
            'use_reranking': data.get('useReranking', False),
            'use_web_search': data.get('useWebSearch', False),
            'model': data.get('model', 'llama3.2:3b'),
            'temperature': data.get('temperature', 0.7),
        }

        # Forward to chat service
        response = requests.post(
            f"{CHAT_SERVICE_URL}/ask",
            json=chat_request,
            timeout=120
        )
        response.raise_for_status()

        metrics.increment('ask_success')

        return jsonify(response.json())
    except Exception as e:
        metrics.increment('ask_errors')
        return jsonify({'error': str(e)}), 500

# === Admin Endpoints ===

@app.route('/api/presets', methods=['GET'])
def get_presets():
    """Get configuration presets"""
    try:
        import json
        import os

        # Read from config/presets.json
        presets_path = '/workspace/config/presets.json'

        with open(presets_path, 'r') as f:
            presets_data = json.load(f)

        # Convert presets dictionary to array
        presets_dict = presets_data.get('presets', {})
        presets_array = []

        for key, value in presets_dict.items():
            presets_array.append({
                'name': key,
                'description': value.get('description', ''),
                'config': value.get('config', {}),
                'llm_config': value.get('llm_config', {}),
                'expected_metrics': value.get('expected_metrics', {}),
                'notes': value.get('notes', '')
            })

        return jsonify(presets_array)
    except Exception as e:
        # Return default presets if file not found
        return jsonify([
            {
                "name": "minimal",
                "description": "Everything OFF - baseline performance",
                "config": {
                    "use_query_expansion": False,
                    "use_bm25": False,
                    "use_hybrid": False,
                    "use_graph": False,
                    "use_reranking": False,
                    "use_web_search": False,
                    "top_k": 5
                }
            },
            {
                "name": "production",
                "description": "All optimizations enabled",
                "config": {
                    "use_query_expansion": True,
                    "use_bm25": True,
                    "use_hybrid": True,
                    "use_graph": True,
                    "use_reranking": False,
                    "use_web_search": True,
                    "top_k": 10
                }
            }
        ])

@app.route('/api/models', methods=['GET'])
def get_models():
    """Get available Ollama models"""
    try:
        import os
        ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://ollama:11434')
        response = requests.get(f"{ollama_url}/api/tags", timeout=10)

        if response.status_code == 200:
            return jsonify(response.json())

        # Return default if Ollama is not available
        return jsonify({
            'models': [
                {
                    'name': 'llama3.2:3b',
                    'model': 'llama3.2:3b',
                    'size': 2000000000
                }
            ]
        })
    except Exception as e:
        return jsonify({'error': str(e), 'models': []}), 500

@app.route('/api/documents', methods=['GET'])
def get_documents():
    """Get list of documents"""
    try:
        # Get all chunks from vector DB to extract unique filenames
        response = requests.post(
            f"{VECTOR_DB_URL}/get_all",
            json={},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            metadatas = data.get('metadatas', [])

            # Extract unique filenames from metadata
            filenames = set()
            for metadata in metadatas:
                filename = metadata.get('filename') or metadata.get('file_name')
                if filename:
                    filenames.add(filename)

            # Convert to sorted list
            documents = sorted(list(filenames))
            return jsonify({
                'documents': documents,
                'count': len(documents)
            })

        return jsonify({'documents': [], 'count': 0})
    except Exception as e:
        return jsonify({'error': str(e), 'documents': [], 'count': 0}), 500

@app.route('/api/admin/reset', methods=['POST'])
def admin_reset():
    """Reset the vector database (admin only)"""
    try:
        # Forward to vector DB
        response = requests.post(f"{VECTOR_DB_URL}/reset", timeout=30)
        response.raise_for_status()

        metrics.increment('admin_resets')

        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# === Root ===

@app.route('/')
def root():
    """API Gateway info"""
    return jsonify({
        'service': 'RAG Lab API Gateway',
        'version': '1.0.0',
        'services': list(SERVICES.keys()),
        'endpoints': {
            'health': '/health',
            'metrics': '/metrics',
            'services': '/services',
            'stats': '/api/stats',
            'upload': '/api/upload',
            'search': '/api/search',
            'chat': '/api/chat',
            'ask': '/api/ask'
        }
    })

if __name__ == '__main__':
    print("🚀 API Gateway starting...")
    print(f"🌐 Port: {SERVICE_PORT}")
    print("\n📡 Service Registry:")
    for name, url in SERVICES.items():
        print(f"  {name:15} → {url}")

    # Start server
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=False)

