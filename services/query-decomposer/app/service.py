"""
Query Decomposer Service - Breaks complex queries into simpler sub-queries
Uses LLM to analyze query complexity and decompose if needed
"""
from flask import Flask, request, jsonify
import requests
import os
import sys
import time
import re

# Add common to path
sys.path.insert(0, '/workspace/services/common')

from metrics import ServiceMetrics
from health import HealthCheck

app = Flask(__name__)

# Initialize metrics
metrics = ServiceMetrics("query-decomposer")

# Initialize health checks
health = HealthCheck("query-decomposer")

# Service URLs
OLLAMA_URL = os.getenv('OLLAMA_BASE_URL', 'http://ollama:11434')
MODEL = os.getenv('DECOMPOSER_MODEL', 'llama3.2:3b')  # Use fast model for decomposition

def assess_complexity(query: str) -> str:
    """
    Quick heuristic assessment of query complexity
    
    Returns: 'simple' or 'complex'
    """
    # Check for multiple concepts
    multi_concept_indicators = [
        'and', 'compare', 'contrast', 'both', 'also', 'additionally',
        'versus', 'vs', 'difference between', 'similarities', 'as well as',
        'furthermore', 'moreover', 'in addition'
    ]
    
    query_lower = query.lower()
    has_multiple = any(indicator in query_lower for indicator in multi_concept_indicators)
    
    # Check for multiple questions
    question_count = query.count('?')
    has_multiple_questions = question_count > 1
    
    # Check length (words)
    word_count = len(query.split())
    is_long = word_count > 20
    
    # Check for multiple sentences
    sentence_count = len([s for s in re.split(r'[.!?]+', query) if s.strip()])
    has_multiple_sentences = sentence_count > 1
    
    # Determine complexity
    if has_multiple or has_multiple_questions or (is_long and has_multiple_sentences):
        return 'complex'
    return 'simple'

def parse_subqueries(llm_output: str, max_count: int = 3) -> list:
    """
    Extract numbered sub-questions from LLM output
    Handles various formats: "1. question", "- question", "Q1: question"
    """
    lines = llm_output.strip().split('\n')
    sub_queries = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Match patterns like "1. question", "- question", "Q1: question", etc.
        # Remove common prefixes
        cleaned = re.sub(r'^[\d]+[\.\)\:]?\s*', '', line)  # Remove "1. " or "1) " or "1: "
        cleaned = re.sub(r'^[-•\*]\s*', '', cleaned)        # Remove "- " or "• " or "* "
        cleaned = re.sub(r'^Q[\d]+[\:\.]?\s*', '', cleaned)  # Remove "Q1: " or "Q1. "
        
        # Check if this looks like a valid question
        if len(cleaned) > 10 and (cleaned != line):  # Must have been modified (had a prefix)
            sub_queries.append(cleaned)
        
        if len(sub_queries) >= max_count:
            break
    
    # If we didn't find any sub-queries, return the original output
    if not sub_queries:
        # Try to split by newlines as a fallback
        potential_queries = [l.strip() for l in lines if len(l.strip()) > 10]
        sub_queries = potential_queries[:max_count] if potential_queries else [llm_output.strip()]
    
    return sub_queries

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check if Ollama is accessible
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        ollama_healthy = response.status_code == 200
        
        return jsonify({
            'status': 'healthy' if ollama_healthy else 'degraded',
            'service': 'query-decomposer',
            'ollama_accessible': ollama_healthy,
            'model': MODEL
        })
    except:
        return jsonify({
            'status': 'unhealthy',
            'service': 'query-decomposer',
            'ollama_accessible': False
        }), 503

@app.route('/metrics', methods=['GET'])
def get_metrics():
    """Metrics endpoint"""
    return jsonify(metrics.get_stats())

@app.route('/decompose', methods=['POST'])
def decompose_query():
    """
    Decompose complex query into simpler sub-queries
    
    Body:
    {
        "query": "Compare transformers vs RNNs and explain attention mechanism",
        "max_subqueries": 3
    }
    
    Returns:
    {
        "original_query": "...",
        "needs_decomposition": true/false,
        "complexity": "simple/complex",
        "sub_queries": ["query1", "query2", ...],
        "strategy": "single/parallel",
        "processing_time_ms": 123.45
    }
    """
    try:
        start_time = time.time()
        
        data = request.json
        query = data.get('query', '')
        max_subqueries = data.get('max_subqueries', 3)
        
        if not query:
            return jsonify({'error': 'query required'}), 400
        
        print(f"🧩 Decompose request: {query[:100]}...")
        metrics.increment('decompose_requests')
        
        # Step 1: Assess complexity
        complexity = assess_complexity(query)
        print(f"📊 Complexity assessment: {complexity}")
        
        if complexity == 'simple':
            metrics.increment('simple_queries')
            processing_time = (time.time() - start_time) * 1000
            return jsonify({
                'original_query': query,
                'needs_decomposition': False,
                'complexity': complexity,
                'sub_queries': [query],
                'strategy': 'single',
                'processing_time_ms': round(processing_time, 2)
            })
        
        # Step 2: Use LLM to decompose complex query
        print(f"🤖 Using LLM to decompose query...")
        decomposition_prompt = f"""You are a query decomposition expert. Break this complex question into 2-3 simpler, focused sub-questions.

Original Question: "{query}"

Requirements for sub-questions:
- Each must be self-contained and clear
- Each must focus on ONE specific concept or comparison
- Each must be searchable independently
- Keep them concise (under 15 words each)
- Number them clearly (1., 2., 3.)

Sub-questions:"""

        # Call Ollama
        try:
            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    'model': MODEL,
                    'prompt': decomposition_prompt,
                    'stream': False,
                    'options': {
                        'temperature': 0.3,  # Low temperature for consistency
                        'num_predict': 200   # Short response expected
                    }
                },
                timeout=30  # 30 seconds timeout
            )
            
            if response.status_code != 200:
                print(f"❌ Ollama error: {response.status_code}")
                metrics.increment('decomposition_errors')
                # Fallback: return original query
                processing_time = (time.time() - start_time) * 1000
                return jsonify({
                    'original_query': query,
                    'needs_decomposition': False,
                    'complexity': complexity,
                    'sub_queries': [query],
                    'strategy': 'single',
                    'error': 'LLM decomposition failed',
                    'processing_time_ms': round(processing_time, 2)
                })
            
            llm_output = response.json()['response']
            print(f"✅ LLM output: {llm_output[:200]}...")
            
            # Parse sub-queries
            sub_queries = parse_subqueries(llm_output, max_subqueries)
            print(f"📝 Parsed {len(sub_queries)} sub-queries")
            
            # Ensure we have valid sub-queries
            if not sub_queries or len(sub_queries) == 0:
                sub_queries = [query]
            
            metrics.increment('decomposition_success')
            processing_time = (time.time() - start_time) * 1000
            
            return jsonify({
                'original_query': query,
                'needs_decomposition': True,
                'complexity': complexity,
                'sub_queries': sub_queries,
                'strategy': 'parallel',
                'processing_time_ms': round(processing_time, 2)
            })
            
        except requests.exceptions.Timeout:
            print(f"⏱️  LLM timeout")
            metrics.increment('llm_timeouts')
            processing_time = (time.time() - start_time) * 1000
            return jsonify({
                'original_query': query,
                'needs_decomposition': False,
                'complexity': complexity,
                'sub_queries': [query],
                'strategy': 'single',
                'error': 'LLM timeout',
                'processing_time_ms': round(processing_time, 2)
            })
        except Exception as e:
            print(f"❌ LLM error: {e}")
            metrics.increment('decomposition_errors')
            processing_time = (time.time() - start_time) * 1000
            return jsonify({
                'original_query': query,
                'needs_decomposition': False,
                'complexity': complexity,
                'sub_queries': [query],
                'strategy': 'single',
                'error': str(e),
                'processing_time_ms': round(processing_time, 2)
            })
        
    except Exception as e:
        print(f"❌ Decompose error: {e}")
        metrics.increment('decompose_errors')
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/', methods=['GET'])
def root():
    """Service info"""
    return jsonify({
        'service': 'Query Decomposer',
        'version': '1.0.0',
        'model': MODEL,
        'endpoints': {
            'health': '/health',
            'metrics': '/metrics',
            'decompose': '/decompose (POST)'
        }
    })

if __name__ == '__main__':
    print("🚀 Query Decomposer Service starting...")
    print(f"🤖 Model: {MODEL}")
    print(f"🔗 Ollama URL: {OLLAMA_URL}")
    
    port = int(os.getenv('SERVICE_PORT', '8019'))
    app.run(host='0.0.0.0', port=port, debug=False)

