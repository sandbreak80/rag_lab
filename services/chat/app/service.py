"""
Chat Service - RAG orchestration
Coordinates search, context building, and LLM generation
"""
from flask import Flask, request, jsonify, Response, stream_with_context
import requests
import json
import sys
import time

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

@app.route('/version', methods=['GET'])
def get_version():
    """Version endpoint"""
    return jsonify(health.get_version())

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
            timeout=900  # 15 minutes for search (Maximum preset needs time)
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
            print("❌ Error: question required")
            return jsonify({'error': 'question required'}), 400

        print(f"📥 Received question: {question[:100]}...")
        print(f"🔍 DEBUG - Full request data keys: {list(data.keys())}")
        print(f"🔍 DEBUG - top_k from request: {data.get('top_k', 'NOT PROVIDED')}")
        print(f"🔍 DEBUG - use_web_search from request: {data.get('use_web_search', 'NOT PROVIDED')}")
        print(f"🔍 DEBUG - web_search_docs from request: {data.get('web_search_docs', 'NOT PROVIDED')}")
        metrics.increment('ask_requests')

        # Get RAG config from request (use ALL parameters from frontend)
        search_config = {
            'top_k': data.get('top_k', num_contexts),  # Use frontend value or fallback
            'use_query_expansion': data.get('use_query_expansion', False),
            'use_bm25': data.get('use_bm25', False),
            'use_hybrid': data.get('use_hybrid', False),
            'use_graph': data.get('use_graph', False),
            'use_reranking': data.get('use_reranking', False),
            'use_web_search': data.get('use_web_search', False),
            'web_search_docs': data.get('web_search_docs', 5),
            'web_search_pages_per_doc': data.get('web_search_pages_per_doc', 1),
            'rerank_top_k': data.get('rerank_top_k', 10),
        }
        print(f"⚙️  RAG config: {search_config}")

        # Track detailed timing
        perf_metrics = {}
        overall_start = time.time()

        # QUERY DECOMPOSITION (Optional): Break complex queries into sub-queries
        use_decomposition = data.get('use_query_decomposition', False)
        decomposition_data = None

        if use_decomposition:
            try:
                decomposer_url = os.getenv('QUERY_DECOMPOSER_URL', 'http://query-decomposer:8019')
                decomp_start = time.time()

                decomp_response = requests.post(
                    f"{decomposer_url}/decompose",
                    json={'query': question, 'max_subqueries': 3},
                    timeout=30
                )

                if decomp_response.status_code == 200:
                    decomposition_data = decomp_response.json()
                    perf_metrics['query_decomposition_ms'] = round((time.time() - decomp_start) * 1000, 2)
                    print(f"🧩 Query decomposition: {decomposition_data['needs_decomposition']} in {perf_metrics['query_decomposition_ms']}ms")
                else:
                    print(f"⚠️  Query decomposition failed: {decomp_response.status_code}")
            except Exception as e:
                print(f"⚠️  Query decomposition error: {e}")

        # Determine search strategy based on decomposition
        if decomposition_data and decomposition_data.get('needs_decomposition'):
            # Complex query: Use sub-queries for parallel search
            sub_queries = decomposition_data.get('sub_queries', [question])
            print(f"🧩 Decomposed into {len(sub_queries)} sub-queries: {sub_queries}")
        else:
            # Simple query: Single search
            sub_queries = [question]

        # Get context with config
        print(f"🔍 Calling search service at {SEARCH_SERVICE_URL}/search_with_config")
        search_start = time.time()
        context_response = requests.post(
            f"{SEARCH_SERVICE_URL}/search_with_config",
            json={
                'query': question,
                'config': search_config
            },
            timeout=900  # 15 minutes for complex RAG pipelines (Maximum preset)
        )
        context_response.raise_for_status()
        perf_metrics['search_service_latency_ms'] = round((time.time() - search_start) * 1000, 2)
        print(f"✅ Search completed in {perf_metrics['search_service_latency_ms']}ms")

        search_data = context_response.json()
        results = search_data.get('results', [])
        search_metrics = search_data.get('metrics', {})
        print(f"📊 Retrieved {len(results)} results")

        if not results:
            print("⚠️  No relevant context found")
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
                'source': result.get('source', 'rag'),  # Pass through source type!
                'metadata': metadata,
                'page_number': metadata.get('page_number', 1)
            })

        # Create prompt - Enhanced for depth and detail
        prompt = f"""You are an expert technical assistant with deep knowledge across multiple domains. Answer the following question using the provided context as your primary source, but feel free to draw on your training to provide comprehensive, detailed explanations.

Question: {question}

{context_text}

Instructions:
- Provide a thorough, detailed answer that demonstrates deep understanding
- Use the context provided as your foundation, but expand with additional relevant details and explanations
- Include technical details, examples, and connections between concepts where appropriate
- If discussing multiple concepts, explain each one comprehensively
- Cite which sources you used (by source number) when referencing specific information from the context
- Structure your answer with clear sections if covering multiple topics
- Be educational and informative - assume the reader wants to truly understand the subject

Provide a comprehensive, detailed answer:"""

        # Generate answer via Ollama
        model = data.get('model', CHAT_MODEL)
        temperature = data.get('temperature', 0.7)
        print(f"🤖 Generating answer with model: {model}, temp: {temperature}")
        print(f"🔗 LLM URL: {LLM_SERVICE_URL}/api/generate")

        # Retry logic for Ollama (sometimes model needs to load)
        max_retries = 3  # Increased to 3 retries
        retry_delay = 3  # Increased to 3 seconds
        llm_response = None

        llm_start = time.time()
        for attempt in range(max_retries):
            try:
                print(f"🔄 Attempt {attempt + 1}/{max_retries}: Calling Ollama...")
                llm_response = requests.post(
                    f"{LLM_SERVICE_URL}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": 2000,  # Increased for detailed responses
                            "top_k": 40,
                            "top_p": 0.9
                        }
                    },
                    timeout=900  # 15 minutes for slow LLM generation (Maximum preset)
                )

                # Check if response is successful
                if llm_response.status_code == 200:
                    print(f"✅ Ollama responded successfully")
                    break

                # Log non-200 response
                print(f"⚠️  Ollama returned {llm_response.status_code}: {llm_response.text[:200]}")

                # If 404, model might not be loaded - retry
                if llm_response.status_code == 404 and attempt < max_retries - 1:
                    print(f"🔄 Model not found, waiting {retry_delay}s and retrying...")
                    time.sleep(retry_delay)
                    continue

                # If last attempt and still failing, raise
                if attempt == max_retries - 1:
                    llm_response.raise_for_status()

            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    print(f"⏱️  Timeout, retrying (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(retry_delay)
                    continue
                raise
            except requests.exceptions.ConnectionError as e:
                if attempt < max_retries - 1:
                    print(f"🔌 Connection error, retrying (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(retry_delay)
                    continue
                raise
            except requests.exceptions.HTTPError:
                # Only raise if it's the last attempt
                if attempt == max_retries - 1:
                    raise
                print(f"⚠️  HTTP error, retrying...")
                time.sleep(retry_delay)
                continue

        # Final check - if we never got a 200 response, raise the last error
        if llm_response is None or llm_response.status_code != 200:
            if llm_response is not None:
                llm_response.raise_for_status()
            else:
                raise Exception("Failed to get response from Ollama after all retries")

        perf_metrics['llm_generation_ms'] = round((time.time() - llm_start) * 1000, 2)
        print(f"✅ LLM generation completed in {perf_metrics['llm_generation_ms']}ms")

        llm_json = llm_response.json()
        answer = llm_json['response']
        print(f"📝 Answer length: {len(answer)} characters")

        # Extract Ollama-specific metrics if available
        if 'eval_count' in llm_json:
            perf_metrics['llm_tokens_generated'] = llm_json.get('eval_count', 0)
            perf_metrics['llm_tokens_prompt'] = llm_json.get('prompt_eval_count', 0)
            perf_metrics['llm_eval_duration_ms'] = round(llm_json.get('eval_duration', 0) / 1_000_000, 2)  # Convert ns to ms
            perf_metrics['llm_prompt_eval_duration_ms'] = round(llm_json.get('prompt_eval_duration', 0) / 1_000_000, 2)

            # Calculate tokens per second
            if perf_metrics['llm_eval_duration_ms'] > 0:
                perf_metrics['llm_tokens_per_second'] = round(
                    (perf_metrics['llm_tokens_generated'] / perf_metrics['llm_eval_duration_ms']) * 1000, 2
                )

            print(f"📊 Ollama metrics: {perf_metrics['llm_tokens_generated']} tokens @ {perf_metrics.get('llm_tokens_per_second', 0)} tok/s")

        # Calculate total latency
        perf_metrics['total_latency_ms'] = round((time.time() - overall_start) * 1000, 2)
        perf_metrics['chat_service_overhead_ms'] = round(
            perf_metrics['total_latency_ms'] -
            perf_metrics['search_service_latency_ms'] -
            perf_metrics['llm_generation_ms'], 2
        )

        metrics.increment('ask_success')

        response_data = {
            'answer': answer,
            'sources': sources,
            'metrics': {
                **search_metrics,  # All the search service metrics
                **perf_metrics,    # Chat service + LLM metrics
                'model': model,
                'temperature': temperature,
                'context_chunks': len(sources),
                # Add token counts in frontend-expected format
                'prompt_tokens': perf_metrics.get('llm_tokens_prompt', 0),
                'completion_tokens': perf_metrics.get('llm_tokens_generated', 0),
                'total_tokens': perf_metrics.get('llm_tokens_prompt', 0) + perf_metrics.get('llm_tokens_generated', 0),
            }
        }

        # Add decomposition data if available
        if decomposition_data:
            response_data['decomposition'] = {
                'needs_decomposition': decomposition_data.get('needs_decomposition', False),
                'complexity': decomposition_data.get('complexity', 'simple'),
                'sub_queries': decomposition_data.get('sub_queries', []),
                'original_query': decomposition_data.get('original_query', question)
            }

        return jsonify(response_data)

    except requests.exceptions.ConnectionError as e:
        error_msg = f'Cannot connect to search/LLM service: {str(e)}'
        print(f"❌ ConnectionError: {error_msg}")
        metrics.increment('ask_errors')
        return jsonify({'error': error_msg, 'type': 'connection_error'}), 503
    except requests.exceptions.Timeout as e:
        error_msg = f'Service timeout after waiting: {str(e)}'
        print(f"❌ Timeout: {error_msg}")
        metrics.increment('ask_errors')
        return jsonify({'error': error_msg, 'type': 'timeout'}), 504
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"❌ Exception: {error_msg}")
        metrics.increment('ask_errors')
        import traceback
        traceback.print_exc()
        return jsonify({'error': error_msg, 'type': 'internal_error'}), 500

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
                timeout=180
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
                timeout=180
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

