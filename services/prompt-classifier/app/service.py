"""
Prompt Classifier Service
Categorizes prompts for intelligent routing and enhancement
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# Add common to path
sys.path.insert(0, '/workspace/services/common')
sys.path.insert(0, '/workspace')

from classifier import classifier
from config import SERVICE_NAME, SERVICE_PORT

# Import build info
try:
    from services.common.build_info import get_service_version
except ImportError:
    # Fallback if build_info not available
    def get_service_version(name):
        return {'service': name, 'version': '1.0.0', 'build_number': 'dev', 'environment': 'development'}

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health():
    """Health check with build information"""
    build_info = get_service_version(SERVICE_NAME)
    return jsonify({
        'status': 'healthy',
        **build_info
    })

@app.route('/classify', methods=['POST'])
def classify_prompt():
    """
    Classify a prompt

    Body:
    {
        "query": "How does attention mechanism work in transformers?"
    }

    Returns:
    {
        "intent": "explanation",
        "complexity": "moderate",
        "domain": "technical",
        "output_format": "detailed",
        "confidence": 0.85,
        "metadata": {
            "word_count": 7,
            ...
        },
        "recommendations": {
            "model": "8b",
            "enhancement": "chain_of_thought",
            "timeout_seconds": 30
        }
    }
    """
    try:
        data = request.get_json()
        query = data.get('query', '')

        if not query:
            return jsonify({'error': 'Query required'}), 400

        # Classify
        classification = classifier.classify(query)

        # Add recommendations
        recommendations = _generate_recommendations(classification)
        classification['recommendations'] = recommendations

        return jsonify(classification)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/classify/batch', methods=['POST'])
def classify_batch():
    """
    Classify multiple prompts

    Body:
    {
        "queries": ["query1", "query2", ...]
    }
    """
    try:
        data = request.get_json()
        queries = data.get('queries', [])

        if not queries:
            return jsonify({'error': 'Queries required'}), 400

        results = []
        for query in queries:
            classification = classifier.classify(query)
            recommendations = _generate_recommendations(classification)
            classification['recommendations'] = recommendations
            classification['query'] = query  # Include original query
            results.append(classification)

        return jsonify({'results': results})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def _generate_recommendations(classification: dict) -> dict:
    """
    Generate recommendations based on classification
    """
    complexity = classification['complexity']
    intent = classification['intent']
    domain = classification['domain']

    # Model recommendation
    if complexity in ['simple']:
        model = '3b'  # Fast model for simple queries
        timeout = 10
    elif complexity in ['moderate']:
        model = '8b'  # Standard model
        timeout = 30
    else:  # complex, expert
        model = '8b'  # or '70b' if available
        timeout = 60

    # Enhancement strategy
    if complexity in ['complex', 'expert']:
        enhancement = 'chain_of_thought'  # CoT for complex reasoning
    elif intent == 'coding':
        enhancement = 'structured_output'  # Structured for code
    elif intent == 'instruction':
        enhancement = 'step_by_step'  # Clear steps
    else:
        enhancement = 'standard'  # Basic enhancement

    # RAG recommendation
    use_rag = domain in ['technical', 'academic'] or intent in ['factual', 'explanation']

    # Web search recommendation
    use_web_search = intent in ['factual'] and domain in ['general', 'business']

    return {
        'model': model,
        'enhancement': enhancement,
        'timeout_seconds': timeout,
        'use_rag': use_rag,
        'use_web_search': use_web_search,
        'reasoning': f"{complexity} {intent} query about {domain}"
    }

if __name__ == '__main__':
    print(f"🧠 {SERVICE_NAME} starting on port {SERVICE_PORT}...")
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=False)

