"""
Prompt Categorization Service
Analyzes user queries and categorizes them for optimal processing
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import json
import sys

# Add common to path
sys.path.insert(0, '/workspace/services/common')

from config import SERVICE_NAME, SERVICE_PORT

app = Flask(__name__)
CORS(app)

# Configuration
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://ollama:11434')
CATEGORIZER_MODEL = os.getenv('CATEGORIZER_MODEL', 'llama3.2:3b')  # Use fast model

# Taxonomy for categorization
TAXONOMY = {
    'intent': [
        'factual',       # Simple factual question
        'analytical',    # Requires analysis/comparison
        'creative',      # Creative/generative task
        'instructional', # How-to or step-by-step
        'conversational',# Chatty/open-ended
        'code'          # Programming/technical code
    ],
    'domain': [
        'general',      # General knowledge
        'technical',    # Technical/scientific
        'academic',     # Academic/research
        'business',     # Business/professional
        'creative',     # Arts/creative
        'code'          # Programming
    ],
    'complexity': [
        'simple',       # One-sentence answer
        'moderate',     # Paragraph explanation
        'complex',      # Multi-part, detailed
        'expert'        # Requires deep expertise
    ],
    'reasoning_type': [
        'factual',      # Just recall facts
        'analytical',   # Need to analyze
        'multi_step',   # Multiple reasoning steps
        'comparative',  # Compare and contrast
        'causal'        # Cause and effect
    ]
}

class PromptCategorizer:
    """LLM-based prompt categorizer"""
    
    def __init__(self):
        self.ollama_url = OLLAMA_URL
        self.model = CATEGORIZER_MODEL
    
    def categorize(self, query: str) -> dict:
        """
        Categorize a user query
        
        Returns classification across multiple dimensions
        """
        
        # Build categorization prompt
        prompt = f"""Analyze this user query and categorize it. Return ONLY a JSON object.

User Query: "{query}"

Categorize the query:

1. Intent (what does the user want?):
   - factual: Simple factual question
   - analytical: Requires analysis or comparison
   - creative: Creative or generative task
   - instructional: How-to or step-by-step guide
   - conversational: Open-ended conversation
   - code: Programming or technical code

2. Domain (what field?):
   - general: General knowledge
   - technical: Technical/scientific topic
   - academic: Academic/research topic
   - business: Business/professional
   - creative: Arts/creative field
   - code: Programming/software

3. Complexity (how detailed?):
   - simple: Can be answered in 1-2 sentences
   - moderate: Needs a paragraph explanation
   - complex: Requires multiple paragraphs or steps
   - expert: Requires deep expertise

4. Reasoning Type (what kind of thinking?):
   - factual: Just recall facts
   - analytical: Analyze information
   - multi_step: Multiple reasoning steps needed
   - comparative: Compare and contrast things
   - causal: Explain cause and effect

Return ONLY this JSON (no other text):
{{
  "intent": "...",
  "domain": "...",
  "complexity": "...",
  "reasoning_type": "...",
  "confidence": 0.0-1.0
}}"""

        try:
            # Call Ollama for classification
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    'model': self.model,
                    'prompt': prompt,
                    'stream': False,
                    'options': {
                        'temperature': 0.1,  # Low temp for consistent classification
                        'num_predict': 200   # Short response
                    }
                },
                timeout=10  # Fast timeout for classification
            )
            
            if response.status_code != 200:
                print(f"Ollama error: {response.status_code}")
                return self._fallback_categorize(query)
            
            result = response.json()
            classification_text = result.get('response', '')
            
            # Parse JSON from response
            try:
                # Try to extract JSON from response
                start = classification_text.find('{')
                end = classification_text.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = classification_text[start:end]
                    classification = json.loads(json_str)
                    
                    # Validate fields
                    if all(k in classification for k in ['intent', 'domain', 'complexity', 'reasoning_type']):
                        return classification
                
                print(f"Failed to parse JSON from: {classification_text[:200]}")
                return self._fallback_categorize(query)
                
            except json.JSONDecodeError as e:
                print(f"JSON parse error: {e}")
                return self._fallback_categorize(query)
            
        except Exception as e:
            print(f"Categorization error: {e}")
            return self._fallback_categorize(query)
    
    def _fallback_categorize(self, query: str) -> dict:
        """
        Rule-based fallback categorization
        Fast and always works
        """
        query_lower = query.lower()
        
        # Detect intent
        intent = 'factual'
        if any(word in query_lower for word in ['how to', 'steps', 'guide', 'tutorial']):
            intent = 'instructional'
        elif any(word in query_lower for word in ['compare', 'difference', 'versus', 'vs']):
            intent = 'analytical'
        elif any(word in query_lower for word in ['write', 'create', 'generate', 'design']):
            intent = 'creative'
        elif any(word in query_lower for word in ['code', 'function', 'class', 'implement']):
            intent = 'code'
        
        # Detect domain
        domain = 'general'
        if any(word in query_lower for word in ['code', 'programming', 'python', 'javascript', 'api']):
            domain = 'code'
        elif any(word in query_lower for word in ['research', 'paper', 'study', 'academic']):
            domain = 'academic'
        elif any(word in query_lower for word in ['algorithm', 'neural', 'machine learning', 'ai']):
            domain = 'technical'
        
        # Detect complexity
        complexity = 'simple'
        word_count = len(query.split())
        if word_count > 20 or '?' in query and query.count('?') > 1:
            complexity = 'complex'
        elif word_count > 10:
            complexity = 'moderate'
        
        # Detect reasoning type
        reasoning_type = 'factual'
        if intent == 'analytical' or 'compare' in query_lower:
            reasoning_type = 'comparative'
        elif 'why' in query_lower or 'because' in query_lower:
            reasoning_type = 'causal'
        elif intent == 'instructional' or 'step' in query_lower:
            reasoning_type = 'multi_step'
        
        return {
            'intent': intent,
            'domain': domain,
            'complexity': complexity,
            'reasoning_type': reasoning_type,
            'confidence': 0.7,  # Lower confidence for rule-based
            'method': 'fallback'
        }

# Global categorizer
categorizer = PromptCategorizer()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'prompt-categorizer',
        'model': CATEGORIZER_MODEL
    })

@app.route('/categorize', methods=['POST'])
def categorize_prompt():
    """
    Categorize a user query
    
    POST /categorize
    {
        "query": "What is the attention mechanism in transformers?"
    }
    
    Returns:
    {
        "query": "...",
        "intent": "factual",
        "domain": "technical",
        "complexity": "moderate",
        "reasoning_type": "factual",
        "confidence": 0.85,
        "processing_time_ms": 234
    }
    """
    import time
    start = time.time()
    
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({'error': 'Query required'}), 400
        
        # Categorize
        print(f"📊 Categorizing: {query[:50]}...")
        classification = categorizer.categorize(query)
        
        processing_time = (time.time() - start) * 1000
        
        result = {
            'query': query,
            **classification,
            'processing_time_ms': round(processing_time, 1)
        }
        
        print(f"✅ Category: {classification['intent']}/{classification['complexity']} ({processing_time:.0f}ms)")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Categorization error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/taxonomy', methods=['GET'])
def get_taxonomy():
    """Get the categorization taxonomy"""
    return jsonify(TAXONOMY)

if __name__ == '__main__':
    print("🧠 Prompt Categorizer Service starting...")
    print(f"   Model: {CATEGORIZER_MODEL}")
    print(f"   Port: {SERVICE_PORT}")
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=False)

