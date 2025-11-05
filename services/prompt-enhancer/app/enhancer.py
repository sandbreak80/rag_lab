"""
Prompt Enhancement Engine
Applies various enhancement strategies to improve query quality
"""
from typing import Dict, Optional
from enum import Enum

class EnhancementStrategy(str, Enum):
    """Available enhancement strategies"""
    STANDARD = "standard"
    CHAIN_OF_THOUGHT = "chain_of_thought"  # CoT for complex reasoning
    REACT = "react"  # Reasoning + Acting
    FEW_SHOT = "few_shot"  # Include examples
    STEP_BY_STEP = "step_by_step"  # Break into steps
    STRUCTURED_OUTPUT = "structured_output"  # Format guidance
    DETAILED = "detailed"  # Request comprehensive answer
    SOCRATIC = "socratic"  # Guide with questions

class PromptEnhancer:
    """
    Enhances prompts using various strategies
    """

    def enhance(self, query: str, strategy: str = "standard",
                context: Optional[Dict] = None) -> Dict:
        """
        Enhance a prompt using specified strategy

        Args:
            query: Original user query
            strategy: Enhancement strategy to use
            context: Additional context (classification, metadata, etc.)

        Returns:
            {
                'original_query': str,
                'enhanced_prompt': str,
                'strategy_used': str,
                'metadata': dict
            }
        """
        context = context or {}

        # Select enhancement function
        if strategy == EnhancementStrategy.CHAIN_OF_THOUGHT:
            enhanced = self._apply_chain_of_thought(query, context)
        elif strategy == EnhancementStrategy.REACT:
            enhanced = self._apply_react(query, context)
        elif strategy == EnhancementStrategy.FEW_SHOT:
            enhanced = self._apply_few_shot(query, context)
        elif strategy == EnhancementStrategy.STEP_BY_STEP:
            enhanced = self._apply_step_by_step(query, context)
        elif strategy == EnhancementStrategy.STRUCTURED_OUTPUT:
            enhanced = self._apply_structured_output(query, context)
        elif strategy == EnhancementStrategy.DETAILED:
            enhanced = self._apply_detailed(query, context)
        elif strategy == EnhancementStrategy.SOCRATIC:
            enhanced = self._apply_socratic(query, context)
        else:
            enhanced = self._apply_standard(query, context)

        return {
            'original_query': query,
            'enhanced_prompt': enhanced,
            'strategy_used': strategy,
            'metadata': {
                'original_length': len(query),
                'enhanced_length': len(enhanced),
                'expansion_ratio': len(enhanced) / len(query) if query else 0
            }
        }

    def _apply_standard(self, query: str, context: Dict) -> str:
        """Standard enhancement - minimal changes"""
        # Add educational context
        return f"""Question: {query}

Please provide a clear, accurate answer focused on educational value.
If relevant, include examples and explain key concepts."""

    def _apply_chain_of_thought(self, query: str, context: Dict) -> str:
        """
        Chain-of-Thought prompting for complex reasoning
        Encourages step-by-step thinking
        """
        return f"""Question: {query}

Let's approach this step-by-step:

1. First, break down the key concepts and requirements
2. Consider the relevant information and context
3. Reason through the problem systematically
4. Draw conclusions based on the analysis
5. Provide a clear, well-reasoned answer

Think through each step carefully before answering."""

    def _apply_react(self, query: str, context: Dict) -> str:
        """
        ReAct (Reasoning + Acting) prompting
        Alternates between reasoning and taking action
        """
        return f"""Question: {query}

Use the following format:

**Thought:** What do I need to understand or figure out?
**Action:** What information or approach should I use?
**Observation:** What did I learn or discover?
**Thought:** How does this help answer the question?
**Answer:** [Final answer based on reasoning]

Apply this reasoning process to provide a thorough response."""

    def _apply_few_shot(self, query: str, context: Dict) -> str:
        """
        Few-shot prompting with examples
        """
        domain = context.get('domain', 'general')

        # Add relevant examples based on domain
        if domain == 'technical':
            examples = """
Example 1:
Q: What is recursion?
A: Recursion is when a function calls itself to solve smaller instances of the same problem. For example, calculating factorial: factorial(5) = 5 * factorial(4).

Example 2:
Q: Explain binary search.
A: Binary search finds an element in a sorted array by repeatedly dividing the search space in half. Time complexity is O(log n).
"""
        else:
            examples = """
Example 1:
Q: What is photosynthesis?
A: Photosynthesis is the process plants use to convert sunlight into energy, producing oxygen as a byproduct.

Example 2:
Q: How do vaccines work?
A: Vaccines train the immune system by introducing a harmless version of a pathogen, helping the body recognize and fight it later.
"""

        return f"""{examples}

Now answer this question in a similar clear, educational manner:

Question: {query}
Answer:"""

    def _apply_step_by_step(self, query: str, context: Dict) -> str:
        """
        Step-by-step instruction format
        """
        return f"""Question: {query}

Please provide a step-by-step answer:

**Step 1:** [First step]
**Step 2:** [Second step]
**Step 3:** [Third step]
...

Make each step clear and actionable. Include explanations where helpful."""

    def _apply_structured_output(self, query: str, context: Dict) -> str:
        """
        Request structured output (for code, lists, etc.)
        """
        intent = context.get('intent', '')

        if intent == 'coding':
            return f"""Question: {query}

Please provide your response in this format:

**Code:**
```python
# Well-commented, clean code here
```

**Explanation:**
- What the code does
- Key concepts used
- Time/space complexity (if applicable)

**Usage Example:**
```python
# Example of how to use the code
```"""
        else:
            return f"""Question: {query}

Please structure your response clearly:

**Summary:** [Brief overview]

**Key Points:**
- Point 1
- Point 2
- Point 3

**Details:** [Comprehensive explanation]

**Examples:** [If applicable]"""

    def _apply_detailed(self, query: str, context: Dict) -> str:
        """
        Request comprehensive, detailed answer
        """
        return f"""Question: {query}

Please provide a comprehensive, detailed answer that includes:

1. **Core Concept:** Explain the fundamental idea clearly
2. **Background:** Provide relevant context and history
3. **How It Works:** Explain the mechanism or process
4. **Examples:** Give concrete, practical examples
5. **Applications:** Describe real-world uses
6. **Considerations:** Mention important nuances or edge cases

Aim for depth and educational value."""

    def _apply_socratic(self, query: str, context: Dict) -> str:
        """
        Socratic method - guide learning through questions
        """
        return f"""Original Question: {query}

Let's explore this through guided questions and answers:

**Q1:** What are the key concepts we need to understand?
**A1:** [Explanation]

**Q2:** How do these concepts relate to the question?
**A2:** [Explanation]

**Q3:** What's the most important thing to understand?
**A3:** [Explanation]

**Final Answer:** [Comprehensive response]

This approach helps build understanding from fundamentals."""

    def enhance_batch(self, queries: list, strategy: str = "standard",
                     contexts: Optional[list] = None) -> list:
        """Enhance multiple queries at once"""
        contexts = contexts or [{}] * len(queries)
        results = []

        for query, context in zip(queries, contexts):
            enhanced = self.enhance(query, strategy, context)
            results.append(enhanced)

        return results


# Singleton instance
enhancer = PromptEnhancer()

