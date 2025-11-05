#!/usr/bin/env python3
"""
Prompt Enhancement Service - Auto-improve user prompts for better LLM responses
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
from datetime import datetime

# Add common to path
sys.path.insert(0, '/workspace')
from services.common.config import *
from services.common.metrics import ServiceMetrics, timed
from services.common.health import HealthCheck

# Import build info
try:
    from services.common.build_info import get_service_version
except ImportError:
    def get_service_version(name):
        return {'service': name, 'version': '1.0.0', 'build_number': 'dev', 'environment': 'development'}

app = Flask(__name__)
CORS(app)

# Configuration
SERVICE_NAME = os.getenv('SERVICE_NAME', 'prompt-enhancement')
SERVICE_PORT = int(os.getenv('SERVICE_PORT', 8012))

# Initialize metrics and health checks
metrics = ServiceMetrics(SERVICE_NAME)
health = HealthCheck(SERVICE_NAME)

# Import enhancer
from enhancer import PromptEnhancer
from templates import PromptTemplates

# Initialize components
prompt_enhancer = PromptEnhancer()
templates = PromptTemplates()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint with build information"""
    build_info = get_service_version(SERVICE_NAME)
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'components': {
            'prompt_enhancer': 'ready',
            'templates': 'ready'
        },
        **build_info
    })

@app.route('/metrics', methods=['GET'])
def get_metrics():
    """Get service metrics"""
    return jsonify(metrics.get_stats())

@app.route('/enhance', methods=['POST'])
@timed(metrics, 'enhance_prompt')
def enhance_prompt():
    """
    Enhance user prompt for better LLM responses

    Request:
    {
        "query": "What's RAG?",
        "context": {
            "documents": [...],
            "conversation_history": [...],
            "user_profile": {}
        },
        "config": {
            "enhancement_level": "standard" | "minimal" | "advanced",
            "output_format": "markdown" | "json" | "bullet_points",
            "query_type": "default" | "technical" | "educational",
            "add_safety_instructions": true
        }
    }

    Response:
    {
        "original_query": "What's RAG?",
        "enhanced_prompt": "You are a helpful AI assistant...",
        "enhancements_applied": [
            "template_wrapper",
            "context_injection",
            "format_instructions"
        ],
        "estimated_improvement": 0.35,
        "latency_ms": 25
    }
    """
    try:
        start_time = datetime.utcnow()
        data = request.json

        query = data.get('query', '')
        context = data.get('context', {})
        config = data.get('config', {})

        # Enhance the prompt
        result = prompt_enhancer.enhance(query, context, config)

        # Calculate latency
        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        result['latency_ms'] = latency_ms

        # Update metrics
        metrics.increment('enhancement_requests')

        return jsonify(result)

    except Exception as e:
        metrics.increment('enhancement_errors')
        return jsonify({'error': str(e)}), 500

@app.route('/templates', methods=['GET'])
def get_templates():
    """Get available prompt templates"""
    return jsonify({
        'system_templates': list(templates.SYSTEM_TEMPLATES.keys()),
        'context_templates': list(templates.CONTEXT_TEMPLATES.keys()),
        'format_templates': list(templates.FORMAT_TEMPLATES.keys())
    })

@app.route('/')
def root():
    """Service info"""
    return jsonify({
        'service': 'Prompt Enhancement Service',
        'version': '1.0.0',
        'status': 'operational',
        'components': [
            'Query Classifier',
            'Template Engine',
            'Context Injector',
            'Format Instructor',
            'Safety Instructor'
        ],
        'endpoints': {
            'health': '/health',
            'metrics': '/metrics',
            'enhance': '/enhance',
            'templates': '/templates'
        }
    })

if __name__ == '__main__':
    print(f"✨ Starting {SERVICE_NAME} on port {SERVICE_PORT}")
    print(f"📝 Enhancement Components:")
    print(f"   ✅ Query Classifier")
    print(f"   ✅ Template Engine")
    print(f"   ✅ Context Injector")
    print(f"   ✅ Format Instructor")
    print(f"   ✅ Safety Instructor")
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=False)

