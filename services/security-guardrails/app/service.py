#!/usr/bin/env python3
"""
Security Guardrails Service - Enterprise LLM Security
Provides multi-layer defense against prompt injection, PII leakage, and content violations
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

app = Flask(__name__)
CORS(app)

# Configuration
SERVICE_NAME = os.getenv('SERVICE_NAME', 'security-guardrails')
SERVICE_PORT = int(os.getenv('SERVICE_PORT', 8013))

# Initialize metrics and health checks
metrics = ServiceMetrics(SERVICE_NAME)
health = HealthCheck(SERVICE_NAME)

# Import validators
from validators import InputValidator
from pii_detector import PIIDetector
from injection_detector import InjectionDetector
from topic_classifier import TopicClassifier
from unicode_sanitizer import UnicodeSanitizer
from output_validator import OutputValidator

# Initialize components
input_validator = InputValidator()
pii_detector = PIIDetector()
injection_detector = InjectionDetector()
topic_classifier = TopicClassifier()
unicode_sanitizer = UnicodeSanitizer()
output_validator = OutputValidator(pii_detector=pii_detector)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': SERVICE_NAME,
        'timestamp': datetime.utcnow().isoformat(),
        'components': {
            'input_validator': 'ready',
            'pii_detector': 'ready',
            'injection_detector': 'ready',
            'topic_classifier': 'ready',
            'unicode_sanitizer': 'ready',
            'output_validator': 'ready'
        }
    })

@app.route('/metrics', methods=['GET'])
def get_metrics():
    """Get service metrics"""
    return jsonify(metrics.get_stats())

@app.route('/validate_input', methods=['POST'])
@timed(metrics, 'validate_input')
def validate_input():
    """
    Comprehensive input validation pipeline

    Request:
    {
        "query": "user input",
        "use_case": "educational",
        "user_id": "user123",
        "config": {
            "check_pii": true,
            "check_injection": true,
            "check_topics": true,
            "check_unicode": true,
            "block_on_violation": true
        }
    }

    Response:
    {
        "status": "allowed" | "blocked" | "warning",
        "cleaned_query": "sanitized input",
        "violations": [
            {"type": "pii", "severity": "high", "details": "SSN detected"},
            {"type": "injection", "severity": "critical", "details": "Prompt injection attempt"}
        ],
        "topics": ["rag_systems", "ai_ml_concepts"],
        "confidence": 0.92,
        "latency_ms": 150
    }
    """
    try:
        start_time = datetime.utcnow()
        data = request.json

        query = data.get('query', '')
        use_case = data.get('use_case', 'educational')
        user_id = data.get('user_id')
        config = data.get('config', {})

        violations = []
        cleaned_query = query
        status = 'allowed'

        # Step 1: Basic Input Validation
        validation_result = input_validator.validate(query)
        if not validation_result['valid']:
            return jsonify({
                'status': 'blocked',
                'error': validation_result['error'],
                'violations': [{'type': 'input_validation', 'severity': 'high', 'details': validation_result['error']}]
            }), 400

        # Step 2: Unicode Sanitization (NEW - Emoji Smuggling Defense)
        if config.get('check_unicode', True):
            unicode_result = unicode_sanitizer.sanitize(cleaned_query)
            cleaned_query = unicode_result['cleaned_text']
            if unicode_result['violations']:
                violations.extend([{
                    'type': 'unicode_attack',
                    'severity': 'high',
                    'details': v
                } for v in unicode_result['violations']])
                status = 'warning'

        # Step 3: PII Detection
        if config.get('check_pii', True):
            pii_result = pii_detector.detect(cleaned_query)
            if pii_result['pii_found']:
                violations.extend([{
                    'type': 'pii',
                    'severity': 'high',
                    'details': f"{entity['type']}: {entity['text']}"
                } for entity in pii_result['entities']])

                # Redact PII
                cleaned_query = pii_result['redacted_text']

                # Block if configured
                if config.get('block_on_violation', False):
                    status = 'blocked'

        # Step 4: Prompt Injection Detection (3-Layer)
        if config.get('check_injection', True):
            injection_result = injection_detector.detect(cleaned_query)
            if injection_result['is_injection']:
                violations.append({
                    'type': 'injection',
                    'severity': 'critical',
                    'details': f"Confidence: {injection_result['confidence']:.2f}, Method: {injection_result['detection_method']}"
                })

                # Always block injection attempts
                status = 'blocked'

        # Step 5: Topic Classification
        if config.get('check_topics', True):
            topic_result = topic_classifier.classify(cleaned_query, use_case)
            if not topic_result['allowed']:
                violations.append({
                    'type': 'topic_violation',
                    'severity': 'medium',
                    'details': f"Disallowed topic: {topic_result['primary_topic']}"
                })

                # Block if configured
                if config.get('block_on_violation', False):
                    status = 'blocked'

        # Calculate latency
        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        # Update metrics
        metrics.increment('validation_requests')
        if status == 'blocked':
            metrics.increment('blocked_requests')

        return jsonify({
            'status': status,
            'cleaned_query': cleaned_query,
            'violations': violations,
            'topics': topic_result.get('topics', []) if config.get('check_topics') else [],
            'confidence': topic_result.get('confidence', 1.0) if config.get('check_topics') else 1.0,
            'latency_ms': latency_ms
        })

    except Exception as e:
        metrics.increment('validation_errors')
        return jsonify({'error': str(e)}), 500

@app.route('/validate_output', methods=['POST'])
@timed(metrics, 'validate_output')
def validate_output():
    """
    Comprehensive LLM output validation

    Fast Track Phase 7 - Week 8 Day 6-7

    Validates LLM outputs for:
    - PII disclosure
    - Harmful content
    - System metadata leaks
    - Response quality
    - Injection echo detection

    Request:
    {
        "response": "LLM output",
        "original_query": "user input",
        "config": {
            "check_pii": true,
            "check_harmful": true,
            "check_metadata": true,
            "redact_pii": true,
            "block_harmful": true
        }
    }

    Response:
    {
        "status": "safe" | "warning" | "unsafe",
        "cleaned_response": "sanitized output",
        "violations": [...],
        "redactions_made": 3,
        "latency_ms": 50
    }
    """
    try:
        data = request.json

        response_text = data.get('response', '')
        original_query = data.get('original_query', '')
        config = data.get('config', {})

        # Use comprehensive output validator
        result = output_validator.validate(
            response=response_text,
            original_query=original_query,
            config=config
        )

        # Update metrics
        metrics.increment('output_validations')
        if result['status'] == 'unsafe':
            metrics.increment('unsafe_outputs')
        elif result['status'] == 'warning':
            metrics.increment('output_warnings')

        # Log violations
        if result['violations']:
            for violation in result['violations']:
                metrics.increment(f"output_violations_{violation['type']}")

        return jsonify(result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/')
def root():
    """Service info"""
    return jsonify({
        'service': 'Security Guardrails Service',
        'version': '2.0.0 - Fast Track Phase 7',
        'status': 'operational',
        'components': [
            'Input Validator (Length, Format, Encoding)',
            'PII Detector (Presidio - 50+ types)',
            'Injection Detector (3-layer: Pattern + ML + Heuristic)',
            'ML Classifier (DeBERTa - 85%+ accuracy)',
            'Topic Classifier (Rule-based + Policies)',
            'Unicode Sanitizer (Zero-width, Homoglyphs, Emoji)',
            'Output Validator (PII, Harmful, Metadata, Quality)'
        ],
        'security_features': {
            'input_validation': 'Length limits, format checks, encoding validation',
            'pii_protection': 'EMAIL, PHONE, SSN, CREDIT_CARD, IP_ADDRESS, + 45 more',
            'injection_defense': '3-layer cascade (Pattern < 1ms, ML 30-50ms, Heuristic < 10ms)',
            'unicode_attacks': 'Zero-width chars, homoglyphs, emoji smuggling, RTL override',
            'topic_filtering': 'Allowed/disallowed topics, use-case policies',
            'output_safety': 'PII redaction, harmful content blocking, metadata stripping'
        },
        'performance': {
            'input_validation': '< 200ms total',
            'ml_inference': '30-50ms',
            'output_validation': '< 100ms'
        },
        'endpoints': {
            'health': '/health',
            'metrics': '/metrics',
            'validate_input': '/validate_input',
            'validate_output': '/validate_output'
        }
    })

if __name__ == '__main__':
    print(f"🔒 Starting {SERVICE_NAME} on port {SERVICE_PORT}")
    print(f"🛡️  Security Components:")
    print(f"   ✅ Input Validator")
    print(f"   ✅ PII Detector (Presidio)")
    print(f"   ✅ Injection Detector (3-layer)")
    print(f"   ✅ Topic Classifier")
    print(f"   ✅ Unicode Sanitizer")
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=False)

