#!/usr/bin/env python3
"""
Simple web frontend for RAG Q&A
"""
from flask import Flask, render_template, request, jsonify, stream_with_context, Response
import requests
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
        # Search for relevant context
        results = searcher.search(question, limit=num_contexts)
        
        if not results:
            return jsonify({
                'answer': 'No relevant information found in your vault.',
                'sources': []
            })
        
        # Build context
        context_text = "# Relevant Information from Your Vault\n\n"
        sources = []
        
        for i, result in enumerate(results, 1):
            context_text += f"## Source {i}: {result['metadata']['title']}\n"
            context_text += f"File: {result['metadata']['file_name']}\n"
            context_text += f"Relevance: {result['score']:.3f}\n\n"
            context_text += f"{result['content']}\n\n"
            context_text += "---\n\n"
            
            sources.append({
                'title': result['metadata']['title'],
                'file': result['metadata']['file_name'],
                'score': round(result['score'], 3)
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
                yield json.dumps({'type': 'status', 'message': f'🔍 Searching vault ({search_mode})...'}) + '\n'
                
                # Perform search
                if search_mode == 'advanced':
                    results = searcher.search(
                        question,
                        limit=num_contexts,
                        expand_query=True,
                        use_graph=True,
                        rerank=False  # Disable LLM re-ranking (too slow)
                    )
                else:
                    results = searcher.search(question, limit=num_contexts)
                
                # Send another status
                yield json.dumps({'type': 'status', 'message': '📝 Context retrieved. Generating answer...'}) + '\n'
                
                response = requests.post(
                    f"{config.OLLAMA_BASE_URL}/api/generate",
                    json={
                        "model": config.CHAT_MODEL,
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


if __name__ == '__main__':
    # Use port 5555 (ports 5000/8080 often in use on macOS)
    app.run(host='0.0.0.0', port=5555, debug=False)

