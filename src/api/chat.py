"""
Chat API routes
"""
from flask import Blueprint, request, jsonify, Response, stream_with_context
import requests
import os
import json
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

bp = Blueprint('chat', __name__)

@bp.route('/chat', methods=['POST'])
def chat():
    """Chat with RAG system"""
    data = request.json
    query = data.get('query', '')

    # Get configuration from request
    top_k = data.get('topK', 5)
    use_query_expansion = data.get('useQueryExpansion', False)
    use_bm25 = data.get('useBM25', False)
    use_hybrid = data.get('useHybrid', False)
    use_graph = data.get('useGraph', False)
    use_reranking = data.get('useReranking', False)
    use_web_search = data.get('useWebSearch', False)
    model = data.get('model', 'llama3.2:3b')
    temperature = data.get('temperature', 0.7)

    if not query:
        return jsonify({'error': 'Query is required'}), 400

    try:
        # Search for relevant documents
        search_url = os.getenv('SEARCH_SERVICE_URL', 'http://search-service:8002')
        search_response = requests.post(
            f"{search_url}/search_with_config",
            json={
                'query': query,
                'config': {
                    'top_k': top_k,
                    'use_query_expansion': use_query_expansion,
                    'use_bm25': use_bm25,
                    'use_hybrid': use_hybrid,
                    'use_graph': use_graph,
                    'use_reranking': use_reranking,
                    'use_web_search': use_web_search,
                }
            },
            timeout=60
        )

        if search_response.status_code != 200:
            return jsonify({'error': 'Search failed'}), 500

        search_data = search_response.json()
        results = search_data.get('results', [])
        metrics = search_data.get('metrics', {})

        if not results:
            return jsonify({
                'answer': 'No relevant information found.',
                'sources': [],
                'metrics': metrics
            })

        # Build context for LLM
        context_text = "# Relevant Information\n\n"
        sources = []

        for i, result in enumerate(results, 1):
            file_name = result.get('file_name', 'Unknown')
            chunk_text = result.get('chunk_text', '')
            score = result.get('score', 0)

            context_text += f"## Source {i}: {file_name}\n"
            context_text += f"Relevance: {score:.3f}\n\n"
            context_text += f"{chunk_text}\n\n"
            context_text += "---\n\n"

            sources.append({
                'file_name': file_name,
                'chunk_text': chunk_text[:200] + '...' if len(chunk_text) > 200 else chunk_text,
                'score': round(score, 3),
                'metadata': result.get('metadata', {})
            })

        # Create prompt
        prompt = f"""Based on the following information, please answer this question:

Question: {query}

{context_text}

Instructions:
- Answer using ONLY the information provided above
- If the information isn't sufficient, say so
- Cite which sources you used (by source number)
- Be concise but thorough

Answer:"""

        # Call Ollama
        ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://ollama:11434')
        llm_response = requests.post(
            f"{ollama_url}/api/generate",
            json={
                'model': model,
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': temperature,
                }
            },
            timeout=120
        )

        if llm_response.status_code != 200:
            return jsonify({'error': 'LLM generation failed'}), 500

        llm_data = llm_response.json()
        answer = llm_data.get('response', '')

        return jsonify({
            'answer': answer,
            'sources': sources,
            'metrics': {
                **metrics,
                'model': model,
                'temperature': temperature,
                'top_k': top_k,
            }
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/search', methods=['POST'])
def search():
    """Search documents without LLM generation"""
    data = request.json
    query = data.get('query', '')
    top_k = data.get('topK', 5)

    if not query:
        return jsonify({'error': 'Query is required'}), 400

    try:
        search_url = os.getenv('SEARCH_SERVICE_URL', 'http://search-service:8002')
        response = requests.post(
            f"{search_url}/search",
            json={'query': query, 'limit': top_k},
            timeout=30
        )

        if response.status_code != 200:
            return jsonify({'error': 'Search failed'}), 500

        return jsonify(response.json())

    except Exception as e:
        return jsonify({'error': str(e)}), 500

