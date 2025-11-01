#!/usr/bin/env python3
"""
Simple web frontend for RAG Q&A
"""
from flask import Flask, render_template, request, jsonify, stream_with_context, Response
import requests
import os
from search import VaultSearcher
from advanced_search import AdvancedSearcher
import config
import json

app = Flask(__name__)
# Use advanced search if available, fall back to vector search
try:
    searcher = AdvancedSearcher()
    search_mode = 'advanced'
except Exception as e:
    print(f"⚠️  Advanced search failed to initialize: {e}")
    print(f"   Falling back to vector search only")
    searcher = VaultSearcher()
    search_mode = 'vector'

print(f"🔍 Search mode: {search_mode}")


@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')


@app.route('/api/stats')
def stats():
    """Get vault statistics"""
    try:
        # First try microservices
        vector_db_url = os.getenv('VECTOR_DB_URL', 'http://vector-db:8005')
        try:
            import requests
            response = requests.get(f"{vector_db_url}/stats", timeout=5)
            if response.status_code == 200:
                stats_data = response.json()
                print(f"✅ Got stats from microservices: {stats_data}")
                return jsonify({
                    'total_chunks': stats_data.get('total_chunks', 0),
                    'unique_files': stats_data.get('unique_files', 0),
                    'embedding_model': stats_data.get('embedding_model', 'nomic-embed-text'),
                    'chat_model': os.getenv('CHAT_MODEL', 'llama3.2:3b'),
                    'vault_path': str(config.VAULT_PATH),
                    'search_mode': 'microservices'
                })
        except Exception as microservices_error:
            print(f"⚠️ Microservices unavailable: {microservices_error}")

        # Fallback to monolithic mode
        # Get collection from searcher (works for both VaultSearcher and AdvancedSearcher)
        collection = None

        if hasattr(searcher, 'collection'):
            # VaultSearcher has direct collection
            collection = searcher.collection
        elif hasattr(searcher, 'hybrid_searcher'):
            # AdvancedSearcher -> HybridSearcher -> VaultSearcher -> collection
            collection = searcher.hybrid_searcher.vector_searcher.collection
        elif hasattr(searcher, 'vector_searcher'):
            # HybridSearcher -> VaultSearcher -> collection
            collection = searcher.vector_searcher.collection

        if not collection:
            return jsonify({'error': 'No index found'}), 500

        return jsonify({
            'total_chunks': collection.count(),
            'embedding_model': config.EMBEDDING_MODEL,
            'chat_model': config.CHAT_MODEL,
            'vault_path': str(config.VAULT_PATH),
            'search_mode': search_mode
        })
    except Exception as e:
        print(f"❌ Stats error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/search', methods=['POST'])
def search():
    """Search the vault"""
    data = request.json
    query = data.get('query', '')
    limit = data.get('limit', 5)

    if not query:
        return jsonify({'error': 'Query is required'}), 400

    try:
        # Try microservices first
        search_url = os.getenv('SEARCH_SERVICE_URL', 'http://search-service:8002')
        try:
            response = requests.post(
                f"{search_url}/search",
                json={'query': query, 'limit': limit, 'expand_query': True},
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                print(f"✅ Got {len(results)} results from microservices")

                # Format results for UI
                formatted_results = []
                for r in results:
                    formatted_results.append({
                        'title': r.get('metadata', {}).get('title', 'Unknown'),
                        'file': r.get('metadata', {}).get('file_name', 'Unknown'),
                        'score': round(r.get('score', 0), 3),
                        'content': r.get('content', '')[:300] + '...' if len(r.get('content', '')) > 300 else r.get('content', '')
                    })
                return jsonify({'results': formatted_results})
        except Exception as e:
            print(f"⚠️ Microservices search failed: {e}")

        # Fallback to monolithic
        # Use advanced search if available
        if search_mode == 'advanced':
            results = searcher.search(
                query,
                limit=limit,
                expand_query=True,
                use_graph=True,
                rerank=False  # Disable LLM re-ranking (too slow)
            )
        else:
            results = searcher.search(query, limit=limit)

        # Format results
        formatted_results = []
        for r in results:
            formatted_results.append({
                'title': r['metadata']['title'],
                'file': r['metadata']['file_name'],
                'score': round(r['score'], 3),
                'content': r['content'][:300] + '...' if len(r['content']) > 300 else r['content']
            })

        return jsonify({'results': formatted_results})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat with RAG (streaming)"""
    data = request.json
    question = data.get('question', '')
    num_contexts = data.get('num_contexts', 5)

    if not question:
        return jsonify({'error': 'Question is required'}), 400

    try:
        # Try microservices first
        search_url = os.getenv('SEARCH_SERVICE_URL', 'http://search-service:8002')
        results = []

        try:
            response = requests.post(
                f"{search_url}/search",
                json={'query': question, 'limit': num_contexts, 'expand_query': True},
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                print(f"✅ Got {len(results)} results from microservices for chat")
        except Exception as e:
            print(f"⚠️ Microservices search failed, trying monolithic: {e}")
            # Fallback to monolithic
            try:
                results = searcher.search(question, limit=num_contexts)
            except:
                pass

        if not results:
            return jsonify({
                'answer': 'No relevant information found in your vault.',
                'sources': []
            })

        # Build context
        context_text = "# Relevant Information from Your Vault\n\n"
        sources = []

        for i, result in enumerate(results, 1):
            metadata = result.get('metadata', {})
            context_text += f"## Source {i}: {metadata.get('title', 'Unknown')}\n"
            context_text += f"File: {metadata.get('file_name', 'Unknown')}\n"
            context_text += f"Relevance: {result.get('score', 0):.3f}\n\n"
            context_text += f"{result.get('content', '')}\n\n"
            context_text += "---\n\n"

            sources.append({
                'title': metadata.get('title', 'Unknown'),
                'file': metadata.get('file_name', 'Unknown'),
                'score': round(result.get('score', 0), 3)
            })

        # Create prompt
        prompt = f"""Based on the following information from my knowledge vault, please answer this question:

Question: {question}

{context_text}

Instructions:
- Answer the question using ONLY the information provided above
- If the information isn't sufficient, say so
- Cite which sources you used (by source number)
- Be concise but thorough

Answer:"""

        # Call Ollama with streaming
        def generate():
            try:
                # Send status update
                yield json.dumps({'type': 'status', 'message': f'🔍 Searching vault (microservices)...'}) + '\n'
                yield json.dumps({'type': 'status', 'message': f'📝 Found {len(results)} relevant chunks. Generating answer...'}) + '\n'

                ollama_url = os.getenv('OLLAMA_BASE_URL', config.OLLAMA_BASE_URL)
                response = requests.post(
                    f"{ollama_url}/api/generate",
                    json={
                        "model": config.CHAT_MODEL,
                        "prompt": prompt,
                        "stream": True,
                        "options": {
                            "temperature": 0.7,
                            "num_predict": 500
                        }
                    },
                    stream=True,
                    timeout=120
                )
                response.raise_for_status()

                # Stream answer chunks
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line)
                            if 'response' in chunk:
                                yield json.dumps({'type': 'chunk', 'content': chunk['response']}) + '\n'
                            if chunk.get('done'):
                                break
                        except json.JSONDecodeError:
                            continue

                # Send sources at the end
                yield json.dumps({'type': 'end', 'sources': sources}) + '\n'

            except requests.exceptions.ConnectionError:
                yield json.dumps({'type': 'error', 'message': 'Cannot connect to Ollama. Is it running?'}) + '\n'
            except requests.exceptions.Timeout:
                yield json.dumps({'type': 'error', 'message': 'Ollama response timed out.'}) + '\n'
            except Exception as e:
                yield json.dumps({'type': 'error', 'message': str(e)}) + '\n'

        return Response(stream_with_context(generate()), mimetype='application/json')

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload file to ingest service"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided', 'success': False}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected', 'success': False}), 400

        # Forward to ingest service
        ingest_url = os.getenv('INGEST_SERVICE_URL', 'http://ingest-service:8001')

        try:
            files = {'file': (file.filename, file.stream, file.content_type)}
            response = requests.post(f"{ingest_url}/upload", files=files, timeout=300)

            if response.status_code == 200:
                result = response.json()
                return jsonify(result)
            else:
                error_msg = response.json().get('error', 'Upload failed') if response.headers.get('content-type') == 'application/json' else 'Upload failed'
                return jsonify({'error': error_msg, 'success': False}), response.status_code
        except requests.exceptions.Timeout:
            return jsonify({'error': 'Upload timeout - file may be too large or processing is slow', 'success': False}), 504
        except Exception as e:
            return jsonify({'error': f'Error contacting ingest service: {str(e)}', 'success': False}), 500

    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


if __name__ == '__main__':
    # Use port 5555 (ports 5000/8080 often in use on macOS)
    app.run(host='0.0.0.0', port=5555, debug=False)

