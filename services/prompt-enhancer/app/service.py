"""
Prompt Enhancer Service
Applies intelligent enhancement strategies to improve prompts
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# Add common to path
sys.path.insert(0, '/workspace/services/common')

from enhancer import enhancer, EnhancementStrategy
from config import SERVICE_NAME, SERVICE_PORT

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'service': SERVICE_NAME,
        'version': '1.0.0',
        'strategies': [s.value for s in EnhancementStrategy]
    })

@app.route('/enhance', methods=['POST'])
def enhance_prompt():
    """
    Enhance a single prompt

    Body:
    {
        "query": "How does attention work?",
        "strategy": "chain_of_thought",  // optional
        "context": {                     // optional
            "domain": "technical",
            "complexity": "complex",
            "intent": "explanation"
        }
    }

    Returns:
    {
        "original_query": "...",
        "enhanced_prompt": "...",
        "strategy_used": "chain_of_thought",
        "metadata": {...}
    }
    """
    try:
        data = request.get_json()
        query = data.get('query', '')
        strategy = data.get('strategy', 'standard')
        context = data.get('context', {})

        if not query:
            return jsonify({'error': 'Query required'}), 400

        # Validate strategy
        valid_strategies = [s.value for s in EnhancementStrategy]
        if strategy not in valid_strategies:
            return jsonify({
                'error': f'Invalid strategy. Must be one of: {valid_strategies}'
            }), 400

        # Enhance
        result = enhancer.enhance(query, strategy, context)

        return jsonify(result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/enhance/batch', methods=['POST'])
def enhance_batch():
    """
    Enhance multiple prompts

    Body:
    {
        "queries": ["query1", "query2", ...],
        "strategy": "chain_of_thought",  // optional, applies to all
        "contexts": [{}, {}, ...]         // optional, per-query context
    }
    """
    try:
        data = request.get_json()
        queries = data.get('queries', [])
        strategy = data.get('strategy', 'standard')
        contexts = data.get('contexts')

        if not queries:
            return jsonify({'error': 'Queries required'}), 400

        # Enhance all
        results = enhancer.enhance_batch(queries, strategy, contexts)

        return jsonify({'results': results})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/strategies', methods=['GET'])
def list_strategies():
    """List available enhancement strategies"""
    strategies = {
        'standard': {
            'name': 'Standard',
            'description': 'Basic enhancement with educational focus',
            'best_for': 'General queries',
            'complexity_overhead': 'low'
        },
        'chain_of_thought': {
            'name': 'Chain of Thought (CoT)',
            'description': 'Step-by-step reasoning for complex problems',
            'best_for': 'Complex reasoning, analysis, comparisons',
            'complexity_overhead': 'medium'
        },
        'react': {
            'name': 'ReAct (Reasoning + Acting)',
            'description': 'Alternates between reasoning and action steps',
            'best_for': 'Multi-step problems requiring planning',
            'complexity_overhead': 'high'
        },
        'few_shot': {
            'name': 'Few-Shot Learning',
            'description': 'Provides examples before the query',
            'best_for': 'Format consistency, pattern learning',
            'complexity_overhead': 'medium'
        },
        'step_by_step': {
            'name': 'Step-by-Step Instructions',
            'description': 'Structured step-by-step format',
            'best_for': 'Tutorials, how-to guides, procedures',
            'complexity_overhead': 'low'
        },
        'structured_output': {
            'name': 'Structured Output',
            'description': 'Requests specific output format (code, lists, etc.)',
            'best_for': 'Coding tasks, structured data',
            'complexity_overhead': 'low'
        },
        'detailed': {
            'name': 'Detailed Analysis',
            'description': 'Requests comprehensive, in-depth response',
            'best_for': 'Research questions, deep dives',
            'complexity_overhead': 'medium'
        },
        'socratic': {
            'name': 'Socratic Method',
            'description': 'Guides learning through questions',
            'best_for': 'Educational contexts, conceptual learning',
            'complexity_overhead': 'medium'
        }
    }

    return jsonify({
        'strategies': strategies,
        'count': len(strategies)
    })

if __name__ == '__main__':
    print(f"✨ {SERVICE_NAME} starting on port {SERVICE_PORT}...")
    print(f"📚 Available strategies: {[s.value for s in EnhancementStrategy]}")
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=False)

