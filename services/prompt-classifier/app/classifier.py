"""
Prompt Classifier
Categorizes user queries by intent, complexity, domain, and output type
"""
import re
from typing import Dict, List
from enum import Enum

class QueryIntent(str, Enum):
    """Types of user intent"""
    FACTUAL = "factual"           # "What is X?"
    EXPLANATION = "explanation"    # "How does X work?"
    COMPARISON = "comparison"      # "Compare X and Y"
    INSTRUCTION = "instruction"    # "How to do X?"
    CREATIVE = "creative"          # "Write a story about X"
    ANALYTICAL = "analytical"      # "Analyze X"
    CODING = "coding"             # "Write code to X"
    TROUBLESHOOTING = "troubleshooting"  # "Fix X", "Debug Y"

class QueryComplexity(str, Enum):
    """Query complexity levels"""
    SIMPLE = "simple"       # Single fact, basic question
    MODERATE = "moderate"   # Multi-step, some reasoning
    COMPLEX = "complex"     # Deep analysis, multiple concepts
    EXPERT = "expert"       # Advanced technical, research-level

class QueryDomain(str, Enum):
    """Domain/subject area"""
    TECHNICAL = "technical"       # Programming, AI, ML
    GENERAL = "general"           # General knowledge
    ACADEMIC = "academic"         # Research, papers
    BUSINESS = "business"         # Strategy, management
    CREATIVE = "creative"         # Writing, art
    MEDICAL = "medical"           # Health, medicine
    LEGAL = "legal"              # Law, regulations
    EDUCATIONAL = "educational"   # Learning, teaching

class OutputFormat(str, Enum):
    """Desired output format"""
    SHORT = "short"               # Brief answer
    DETAILED = "detailed"         # Comprehensive explanation
    STEP_BY_STEP = "step_by_step" # Tutorial format
    CODE = "code"                 # Code snippet
    STRUCTURED = "structured"     # List, table, etc.
    CONVERSATIONAL = "conversational"  # Natural dialogue

class PromptClassifier:
    """
    Classifies prompts using rule-based + pattern matching
    Fast, deterministic, no external LLM calls needed
    """

    # Intent detection patterns
    INTENT_PATTERNS = {
        QueryIntent.FACTUAL: [
            r'\bwhat is\b', r'\bwhat are\b', r'\bdefine\b', r'\bdefinition\b',
            r'\bwho is\b', r'\bwhen was\b', r'\bwhere is\b'
        ],
        QueryIntent.EXPLANATION: [
            r'\bhow does\b', r'\bhow do\b', r'\bexplain\b', r'\bwhy does\b',
            r'\bwhy do\b', r'\btell me about\b', r'\bwhat makes\b'
        ],
        QueryIntent.COMPARISON: [
            r'\bcompare\b', r'\bdifference between\b', r'\bvs\b', r'\bversus\b',
            r'\bbetter than\b', r'\bcontrast\b', r'\bsimilar to\b'
        ],
        QueryIntent.INSTRUCTION: [
            r'\bhow to\b', r'\bsteps to\b', r'\bguide\b', r'\btutorial\b',
            r'\bteach me\b', r'\bshow me how\b'
        ],
        QueryIntent.CREATIVE: [
            r'\bwrite\b', r'\bcreate\b', r'\bgenerate\b', r'\bcompose\b',
            r'\bstory\b', r'\bpoem\b', r'\bblog post\b'
        ],
        QueryIntent.ANALYTICAL: [
            r'\banalyze\b', r'\bevaluate\b', r'\bassess\b', r'\bcritique\b',
            r'\breview\b', r'\bexamine\b'
        ],
        QueryIntent.CODING: [
            r'\bcode\b', r'\bfunction\b', r'\bimplementation\b', r'\bprogram\b',
            r'\bscript\b', r'\balgorithm\b', r'\bwrite a\b.*\bfunction\b'
        ],
        QueryIntent.TROUBLESHOOTING: [
            r'\bfix\b', r'\bdebug\b', r'\berror\b', r'\bissue\b',
            r'\bproblem with\b', r'\bnot working\b', r'\bfailing\b'
        ]
    }

    # Complexity indicators
    COMPLEXITY_INDICATORS = {
        QueryComplexity.SIMPLE: {
            'max_words': 8,
            'keywords': ['what', 'is', 'define'],
            'score_threshold': 3
        },
        QueryComplexity.MODERATE: {
            'max_words': 15,
            'keywords': ['how', 'why', 'explain', 'compare'],
            'score_threshold': 5
        },
        QueryComplexity.COMPLEX: {
            'max_words': 25,
            'keywords': ['analyze', 'evaluate', 'detailed', 'comprehensive'],
            'score_threshold': 7
        },
        QueryComplexity.EXPERT: {
            'min_words': 20,
            'keywords': ['research', 'advanced', 'technical', 'architecture', 'framework'],
            'score_threshold': 9
        }
    }

    # Domain keywords
    DOMAIN_KEYWORDS = {
        QueryDomain.TECHNICAL: [
            'code', 'programming', 'algorithm', 'API', 'database', 'function',
            'server', 'framework', 'library', 'bug', 'debug', 'software',
            'AI', 'ML', 'neural', 'transformer', 'model', 'training'
        ],
        QueryDomain.ACADEMIC: [
            'paper', 'research', 'study', 'theory', 'hypothesis', 'experiment',
            'journal', 'publication', 'citation', 'methodology'
        ],
        QueryDomain.BUSINESS: [
            'strategy', 'market', 'revenue', 'growth', 'customer', 'sales',
            'marketing', 'management', 'ROI', 'metrics'
        ],
        QueryDomain.CREATIVE: [
            'story', 'narrative', 'character', 'plot', 'creative', 'write',
            'poem', 'art', 'design', 'aesthetic'
        ],
        QueryDomain.MEDICAL: [
            'health', 'medical', 'disease', 'treatment', 'symptom', 'diagnosis',
            'patient', 'clinical', 'therapy'
        ],
        QueryDomain.LEGAL: [
            'law', 'legal', 'regulation', 'compliance', 'contract', 'rights',
            'liability', 'statute', 'court'
        ],
        QueryDomain.EDUCATIONAL: [
            'learn', 'teach', 'student', 'course', 'lesson', 'tutorial',
            'beginner', 'basics', 'introduction'
        ]
    }

    def classify(self, query: str) -> Dict:
        """
        Classify a query across all dimensions

        Returns:
            {
                'intent': QueryIntent,
                'complexity': QueryComplexity,
                'domain': QueryDomain,
                'output_format': OutputFormat,
                'confidence': float (0-1),
                'metadata': {
                    'word_count': int,
                    'has_code_markers': bool,
                    'has_question_mark': bool,
                    ...
                }
            }
        """
        query_lower = query.lower()

        # Detect intent
        intent = self._detect_intent(query_lower)

        # Assess complexity
        complexity = self._assess_complexity(query_lower)

        # Identify domain
        domain = self._identify_domain(query_lower)

        # Determine output format
        output_format = self._determine_output_format(query_lower, intent)

        # Calculate confidence
        confidence = self._calculate_confidence(query_lower, intent, complexity, domain)

        # Extract metadata
        metadata = self._extract_metadata(query)

        return {
            'intent': intent,
            'complexity': complexity,
            'domain': domain,
            'output_format': output_format,
            'confidence': confidence,
            'metadata': metadata
        }

    def _detect_intent(self, query: str) -> QueryIntent:
        """Detect user intent from query"""
        scores = {}

        for intent, patterns in self.INTENT_PATTERNS.items():
            score = sum(1 for pattern in patterns if re.search(pattern, query, re.IGNORECASE))
            if score > 0:
                scores[intent] = score

        if not scores:
            # Default: factual for questions, instruction for imperatives
            if '?' in query:
                return QueryIntent.FACTUAL
            else:
                return QueryIntent.INSTRUCTION

        # Return intent with highest score
        return max(scores, key=scores.get)

    def _assess_complexity(self, query: str) -> QueryComplexity:
        """Assess query complexity"""
        word_count = len(query.split())

        # Count complexity indicators
        complexity_score = 0

        # Word count factor
        if word_count > 25:
            complexity_score += 3
        elif word_count > 15:
            complexity_score += 2
        elif word_count > 8:
            complexity_score += 1

        # Check for complex keywords
        complex_keywords = ['architecture', 'framework', 'comprehensive', 'detailed',
                          'analyze', 'evaluate', 'compare and contrast', 'research']
        complexity_score += sum(1 for kw in complex_keywords if kw in query)

        # Check for multiple concepts (presence of 'and', 'or', conjunctions)
        complexity_score += len(re.findall(r'\band\b|\bor\b|\bwhile\b|\bhowever\b', query))

        # Check for nested questions
        if query.count('?') > 1:
            complexity_score += 1

        # Map score to complexity level
        if complexity_score >= 7:
            return QueryComplexity.EXPERT
        elif complexity_score >= 5:
            return QueryComplexity.COMPLEX
        elif complexity_score >= 3:
            return QueryComplexity.MODERATE
        else:
            return QueryComplexity.SIMPLE

    def _identify_domain(self, query: str) -> QueryDomain:
        """Identify query domain"""
        scores = {}

        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in query)
            if score > 0:
                scores[domain] = score

        if not scores:
            return QueryDomain.GENERAL

        return max(scores, key=scores.get)

    def _determine_output_format(self, query: str, intent: QueryIntent) -> OutputFormat:
        """Determine desired output format"""

        # Check for explicit format requests
        if re.search(r'\bbrief\b|\bshort\b|\bquick\b|\bsummar', query):
            return OutputFormat.SHORT

        if re.search(r'\bdetailed\b|\bcomprehensive\b|\bin-depth\b|\bthorough\b', query):
            return OutputFormat.DETAILED

        if re.search(r'\bstep by step\b|\bsteps\b|\btutorial\b|\bguide\b', query):
            return OutputFormat.STEP_BY_STEP

        if re.search(r'\bcode\b|\bfunction\b|\bscript\b|\bimplementation\b', query):
            return OutputFormat.CODE

        if re.search(r'\blist\b|\btable\b|\bcompare\b|\bbullet points\b', query):
            return OutputFormat.STRUCTURED

        # Default based on intent
        if intent == QueryIntent.CODING:
            return OutputFormat.CODE
        elif intent == QueryIntent.INSTRUCTION:
            return OutputFormat.STEP_BY_STEP
        elif intent == QueryIntent.COMPARISON:
            return OutputFormat.STRUCTURED
        elif intent in [QueryIntent.FACTUAL]:
            return OutputFormat.SHORT
        else:
            return OutputFormat.CONVERSATIONAL

    def _calculate_confidence(self, query: str, intent: QueryIntent,
                            complexity: QueryComplexity, domain: QueryDomain) -> float:
        """Calculate classification confidence (0-1)"""

        confidence = 0.5  # Base confidence

        # Increase if clear intent markers
        intent_patterns = self.INTENT_PATTERNS.get(intent, [])
        if any(re.search(pattern, query) for pattern in intent_patterns):
            confidence += 0.2

        # Increase if clear domain keywords
        domain_keywords = self.DOMAIN_KEYWORDS.get(domain, [])
        keyword_matches = sum(1 for kw in domain_keywords if kw in query)
        confidence += min(keyword_matches * 0.05, 0.2)

        # Increase if query is well-formed
        if '?' in query or query.endswith('.'):
            confidence += 0.1

        return min(confidence, 1.0)

    def _extract_metadata(self, query: str) -> Dict:
        """Extract additional metadata from query"""
        return {
            'word_count': len(query.split()),
            'char_count': len(query),
            'has_question_mark': '?' in query,
            'has_code_markers': bool(re.search(r'```|`|\bcode\b', query)),
            'has_url': bool(re.search(r'https?://', query)),
            'sentence_count': len(re.split(r'[.!?]+', query))
        }


# Singleton instance
classifier = PromptClassifier()

