"""
Model Router Service
Intelligently routes queries to optimal LLM models based on complexity
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import sys
import time

# Add common to path
sys.path.insert(0, '/workspace/services/common')
sys.path.insert(0, '/workspace')

from config import SERVICE_NAME, SERVICE_PORT

# Import build info
try:
    from services.common.build_info import get_service_version
except ImportError:
    def get_service_version(name):
        return {'service': name, 'version': '1.0.0', 'build_number': 'dev', 'environment': 'development'}

app = Flask(__name__)
CORS(app)

# Configuration
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://ollama:11434')
CLASSIFIER_URL = os.getenv('PROMPT_CLASSIFIER_URL', 'http://prompt-classifier:8017')

# Model Routing Table
# Maps complexity + domain → model selection
MODEL_ROUTING = {
    # Simple queries → Fast, small models
    'simple': {
        'default': 'llama3.2:3b',      # Fast general-purpose
        'code': 'llama3.2:3b',         # Code generation
        'technical': 'gemma2:2b',      # Technical factual
    },
    # Moderate queries → Balanced models
    'moderate': {
        'default': 'llama3.1:8b',      # Balanced performance
        'code': 'mistral:7b',          # Good for code
        'technical': 'llama3.1:8b',    # Technical reasoning
        'academic': 'gemma2:9b',       # Research/academic
    },
    # Complex queries → Larger, more capable models
    'complex': {
        'default': 'gemma2:9b',        # Strong reasoning
        'code': 'qwen2.5:14b',         # Advanced code
        'technical': 'qwen2.5:14b',    # Deep technical
        'academic': 'qwen2.5:14b',     # Research analysis
    },
    # Expert queries → Largest available model
    'expert': {
        'default': 'qwen2.5:14b',      # Best model
        'code': 'qwen2.5:14b',         # Expert code
        'technical': 'qwen2.5:14b',    # Expert technical
        'academic': 'qwen2.5:14b',     # Expert research
    }
}

# Performance characteristics (estimated)
MODEL_CHARACTERISTICS = {
    'llama3.2:1b': {'size': '1b', 'speed': 'very_fast', 'quality': 'basic', 'context': 2048},
    'gemma2:2b': {'size': '2b', 'speed': 'very_fast', 'quality': 'good', 'context': 8192},
    'llama3.2:3b': {'size': '3b', 'speed': 'fast', 'quality': 'good', 'context': 2048},
    'mistral:7b': {'size': '7b', 'speed': 'moderate', 'quality': 'excellent', 'context': 8192},
    'llama3.1:8b': {'size': '8b', 'speed': 'moderate', 'quality': 'excellent', 'context': 8192},
    'gemma2:9b': {'size': '9b', 'speed': 'moderate', 'quality': 'excellent', 'context': 8192},
    'qwen2.5:14b': {'size': '14b', 'speed': 'slow', 'quality': 'best', 'context': 32768},
}

class ModelRouter:
    """Intelligent model selection based on query characteristics"""

    def __init__(self):
        self.ollama_url = OLLAMA_URL
        self.classifier_url = CLASSIFIER_URL

    def route(self, query: str, classification: dict = None, config: dict = None) -> dict:
        """
        Route query to optimal model

        Returns:
            {
                'model': 'llama3.1:8b',
                'reasoning': 'Selected for moderate complexity technical query',
                'characteristics': {...},
                'classification': {...}
            }
        """
        config = config or {}

        # Step 1: Get classification if not provided
        if not classification:
            classification = self._classify(query)

        complexity = classification.get('complexity', 'moderate')
        domain = classification.get('domain', 'general')

        # Step 2: Check for user override
        if config.get('force_model'):
            model = config['force_model']
            reasoning = f"User specified model: {model}"
        else:
            # Step 3: Select model based on routing table
            model = self._select_model(complexity, domain, config)
            reasoning = f"Auto-selected for {complexity} complexity {domain} query"

        # Step 4: Get model characteristics
        characteristics = MODEL_CHARACTERISTICS.get(model, {})

        return {
            'model': model,
            'reasoning': reasoning,
            'characteristics': characteristics,
            'classification': classification
        }

    def _classify(self, query: str) -> dict:
        """Classify query using classifier service"""
        try:
            response = requests.post(
                f"{self.classifier_url}/classify",
                json={'query': query},
                timeout=5
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"⚠️ Classifier error: {e}")

        # Fallback
        return {
            'complexity': 'moderate',
            'domain': 'general',
            'intent': 'factual'
        }

    def _select_model(self, complexity: str, domain: str, config: dict) -> str:
        """Select model from routing table"""

        # Get routing options for this complexity
        options = MODEL_ROUTING.get(complexity, MODEL_ROUTING['moderate'])

        # Try domain-specific model first
        if domain in options:
            return options[domain]

        # Fall back to default for this complexity
        return options.get('default', 'llama3.1:8b')


# Global router
router = ModelRouter()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint with build information"""
    build_info = get_service_version(SERVICE_NAME)
    return jsonify({
        'status': 'healthy',
        'available_models': list(MODEL_CHARACTERISTICS.keys()),
        **build_info
    })

@app.route('/route', methods=['POST'])
def route_query():
    """
    Route a query to the optimal model

    POST /route
    {
        "query": "Explain quantum computing",
        "classification": {...},  // optional
        "config": {
            "force_model": "qwen2.5:14b",  // optional override
            "prefer_speed": true,           // prefer faster models
            "prefer_quality": true          // prefer better models
        }
    }

    Returns:
    {
        "model": "llama3.1:8b",
        "reasoning": "...",
        "characteristics": {...},
        "classification": {...},
        "processing_time_ms": 12
    }
    """
    start = time.time()

    try:
        data = request.get_json()
        query = data.get('query', '')
        classification = data.get('classification')
        config = data.get('config', {})

        if not query:
            return jsonify({'error': 'Query required'}), 400

        # Route the query
        result = router.route(query, classification, config)

        processing_time = (time.time() - start) * 1000
        result['processing_time_ms'] = round(processing_time, 1)

        print(f"🎯 Routed to {result['model']}: {query[:50]}...")

        return jsonify(result)

    except Exception as e:
        print(f"❌ Routing error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/models', methods=['GET'])
def list_models():
    """List all available models and their characteristics"""
    return jsonify({
        'models': MODEL_CHARACTERISTICS,
        'routing_table': MODEL_ROUTING
    })

if __name__ == '__main__':
    print("🎯 Model Router Service starting...")
    print(f"   Ollama: {OLLAMA_URL}")
    print(f"   Classifier: {CLASSIFIER_URL}")
    print(f"   Available models: {len(MODEL_CHARACTERISTICS)}")
    print(f"   Port: {SERVICE_PORT}")
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=False)

