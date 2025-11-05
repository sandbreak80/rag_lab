"""
Injection Detector - 3-layer prompt injection detection
Layer 1: Pattern matching (< 1ms)
Layer 2: ML Classifier (30-50ms) - NEW: 85%+ accuracy
Layer 3: Heuristic fallback (< 10ms)

Fast Track Phase 7 - Week 8 Day 3-5
"""

import re
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class InjectionDetector:
    """
    Multi-layer prompt injection detection
    """

    def __init__(self, use_ml: bool = True):
        """
        Initialize injection detector with optional ML classifier

        Args:
            use_ml: If True, use ML classifier (Layer 2). If False, fallback to heuristics only.
        """
        self.use_ml = use_ml
        self.ml_classifier = None

        # Try to load ML classifier
        if self.use_ml:
            try:
                from ml_classifier import get_classifier
                self.ml_classifier = get_classifier()
                logger.info("✅ ML injection classifier loaded (85%+ accuracy)")
            except Exception as e:
                logger.warning(f"Failed to load ML classifier, falling back to heuristics: {e}")
                self.use_ml = False

        # Layer 1: Suspicious patterns (regex)
        self.suspicious_patterns = [
            # Direct instruction override
            r'ignore\s+(all\s+)?previous\s+instructions?',
            r'disregard\s+(all\s+)?previous\s+instructions?',
            r'forget\s+(all\s+)?previous\s+instructions?',

            # System prompt extraction
            r'(show|print|display|reveal|output)\s+(your\s+)?(system\s+)?prompt',
            r'what\s+(is|are)\s+your\s+instructions?',
            r'repeat\s+your\s+instructions?',

            # Role-playing attacks
            r'you\s+are\s+now\s+(in\s+)?developer\s+mode',
            r'you\s+are\s+now\s+DAN',
            r'pretend\s+you\s+are',
            r'act\s+as\s+if\s+you\s+(are|were)',

            # Delimiter injection
            r'```\s*system:',
            r'<\s*system\s*>',
            r'\[system\]',

            # Bypass attempts
            r'without\s+restrictions?',
            r'no\s+limitations?',
            r'bypass\s+(all\s+)?(rules?|filters?|safety)',
        ]

        # Compile patterns
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.suspicious_patterns
        ]

        # Suspicious keywords
        self.suspicious_keywords = [
            'jailbreak', 'hack', 'exploit', 'bypass', 'override',
            'administrator', 'root', 'sudo', 'privilege'
        ]

    def detect(self, text: str) -> Dict:
        """
        Detect prompt injection attempts using 3-layer cascade

        Layer 1: Fast pattern matching (< 1ms)
        Layer 2: ML Classifier (30-50ms, 85%+ accuracy)
        Layer 3: Heuristic fallback (< 10ms)

        Returns:
            {
                'is_injection': bool,
                'confidence': float,  # 0.0-1.0
                'detection_method': str,  # 'pattern' | 'ml' | 'heuristic'
                'matched_patterns': List[str],
                'ml_result': Dict,  # Only if ML used
                'latency_ms': float
            }
        """
        import time
        start_time = time.time()

        matched_patterns = []

        # ============================================================
        # Layer 1: Pattern Matching (Fast Filter)
        # Purpose: Catch obvious injection attempts immediately
        # Latency: < 1ms
        # ============================================================
        for i, pattern in enumerate(self.compiled_patterns):
            if pattern.search(text):
                matched_patterns.append(self.suspicious_patterns[i])

        # If obvious patterns found, immediately flag as injection
        if matched_patterns:
            latency_ms = (time.time() - start_time) * 1000
            logger.info(f"Layer 1 BLOCK: Pattern match in {latency_ms:.2f}ms")
            return {
                'is_injection': True,
                'confidence': 0.95,
                'detection_method': 'pattern',
                'matched_patterns': matched_patterns,
                'latency_ms': latency_ms
            }

        # ============================================================
        # Layer 2: ML Classifier (Primary Defense)
        # Purpose: High-accuracy classification
        # Latency: 30-50ms
        # Accuracy: 85-92%
        # ============================================================
        if self.use_ml and self.ml_classifier:
            try:
                ml_result = self.ml_classifier.predict(text)

                # Use ML recommendation
                if ml_result['recommendation'] == 'block':
                    latency_ms = (time.time() - start_time) * 1000
                    logger.info(f"Layer 2 BLOCK: ML classified as {ml_result['label']} "
                               f"({ml_result['confidence']:.2%}) in {latency_ms:.2f}ms")
                    return {
                        'is_injection': True,
                        'confidence': ml_result['confidence'],
                        'detection_method': 'ml',
                        'matched_patterns': [],
                        'ml_result': ml_result,
                        'latency_ms': latency_ms
                    }
                elif ml_result['recommendation'] == 'allow':
                    latency_ms = (time.time() - start_time) * 1000
                    logger.debug(f"Layer 2 ALLOW: ML classified as {ml_result['label']} "
                                f"({ml_result['confidence']:.2%}) in {latency_ms:.2f}ms")
                    return {
                        'is_injection': False,
                        'confidence': ml_result['confidence'],
                        'detection_method': 'ml',
                        'matched_patterns': [],
                        'ml_result': ml_result,
                        'latency_ms': latency_ms
                    }
                # If 'escalate', continue to Layer 3
                logger.debug(f"Layer 2: Low confidence ({ml_result['confidence']:.2%}), "
                            f"escalating to Layer 3")

            except Exception as e:
                logger.error(f"Layer 2 ML classifier failed: {e}, falling back to Layer 3")

        # ============================================================
        # Layer 3: Heuristic Analysis (Fallback)
        # Purpose: Handle edge cases and low-confidence predictions
        # Latency: < 10ms
        # ============================================================
        heuristic_score = self._heuristic_analysis(text)

        latency_ms = (time.time() - start_time) * 1000

        if heuristic_score > 0.7:
            logger.info(f"Layer 3 BLOCK: Heuristic score {heuristic_score:.2f} in {latency_ms:.2f}ms")
            return {
                'is_injection': True,
                'confidence': heuristic_score,
                'detection_method': 'heuristic',
                'matched_patterns': [],
                'latency_ms': latency_ms
            }

        # All layers passed - input is safe
        logger.debug(f"All layers ALLOW in {latency_ms:.2f}ms")
        return {
            'is_injection': False,
            'confidence': 1.0 - heuristic_score,
            'detection_method': 'heuristic',
            'matched_patterns': [],
            'latency_ms': latency_ms
        }

    def _heuristic_analysis(self, text: str) -> float:
        """
        Heuristic-based analysis for suspicious content

        Returns:
            float: Suspicion score (0.0-1.0)
        """
        score = 0.0
        text_lower = text.lower()

        # Check for suspicious keywords
        keyword_count = sum(1 for keyword in self.suspicious_keywords if keyword in text_lower)
        score += min(keyword_count * 0.15, 0.4)  # Max 0.4 from keywords

        # Check for excessive special characters (obfuscation attempt)
        special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
        if special_chars > len(text) * 0.3:  # More than 30% special chars
            score += 0.2

        # Check for repetitive patterns (context overflow attempt)
        words = text.split()
        if len(words) > 10:
            unique_words = len(set(words))
            if unique_words / len(words) < 0.3:  # Less than 30% unique words
                score += 0.2

        # Check for multiple delimiters (delimiter injection)
        delimiter_count = text.count('```') + text.count('---') + text.count('===')
        if delimiter_count > 3:
            score += 0.2

        return min(score, 1.0)

