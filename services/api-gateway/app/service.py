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
from security_client import SecurityClient, EnhancementClient
from rate_limiter import RateLimiter

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Initialize metrics
metrics = ServiceMetrics("api-gateway")

# Initialize health checks
health = HealthCheck("api-gateway")

# Initialize rate limiter
try:
    rate_limiter = RateLimiter()
    print("✅ Rate limiter initialized")
except Exception as e:
    print(f"⚠️ Rate limiter initialization failed: {e}")
    rate_limiter = None

# Initialize security clients
SECURITY_GUARDRAILS_URL = os.getenv('SECURITY_GUARDRAILS_URL', 'http://security-guardrails:8013')
PROMPT_ENHANCEMENT_URL = os.getenv('PROMPT_ENHANCEMENT_URL', 'http://prompt-enhancement:8012')

security_client = SecurityClient(SECURITY_GUARDRAILS_URL)
enhancement_client = EnhancementClient(PROMPT_ENHANCEMENT_URL)

# Service registry
AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://auth-service:8014')

SERVICES = {
    'ingest': INGEST_SERVICE_URL,
    'search': SEARCH_SERVICE_URL,
    'chat': CHAT_SERVICE_URL,
    'vector_db': VECTOR_DB_URL,
    'embedding': EMBEDDING_SERVICE_URL,
    'docling': DOCLING_SERVICE_URL,
    'security': SECURITY_GUARDRAILS_URL,
    'enhancement': PROMPT_ENHANCEMENT_URL,
    'auth': AUTH_SERVICE_URL,
}

def _detect_hallucinated_citations(answer: str, sources: list) -> list:
    """
    Detect potentially hallucinated citations in the answer
    Returns list of warnings about suspicious citations
    """
    import re
    warnings = []

    # Extract all citations from the answer
    # Common citation patterns: [1], [Source 1], [Paper et al. 2023], etc.
    citation_patterns = [
        r'\[(\d+)\]',  # [1], [2], etc.
        r'\[([^\]]+?et al\.\s*\d{4})\]',  # [Author et al. 2023]
        r'\[([^\]]+?\d{4})\]',  # [Paper 2023]
        r'arXiv:\d{4}\.\d{4,5}',  # arXiv IDs
        r'doi:\S+',  # DOI identifiers
    ]

    found_citations = set()
    for pattern in citation_patterns:
        matches = re.findall(pattern, answer, re.IGNORECASE)
        found_citations.update(matches)

    if not found_citations:
        return warnings

    # Build index of valid source identifiers from retrieved documents
    valid_identifiers = set()
    for i, source in enumerate(sources, 1):
        valid_identifiers.add(str(i))
        if isinstance(source, dict):
            metadata = source.get('metadata', {})
            # Add known identifiers
            if 'external_id' in metadata:
                valid_identifiers.add(metadata['external_id'])
            if 'arxiv_id' in metadata:
                valid_identifiers.add(f"arXiv:{metadata['arxiv_id']}")
            if 'title' in metadata:
                valid_identifiers.add(metadata['title'])

    # Check each citation against valid sources
    for citation in found_citations:
        # Simple numeric citations should match source numbers
        if citation.isdigit():
            if int(citation) > len(sources):
                warnings.append({
                    'type': 'out_of_range',
                    'citation': f'[{citation}]',
                    'message': f'Citation [{citation}] refers to source beyond retrieved documents (only {len(sources)} sources available)'
                })
        # Check for academic-style citations that might be hallucinated
        elif 'et al' in citation.lower() or any(year in citation for year in ['2020', '2021', '2022', '2023', '2024', '2025']):
            # This looks like an academic citation - check if it matches any source
            found_match = False
            for source in sources:
                if isinstance(source, dict):
                    metadata = source.get('metadata', {})
                    title = metadata.get('title', '')
                    authors = metadata.get('authors', '')
                    if citation.lower() in title.lower() or citation.lower() in str(authors).lower():
                        found_match = True
                        break

            if not found_match:
                warnings.append({
                    'type': 'unverified_academic',
                    'citation': f'[{citation}]',
                    'message': f'Academic citation "{citation}" could not be verified against retrieved sources. This may be generated rather than cited.'
                })

    return warnings

def _enrich_source_metadata(sources: list) -> list:
    """
    Enrich source metadata with transparent, verifiable information
    Returns enhanced sources with full metadata
    """
    enriched = []

    for i, source in enumerate(sources, 1):
        if not isinstance(source, dict):
            # Convert simple sources to dict format
            enriched.append({
                'id': i,
                'content': str(source),
                'metadata': {}
            })
            continue

        metadata = source.get('metadata', {})

        # Build enriched source with all available metadata
        enriched_source = {
            'id': i,
            'content': source.get('content', source.get('text', '')),
            'metadata': {
                'title': metadata.get('title', metadata.get('source', f'Source {i}')),
                'type': metadata.get('source_type', metadata.get('type', 'document')),
                'score': source.get('score', 0.0),
            }
        }

        # Add optional metadata if available
        if 'url' in metadata or 'pdf_url' in metadata:
            enriched_source['metadata']['url'] = metadata.get('url', metadata.get('pdf_url'))

        if 'published_date' in metadata or 'updated_date' in metadata:
            enriched_source['metadata']['date'] = metadata.get('published_date', metadata.get('updated_date'))

        if 'authors' in metadata or 'author_list' in metadata:
            authors = metadata.get('authors', metadata.get('author_list', ''))
            if isinstance(authors, list):
                enriched_source['metadata']['authors'] = ', '.join(authors[:3])  # First 3 authors
            else:
                enriched_source['metadata']['authors'] = str(authors)

        if 'external_id' in metadata:
            enriched_source['metadata']['external_id'] = metadata['external_id']

        if 'arxiv_id' in metadata:
            enriched_source['metadata']['arxiv_id'] = metadata['arxiv_id']
            enriched_source['metadata']['arxiv_url'] = f"https://arxiv.org/abs/{metadata['arxiv_id']}"

        if 'doi' in metadata:
            enriched_source['metadata']['doi'] = metadata['doi']
            enriched_source['metadata']['doi_url'] = f"https://doi.org/{metadata['doi']}"

        enriched.append(enriched_source)

    return enriched

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

@app.route('/version', methods=['GET'])
def get_version():
    """Version endpoint - aggregates versions from all services"""
    try:
        all_versions = {
            'gateway': health.get_version(),
            'services': {}
        }

        # Collect versions from all services
        for name, url in SERVICES.items():
            try:
                response = requests.get(f"{url}/version", timeout=5)
                if response.status_code == 200:
                    all_versions['services'][name] = response.json()
                else:
                    all_versions['services'][name] = {'service': name, 'version': 'unavailable'}
            except:
                all_versions['services'][name] = {'service': name, 'version': 'unavailable'}

        return jsonify(all_versions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
    import time

    try:
        metrics.increment('ask_requests')

        # Track timing for performance metrics
        timing_metrics = {}
        gateway_start = time.time()

        # RATE LIMITING: Check if request is within limits
        rate_limit_start = time.time()
        if rate_limiter:
            rate_check = rate_limiter.check_rate_limit(request)

            # Add rate limit headers
            if not rate_check['allowed']:
                metrics.increment('rate_limit_exceeded')
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f"Too many requests. Please try again in {rate_check['retry_after']} seconds.",
                    'retry_after': rate_check['retry_after'],
                    'limit': rate_check['limit']
                }), 429, {
                    'X-RateLimit-Limit': str(rate_check['limit']),
                    'X-RateLimit-Remaining': '0',
                    'X-RateLimit-Reset': str(rate_check['reset_at']),
                    'Retry-After': str(rate_check['retry_after'])
                }

            # Log rate limit info
            print(f"🔒 Rate limit: {rate_check['remaining']}/{rate_check['limit']} remaining")

        timing_metrics['rate_limit_check_ms'] = (time.time() - rate_limit_start) * 1000

        # Get React UI format
        data = request.json
        original_query = data.get('query', data.get('question', ''))
        print(f"🌐 API Gateway received request: query={original_query[:50]}, model={data.get('model')}")

        # SECURITY: Step 1 - Validate input
        use_security = data.get('use_security', True)  # Enable by default
        security_violations = []
        cleaned_query = original_query
        timing_metrics['security_validation_ms'] = 0

        if use_security:
            print(f"🔒 Security validation enabled")
            security_start = time.time()

            security_result = security_client.validate_input(
                query=original_query,
                use_case='educational',
                config={
                    'check_pii': True,
                    'check_injection': True,
                    'check_topics': True,
                    'check_unicode': True,
                    'block_on_violation': False  # Warn instead of block
                }
            )

            timing_metrics['security_validation_ms'] = (time.time() - security_start) * 1000
            print(f"⏱️  Security validation took {timing_metrics['security_validation_ms']:.1f}ms")

            # Check if blocked
            if security_result['status'] == 'blocked':
                metrics.increment('security_blocked_requests')
                print(f"🚫 Request blocked by security: {security_result['violations']}")
                return jsonify({
                    'error': 'Query blocked by security policy',
                    'violations': security_result['violations'],
                    'status': 'blocked'
                }), 403

            # Use cleaned query and track violations
            cleaned_query = security_result.get('cleaned_query', original_query)
            security_violations = security_result.get('violations', [])

            if security_violations:
                print(f"⚠️  Security warnings: {len(security_violations)} violations detected")

        # ENHANCEMENT: Step 2 - Enhance prompt (optional)
        use_enhancement = data.get('use_enhancement', False)  # Disabled by default for now
        timing_metrics['prompt_enhancement_ms'] = 0

        if use_enhancement:
            print(f"✨ Prompt enhancement enabled")
            enhancement_start = time.time()

            enhancement_result = enhancement_client.enhance(
                query=cleaned_query,
                config={
                    'enhancement_level': 'standard',
                    'output_format': 'markdown',
                    'query_type': 'default'
                }
            )

            timing_metrics['prompt_enhancement_ms'] = (time.time() - enhancement_start) * 1000
            print(f"⏱️  Prompt enhancement took {timing_metrics['prompt_enhancement_ms']:.1f}ms")

            enhanced_query = enhancement_result.get('enhanced_prompt', cleaned_query)
        else:
            enhanced_query = cleaned_query

        # Transform to chat service format (frontend sends snake_case)
        chat_request = {
            'question': enhanced_query,
            'top_k': data.get('top_k', 5),
            'use_query_expansion': data.get('use_query_expansion', False),
            'use_bm25': data.get('use_bm25', False),
            'use_hybrid': data.get('use_hybrid', False),
            'use_graph': data.get('use_graph', False),
            'use_reranking': data.get('use_reranking', False),
            'use_web_search': data.get('use_web_search', False),
            'web_search_docs': data.get('web_search_docs', 5),
            'web_search_pages_per_doc': data.get('web_search_pages_per_doc', 1),
            'rerank_top_k': data.get('rerank_top_k', 10),
            'model': data.get('model', 'llama3.2:3b'),
            'temperature': data.get('temperature', 0.7),
        }
        print(f"🔍 API Gateway forwarding config: top_k={chat_request['top_k']}, use_web_search={chat_request['use_web_search']}, web_search_docs={chat_request['web_search_docs']}")
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

        # Add security information and timing metrics to response
        chat_response = response.json()

        # Calculate total API Gateway overhead
        gateway_overhead_ms = (time.time() - gateway_start) * 1000
        # Subtract the chat service time to get just gateway overhead
        chat_service_time = chat_response.get('metrics', {}).get('total_latency_ms', 0)
        timing_metrics['api_gateway_overhead_ms'] = max(0, gateway_overhead_ms - chat_service_time)

        # Merge timing metrics into response
        if 'metrics' not in chat_response:
            chat_response['metrics'] = {}

        chat_response['metrics'].update(timing_metrics)
        print(f"⏱️  Total gateway overhead: {timing_metrics['api_gateway_overhead_ms']:.1f}ms")

        # HALLUCINATION DETECTION: Validate citations against retrieved sources
        hallucination_warnings = _detect_hallucinated_citations(
            chat_response.get('answer', ''),
            chat_response.get('sources', [])
        )
        if hallucination_warnings:
            chat_response['citation_warnings'] = hallucination_warnings
            print(f"⚠️  Detected {len(hallucination_warnings)} potential citation issues")

        # ENRICH SOURCE METADATA: Add transparent source information
        if 'sources' in chat_response:
            chat_response['sources'] = _enrich_source_metadata(chat_response['sources'])

        # Add security information
        if use_security and security_violations:
            chat_response['security'] = {
                'violations': security_violations,
                'cleaned_query_used': cleaned_query != original_query
            }

        return jsonify(chat_response)
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

@app.route('/api/gpu_status', methods=['GET'])
def get_gpu_status():
    """Check if Ollama is using GPU"""
    try:
        import subprocess
        import os

        # Try to detect GPU from Ollama container
        ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://ollama:11434')

        # Check if Ollama is accessible
        try:
            response = requests.get(f"{ollama_url}/api/tags", timeout=5)
            ollama_accessible = response.status_code == 200
        except:
            ollama_accessible = False

        # Try to check GPU via docker exec (if running in Docker)
        gpu_available = False
        gpu_info = "Unknown"

        try:
            # Try nvidia-smi command
            result = subprocess.run(
                ['docker', 'exec', 'rag-ollama', 'nvidia-smi', '--query-gpu=name,utilization.gpu,memory.used,memory.total', '--format=csv,noheader'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout:
                gpu_available = True
                gpu_info = result.stdout.strip()
        except:
            # If nvidia-smi fails, GPU is not available
            pass

        return jsonify({
            'gpu_available': gpu_available,
            'gpu_enabled': gpu_available,  # If nvidia-smi works, GPU is enabled
            'gpu_info': gpu_info,
            'ollama_accessible': ollama_accessible,
            'mode': 'GPU' if gpu_available else 'CPU',
            'recommendation': 'Optimal performance' if gpu_available else '⚠️ GPU not detected - running on CPU (slower)'
        })
    except Exception as e:
        return jsonify({
            'gpu_available': False,
            'gpu_enabled': False,
            'gpu_info': f'Error: {str(e)}',
            'ollama_accessible': False,
            'mode': 'Unknown',
            'recommendation': 'Unable to detect GPU status'
        }), 500

# === Root ===

# ============================================================
# Authentication Proxy Routes
# ============================================================

@app.route('/api/auth/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_auth(subpath):
    """Proxy all auth requests to auth service"""
    try:
        # Build target URL
        target_url = f"{AUTH_SERVICE_URL}/{subpath}"
        
        # Forward the request
        if request.method == 'GET':
            response = requests.get(target_url, params=request.args, headers=dict(request.headers))
        elif request.method == 'POST':
            response = requests.post(target_url, json=request.json, headers=dict(request.headers))
        elif request.method == 'PUT':
            response = requests.put(target_url, json=request.json, headers=dict(request.headers))
        elif request.method == 'DELETE':
            response = requests.delete(target_url, headers=dict(request.headers))
        
        # Return response
        return Response(
            response.content,
            status=response.status_code,
            headers=dict(response.headers)
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
            'ask': '/api/ask',
            'auth': '/api/auth/*'
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

