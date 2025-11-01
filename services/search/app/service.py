"""
Search Service - Hybrid search orchestration
Combines vector search, BM25, and knowledge graph for optimal retrieval
"""
from flask import Flask, request, jsonify
import requests
import sys
import pickle
import os
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict
import re

# Add common and src to path
sys.path.insert(0, '/workspace/services/common')
sys.path.insert(0, '/workspace/src')

from config import *
from metrics import ServiceMetrics, timed
from health import HealthCheck

# Import BM25
from rank_bm25 import BM25Okapi

# Import query expansion
try:
    from query_expansion import QueryExpander
    QUERY_EXPANSION_AVAILABLE = True
except ImportError:
    QUERY_EXPANSION_AVAILABLE = False
    print("⚠️  Query expansion not available")

app = Flask(__name__)

# Initialize metrics
metrics = ServiceMetrics("search-service")

# Initialize health checks
health = HealthCheck("search-service")

# Initialize query expander
if QUERY_EXPANSION_AVAILABLE:
    query_expander = QueryExpander()
    print("✅ Query expansion enabled")
else:
    query_expander = None
    print("❌ Query expansion disabled")

# BM25 index (loaded on startup)
bm25_index = None
bm25_docs = []
bm25_metadata = []
bm25_index_path = Path("/indices/bm25_index.pkl")

def load_bm25_index():
    """Load BM25 index from disk"""
    global bm25_index, bm25_docs, bm25_metadata

    if bm25_index_path.exists():
        try:
            with open(bm25_index_path, 'rb') as f:
                data = pickle.load(f)
                bm25_index = data['bm25']
                bm25_docs = data['docs']
                bm25_metadata = data['metadata']
            print(f"✅ Loaded BM25 index: {len(bm25_docs)} documents")
            return True
        except Exception as e:
            print(f"❌ Failed to load BM25 index: {e}")
            return False
    else:
        print(f"⚠️  BM25 index not found at {bm25_index_path}")
        return False

def tokenize(text: str) -> List[str]:
    """Simple tokenization"""
    text = text.lower()
    tokens = re.findall(r'\b\w+\b', text)
    return tokens

def reciprocal_rank_fusion(rankings: List[List[Dict]], k: int = 60) -> List[Dict]:
    """
    Combine multiple rankings using Reciprocal Rank Fusion

    Args:
        rankings: List of ranking lists (each with 'id' and 'score')
        k: RRF constant (default 60)

    Returns:
        Fused ranking
    """
    scores = defaultdict(float)
    doc_data = {}

    for ranking in rankings:
        for rank, doc in enumerate(ranking):
            doc_id = doc.get('id') or doc.get('metadata', {}).get('file_name', '')
            scores[doc_id] += 1.0 / (k + rank + 1)
            if doc_id not in doc_data:
                doc_data[doc_id] = doc

    # Sort by score
    fused = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # Build result
    result = []
    for doc_id, score in fused:
        doc = doc_data[doc_id].copy()
        doc['score'] = score
        doc['fusion_score'] = score
        result.append(doc)

    return result

# Health checks
health.add_check("vector_db_connection", lambda: check_service(os.getenv('VECTOR_DB_URL', 'http://vector-db:8005')))
health.add_check("bm25_index_loaded", lambda: bm25_index is not None)

def check_service(url: str) -> bool:
    """Check if service is available"""
    try:
        response = requests.get(f"{url}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify(health.get_health())

@app.route('/metrics', methods=['GET'])
def get_metrics():
    """Metrics endpoint"""
    return jsonify(metrics.get_stats())

@app.route('/index/build', methods=['POST'])
@timed(metrics, 'build_index')
def build_bm25_index():
    """Build BM25 index from vector database"""
    global bm25_index, bm25_docs, bm25_metadata

    try:
        print("🔨 Building BM25 index...")

        # Get config values
        vector_db_url = os.getenv('VECTOR_DB_URL', 'http://vector-db:8005')
        bm25_path = os.getenv('BM25_INDEX_PATH', '/indices/bm25_index.pkl')

        # Get all documents from vector DB
        response = requests.get(f"{vector_db_url}/stats", timeout=30)
        response.raise_for_status()
        stats = response.json()

        total_chunks = stats.get('total_chunks', 0)
        if total_chunks == 0:
            return jsonify({
                'success': False,
                'message': 'No documents in vector database'
            }), 400

        # Fetch all documents
        response = requests.post(
            f"{vector_db_url}/get_all",
            json={},
            timeout=60
        )
        response.raise_for_status()
        data = response.json()

        documents = data.get('documents', [])
        metadatas = data.get('metadatas', [])

        if not documents:
            return jsonify({
                'success': False,
                'message': 'No documents retrieved from vector database'
            }), 400

        print(f"📚 Retrieved {len(documents)} documents")

        # Tokenize documents
        tokenized_docs = [tokenize(doc) for doc in documents]

        # Build BM25 index
        bm25_index = BM25Okapi(tokenized_docs)
        bm25_docs = documents
        bm25_metadata = metadatas

        # Save to disk
        index_path = Path(bm25_path)
        index_path.parent.mkdir(parents=True, exist_ok=True)

        with open(index_path, 'wb') as f:
            pickle.dump({
                'index': bm25_index,
                'docs': bm25_docs,
                'metadata': bm25_metadata
            }, f)

        print(f"✅ BM25 index built and saved: {len(documents)} documents")
        metrics.increment('index_builds')
        metrics.set_gauge('indexed_documents', len(documents))

        return jsonify({
            'success': True,
            'documents_indexed': len(documents),
            'unique_files': len(set(m.get('file_name', '') for m in metadatas))
        })

    except Exception as e:
        print(f"❌ Error building BM25 index: {e}")
        metrics.increment('index_build_errors')
        return jsonify({'error': str(e)}), 500

@app.route('/search/vector', methods=['POST'])
@timed(metrics, 'vector_search')
def vector_search():
    """
    Vector similarity search only

    Body:
    {
        "query": "search text",
        "limit": 10
    }
    """
    try:
        data = request.json
        query = data.get('query', '')
        limit = data.get('limit', DEFAULT_SEARCH_LIMIT)

        if not query:
            return jsonify({'error': 'query required'}), 400

        metrics.increment('vector_search_requests')

        # Generate embedding for query
        embed_response = requests.post(
            f"{EMBEDDING_SERVICE_URL}/embed",
            json={'text': query},
            timeout=30
        )
        embed_response.raise_for_status()
        query_embedding = embed_response.json()['embedding']

        # Search vector DB
        search_response = requests.post(
            f"{VECTOR_DB_URL}/search",
            json={
                'query_embeddings': [query_embedding],
                'n_results': limit
            },
            timeout=30
        )
        search_response.raise_for_status()

        results = search_response.json()

        # Format results
        formatted = []
        if results.get('documents') and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                formatted.append({
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'score': 1.0 - results['distances'][0][i],  # Convert distance to similarity
                    'id': results['ids'][0][i]
                })

        metrics.increment('vector_search_success')

        return jsonify({
            'results': formatted,
            'count': len(formatted)
        })

    except Exception as e:
        metrics.increment('vector_search_errors')
        return jsonify({'error': str(e)}), 500

@app.route('/search/bm25', methods=['POST'])
@timed(metrics, 'bm25_search')
def bm25_search():
    """
    BM25 keyword search only

    Body:
    {
        "query": "search text",
        "limit": 10
    }
    """
    try:
        data = request.json
        query = data.get('query', '')
        limit = data.get('limit', DEFAULT_SEARCH_LIMIT)

        if not query:
            return jsonify({'error': 'query required'}), 400

        if not bm25_index:
            return jsonify({'error': 'BM25 index not available'}), 503

        metrics.increment('bm25_search_requests')

        # Tokenize query
        query_tokens = tokenize(query)

        # BM25 search
        scores = bm25_index.get_scores(query_tokens)

        # Get top k indices
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:limit]

        # Format results
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append({
                    'content': bm25_docs[idx],
                    'metadata': bm25_metadata[idx],
                    'score': float(scores[idx]),
                    'id': bm25_metadata[idx].get('file_name', f'doc_{idx}')
                })

        metrics.increment('bm25_search_success')

        return jsonify({
            'results': results,
            'count': len(results)
        })

    except Exception as e:
        metrics.increment('bm25_search_errors')
        return jsonify({'error': str(e)}), 500

@app.route('/search/hybrid', methods=['POST'])
@timed(metrics, 'hybrid_search')
def hybrid_search():
    """
    Hybrid search combining vector and BM25

    Body:
    {
        "query": "search text",
        "limit": 10,
        "vector_weight": 0.7,
        "bm25_weight": 0.3
    }
    """
    try:
        data = request.json
        query = data.get('query', '')
        limit = data.get('limit', DEFAULT_SEARCH_LIMIT)

        if not query:
            return jsonify({'error': 'query required'}), 400

        metrics.increment('hybrid_search_requests')

        # Perform both searches
        vector_results = vector_search_internal(query, limit * 2)  # Get more for fusion
        bm25_results = bm25_search_internal(query, limit * 2) if bm25_index else []

        # Fuse results
        if bm25_results:
            fused = reciprocal_rank_fusion([vector_results, bm25_results])
        else:
            fused = vector_results

        # Limit results
        fused = fused[:limit]

        metrics.increment('hybrid_search_success')

        return jsonify({
            'results': fused,
            'count': len(fused),
            'method': 'hybrid' if bm25_results else 'vector_only'
        })

    except Exception as e:
        metrics.increment('hybrid_search_errors')
        return jsonify({'error': str(e)}), 500

def vector_search_internal(query: str, limit: int) -> List[Dict]:
    """Internal vector search"""
    # Get config values
    embedding_url = os.getenv('EMBEDDING_SERVICE_URL', 'http://embedding-service:8006')
    vector_db_url = os.getenv('VECTOR_DB_URL', 'http://vector-db:8005')

    # Generate embedding
    embed_response = requests.post(
        f"{embedding_url}/embed",
        json={'text': query},
        timeout=30
    )
    embed_response.raise_for_status()
    query_embedding = embed_response.json()['embedding']

    # Search
    search_response = requests.post(
        f"{vector_db_url}/search",
        json={
            'query_embeddings': [query_embedding],
            'n_results': limit
        },
        timeout=30
    )
    search_response.raise_for_status()

    results = search_response.json()

    formatted = []
    if results.get('documents') and results['documents'][0]:
        for i in range(len(results['documents'][0])):
            formatted.append({
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'score': 1.0 - results['distances'][0][i],
                'id': results['ids'][0][i]
            })

    return formatted

def bm25_search_internal(query: str, limit: int) -> List[Dict]:
    """Internal BM25 search"""
    if not bm25_index:
        return []

    query_tokens = tokenize(query)
    scores = bm25_index.get_scores(query_tokens)
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:limit]

    results = []
    for idx in top_indices:
        if scores[idx] > 0:
            results.append({
                'content': bm25_docs[idx],
                'metadata': bm25_metadata[idx],
                'score': float(scores[idx]),
                'id': bm25_metadata[idx].get('file_name', f'doc_{idx}')
            })

    return results

@app.route('/search', methods=['POST'])
@timed(metrics, 'search')
def search():
    """
    Advanced search with query expansion and hybrid search

    Body:
    {
        "query": "search text",
        "limit": 10,
        "expand_query": true,    // Enable query expansion (default: true)
        "use_graph": false,       // Enable knowledge graph (default: false)
        "use_reranking": false    // Enable LLM re-ranking (default: false, adds 2000ms)
    }
    """
    try:
        data = request.json
        query = data.get('query', '')
        limit = data.get('limit', DEFAULT_SEARCH_LIMIT)
        expand = data.get('expand_query', True)
        use_graph = data.get('use_graph', False)
        use_reranking = data.get('use_reranking', False)

        if not query:
            return jsonify({'error': 'query required'}), 400

        # Step 1: Query Expansion
        original_query = query
        if expand and query_expander:
            query = query_expander.expand_with_context(query)
            print(f"📝 Query expanded: '{original_query}' → '{query}'")
            metrics.increment('queries_expanded')

        # Step 2: Hybrid Search
        # Use hybrid if BM25 available, otherwise vector
        if bm25_index:
            # Perform both searches
            vector_results = vector_search_internal(query, limit * 2)
            bm25_results = bm25_search_internal(query, limit * 2)

            # Fuse results
            fused = reciprocal_rank_fusion([vector_results, bm25_results])
            fused = fused[:limit * 2]  # Keep extra for graph/reranking
            method = 'hybrid'
        else:
            fused = vector_search_internal(query, limit * 2)
            method = 'vector_only'

        # Step 3: Knowledge Graph Enhancement (optional)
        if use_graph and fused:
            kg_url = os.getenv('KNOWLEDGE_GRAPH_URL', 'http://knowledge-graph:8007')
            try:
                # Get related documents for top 5 results
                related_docs = set()
                for result in fused[:5]:
                    doc_id = result.get('metadata', {}).get('file_name', '')
                    if doc_id:
                        response = requests.get(
                            f"{kg_url}/related/{doc_id}",
                            params={'limit': 5},
                            timeout=5
                        )
                        if response.status_code == 200:
                            related = response.json().get('related', [])
                            related_docs.update(related)

                # Add related documents (with lower scores)
                existing_ids = {r.get('metadata', {}).get('file_name', '') for r in fused}
                for doc_id in related_docs:
                    if doc_id not in existing_ids:
                        # Fetch from vector DB
                        vector_db_url = os.getenv('VECTOR_DB_URL', 'http://vector-db:8005')
                        response = requests.post(
                            f"{vector_db_url}/search",
                            json={'query': doc_id, 'limit': 1},
                            timeout=5
                        )
                        if response.status_code == 200:
                            results = response.json().get('results', [])
                            if results:
                                result = results[0]
                                result['score'] = result.get('score', 0) * 0.5  # Lower score
                                result['source'] = 'knowledge_graph'
                                fused.append(result)

                print(f"🕸️  Graph enhanced to {len(fused)} results")
                metrics.increment('graph_enhancements')
            except Exception as e:
                print(f"⚠️  Knowledge graph enhancement failed: {e}")
                metrics.increment('graph_enhancement_errors')

        # Step 4: LLM Re-ranking (optional, slow)
        if use_reranking and fused:
            reranker_url = os.getenv('RERANKER_URL', 'http://reranker:8008')
            try:
                response = requests.post(
                    f"{reranker_url}/rerank",
                    json={
                        'query': original_query,
                        'results': fused,
                        'limit': limit
                    },
                    timeout=60  # Long timeout for LLM processing
                )
                if response.status_code == 200:
                    reranked_data = response.json()
                    fused = reranked_data.get('results', fused)
                    print(f"📊 Re-ranked to {len(fused)} results")
                    metrics.increment('reranking_success')
                else:
                    print(f"⚠️  Re-ranking failed with status {response.status_code}")
                    metrics.increment('reranking_errors')
            except Exception as e:
                print(f"⚠️  Re-ranking failed: {e}")
                metrics.increment('reranking_errors')

        # Final limit
        final_results = fused[:limit]

        metrics.increment('search_success')

        return jsonify({
            'results': final_results,
            'count': len(final_results),
            'method': method,
            'original_query': original_query,
            'expanded_query': query if expand and query != original_query else None,
            'used_graph': use_graph,
            'used_reranking': use_reranking
        })

    except Exception as e:
        metrics.increment('search_errors')
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Search Service starting...")
    print(f"📊 Vector DB URL configured")
    print(f"🧮 Embedding Service URL configured")

    # Load BM25 index
    load_bm25_index()

    # Start server
    port = int(os.getenv('SERVICE_PORT', '8002'))
    app.run(host='0.0.0.0', port=port, debug=False)

