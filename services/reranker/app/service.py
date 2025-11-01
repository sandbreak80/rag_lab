"""
LLM Re-ranking Service - Precision improvement via LLM relevance scoring
Optional service that can be enabled for higher precision (+10%) at cost of latency (+2000ms)
"""
from flask import Flask, request, jsonify
import requests
import sys
import os
from typing import List, Dict, Any

# Add common and src to path
sys.path.insert(0, '/workspace/services/common')
sys.path.insert(0, '/workspace/src')

from config import *
from metrics import ServiceMetrics, timed
from health import HealthCheck

app = Flask(__name__)

# Get service port and config from environment
SERVICE_PORT = int(os.getenv('SERVICE_PORT', 8008))
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://host.docker.internal:11434')
CHAT_MODEL = os.getenv('CHAT_MODEL', 'llama3.2:3b')

# Initialize metrics
metrics = ServiceMetrics("reranker-service")

# Initialize health checks
health = HealthCheck("reranker-service")

# Health checks
health.add_check("ollama_connection", lambda: check_ollama())

def check_ollama() -> bool:
    """Check if Ollama is available"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
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

@app.route('/rerank', methods=['POST'])
@timed(metrics, 'rerank')
def rerank():
    """
    Re-rank search results using LLM relevance scoring
    
    Body:
    {
        "query": "search query",
        "results": [
            {
                "content": "document text",
                "metadata": {"title": "...", "file_name": "..."},
                "score": 0.85
            },
            ...
        ],
        "limit": 10,
        "model": "llama3.2:3b"  # optional
    }
    
    Returns:
    {
        "results": [...],  # Re-ranked results
        "count": 10
    }
    """
    try:
        data = request.json
        query = data.get('query', '')
        results = data.get('results', [])
        limit = data.get('limit', 10)
        model = data.get('model', CHAT_MODEL)
        
        if not query:
            return jsonify({'error': 'query required'}), 400
        
        if not results:
            return jsonify({'error': 'results required'}), 400
        
        metrics.increment('rerank_requests')
        
        print(f"🔄 Re-ranking {len(results)} results for query: {query[:50]}...")
        
        # Score each result
        scored_results = []
        for result in results:
            content = result.get('content', '')
            metadata = result.get('metadata', {})
            title = metadata.get('title', metadata.get('file_name', 'Unknown'))
            original_score = result.get('score', 0)
            
            # Truncate content for efficiency
            content_preview = content[:500] if len(content) > 500 else content
            
            # Score relevance with LLM
            llm_score = score_relevance(query, title, content_preview, model)
            
            # Combine scores (60% hybrid search, 40% LLM)
            final_score = (original_score * 0.6) + (llm_score * 0.4)
            
            result['llm_relevance'] = llm_score
            result['final_score'] = final_score
            result['original_score'] = original_score
            
            scored_results.append(result)
        
        # Sort by final score
        scored_results.sort(key=lambda x: x['final_score'], reverse=True)
        
        # Return top N
        reranked = scored_results[:limit]
        
        metrics.increment('rerank_success')
        
        print(f"✅ Re-ranked to {len(reranked)} results")
        
        return jsonify({
            'results': reranked,
            'count': len(reranked)
        })
    
    except Exception as e:
        metrics.increment('rerank_errors')
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

def score_relevance(query: str, title: str, content: str, model: str) -> float:
    """
    Score relevance using LLM
    
    Returns score between 0.0 and 1.0
    """
    prompt = f"""Rate the relevance of this document to the query on a scale of 0.0 to 1.0.

Query: {query}

Document Title: {title}
Document Content: {content}

Provide ONLY a number between 0.0 (not relevant) and 1.0 (very relevant).
Do not explain, just provide the number.

Relevance Score:"""
    
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Low temperature for consistency
                    "num_predict": 10    # Just need a number
                }
            },
            timeout=30  # Longer timeout for generation
        )
        
        if response.status_code == 200:
            result = response.json()
            score_text = result.get('response', '0.5').strip()
            
            # Extract number from response
            import re
            numbers = re.findall(r'0\.\d+|1\.0|0|1', score_text)
            if numbers:
                score = float(numbers[0])
                # Clamp to [0, 1]
                return max(0.0, min(1.0, score))
        
        # Default to neutral score if failed
        return 0.5
        
    except Exception as e:
        print(f"⚠️  LLM scoring failed: {e}")
        return 0.5

if __name__ == '__main__':
    print("🚀 Re-ranking Service starting...")
    print(f"   Model: {CHAT_MODEL}")
    print(f"   Ollama: {OLLAMA_BASE_URL}")
    print(f"   ⚠️  This service adds ~2000ms latency but improves precision by ~10%")
    
    # Start server
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=False)

