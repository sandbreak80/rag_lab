"""
Embedding Service - Generate embeddings via Ollama
Provides text embedding with caching and batching
"""
from flask import Flask, request, jsonify
import requests
from typing import List
import sys
import hashlib
import json

# Add common to path
sys.path.insert(0, '/workspace/services/common')
from config import *
from metrics import ServiceMetrics, timed
from health import HealthCheck

app = Flask(__name__)

# Initialize metrics
metrics = ServiceMetrics("embedding-service")

# Initialize health checks
health = HealthCheck("embedding-service")

# Simple in-memory cache (could use Redis in production)
embedding_cache = {}

def check_ollama_connection():
    """Check if Ollama is accessible"""
    try:
        response = requests.get(f"{LLM_SERVICE_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

# Add health checks
health.add_check("ollama_connection", check_ollama_connection)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify(health.get_health())

@app.route('/metrics', methods=['GET'])
def get_metrics():
    """Metrics endpoint"""
    stats = metrics.get_stats()
    stats['cache_size'] = len(embedding_cache)
    stats['cache_hit_rate'] = (
        metrics.counters.get('cache_hits', 0) /
        max(metrics.counters.get('embed_requests', 1), 1)
    )
    return jsonify(stats)

def get_cache_key(text: str, model: str) -> str:
    """Generate cache key for text"""
    content = f"{model}:{text}"
    return hashlib.md5(content.encode()).hexdigest()

@app.route('/embed', methods=['POST'])
@timed(metrics, 'embed_text')
def embed_text():
    """
    Generate embedding for text

    Body:
    {
        "text": "some text to embed",
        "model": "nomic-embed-text"  // optional
    }
    """
    try:
        data = request.json
        text = data.get('text', '')
        model = data.get('model', EMBEDDING_MODEL)

        if not text:
            return jsonify({'error': 'text required'}), 400

        metrics.increment('embed_requests')

        # Check cache
        cache_key = get_cache_key(text, model)
        if cache_key in embedding_cache:
            metrics.increment('cache_hits')
            return jsonify({
                'embedding': embedding_cache[cache_key],
                'cached': True
            })

        metrics.increment('cache_misses')

        # Generate embedding via Ollama
        response = requests.post(
            f"{LLM_SERVICE_URL}/api/embeddings",
            json={
                "model": model,
                "prompt": text
            },
            timeout=30
        )
        response.raise_for_status()

        embedding = response.json()['embedding']

        # Cache result
        embedding_cache[cache_key] = embedding

        # Limit cache size
        if len(embedding_cache) > 10000:
            # Remove oldest 20% of entries (simple FIFO)
            to_remove = list(embedding_cache.keys())[:2000]
            for key in to_remove:
                del embedding_cache[key]

        metrics.increment('embeddings_generated')

        return jsonify({
            'embedding': embedding,
            'cached': False
        })

    except requests.exceptions.ConnectionError:
        metrics.increment('errors')
        return jsonify({'error': 'Cannot connect to Ollama'}), 503
    except requests.exceptions.Timeout:
        metrics.increment('errors')
        return jsonify({'error': 'Ollama timeout'}), 504
    except Exception as e:
        metrics.increment('errors')
        return jsonify({'error': str(e)}), 500

@app.route('/embed/batch', methods=['POST'])
@timed(metrics, 'embed_batch')
def embed_batch():
    """
    Generate embeddings for multiple texts

    Body:
    {
        "texts": ["text1", "text2", ...],
        "model": "nomic-embed-text"  // optional
    }
    """
    try:
        data = request.json
        texts = data.get('texts', [])
        model = data.get('model', EMBEDDING_MODEL)

        if not texts:
            return jsonify({'error': 'texts required'}), 400

        metrics.increment('batch_requests')
        metrics.increment('batch_size', len(texts))

        embeddings = []
        cached_count = 0

        for text in texts:
            # Check cache
            cache_key = get_cache_key(text, model)
            if cache_key in embedding_cache:
                embeddings.append(embedding_cache[cache_key])
                cached_count += 1
                continue

            # Generate embedding
            response = requests.post(
                f"{LLM_SERVICE_URL}/api/embeddings",
                json={
                    "model": model,
                    "prompt": text
                },
                timeout=30
            )
            response.raise_for_status()

            embedding = response.json()['embedding']
            embeddings.append(embedding)

            # Cache result
            embedding_cache[cache_key] = embedding

        metrics.increment('embeddings_generated', len(texts) - cached_count)
        metrics.increment('cache_hits', cached_count)

        return jsonify({
            'embeddings': embeddings,
            'count': len(embeddings),
            'cached': cached_count
        })

    except Exception as e:
        metrics.increment('errors')
        return jsonify({'error': str(e)}), 500

@app.route('/cache/clear', methods=['POST'])
def clear_cache():
    """Clear embedding cache"""
    global embedding_cache
    size = len(embedding_cache)
    embedding_cache = {}
    metrics.increment('cache_clears')
    return jsonify({
        'status': 'success',
        'cleared': size
    })

@app.route('/cache/stats', methods=['GET'])
def cache_stats():
    """Get cache statistics"""
    return jsonify({
        'size': len(embedding_cache),
        'hit_rate': (
            metrics.counters.get('cache_hits', 0) /
            max(metrics.counters.get('embed_requests', 1), 1)
        ),
        'hits': metrics.counters.get('cache_hits', 0),
        'misses': metrics.counters.get('cache_misses', 0)
    })

if __name__ == '__main__':
    print("🚀 Embedding Service starting...")
    print(f"🤖 LLM URL: {LLM_SERVICE_URL}")
    print(f"📊 Model: {EMBEDDING_MODEL}")

    # Start server
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=False)

