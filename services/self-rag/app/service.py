"""
Self-RAG Service - Retrieval with Self-Reflection
Implements self-reflective RAG with quality assessment
"""
from flask import Flask, request, jsonify
import sys
import os
import requests

# Add common to path
sys.path.insert(0, '/workspace/services/common')
from config import *
from metrics import ServiceMetrics, timed
from health import HealthCheck

app = Flask(__name__)

# Initialize metrics and health
metrics = ServiceMetrics("self-rag")
health = HealthCheck("self-rag")

# Service URLs
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://ollama:11434')
SEARCH_SERVICE_URL = os.getenv('SEARCH_SERVICE_URL', 'http://search-service:8003')

# Add health checks
health.add_check("ollama_connection", lambda: check_service(OLLAMA_URL))

def check_service(url: str) -> bool:
    """Check if service is available"""
    try:
        response = requests.get(f"{url}/api/tags", timeout=5)
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

@app.route('/evaluate', methods=['POST'])
@timed(metrics, 'evaluate')
def evaluate_response():
    """
    Evaluate a generated response using self-reflection
    
    Request:
    {
        "query": "user question",
        "response": "generated answer",
        "sources": [...],
        "model": "llama3.2:3b"
    }
    
    Response:
    {
        "quality_score": 0.85,  # 0-1 scale
        "needs_retrieval": false,
        "critique": {
            "relevance": 0.9,      # Does it answer the question?
            "accuracy": 0.8,       # Is it factually correct?
            "completeness": 0.85,  # Is it complete?
            "grounding": 0.9       # Is it grounded in sources?
        },
        "suggestions": ["Add more details about X", "Clarify Y"],
        "improved_response": "..."  # Optional: improved version
    }
    """
    try:
        data = request.json
        query = data.get('query', '')
        response = data.get('response', '')
        sources = data.get('sources', [])
        model = data.get('model', DEFAULT_MODEL)
        
        if not query or not response:
            return jsonify({'error': 'query and response required'}), 400
        
        # Step 1: Evaluate response quality
        critique = _critique_response(query, response, sources, model)
        
        # Step 2: Determine if re-retrieval is needed
        quality_score = _compute_quality_score(critique)
        needs_retrieval = quality_score < 0.7  # Threshold for re-retrieval
        
        # Step 3: Generate suggestions if quality is low
        suggestions = []
        if quality_score < 0.8:
            suggestions = _generate_suggestions(query, response, critique, model)
        
        # Step 4: Optionally improve the response
        improved_response = None
        if data.get('auto_improve', False) and quality_score < 0.9:
            improved_response = _improve_response(query, response, suggestions, sources, model)
        
        metrics.increment('evaluations')
        metrics.set_gauge('avg_quality_score', quality_score)
        
        return jsonify({
            'quality_score': quality_score,
            'needs_retrieval': needs_retrieval,
            'critique': critique,
            'suggestions': suggestions,
            'improved_response': improved_response
        })
        
    except Exception as e:
        metrics.increment('errors')
        print(f"❌ Error evaluating response: {e}")
        return jsonify({'error': str(e)}), 500

def _critique_response(query: str, response: str, sources: list, model: str) -> dict:
    """
    Use LLM to critique the response across multiple dimensions
    """
    # Build source context
    source_context = "\n\n".join([
        f"Source {i+1}: {src.get('content', '')[:500]}"
        for i, src in enumerate(sources[:3])
    ])
    
    prompt = f"""You are a critical evaluator of AI-generated responses. Evaluate the following response on these criteria:

QUERY: {query}

RESPONSE: {response}

SOURCES:
{source_context if source_context else "No sources provided"}

Rate each criterion from 0.0 to 1.0:

1. RELEVANCE: Does the response directly address the query?
2. ACCURACY: Is the information factually correct based on the sources?
3. COMPLETENESS: Does it fully answer the question without omissions?
4. GROUNDING: Is it well-supported by the provided sources?

Respond ONLY with this exact JSON format (no extra text):
{{
    "relevance": 0.0-1.0,
    "accuracy": 0.0-1.0,
    "completeness": 0.0-1.0,
    "grounding": 0.0-1.0,
    "reasoning": "Brief explanation"
}}"""
    
    try:
        # Call Ollama
        response_data = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                'model': model,
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': 0.1,  # Low temperature for consistent evaluation
                    'num_predict': 200
                }
            },
            timeout=30
        )
        response_data.raise_for_status()
        
        llm_response = response_data.json().get('response', '{}')
        
        # Parse JSON from response
        import json
        # Extract JSON from markdown code blocks if present
        if '```json' in llm_response:
            llm_response = llm_response.split('```json')[1].split('```')[0]
        elif '```' in llm_response:
            llm_response = llm_response.split('```')[1].split('```')[0]
        
        critique = json.loads(llm_response.strip())
        
        # Ensure all scores are present and valid
        for key in ['relevance', 'accuracy', 'completeness', 'grounding']:
            if key not in critique:
                critique[key] = 0.5  # Default to neutral
            else:
                # Clamp to 0-1 range
                critique[key] = max(0.0, min(1.0, float(critique[key])))
        
        return critique
        
    except Exception as e:
        print(f"⚠️  Error in critique: {e}")
        # Return neutral scores on error
        return {
            'relevance': 0.5,
            'accuracy': 0.5,
            'completeness': 0.5,
            'grounding': 0.5,
            'reasoning': f'Error during evaluation: {str(e)}'
        }

def _compute_quality_score(critique: dict) -> float:
    """
    Compute overall quality score from critique dimensions
    Weighted average with emphasis on accuracy and grounding
    """
    weights = {
        'relevance': 0.25,
        'accuracy': 0.30,
        'completeness': 0.20,
        'grounding': 0.25
    }
    
    score = sum(critique.get(key, 0.5) * weight for key, weight in weights.items())
    return round(score, 2)

def _generate_suggestions(query: str, response: str, critique: dict, model: str) -> list:
    """
    Generate specific suggestions for improving the response
    """
    low_scores = [k for k, v in critique.items() if v < 0.7 and k != 'reasoning']
    
    if not low_scores:
        return []
    
    prompt = f"""The response to "{query}" has low scores in: {', '.join(low_scores)}.

Response: {response}

Critique: {critique.get('reasoning', 'Quality issues detected')}

Provide 2-3 specific, actionable suggestions to improve the response. Format as a simple list.
"""
    
    try:
        response_data = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                'model': model,
                'prompt': prompt,
                'stream': False,
                'options': {'temperature': 0.3, 'num_predict': 150}
            },
            timeout=30
        )
        response_data.raise_for_status()
        
        suggestions_text = response_data.json().get('response', '')
        
        # Parse suggestions (split by newlines, filter empties)
        suggestions = [
            line.strip().lstrip('- ').lstrip('* ').lstrip('1234567890.').strip()
            for line in suggestions_text.split('\n')
            if line.strip() and len(line.strip()) > 10
        ][:3]  # Limit to 3 suggestions
        
        return suggestions if suggestions else ["Consider adding more detail", "Verify factual accuracy"]
        
    except Exception as e:
        print(f"⚠️  Error generating suggestions: {e}")
        return ["Review response quality", "Consider additional sources"]

def _improve_response(query: str, original_response: str, suggestions: list, sources: list, model: str) -> str:
    """
    Generate an improved version of the response based on suggestions
    """
    source_context = "\n\n".join([
        f"Source {i+1}: {src.get('content', '')[:500]}"
        for i, src in enumerate(sources[:3])
    ])
    
    suggestions_text = "\n".join([f"- {s}" for s in suggestions])
    
    prompt = f"""Improve this response based on the suggestions:

QUERY: {query}

ORIGINAL RESPONSE: {original_response}

SUGGESTIONS:
{suggestions_text}

SOURCES:
{source_context}

Provide an improved, more accurate response that addresses the suggestions while staying grounded in the sources.
"""
    
    try:
        response_data = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                'model': model,
                'prompt': prompt,
                'stream': False,
                'options': {'temperature': 0.5, 'num_predict': 500}
            },
            timeout=60
        )
        response_data.raise_for_status()
        
        improved = response_data.json().get('response', '').strip()
        return improved if improved else original_response
        
    except Exception as e:
        print(f"⚠️  Error improving response: {e}")
        return original_response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8020, debug=False)

