"""
Search Service - Hybrid search orchestration
Combines vector search, BM25, and knowledge graph for optimal retrieval
"""
from flask import Flask, request, jsonify
import requests
import sys
import pickle
import os
import time
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
                bm25_index = data['index']  # Key is 'index', not 'bm25'
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

@app.route('/version', methods=['GET'])
def get_version():
    """Version endpoint"""
    return jsonify(health.get_version())

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
        response = requests.get(f"{vector_db_url}/stats", timeout=180)
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
            timeout=180
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
            timeout=180
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
            timeout=180
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

def vector_search_internal(query: str, limit: int, metadata_filters: Optional[Dict] = None) -> List[Dict]:
    """Internal vector search with optional metadata filters"""
    # Get config values
    embedding_url = os.getenv('EMBEDDING_SERVICE_URL', 'http://embedding-service:8006')
    vector_db_url = os.getenv('VECTOR_DB_URL', 'http://vector-db:8005')

    # Generate embedding
    embed_response = requests.post(
        f"{embedding_url}/embed",
        json={'text': query},
        timeout=180
    )
    embed_response.raise_for_status()
    query_embedding = embed_response.json()['embedding']

    # Prepare search request
    search_body = {
        'query_embeddings': [query_embedding],
        'n_results': limit
    }

    # Add metadata filters if provided
    if metadata_filters:
        search_body['metadata_filters'] = metadata_filters

    # Search
    search_response = requests.post(
        f"{vector_db_url}/search",
        json=search_body,
        timeout=180
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

def bm25_search_internal(query: str, limit: int, metadata_filters: Optional[Dict] = None) -> List[Dict]:
    """Internal BM25 search with optional metadata filters"""
    if not bm25_index:
        print("⚠️  BM25: No index available")
        return []

    query_tokens = tokenize(query)
    print(f"🔍 BM25: Query tokens: {query_tokens[:10]}")
    print(f"🔍 BM25: Index has {len(bm25_docs)} documents")

    scores = bm25_index.get_scores(query_tokens)
    print(f"🔍 BM25: Score range: {min(scores):.4f} - {max(scores):.4f}")

    # Get all scored indices
    scored_indices = [(i, scores[i]) for i in range(len(scores)) if scores[i] > 0]
    scored_indices.sort(key=lambda x: x[1], reverse=True)

    results = []
    for idx, score in scored_indices:
        metadata = bm25_metadata[idx]

        # Apply metadata filters if provided
        if metadata_filters:
            if not _matches_filters(metadata, metadata_filters):
                continue

        results.append({
            'content': bm25_docs[idx],
            'metadata': metadata,
            'score': float(score),
            'id': metadata.get('file_name', f'doc_{idx}')
        })

        # Stop when we have enough results
        if len(results) >= limit:
            break

    print(f"🔍 BM25: Returning {len(results)} results (filtered: {len(scored_indices)} → {len(results)})")
    return results

def _matches_filters(metadata: Dict, filters: Dict) -> bool:
    """Check if metadata matches the provided filters"""
    # Document types filter
    if filters.get('documentTypes'):
        doc_type = metadata.get('type', metadata.get('file_type', ''))
        if doc_type not in filters['documentTypes']:
            return False

    # Sources filter
    if filters.get('sources'):
        source = metadata.get('source', '')
        if source not in filters['sources']:
            return False

    # Tags filter
    if filters.get('tags'):
        doc_tags = metadata.get('tags', [])
        if not any(tag in doc_tags for tag in filters['tags']):
            return False

    # Date range filter
    if filters.get('dateRange'):
        doc_date = metadata.get('created_at', metadata.get('date', ''))
        if doc_date:
            date_range = filters['dateRange']
            if date_range.get('start') and doc_date < date_range['start']:
                return False
            if date_range.get('end') and doc_date > date_range['end']:
                return False

    # Authors filter
    if filters.get('authors'):
        author = metadata.get('author', '')
        if author not in filters['authors']:
            return False

    return True

def decompose_query_to_multi_queries(query: str, query_expander) -> List[str]:
    """
    🚀 FRONTIER MODEL TECHNIQUE: Multi-Query Decomposition

    Break complex prompts into 3-5 focused sub-queries for parallel search.
    This is how GPT-4, Claude, and Perplexity handle complex multi-topic questions.

    Example:
    Input: "Explain LLMs, RAG, backpropagation, knowledge graphs, and prompt injection attacks"
    Output: [
        "Large Language Models architecture and training",
        "Retrieval Augmented Generation RAG systems",
        "Backpropagation neural networks",
        "Knowledge graphs for LLM applications",
        "Prompt injection security attacks"
    ]

    Args:
        query: Original complex query
        query_expander: LLM-based query expander

    Returns:
        List of 3-5 focused sub-queries
    """
    if not query_expander:
        print("⚠️  Query decomposition: No LLM available, returning original query")
        return [query]

    # Only decompose complex queries (> 30 words or multiple topics)
    word_count = len(query.split())
    if word_count < 30:
        print(f"⚠️  Query decomposition: Query too short ({word_count} words), skipping")
        return [query]

    try:
        print(f"🔍 Multi-Query Decomposition: Breaking down {word_count}-word query...")

        decomposition_prompt = f"""Break this complex query into 3-5 simple search queries. Each query should be 5-10 words and focus on ONE topic.

EXAMPLE:
Input: "Explain LLMs, RAG, and neural networks"
Output:
Large Language Models architecture
Retrieval Augmented Generation systems
Neural network training methods

Now break down this query:
{query[:1000]}

Output (one query per line):"""

        response = query_expander.expand_with_context(decomposition_prompt)

        # Parse response into list of queries
        sub_queries = []

        # Filter out instruction lines (common patterns to skip)
        skip_patterns = [
            'you are', 'break this', 'rules:', 'each sub-query', 'return only',
            'no numbering', 'no explanations', 'make queries', 'complex query',
            'sub-queries:', 'should focus', 'one per line', 'specific and searchable'
        ]

        for line in response.strip().split('\n'):
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Skip instruction lines
            line_lower = line.lower()
            if any(pattern in line_lower for pattern in skip_patterns):
                continue

            # Remove numbering (1., 2., etc.)
            line = re.sub(r'^\d+[\.\)]\s*', '', line)
            # Remove quotes
            line = line.strip('"\'')
            # Remove bullet points
            line = line.lstrip('•-*')
            line = line.strip()

            # Must be 5-50 words (reasonable query length)
            word_count = len(line.split())
            if line and 5 <= word_count <= 50:
                sub_queries.append(line)

        # Limit to 3-5 queries
        sub_queries = sub_queries[:5]

        if len(sub_queries) >= 2:
            print(f"✅ Decomposed into {len(sub_queries)} sub-queries:")
            for i, sq in enumerate(sub_queries, 1):
                print(f"   {i}. {sq}")
            return sub_queries
        else:
            print(f"⚠️  Decomposition returned {len(sub_queries)} queries, using original")
            return [query]

    except Exception as e:
        print(f"❌ Query decomposition failed: {e}, using original query")
        return [query]

def multi_query_web_search(queries: List[str], web_search_url: str, docs_per_query: int = 2, timeout: int = 180) -> List[Dict]:
    """
    🚀 FRONTIER MODEL TECHNIQUE: Parallel Multi-Query Search

    Run multiple focused searches in parallel and combine results.
    This is how Perplexity AI handles complex multi-topic questions.

    Args:
        queries: List of focused sub-queries
        web_search_url: Web search service URL
        docs_per_query: Number of results per query (default: 2)
        timeout: Request timeout in seconds

    Returns:
        Combined and deduplicated web results
    """
    all_results = []
    seen_urls = set()

    print(f"🌐 Running {len(queries)} parallel web searches...")

    for i, query in enumerate(queries, 1):
        try:
            print(f"   🔍 Query {i}/{len(queries)}: {query[:60]}...")

            response = requests.post(
                f"{web_search_url}/search",
                json={
                    'query': query,
                    'limit': docs_per_query,
                    'pages_per_result': 1
                },
                timeout=timeout
            )

            if response.status_code == 200:
                web_data = response.json()
                results = web_data.get('results', [])

                # Deduplicate by URL
                new_results = 0
                for result in results:
                    url = result.get('url', '')
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_results.append(result)
                        new_results += 1

                print(f"      ✅ {len(results)} results ({new_results} new)")
            else:
                print(f"      ⚠️  HTTP {response.status_code}")

        except Exception as e:
            print(f"      ❌ Error: {e}")
            continue

    print(f"✅ Multi-query search complete: {len(all_results)} unique results from {len(queries)} queries")
    return all_results

def filter_web_results_by_quality(results: List[Dict]) -> List[Dict]:
    """
    🚀 BEST PRACTICE: Quality Filtering for Web Results

    Boost high-quality sources (.edu, .gov, Wikipedia, arXiv) and filter spam.

    Args:
        results: Raw web search results

    Returns:
        Filtered and re-scored results
    """
    # Quality domains (boost these)
    quality_domains = {
        'wikipedia.org': 1.3,
        'arxiv.org': 1.4,
        '.edu': 1.3,
        '.gov': 1.2,
        'stackoverflow.com': 1.2,
        'github.com': 1.1,
    }

    # Spam indicators (filter these)
    spam_indicators = [
        'click here',
        'buy now',
        'limited time',
        'subscribe',
        'advertisement',
    ]

    filtered = []

    for result in results:
        url = result.get('url', '').lower()
        content = result.get('content', '').lower()
        title = result.get('title', '').lower()

        # Filter spam
        is_spam = any(indicator in content or indicator in title for indicator in spam_indicators)
        if is_spam:
            print(f"   🚫 Filtered spam: {result.get('title', 'Unknown')[:50]}")
            continue

        # Filter short content (< 100 chars)
        if len(content) < 100:
            print(f"   🚫 Filtered short content: {result.get('title', 'Unknown')[:50]}")
            continue

        # Boost quality domains
        score = result.get('score', 0.5)
        boost = 1.0
        for domain, domain_boost in quality_domains.items():
            if domain in url:
                boost = domain_boost
                print(f"   ⭐ Boosted quality source ({domain}): {result.get('title', 'Unknown')[:50]}")
                break

        result['score'] = score * boost
        filtered.append(result)

    # Sort by score
    filtered.sort(key=lambda x: x.get('score', 0), reverse=True)

    print(f"✅ Quality filter: {len(results)} → {len(filtered)} results")
    return filtered

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
        "use_reranking": false,   // Enable LLM re-ranking (default: false, adds 2000ms)
        "metadata_filters": {...} // Optional metadata filters
    }
    """
    try:
        data = request.json
        query = data.get('query', '')
        limit = data.get('limit', DEFAULT_SEARCH_LIMIT)
        expand = data.get('expand_query', True)
        use_graph = data.get('use_graph', False)
        use_reranking = data.get('use_reranking', False)
        metadata_filters = data.get('metadata_filters', None)

        if not query:
            return jsonify({'error': 'query required'}), 400

        # Log filters if provided
        if metadata_filters:
            print(f"🔍 Applying metadata filters: {metadata_filters}")

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
            vector_results = vector_search_internal(query, limit * 2, metadata_filters)
            bm25_results = bm25_search_internal(query, limit * 2, metadata_filters)

            # Fuse results
            fused = reciprocal_rank_fusion([vector_results, bm25_results])
            fused = fused[:limit * 2]  # Keep extra for graph/reranking
            method = 'hybrid'
        else:
            fused = vector_search_internal(query, limit * 2, metadata_filters)
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
                    timeout=180  # 3 minutes for LLM processing
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

@app.route('/search_with_config', methods=['POST'])
def search_with_config():
    """
    Educational search endpoint with detailed configuration and metrics

    Body:
    {
        "query": "search text",
        "config": {
            "use_query_expansion": true,
            "use_bm25": true,
            "use_hybrid": true,
            "use_graph": false,
            "use_reranking": false,
            "top_k": 10
        }
    }

    Returns results + detailed performance metrics for each component
    """
    try:
        data = request.json
        query = data.get('query', '')
        config = data.get('config', {})

        print(f"\n🔍 ===== SEARCH REQUEST =====")
        print(f"Query: {query[:80]}...")

        if not query:
            return jsonify({'error': 'query required'}), 400

        # Default config
        use_query_expansion = config.get('use_query_expansion', True)
        use_bm25 = config.get('use_bm25', True)
        use_hybrid = config.get('use_hybrid', True)
        use_graph = config.get('use_graph', False)
        use_reranking = config.get('use_reranking', False)
        use_web_search = config.get('use_web_search', False)
        top_k = config.get('top_k', 10)

        print(f"Config: QE={use_query_expansion}, BM25={use_bm25}, Hybrid={use_hybrid}, Graph={use_graph}, Rerank={use_reranking}, WebSearch={use_web_search}, K={top_k}")

        # Performance tracking
        perf_metrics = {}
        start_time = time.time()

        # Step 1: Query Expansion
        original_query = query
        if use_query_expansion and query_expander:
            exp_start = time.time()
            query = query_expander.expand_with_context(query)
            perf_metrics['query_expansion_ms'] = round((time.time() - exp_start) * 1000, 2)
            perf_metrics['query_expanded'] = query != original_query
            print(f"✓ Query Expansion: {perf_metrics['query_expansion_ms']}ms (expanded={perf_metrics['query_expanded']})")
        else:
            perf_metrics['query_expansion_ms'] = 0
            perf_metrics['query_expanded'] = False
            print(f"⊘ Query Expansion: SKIPPED")

        # Step 2: Retrieval
        vector_results = []
        bm25_results = []

        # Vector search (always do this as baseline)
        vec_start = time.time()
        vector_results = vector_search_internal(query, top_k * 2)
        perf_metrics['vector_search_ms'] = round((time.time() - vec_start) * 1000, 2)
        perf_metrics['vector_results_count'] = len(vector_results)
        print(f"✓ Vector Search: {perf_metrics['vector_search_ms']}ms ({perf_metrics['vector_results_count']} results)")

        # BM25 search (if enabled and index available)
        if use_bm25 and bm25_index:
            bm25_start = time.time()
            bm25_results = bm25_search_internal(query, top_k * 2)
            perf_metrics['bm25_search_ms'] = round((time.time() - bm25_start) * 1000, 2)
            perf_metrics['bm25_results_count'] = len(bm25_results)
            print(f"✓ BM25 Search: {perf_metrics['bm25_search_ms']}ms ({perf_metrics['bm25_results_count']} results)")
        else:
            perf_metrics['bm25_search_ms'] = 0
            perf_metrics['bm25_results_count'] = 0

        # Hybrid fusion
        if use_hybrid and bm25_results:
            fusion_start = time.time()
            fused = reciprocal_rank_fusion([vector_results, bm25_results])
            perf_metrics['hybrid_fusion_ms'] = round((time.time() - fusion_start) * 1000, 2)
            perf_metrics['method'] = 'hybrid'
            print(f"✓ Hybrid Fusion: {perf_metrics['hybrid_fusion_ms']}ms")
        else:
            fused = vector_results
            perf_metrics['hybrid_fusion_ms'] = 0
            perf_metrics['method'] = 'vector_only'

        fused = fused[:top_k * 2]  # Keep extra for graph/reranking

        # Step 3: Knowledge Graph Enhancement
        if use_graph and fused:
            graph_start = time.time()
            kg_url = os.getenv('KNOWLEDGE_GRAPH_URL', 'http://knowledge-graph:8007')
            print(f"🕸️  Calling knowledge graph: {kg_url}/search_related")
            try:
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

                # Add related documents
                existing_ids = {r.get('metadata', {}).get('file_name', '') for r in fused}
                graph_added = 0
                for doc_id in related_docs:
                    if doc_id not in existing_ids:
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
                                result['score'] = result.get('score', 0) * 0.5
                                result['source'] = 'knowledge_graph'
                                fused.append(result)
                                graph_added += 1

                perf_metrics['graph_expansion_ms'] = round((time.time() - graph_start) * 1000, 2)
                perf_metrics['graph_docs_added'] = graph_added
                print(f"✓ Knowledge Graph: {perf_metrics['graph_expansion_ms']}ms ({perf_metrics['graph_docs_added']} docs added)")
            except Exception as e:
                perf_metrics['graph_expansion_ms'] = 0
                perf_metrics['graph_docs_added'] = 0
                perf_metrics['graph_error'] = str(e)
        else:
            perf_metrics['graph_expansion_ms'] = 0
            perf_metrics['graph_docs_added'] = 0
            print(f"⊘ Knowledge Graph: SKIPPED")

        # Step 3.5: Web Search (if enabled)
        if use_web_search:
            web_start = time.time()
            web_search_url = os.getenv('WEB_SEARCH_URL', 'http://web-search:8009')
            web_docs_limit = config.get('web_search_docs', 5)
            web_pages_per_doc = config.get('web_search_pages_per_doc', 1)

            try:
                word_count = len(original_query.split())

                # 🚀 FRONTIER MODEL TECHNIQUE: Multi-Query Decomposition
                # For complex queries (> 30 words), break into 3-5 sub-queries
                # This is how GPT-4, Claude, and Perplexity handle complex prompts
                if word_count > 30 and query_expander:
                    print(f"🚀 MULTI-QUERY MODE: {word_count}-word query detected")

                    # Step 1: Decompose into sub-queries
                    sub_queries = decompose_query_to_multi_queries(original_query, query_expander)
                    perf_metrics['web_search_queries_generated'] = len(sub_queries)

                    # Step 2: Run parallel searches (2 results per query)
                    docs_per_query = max(2, web_docs_limit // len(sub_queries))
                    web_results = multi_query_web_search(sub_queries, web_search_url, docs_per_query, timeout=180)

                    # Step 3: Quality filtering
                    web_results = filter_web_results_by_quality(web_results)

                    # Limit to requested number
                    web_results = web_results[:web_docs_limit]

                else:
                    # 🔍 SINGLE-QUERY MODE: Simple queries or short prompts
                    print(f"🔍 SINGLE-QUERY MODE: {word_count}-word query")

                    # For long single queries (> 50 words), extract key terms
                    web_query = original_query
                    if word_count > 50 and query_expander:
                        print(f"🔍 Extracting key search terms from long query...")
                        try:
                            extraction_prompt = f"""Extract 3-5 key search terms or topics from this query that would be good for web search. Return only the terms, comma-separated, no explanation:

{original_query[:500]}"""
                            web_query = query_expander.expand_with_context(extraction_prompt)
                            web_query = web_query.strip().strip('"\'').split('\n')[0]
                            print(f"🔍 Extracted: {web_query[:100]}")
                        except Exception as e:
                            print(f"⚠️ Extraction failed: {e}, using first sentence")
                            sentences = original_query.split('.')
                            web_query = sentences[0] if sentences else original_query[:200]

                    perf_metrics['web_search_queries_generated'] = 1

                    # Single search
                    print(f"🌐 Calling web search: {web_search_url}/search")
                    response = requests.post(
                        f"{web_search_url}/search",
                        json={
                            'query': web_query,
                            'limit': web_docs_limit,
                            'pages_per_result': web_pages_per_doc
                        },
                        timeout=180
                    )

                    if response.status_code == 200:
                        web_data = response.json()
                        web_results = web_data.get('results', [])

                        # Quality filtering
                        web_results = filter_web_results_by_quality(web_results)
                    else:
                        print(f"⚠️  Web Search: HTTP {response.status_code}")
                        web_results = []

                # Convert web results to standard format and add to fused results
                # Give web results competitive scores so they appear in top results
                for idx, web_result in enumerate(web_results):
                    # Score decreases from 0.95 to 0.75
                    web_score = 0.95 - (idx * 0.05)
                    fused.append({
                        'id': web_result.get('url', ''),
                        'content': web_result.get('content', web_result.get('snippet', '')),
                        'score': web_score,  # Competitive score for web results
                        'source': 'web_search',
                        'metadata': {
                            'title': web_result.get('title', 'Web Result'),
                            'file_name': web_result.get('url', 'web'),
                            'url': web_result.get('url', ''),
                            'engine': web_result.get('engine', 'searxng')
                        }
                    })

                perf_metrics['web_search_ms'] = round((time.time() - web_start) * 1000, 2)
                perf_metrics['web_results_count'] = len(web_results)
                perf_metrics['web_search_success'] = True
                print(f"✓ Web Search: {perf_metrics['web_search_ms']}ms ({perf_metrics['web_results_count']} results from {perf_metrics.get('web_search_queries_generated', 1)} queries)")

            except Exception as e:
                perf_metrics['web_search_ms'] = 0
                perf_metrics['web_results_count'] = 0
                perf_metrics['web_search_success'] = False
                perf_metrics['web_search_error'] = str(e)
                print(f"❌ Web Search error: {e}")
        else:
            perf_metrics['web_search_ms'] = 0
            perf_metrics['web_results_count'] = 0
            perf_metrics['web_search_success'] = False
            print(f"⊘ Web Search: SKIPPED")

        # Step 4: LLM Re-ranking
        if use_reranking and fused:
            rerank_start = time.time()
            reranker_url = os.getenv('RERANKER_SERVICE_URL', 'http://reranker:8008')
            print(f"🎯 Calling reranker: {reranker_url}/rerank")
            try:
                response = requests.post(
                    f"{reranker_url}/rerank",
                    json={
                        'query': original_query,
                        'results': fused,
                        'limit': top_k
                    },
                    timeout=180
                )
                if response.status_code == 200:
                    reranked_data = response.json()
                    fused = reranked_data.get('results', fused)
                    perf_metrics['reranking_ms'] = round((time.time() - rerank_start) * 1000, 2)
                    perf_metrics['reranking_success'] = True
                    print(f"✓ Reranking: {perf_metrics['reranking_ms']}ms (success={perf_metrics['reranking_success']})")
                else:
                    perf_metrics['reranking_ms'] = 0
                    perf_metrics['reranking_success'] = False
                    print(f"⚠️  Reranking: HTTP {response.status_code}")
            except Exception as e:
                perf_metrics['reranking_ms'] = 0
                perf_metrics['reranking_success'] = False
                perf_metrics['reranking_error'] = str(e)
                print(f"❌ Reranking error: {e}")
        else:
            perf_metrics['reranking_ms'] = 0
            perf_metrics['reranking_success'] = False
            print(f"⊘ Reranking: SKIPPED (enabled={use_reranking}, results={len(fused)})")

        # Final results - sort by score DESC to mix RAG and web results
        fused_sorted = sorted(fused, key=lambda x: x.get('score', 0), reverse=True)
        final_results = fused_sorted[:top_k]

        # Total time
        perf_metrics['total_latency_ms'] = round((time.time() - start_time) * 1000, 2)
        print(f"⏱️  TOTAL SEARCH: {perf_metrics['total_latency_ms']}ms")
        print(f"✅ Returning {len(final_results)} results\n")

        # Calculate breakdown percentages
        total = perf_metrics['total_latency_ms']
        if total > 0:
            perf_metrics['breakdown_percent'] = {
                'query_expansion': round((perf_metrics['query_expansion_ms'] / total) * 100, 1),
                'vector_search': round((perf_metrics['vector_search_ms'] / total) * 100, 1),
                'bm25_search': round((perf_metrics['bm25_search_ms'] / total) * 100, 1),
                'hybrid_fusion': round((perf_metrics['hybrid_fusion_ms'] / total) * 100, 1),
                'graph_expansion': round((perf_metrics['graph_expansion_ms'] / total) * 100, 1),
                'reranking': round((perf_metrics['reranking_ms'] / total) * 100, 1)
            }

        return jsonify({
            'results': final_results,
            'count': len(final_results),
            'query': {
                'original': original_query,
                'expanded': query if use_query_expansion and query != original_query else None
            },
            'config_used': config,
            'metrics': perf_metrics
        })

    except Exception as e:
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

