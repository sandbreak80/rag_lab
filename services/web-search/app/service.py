"""
Web Search Service - SearXNG Integration with Agentic Query Generation
Provides web search capabilities for RAG enhancement
Features:
- LLM-powered query generation (Llama 3.2:3B)
- Parallel multi-query search
- Result aggregation and deduplication
"""
from flask import Flask, request, jsonify
import requests
import os
import sys
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Set

# Add common to path
sys.path.insert(0, '/workspace/services/common')

from metrics import ServiceMetrics, timed
from health import HealthCheck

app = Flask(__name__)

# Configuration
SERVICE_PORT = int(os.getenv('SERVICE_PORT', 8009))
SEARXNG_URL = os.getenv('SEARXNG_URL', 'http://searxng:8080')
OLLAMA_URL = os.getenv('OLLAMA_BASE_URL', 'http://ollama:11434')
QUERY_GEN_MODEL = os.getenv('QUERY_GEN_MODEL', 'llama3.2:3b')  # Fast model for query generation

# Initialize metrics and health
metrics = ServiceMetrics("web-search-service")
health = HealthCheck("web-search-service")

@app.route('/health')
def health_check():
    """Health check endpoint"""
    # Check if SearXNG is accessible
    try:
        response = requests.get(f"{SEARXNG_URL}/", timeout=2)
        searxng_healthy = response.status_code == 200
    except:
        searxng_healthy = False

    return jsonify({
        'status': 'healthy' if searxng_healthy else 'degraded',
        'service': 'web-search-service',
        'searxng_accessible': searxng_healthy,
        'searxng_url': SEARXNG_URL
    })

@app.route('/metrics')
def get_metrics():
    """Metrics endpoint"""
    return jsonify(metrics.get_metrics())

# ============================================================================
# AGENTIC SEARCH - LLM-Powered Query Generation
# ============================================================================

def generate_search_queries(original_query: str, max_queries: int = 4) -> List[str]:
    """
    Use LLM to generate focused search queries from complex question

    Args:
        original_query: User's original question
        max_queries: Maximum number of queries to generate

    Returns:
        List of focused search queries
    """
    print(f"🧠 Generating search queries for: '{original_query[:80]}...'")

    prompt = f"""You are a web search expert. Generate {max_queries} focused search queries for this question.

User Question: "{original_query}"

Generate SHORT, keyword-focused queries optimized for web search engines:
- 3-8 words each
- Use keywords, not full sentences
- Focus on different aspects/angles
- No punctuation or question marks
- Optimize for Google/Bing/DuckDuckGo

Examples:
Question: "What are the latest transformer models?"
1. latest transformer models 2024 2025
2. new transformer architectures research
3. efficient transformer improvements
4. transformer model benchmarks

Question: "How does RAG work in LLMs?"
1. retrieval augmented generation explained
2. RAG LLM architecture
3. how RAG improves llm responses
4. RAG implementation guide

Now generate {max_queries} queries (number them 1-{max_queries}):
"""

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                'model': QUERY_GEN_MODEL,
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': 0.5,  # Some creativity, but focused
                    'num_predict': 4000,  # Allow detailed query generation with explanations
                    'stop': ['Question:', 'User Question:', '\n\n\n']  # Stop at new question or triple newline
                }
            },
            timeout=60
        )

        if response.status_code != 200:
            print(f"⚠️  LLM query generation failed: {response.status_code}")
            return [original_query]  # Fallback to original

        llm_output = response.json()['response']
        print(f"🤖 LLM output: {llm_output}")

        # Parse generated queries
        queries = parse_generated_queries(llm_output, max_queries)

        if not queries or len(queries) == 0:
            print("⚠️  No queries parsed, using original")
            return [original_query]

        print(f"✅ Generated {len(queries)} queries: {queries}")
        return queries

    except Exception as e:
        print(f"❌ Query generation error: {e}")
        return [original_query]  # Fallback

def parse_generated_queries(llm_output: str, max_count: int) -> List[str]:
    """
    Parse numbered queries from LLM output
    Handles formats: "1. query", "1) query", "- query"
    More robust parser that handles various LLM output formats
    """
    lines = llm_output.strip().split('\n')
    queries = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Skip intro/filler lines
        skip_patterns = [
            r'^here\s+(are|is)',
            r'^i\s+',
            r'^the\s+',
            r'^for\s+',
            r'^question:',
            r'^sub-questions:',
            r'^queries:',
        ]
        if any(re.match(pattern, line, re.IGNORECASE) for pattern in skip_patterns):
            continue

        # Remove common prefixes: "1. ", "1) ", "- ", "• ", "Q1:", etc
        cleaned = re.sub(r'^[\d]+[\.\)\:]?\s*', '', line)  # Remove "1. " or "1) " or "1: "
        cleaned = re.sub(r'^[-•\*]\s*', '', cleaned)       # Remove "- " or "• " or "* "
        cleaned = re.sub(r'^Q[\d]+[\:\.]?\s*', '', cleaned, flags=re.IGNORECASE)  # Remove "Q1: " or "Q1. "

        # Accept if it was modified (had a prefix) OR looks like a query
        had_prefix = (cleaned != line)
        looks_like_query = (
            10 < len(cleaned) < 150 and  # Reasonable length
            not cleaned.endswith('?') and  # Not a question (we want search terms)
            cleaned[0].islower() or cleaned[0].isupper()  # Starts with letter
        )

        if (had_prefix or looks_like_query) and 10 < len(cleaned) < 150:
            queries.append(cleaned)

        if len(queries) >= max_count:
            break

    return queries

def search_single_query(query: str, limit: int = 5) -> List[Dict]:
    """
    Execute a single search query against SearXNG

    Args:
        query: Search query string
        limit: Max results to return

    Returns:
        List of search results
    """
    try:
        search_url = f"{SEARXNG_URL}/search"
        params = {
            'q': query,
            'format': 'json',
            'categories': 'general',
            'pageno': 1
        }

        response = requests.get(search_url, params=params, timeout=30)
        response.raise_for_status()

        search_data = response.json()
        raw_results = search_data.get('results', [])

        # Format results
        results = []
        for item in raw_results[:limit]:
            result = {
                'title': item.get('title', ''),
                'url': item.get('url', ''),
                'content': item.get('content', ''),
                'engine': item.get('engine', 'unknown'),
                'score': item.get('score', 0.5),
                'source_query': query,  # Track which query generated this
                'category': item.get('category', 'general')
            }
            results.append(result)

        return results

    except Exception as e:
        print(f"❌ Search error for '{query}': {e}")
        return []

def execute_parallel_searches(queries: List[str], limit_per_query: int = 5) -> List[Dict]:
    """
    Execute multiple searches in parallel

    Args:
        queries: List of search queries
        limit_per_query: Max results per query

    Returns:
        Combined list of all results
    """
    all_results = []

    with ThreadPoolExecutor(max_workers=min(len(queries), 4)) as executor:
        # Submit all searches
        future_to_query = {
            executor.submit(search_single_query, q, limit_per_query): q
            for q in queries
        }

        # Collect results as they complete
        for future in as_completed(future_to_query):
            query = future_to_query[future]
            try:
                results = future.result()
                print(f"✅ Query '{query}' returned {len(results)} results")
                all_results.extend(results)
            except Exception as e:
                print(f"❌ Query '{query}' failed: {e}")

    return all_results

def aggregate_and_deduplicate(results: List[Dict]) -> List[Dict]:
    """
    Deduplicate results by URL and rank by score
    Results appearing in multiple queries get boosted scores

    Args:
        results: List of search results

    Returns:
        Deduplicated and ranked results
    """
    # Track URLs and their occurrences
    url_to_result: Dict[str, Dict] = {}
    url_appearances: Dict[str, int] = {}

    for result in results:
        url = result['url']

        if url not in url_to_result:
            url_to_result[url] = result.copy()
            url_appearances[url] = 1
        else:
            # URL appeared in multiple queries - boost it!
            url_appearances[url] += 1
            # Keep the result with higher score
            if result['score'] > url_to_result[url]['score']:
                url_to_result[url] = result.copy()

    # Apply multi-query boost
    for url, result in url_to_result.items():
        appearances = url_appearances[url]
        if appearances > 1:
            # Boost score by 0.1 for each additional appearance
            result['score'] = min(1.0, result['score'] + (appearances - 1) * 0.1)
            result['multi_query_match'] = appearances

    # Sort by score (highest first)
    ranked_results = sorted(url_to_result.values(), key=lambda r: r['score'], reverse=True)

    print(f"📊 Deduplication: {len(results)} → {len(ranked_results)} unique results")

    return ranked_results

@app.route('/search', methods=['POST'])
@timed(metrics, 'web_search')
def web_search():
    """
    Perform web search using SearXNG

    Body:
    {
        "query": "search query",
        "limit": 5,
        "categories": ["general", "science", "news"]
    }

    Returns:
    {
        "results": [
            {
                "title": "...",
                "url": "...",
                "content": "...",
                "engine": "google",
                "score": 0.95
            }
        ],
        "count": 5,
        "web_docs_returned": 5,
        "avg_pages_per_doc": 1.2,
        "latency_ms": 850
    }
    """
    try:
        data = request.json
        query = data.get('query', '')
        limit = data.get('limit', 5)
        categories = data.get('categories', 'general')

        if not query:
            return jsonify({'error': 'query required'}), 400

        metrics.increment('search_requests')
        start_time = time.time()

        # Query SearXNG
        search_url = f"{SEARXNG_URL}/search"
        params = {
            'q': query,
            'format': 'json',
            'categories': categories,
            'pageno': 1
        }

        print(f"🌐 Searching web for: '{query}'")

        response = requests.get(search_url, params=params, timeout=180)
        response.raise_for_status()

        search_data = response.json()
        raw_results = search_data.get('results', [])

        # Process and format results
        results = []
        total_pages = 0

        for item in raw_results[:limit]:
            # Estimate pages from content length
            content = item.get('content', '')
            estimated_pages = max(1, len(content) // 3000)
            total_pages += estimated_pages

            result = {
                'title': item.get('title', ''),
                'url': item.get('url', ''),
                'content': content,
                'engine': item.get('engine', 'unknown'),
                'score': item.get('score', 0.5),
                'estimated_pages': estimated_pages,
                'category': item.get('category', 'general')
            }
            results.append(result)

        latency_ms = round((time.time() - start_time) * 1000, 2)
        avg_pages = round(total_pages / len(results), 2) if results else 0

        metrics.increment('successful_searches')
        metrics.set_gauge('last_search_latency_ms', latency_ms)

        print(f"✅ Found {len(results)} web results in {latency_ms}ms")

        return jsonify({
            'results': results,
            'count': len(results),
            'web_docs_returned': len(results),
            'avg_pages_per_doc': avg_pages,
            'latency_ms': latency_ms,
            'query': query,
            'engines_used': list(set(r['engine'] for r in results))
        })

    except requests.exceptions.Timeout:
        metrics.increment('search_timeouts')
        return jsonify({'error': 'Web search timeout'}), 504
    except requests.exceptions.RequestException as e:
        metrics.increment('search_errors')
        print(f"❌ Web search error: {e}")
        return jsonify({'error': f'Web search failed: {str(e)}'}), 500
    except Exception as e:
        metrics.increment('search_errors')
        print(f"❌ Unexpected error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/search_agentic', methods=['POST'])
@timed(metrics, 'agentic_search')
def agentic_web_search():
    """
    Agentic web search with LLM-powered query generation

    Body:
    {
        "query": "user's complex question",
        "limit": 10,
        "num_queries": 4,
        "categories": "general"
    }

    Returns:
    {
        "results": [...],
        "count": 10,
        "generated_queries": ["query1", "query2", ...],
        "total_searches": 4,
        "deduplication_rate": 0.35,
        "latency_ms": 3500
    }
    """
    try:
        data = request.json
        query = data.get('query', '')
        limit = data.get('limit', 10)
        num_queries = data.get('num_queries', 4)
        categories = data.get('categories', 'general')

        if not query:
            return jsonify({'error': 'query required'}), 400

        metrics.increment('agentic_search_requests')
        start_time = time.time()

        print(f"🤖 Agentic search for: '{query[:80]}...'")

        # Step 1: Generate search queries using LLM
        query_gen_start = time.time()
        generated_queries = generate_search_queries(query, max_queries=num_queries)
        query_gen_time = (time.time() - query_gen_start) * 1000

        print(f"✅ Generated {len(generated_queries)} queries in {query_gen_time:.0f}ms")

        # Step 2: Execute parallel searches
        search_start = time.time()
        limit_per_query = max(5, limit // len(generated_queries))
        raw_results = execute_parallel_searches(generated_queries, limit_per_query)
        search_time = (time.time() - search_start) * 1000

        print(f"✅ Executed {len(generated_queries)} searches in {search_time:.0f}ms, got {len(raw_results)} raw results")

        # Step 3: Aggregate and deduplicate
        dedup_start = time.time()
        unique_results = aggregate_and_deduplicate(raw_results)
        dedup_time = (time.time() - dedup_start) * 1000

        # Calculate deduplication rate
        dedup_rate = 0 if len(raw_results) == 0 else (len(raw_results) - len(unique_results)) / len(raw_results)

        print(f"✅ Deduplicated in {dedup_time:.0f}ms, {dedup_rate:.1%} reduction")

        # Step 4: Return top N results
        final_results = unique_results[:limit]

        latency_ms = round((time.time() - start_time) * 1000, 2)

        # Calculate metrics
        avg_pages = sum(max(1, len(r.get('content', '')) // 3000) for r in final_results) / len(final_results) if final_results else 0

        metrics.increment('agentic_search_success')
        metrics.set_gauge('last_agentic_search_latency_ms', latency_ms)

        print(f"✅ Agentic search complete: {len(final_results)} results in {latency_ms}ms")

        return jsonify({
            'results': final_results,
            'count': len(final_results),
            'web_docs_returned': len(final_results),
            'avg_pages_per_doc': round(avg_pages, 2),
            'latency_ms': latency_ms,
            'generated_queries': generated_queries,
            'total_searches': len(generated_queries),
            'total_raw_results': len(raw_results),
            'deduplication_rate': round(dedup_rate, 3),
            'timing': {
                'query_generation_ms': round(query_gen_time, 2),
                'parallel_search_ms': round(search_time, 2),
                'deduplication_ms': round(dedup_time, 2)
            },
            'engines_used': list(set(r['engine'] for r in final_results if 'engine' in r))
        })

    except requests.exceptions.Timeout:
        metrics.increment('agentic_search_timeouts')
        return jsonify({'error': 'Agentic search timeout'}), 504
    except Exception as e:
        metrics.increment('agentic_search_errors')
        print(f"❌ Agentic search error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Web Search Service starting...")
    print(f"🌐 SearXNG URL: {SEARXNG_URL}")
    print(f"🤖 Ollama URL: {OLLAMA_URL}")
    print(f"🧠 Query Generation Model: {QUERY_GEN_MODEL}")
    print(f"📡 Listening on port {SERVICE_PORT}")

    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=False)

