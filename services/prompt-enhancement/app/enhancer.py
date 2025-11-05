"""
Prompt Enhancer - Intelligent framework-based prompt enhancement
Supports: Chain-of-Thought (CoT), ReAct, Few-Shot, Structured Output
"""

from typing import Dict, List, Optional
from templates import PromptTemplates
import requests
import os

class PromptEnhancer:
    """
    Intelligent prompt enhancement with framework-based strategies:
    - Chain-of-Thought (CoT): For complex reasoning
    - ReAct: For multi-step problem solving
    - Few-Shot: For specialized tasks
    - Structured Output: For code/data generation
    """

    def __init__(self):
        self.templates = PromptTemplates()
        self.classifier_url = os.getenv('PROMPT_CLASSIFIER_URL', 'http://prompt-classifier:8017')

    def enhance(self, query: str, context: Dict, config: Dict) -> Dict:
        """
        Intelligently enhance user prompt based on query characteristics

        NEW: Auto-detects query type and applies optimal enhancement strategy

        Returns:
            {
                'original_query': str,
                'enhanced_prompt': str,
                'enhancements_applied': List[str],
                'enhancement_strategy': str,
                'classification': Dict,
                'estimated_improvement': float
            }
        """
        enhancements_applied = []

        # STEP 1: Classify the query (if not already provided)
        classification = config.get('classification')
        if not classification:
            classification = self._classify_query(query)
            print(f"🔍 Classification: {classification}")

        # STEP 2: Choose enhancement strategy based on classification
        strategy = self._choose_strategy(classification, config)
        print(f"📋 Strategy chosen: {strategy}")

        # STEP 3: Apply the chosen strategy
        if strategy == 'chain_of_thought':
            enhanced = self._apply_cot(query, context, classification)
            enhancements_applied.append('chain_of_thought')
        elif strategy == 'react':
            enhanced = self._apply_react(query, context, classification)
            enhancements_applied.append('react_framework')
        elif strategy == 'few_shot':
            enhanced = self._apply_few_shot(query, context, classification)
            enhancements_applied.append('few_shot_examples')
        elif strategy == 'structured_output':
            enhanced = self._apply_structured(query, context, classification)
            enhancements_applied.append('structured_output')
        else:  # 'standard'
            enhanced = self._apply_standard(query, context, config)
            enhancements_applied.append('standard_enhancement')

        # STEP 4: Add context if provided
        if context.get('documents'):
            enhanced = self._inject_documents(enhanced, context['documents'])
            enhancements_applied.append('rag_context')

        # STEP 5: Add format instructions
        output_format = config.get('output_format', 'markdown')
        if output_format in self.templates.FORMAT_TEMPLATES:
            enhanced += "\n\n" + self.templates.FORMAT_TEMPLATES[output_format]
            enhancements_applied.append('format_instructions')

        # Calculate improvement estimate based on strategy
        improvement_map = {
            'chain_of_thought': 0.4,
            'react': 0.5,
            'few_shot': 0.3,
            'structured_output': 0.35,
            'standard': 0.15
        }
        estimated_improvement = improvement_map.get(strategy, 0.2)

        return {
            'original_query': query,
            'enhanced_prompt': enhanced,
            'enhancements_applied': enhancements_applied,
            'enhancement_strategy': strategy,
            'classification': classification,
            'estimated_improvement': estimated_improvement
        }

    def _classify_query(self, query: str) -> Dict:
        """Call classifier service to categorize query"""
        try:
            response = requests.post(
                f"{self.classifier_url}/classify",
                json={'query': query},
                timeout=5
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"⚠️ Classifier unavailable: {e}")

        # Fallback classification
        return {
            'intent': 'factual',
            'complexity': 'moderate',
            'domain': 'general',
            'confidence': 0.5
        }

    def _choose_strategy(self, classification: Dict, config: Dict) -> str:
        """Choose optimal enhancement strategy based on classification"""

        # User can override
        if config.get('force_strategy'):
            return config['force_strategy']

        complexity = classification.get('complexity', 'moderate')
        intent = classification.get('intent', 'factual')
        domain = classification.get('domain', 'general')

        # STRATEGY SELECTION LOGIC
        # Complex reasoning → Chain-of-Thought
        if complexity in ['complex', 'expert']:
            return 'chain_of_thought'

        # Multi-step instructions → ReAct
        if intent in ['instruction', 'instructional'] or 'step' in classification.get('metadata', {}).get('query_lower', ''):
            return 'react'

        # Code/technical → Structured Output
        if intent == 'coding' or domain == 'code':
            return 'structured_output'

        # Creative/analytical → Few-Shot
        if intent in ['creative', 'analytical']:
            return 'few_shot'

        # Default: Standard enhancement
        return 'standard'

    def _apply_cot(self, query: str, context: Dict, classification: Dict) -> str:
        """Apply Chain-of-Thought enhancement"""
        prompt = f"""You are a helpful AI assistant. When answering complex questions, think step-by-step.

User Question: {query}

Please approach this systematically:
1. First, break down what the question is asking
2. Consider the key concepts and their relationships
3. Reason through each part step-by-step
4. Synthesize your reasoning into a clear answer

Let's think through this step by step:"""
        return prompt

    def _apply_react(self, query: str, context: Dict, classification: Dict) -> str:
        """Apply ReAct (Reason + Act) framework"""
        prompt = f"""You are a helpful AI assistant that solves problems systematically.

User Request: {query}

Use the following approach:
1. THOUGHT: Analyze what needs to be done
2. ACTION: Determine the steps required
3. OBSERVATION: Consider what each step accomplishes
4. REPEAT: Until the problem is solved
5. ANSWER: Provide the complete solution

Let's solve this step-by-step using the ReAct framework:"""
        return prompt

    def _apply_few_shot(self, query: str, context: Dict, classification: Dict) -> str:
        """Apply Few-Shot learning with examples"""
        domain = classification.get('domain', 'general')

        # Domain-specific examples
        examples = {
            'technical': """Example 1:
Q: What is a neural network?
A: A neural network is a computational model inspired by biological neurons. It consists of interconnected layers of nodes that process information through weighted connections, learning patterns from data.

Example 2:
Q: How does backpropagation work?
A: Backpropagation is a learning algorithm that adjusts neural network weights by computing gradients of the loss function with respect to each weight, propagating errors backwards through the network.
""",
            'general': """Example 1:
Q: What causes seasons?
A: Seasons are caused by Earth's 23.5° axial tilt as it orbits the Sun. When a hemisphere tilts toward the Sun, it experiences summer; when tilted away, it experiences winter.

Example 2:
Q: Why is the sky blue?
A: The sky appears blue due to Rayleigh scattering - shorter blue wavelengths of sunlight scatter more in Earth's atmosphere than longer red wavelengths, making the sky look blue.
"""
        }

        example_text = examples.get(domain, examples['general'])

        prompt = f"""You are a helpful AI assistant. Here are examples of high-quality answers:

{example_text}

Now answer this question in the same style:
Q: {query}
A:"""
        return prompt

    def _apply_structured(self, query: str, context: Dict, classification: Dict) -> str:
        """Apply structured output format (for code/data)"""
        prompt = f"""You are a helpful AI coding assistant.

User Request: {query}

Provide a structured response with:
1. **Explanation**: Brief overview of the solution
2. **Implementation**: Clean, well-commented code
3. **Example**: Usage example with expected output
4. **Notes**: Any important considerations

Response:"""
        return prompt

    def _apply_standard(self, query: str, context: Dict, config: Dict) -> str:
        """Apply standard enhancement (current behavior)"""
        query_type = config.get('query_type', 'default')
        system_template = self.templates.SYSTEM_TEMPLATES.get(
            query_type,
            self.templates.SYSTEM_TEMPLATES.get('default', '')
        )

        prompt = f"""{system_template}

User Question: {query}

Please provide a clear, accurate, and helpful response."""
        return prompt

    def _inject_documents(self, prompt: str, documents: List[Dict]) -> str:
        """Inject RAG documents into prompt"""
        docs_text = self._format_documents(documents)

        injected = f"""You have access to the following relevant documents:

{docs_text}

---

{prompt}

Base your answer on the provided documents where relevant."""
        return injected

    def _format_documents(self, documents: List[Dict]) -> str:
        """Format retrieved documents for context"""
        if not documents:
            return ""

        formatted = []
        for i, doc in enumerate(documents[:5], 1):  # Max 5 documents
            content = doc.get('content', doc.get('text', ''))
            source = doc.get('source', doc.get('file_name', 'Unknown'))
            formatted.append(f"[Document {i}] {source}:\n{content}\n")

        return "\n".join(formatted)

    def _format_history(self, history: List[Dict]) -> str:
        """Format conversation history"""
        if not history:
            return ""

        formatted = []
        for turn in history[-5:]:  # Last 5 turns
            role = turn.get('role', 'unknown')
            content = turn.get('content', '')
            formatted.append(f"{role.capitalize()}: {content}")

        return "\n".join(formatted)

