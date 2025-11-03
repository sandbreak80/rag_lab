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
    """Get system statistics - Transform to UI format"""
    try:
        metrics.increment('stats_requests')

        # Get stats from vector DB
        db_response = requests.get(f"{VECTOR_DB_URL}/stats", timeout=180)
        db_response.raise_for_status()
        db_stats = db_response.json()

        # Get knowledge graph stats
        try:
            kg_response = requests.get(f"{KNOWLEDGE_GRAPH_URL}/stats", timeout=5)
            kg_stats = kg_response.json() if kg_response.status_code == 200 else {}
        except:
            kg_stats = {}

        # Get document list
        try:
            docs_response = requests.post(f"{VECTOR_DB_URL}/get_all", json={}, timeout=180)
            if docs_response.status_code == 200:
                data = docs_response.json()
                metadatas = data.get('metadatas', [])

                # Extract unique filenames
                filenames = set()
                for metadata in metadatas:
                    filename = metadata.get('filename') or metadata.get('file_name')
                    if filename:
                        filenames.add(filename)

                documents = sorted(list(filenames))
            else:
                documents = []
        except:
            documents = []

        # Transform to UI format
        return jsonify({
            'chunks': db_stats.get('total_chunks', 0),
            'documents': documents,
            'knowledge_graph_nodes': kg_stats.get('nodes', 0),  # KG service returns 'nodes', not 'total_nodes'
            'knowledge_graph_edges': kg_stats.get('edges', 0),
            'chat_model': CHAT_MODEL,
            'search_mode': 'hybrid',
            'embedding_model': db_stats.get('embedding_model', 'nomic-embed-text'),
            'collection_name': db_stats.get('collection_name', 'markdown_vault')
        })
    except Exception as e:
        metrics.increment('stats_errors')
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# === Upload Endpoints ===

@app.route('/api/upload', methods=['POST'])
@timed(metrics, 'upload_request')
def upload_file():
    """Upload file to ingest service"""
    try:
        print(f"📥 Gateway received upload request")
        print(f"   Files: {list(request.files.keys())}")
        print(f"   Form: {list(request.form.keys())}")

        metrics.increment('upload_requests')

        # Check if file exists
        if 'file' not in request.files:
            print(f"❌ No file in request")
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            print(f"❌ Empty filename")
            return jsonify({'error': 'No file selected'}), 400

        print(f"✅ Forwarding file: {file.filename}")

        # Forward to ingest service
        files = {'file': (file.filename, file.stream, file.content_type)}
        response = requests.post(
            f"{INGEST_SERVICE_URL}/upload",
            files=files,
            timeout=300  # Long timeout for large files
        )

        if response.status_code == 200:
            metrics.increment('upload_success')
        else:
            metrics.increment('upload_errors')
            print(f"❌ Ingest service returned {response.status_code}: {response.text[:200]}")

        return (response.json(), response.status_code)
    except Exception as e:
        print(f"❌ Gateway upload error: {e}")
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
            timeout=180  # 3 minutes minimum
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
            timeout=180  # 3 minutes minimum
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

@app.route('/api/cancel', methods=['POST'])
def cancel_request():
    """Cancel active request by restarting Ollama"""
    try:
        import subprocess
        print("🛑 Cancel request received - restarting Ollama container...")

        # Restart Ollama container
        result = subprocess.run(
            ['docker', 'restart', 'ollama'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            print("✅ Ollama container restarted successfully")
            return jsonify({'success': True, 'message': 'Request cancelled - Ollama restarted'}), 200
        else:
            print(f"❌ Failed to restart Ollama: {result.stderr}")
            return jsonify({'success': False, 'error': result.stderr}), 500

    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Restart timeout'}), 500
    except Exception as e:
        print(f"❌ Error restarting Ollama: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ask', methods=['POST'])
@timed(metrics, 'ask_request')
def ask():
    """Ask question (non-streaming) - Transform React UI format to chat service format"""
    try:
        metrics.increment('ask_requests')

        # Get React UI format
        data = request.json
        print(f"🌐 API Gateway received request: query={data.get('query', '')[:50]}, model={data.get('model')}")

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
        print(f"📤 Forwarding to chat service: {CHAT_SERVICE_URL}/ask")

        # Forward to chat service
        response = requests.post(
            f"{CHAT_SERVICE_URL}/ask",
            json=chat_request,
            timeout=1800  # 30 minutes - allows Maximum preset to complete for quality demo
        )

        print(f"📬 Chat service responded with status: {response.status_code}")
        if response.status_code != 200:
            print(f"❌ Error response: {response.text[:200]}")

        response.raise_for_status()

        metrics.increment('ask_success')

        return jsonify(response.json())
    except Exception as e:
        error_msg = str(e)
        print(f"❌ API Gateway error: {error_msg}")
        metrics.increment('ask_errors')
        import traceback
        traceback.print_exc()
        return jsonify({'error': error_msg}), 500

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
        ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://host.docker.internal:11434')
        response = requests.get(f"{ollama_url}/api/tags", timeout=180)

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
            timeout=180  # 3 minutes minimum
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
        response = requests.post(f"{VECTOR_DB_URL}/reset", timeout=180)
        response.raise_for_status()

        metrics.increment('admin_resets')

        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/reset-kg', methods=['POST'])
def admin_reset_kg():
    """Reset the knowledge graph (admin only)"""
    try:
        # Get knowledge graph service URL from environment
        kg_url = os.getenv('KNOWLEDGE_GRAPH_URL', 'http://knowledge-graph:8007')
        
        # Forward to knowledge graph service
        response = requests.post(f"{kg_url}/reset", timeout=180)
        response.raise_for_status()

        metrics.increment('kg_resets')

        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/kg/algorithms', methods=['GET'])
def get_kg_algorithms():
    """Get available KG construction algorithms"""
    try:
        kg_url = os.getenv('KNOWLEDGE_GRAPH_URL', 'http://knowledge-graph:8007')
        response = requests.get(f"{kg_url}/algorithms", timeout=30)
        response.raise_for_status()
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/kg/build', methods=['POST'])
def build_kg():
    """Build knowledge graph with specified algorithm"""
    try:
        data = request.json or {}
        kg_url = os.getenv('KNOWLEDGE_GRAPH_URL', 'http://knowledge-graph:8007')
        
        # Forward to KG service
        response = requests.post(
            f"{kg_url}/build",
            json=data,
            timeout=300  # 5 minutes for KG build
        )
        response.raise_for_status()
        
        metrics.increment('kg_builds')
        
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

