"""
Settings API routes
"""
from flask import Blueprint, request, jsonify
import requests
import os
import json

bp = Blueprint('settings', __name__)

@bp.route('/stats', methods=['GET'])
def get_stats():
    """Get system statistics"""
    try:
        vector_db_url = os.getenv('VECTOR_DB_URL', 'http://vector-db:8005')
        
        # Get chunk count from vector DB
        try:
            response = requests.get(f"{vector_db_url}/stats", timeout=5)
            if response.status_code == 200:
                stats = response.json()
                chunk_count = stats.get('chunk_count', 0)
            else:
                chunk_count = 0
        except:
            chunk_count = 0
        
        # Get model info from Ollama
        ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://host.docker.internal:11434')
        current_model = os.getenv('CHAT_MODEL', 'llama3.2:3b')
        
        return jsonify({
            'chunk_count': chunk_count,
            'current_model': current_model,
            'status': 'ok'
        })
    
    except Exception as e:
        return jsonify({
            'chunk_count': 0,
            'current_model': 'unknown',
            'status': 'error',
            'error': str(e)
        }), 200  # Return 200 to avoid breaking the UI


@bp.route('/presets', methods=['GET'])
def get_presets():
    """Get configuration presets"""
    try:
        # Read from config/presets.json
        presets_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'presets.json')

        with open(presets_path, 'r') as f:
            presets_data = json.load(f)

        return jsonify(presets_data.get('presets', []))

    except Exception as e:
        # Return default presets if file not found
        return jsonify([
            {
                "name": "minimal",
                "description": "Fastest, lowest quality - Vector search only",
                "config": {
                    "use_query_expansion": False,
                    "use_bm25": False,
                    "use_hybrid": False,
                    "use_graph": False,
                    "use_reranking": False,
                    "use_web_search": False,
                    "top_k": 3
                }
            },
            {
                "name": "production",
                "description": "All optimizations enabled",
                "config": {
                    "use_query_expansion": True,
                    "use_bm25": True,
                    "use_hybrid": True,
                    "use_graph": True,
                    "use_reranking": True,
                    "use_web_search": True,
                    "top_k": 10
                }
            }
        ])


@bp.route('/models', methods=['GET'])
def get_models():
    """Get available Ollama models"""
    try:
        ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://ollama:11434')
        response = requests.get(f"{ollama_url}/api/tags", timeout=10)

        if response.status_code == 200:
            data = response.json()
            return jsonify(data)

        # Return default if Ollama is not available
        return jsonify({
            'models': [
                {
                    'name': 'llama3.2:3b',
                    'model': 'llama3.2:3b',
                    'size': 2000000000,
                    'details': {
                        'parameter_size': '3B',
                        'quantization_level': 'Q4_0'
                    }
                }
            ]
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
