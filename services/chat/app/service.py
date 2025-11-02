"""
Chat Service - RAG orchestration
Coordinates search, context building, and LLM generation
"""
from flask import Flask, request, jsonify, Response, stream_with_context
import requests
import json
import sys

# Add common to path
sys.path.insert(0, '/workspace/services/common')

from config import *
from metrics import ServiceMetrics, timed
from health import HealthCheck

app = Flask(__name__)

# Initialize metrics
metrics = ServiceMetrics("chat-service")

# Initialize health checks
health = HealthCheck("chat-service")

def check_services():
    """Check if required services are available"""
    services = {
        'search': SEARCH_SERVICE_URL,
        'llm': LLM_SERVICE_URL
    }

    for name, url in services.items():
        try:
            if name == 'llm':
                response = requests.get(f"{url}/api/tags", timeout=5)
            else:
                response = requests.get(f"{url}/health", timeout=5)
            if response.status_code != 200:
                return False
        except:
            return False
    return True

# Health checks
health.add_check("services_available", check_services)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify(health.get_health())

@app.route('/metrics', methods=['GET'])
def get_metrics():
    """Metrics endpoint"""
    return jsonify(metrics.get_stats())

@app.route('/context', methods=['POST'])
@timed(metrics, 'build_context')
def build_context():
    """
    Build context for a question (without generating answer)

    Body:
    {
        "question": "What is AI?",
        "num_contexts": 5
    }

    Returns:
    {
        "context": "...",
        "sources": [...]
    }
    """
    try:
        data = request.json
        question = data.get('question', '')
        num_contexts = data.get('num_contexts', 5)

        if not question:
            return jsonify({'error': 'question required'}), 400

        metrics.increment('context_requests')

        # Search for relevant context
        search_response = requests.post(
            f"{SEARCH_SERVICE_URL}/search",
            json={
                'query': question,
                'limit': num_contexts
            },
            timeout=30
        )
        search_response.raise_for_status()

        results = search_response.json()['results']

        if not results:
            return jsonify({
                'context': '',
                'sources': [],
                'message': 'No relevant information found'
            })

        # Build context text
        context_text = "# Relevant Information\n\n"
        sources = []

        for i, result in enumerate(results, 1):
            metadata = result['metadata']
            context_text += f"## Source {i}: {metadata.get('title', 'Unknown')}\n"
            context_text += f"File: {metadata.get('file_name', 'Unknown')}\n"
            context_text += f"Relevance: {result['score']:.3f}\n\n"
            context_text += f"{result['content']}\n\n"
            context_text += "---\n\n"

            sources.append({
                'title': metadata.get('title', 'Unknown'),
                'file': metadata.get('file_name', 'Unknown'),
                'score': round(result['score'], 3)
            })

        metrics.increment('context_success')

        return jsonify({
            'context': context_text,
            'sources': sources,
            'count': len(sources)
        })

    except Exception as e:
        metrics.increment('context_errors')
        return jsonify({'error': str(e)}), 500

@app.route('/ask', methods=['POST'])
@timed(metrics, 'ask_question')
def ask_question():
    """
    Ask a question with RAG (non-streaming)

    Body:
    {
        "question": "What is AI?",
        "num_contexts": 5
    }

    Returns:
    {
        "answer": "...",
        "sources": [...]
    }
    """
    try:
        data = request.json
        question = data.get('question', '')
        num_contexts = data.get('num_contexts', 5)

        if not question:
            return jsonify({'error': 'question required'}), 400

        metrics.increment('ask_requests')

        # Get RAG config
        search_config = {
            'top_k': num_contexts,
            'use_query_expansion': data.get('use_query_expansion', False),
            'use_bm25': data.get('use_bm25', False),
            'use_hybrid': data.get('use_hybrid', False),
            'use_graph': data.get('use_graph', False),
            'use_reranking': data.get('use_reranking', False),
            'use_web_search': data.get('use_web_search', False),
        }

        # Get context with config
        context_response = requests.post(
            f"{SEARCH_SERVICE_URL}/search_with_config",
            json={
                'query': question,
                'config': search_config
            },
            timeout=180  # Increased to 3 minutes for slow operations (reranking, graph, web search)
        )
        context_response.raise_for_status()

        search_data = context_response.json()
        results = search_data.get('results', [])
        search_metrics = search_data.get('metrics', {})

        if not results:
            metrics.increment('no_context_found')
            return jsonify({
                'answer': 'No relevant information found in the knowledge base.',
                'sources': [],
                'metrics': search_metrics
            })

        # Build context
        context_text = "# Relevant Information from Knowledge Base\n\n"
        sources = []

        for i, result in enumerate(results, 1):
            metadata = result.get('metadata', {})
            content = result.get('content', '')
            score = result.get('score', 0)

            context_text += f"## Source {i}: {metadata.get('title', 'Unknown')}\n"
            context_text += f"File: {metadata.get('file_name', 'Unknown')}\n"
            context_text += f"Relevance: {score:.3f}\n\n"
            context_text += f"{content}\n\n"
            context_text += "---\n\n"

            sources.append({
                'id': result.get('id', ''),
                'file_name': metadata.get('file_name', 'Unknown'),
                'chunk_text': content[:200] + '...' if len(content) > 200 else content,
                'score': round(score, 3),
                'metadata': metadata,
                'page_number': metadata.get('page_number', 1)
            })

        # Create prompt
        prompt = f"""Based on the following information from the knowledge base, please answer this question:

Question: {question}

{context_text}

Instructions:
- Answer the question using ONLY the information provided above
- If the information isn't sufficient, say so
- Cite which sources you used (by source number)
- Be concise but thorough

Answer:"""

        # Generate answer via Ollama
        model = data.get('model', CHAT_MODEL)
        temperature = data.get('temperature', 0.7)

        llm_response = requests.post(
            f"{LLM_SERVICE_URL}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": 500
                }
            },
            timeout=300  # Increased to 5 minutes for slow LLM generation
        )
        llm_response.raise_for_status()

        answer = llm_response.json()['response']

        metrics.increment('ask_success')

        return jsonify({
            'answer': answer,
            'sources': sources,
            'metrics': {
                **search_metrics,
                'model': model,
                'temperature': temperature,
                'context_chunks': len(sources)
            }
        })

    except requests.exceptions.ConnectionError:
        metrics.increment('ask_errors')
        return jsonify({'error': 'Cannot connect to LLM service'}), 503
    except requests.exceptions.Timeout:
        metrics.increment('ask_errors')
        return jsonify({'error': 'LLM service timeout'}), 504
    except Exception as e:
        metrics.increment('ask_errors')
        return jsonify({'error': str(e)}), 500

@app.route('/stream', methods=['POST'])
def stream_answer():
    """
    Ask a question with RAG (streaming)

    Body:
    {
        "question": "What is AI?",
        "num_contexts": 5
    }

    Returns: Server-Sent Events stream
    """
    def generate():
        try:
            data = request.json
            question = data.get('question', '')
            num_contexts = data.get('num_contexts', 5)

            if not question:
                yield json.dumps({'type': 'error', 'message': 'question required'}) + '\n'
                return

            metrics.increment('stream_requests')

            # Send status
            yield json.dumps({'type': 'status', 'message': '🔍 Searching knowledge base...'}) + '\n'

            # Search for context
            context_response = requests.post(
                f"{SEARCH_SERVICE_URL}/search",
                json={
                    'query': question,
                    'limit': num_contexts
                },
                timeout=30
            )
            context_response.raise_for_status()

            results = context_response.json()['results']

            if not results:
                yield json.dumps({
                    'type': 'answer',
                    'content': 'No relevant information found in the knowledge base.'
                }) + '\n'
                yield json.dumps({'type': 'end', 'sources': []}) + '\n'
                return

            # Build context
            context_text = "# Relevant Information from Knowledge Base\n\n"
            sources = []

            for i, result in enumerate(results, 1):
                metadata = result['metadata']
                context_text += f"## Source {i}: {metadata.get('title', 'Unknown')}\n"
                context_text += f"File: {metadata.get('file_name', 'Unknown')}\n"
                context_text += f"Relevance: {result['score']:.3f}\n\n"
                context_text += f"{result['content']}\n\n"
                context_text += "---\n\n"

                sources.append({
                    'title': metadata.get('title', 'Unknown'),
                    'file': metadata.get('file_name', 'Unknown'),
                    'score': round(result['score'], 3)
                })

            # Send status
            yield json.dumps({'type': 'status', 'message': '📝 Context retrieved. Generating answer...'}) + '\n'

            # Create prompt
            prompt = f"""Based on the following information from the knowledge base, please answer this question:

Question: {question}

{context_text}

Instructions:
- Answer the question using ONLY the information provided above
- If the information isn't sufficient, say so
- Cite which sources you used (by source number)
- Be concise but thorough

Answer:"""

            # Stream answer from Ollama
            llm_response = requests.post(
                f"{LLM_SERVICE_URL}/api/generate",
                json={
                    "model": CHAT_MODEL,
                    "prompt": prompt,
                    "stream": True,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 500
                    }
                },
                stream=True,
                timeout=120
            )
            llm_response.raise_for_status()

            # Stream response chunks
            for line in llm_response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        if 'response' in chunk:
                            yield json.dumps({'type': 'chunk', 'content': chunk['response']}) + '\n'
                        if chunk.get('done'):
                            break
                    except json.JSONDecodeError:
                        continue

            # Send sources
            yield json.dumps({'type': 'end', 'sources': sources}) + '\n'

            metrics.increment('stream_success')

        except Exception as e:
            metrics.increment('stream_errors')
            yield json.dumps({'type': 'error', 'message': str(e)}) + '\n'

    return Response(stream_with_context(generate()), mimetype='application/json')

if __name__ == '__main__':
    print("🚀 Chat Service starting...")
    print(f"🔍 Search Service: {SEARCH_SERVICE_URL}")
    print(f"🤖 LLM Service: {LLM_SERVICE_URL}")
    print(f"💬 Chat Model: {CHAT_MODEL}")

    # Start server
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=False)

