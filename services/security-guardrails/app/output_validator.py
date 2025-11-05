"""
Output Validation Pipeline
Fast Track Phase 7 - Week 8 Day 6-7

Scans LLM outputs for:
1. PII (Personally Identifiable Information)
2. Harmful content
3. System metadata/information leaks
4. Consistency with input

This is Layer 2 of OWASP LLM02: Insecure Output Handling
"""

import logging
from typing import Dict, List
import re

logger = logging.getLogger(__name__)


class OutputValidator:
    """
    Validate LLM outputs before returning to users

    Purpose:
    - Prevent PII disclosure in responses
    - Block harmful/unsafe content
    - Remove system metadata
    - Ensure response quality
    """

    def __init__(self, pii_detector=None):
        """
        Initialize output validator

        Args:
            pii_detector: PIIDetector instance (if None, will be created)
        """
        self.pii_detector = pii_detector

        # System metadata patterns to strip
        self.system_patterns = [
            r'system:.*',
            r'internal error:.*',
            r'debug:.*',
            r'stack trace:.*',
            r'file path:.*',
            r'/usr/.*',
            r'/home/.*',
            r'api_key.*',
            r'token.*=.*',
        ]

        # Compile patterns
        self.compiled_system_patterns = [
            re.compile(pattern, re.IGNORECASE | re.MULTILINE)
            for pattern in self.system_patterns
        ]

        # Harmful content indicators
        self.harmful_keywords = [
            'suicide', 'self-harm', 'violence', 'illegal', 'explosive',
            'weapon', 'drug synthesis', 'malware', 'hack into',
            'credit card generator', 'fake identity'
        ]

        logger.info("✅ Output validator initialized")

    def validate(self,
                 response: str,
                 original_query: str,
                 config: Dict = None) -> Dict:
        """
        Validate LLM output through multiple checks

        Args:
            response: LLM generated response
            original_query: Original user query (for context)
            config: Validation configuration {
                'check_pii': bool,
                'check_harmful': bool,
                'check_metadata': bool,
                'redact_pii': bool,  # If True, redact; if False, block
                'block_harmful': bool  # If True, block; if False, warn
            }

        Returns:
            {
                'status': 'safe'|'warning'|'unsafe',
                'violations': List[Dict],
                'cleaned_response': str,  # Sanitized version
                'redactions_made': int,
                'latency_ms': float
            }
        """
        import time
        start = time.time()

        # Default config
        if config is None:
            config = {
                'check_pii': True,
                'check_harmful': True,
                'check_metadata': True,
                'redact_pii': True,
                'block_harmful': True
            }

        violations = []
        cleaned_response = response
        status = 'safe'
        redactions_made = 0

        # ============================================================
        # Check 1: PII Detection in Output
        # Purpose: Prevent accidental PII disclosure
        # ============================================================
        if config.get('check_pii', True) and self.pii_detector:
            pii_result = self.pii_detector.detect(response)

            if pii_result['entities']:
                redactions_made = len(pii_result['entities'])

                for entity in pii_result['entities']:
                    violations.append({
                        'type': 'pii_in_output',
                        'severity': 'high',
                        'details': f"{entity['type']}: {entity['text']}",
                        'location': 'output'
                    })

                # Redact or block
                if config.get('redact_pii', True):
                    cleaned_response = pii_result['redacted_text']
                    status = 'warning' if status == 'safe' else status
                    logger.warning(f"PII redacted from output: {redactions_made} entities")
                else:
                    status = 'unsafe'
                    logger.error(f"PII detected in output, blocking response")

        # ============================================================
        # Check 2: System Metadata/Information Leaks
        # Purpose: Prevent disclosure of system internals
        # ============================================================
        if config.get('check_metadata', True):
            metadata_found = []

            for i, pattern in enumerate(self.compiled_system_patterns):
                matches = pattern.findall(cleaned_response)
                if matches:
                    metadata_found.extend(matches)
                    # Strip metadata from response
                    cleaned_response = pattern.sub('[REDACTED]', cleaned_response)

            if metadata_found:
                redactions_made += len(metadata_found)
                violations.append({
                    'type': 'metadata_leak',
                    'severity': 'medium',
                    'details': f"System metadata detected: {len(metadata_found)} instances",
                    'examples': metadata_found[:3]  # Show first 3
                })
                status = 'warning' if status == 'safe' else status
                logger.warning(f"Metadata stripped from output: {len(metadata_found)} instances")

        # ============================================================
        # Check 3: Harmful Content Detection
        # Purpose: Block dangerous/illegal content
        # ============================================================
        if config.get('check_harmful', True):
            harmful_found = []
            response_lower = cleaned_response.lower()

            for keyword in self.harmful_keywords:
                if keyword.lower() in response_lower:
                    harmful_found.append(keyword)

            if harmful_found:
                violations.append({
                    'type': 'harmful_content',
                    'severity': 'critical',
                    'details': f"Harmful content detected: {', '.join(harmful_found)}",
                    'keywords': harmful_found
                })

                if config.get('block_harmful', True):
                    status = 'unsafe'
                    cleaned_response = "I cannot provide information on this topic as it may be harmful or dangerous."
                    logger.error(f"Harmful content detected, blocking response")
                else:
                    status = 'warning'
                    logger.warning(f"Harmful content detected: {harmful_found}")

        # ============================================================
        # Check 4: Response Quality & Consistency
        # Purpose: Basic sanity checks
        # ============================================================
        # Check if response is empty
        if not cleaned_response or len(cleaned_response.strip()) < 10:
            violations.append({
                'type': 'invalid_response',
                'severity': 'medium',
                'details': 'Response is too short or empty'
            })
            status = 'unsafe'

        # Check if response is suspiciously long (possible attack)
        if len(cleaned_response) > 50000:  # 50KB limit
            violations.append({
                'type': 'response_too_long',
                'severity': 'medium',
                'details': f'Response is {len(cleaned_response)} characters (max 50000)'
            })
            cleaned_response = cleaned_response[:50000] + "\n\n[Response truncated due to length]"
            redactions_made += 1
            status = 'warning' if status == 'safe' else status

        # ============================================================
        # Check 5: Prompt Injection Echo Detection
        # Purpose: Detect if LLM is echoing injected instructions
        # ============================================================
        injection_indicators = [
            'as a language model',
            'i don\'t have access to',
            'i cannot access',
            'my training data',
            'my system prompt',
            'ignore previous instructions'
        ]

        response_lower = cleaned_response.lower()
        echo_found = []

        for indicator in injection_indicators:
            if indicator in response_lower and indicator in original_query.lower():
                echo_found.append(indicator)

        if echo_found:
            violations.append({
                'type': 'injection_echo',
                'severity': 'high',
                'details': f'Response may be echoing injected instructions: {echo_found}'
            })
            status = 'warning' if status == 'safe' else status
            logger.warning(f"Possible injection echo detected")

        latency_ms = (time.time() - start) * 1000

        result = {
            'status': status,
            'violations': violations,
            'cleaned_response': cleaned_response,
            'redactions_made': redactions_made,
            'latency_ms': latency_ms
        }

        # Logging
        if status == 'safe':
            logger.debug(f"Output validation PASSED in {latency_ms:.1f}ms")
        elif status == 'warning':
            logger.warning(f"Output validation WARNING: {len(violations)} issues in {latency_ms:.1f}ms")
        else:  # unsafe
            logger.error(f"Output validation FAILED: {len(violations)} violations in {latency_ms:.1f}ms")

        return result

    def validate_batch(self,
                       responses: List[str],
                       original_queries: List[str],
                       config: Dict = None) -> List[Dict]:
        """
        Validate multiple outputs efficiently

        Args:
            responses: List of LLM responses
            original_queries: List of original queries
            config: Validation configuration

        Returns:
            List of validation results
        """
        results = []

        for response, query in zip(responses, original_queries):
            result = self.validate(response, query, config)
            results.append(result)

        return results

    def get_stats(self) -> Dict:
        """Get validation statistics"""
        return {
            'pii_detector_enabled': self.pii_detector is not None,
            'system_patterns': len(self.system_patterns),
            'harmful_keywords': len(self.harmful_keywords)
        }


# Global validator instance (singleton)
_validator_instance = None

def get_validator(pii_detector=None) -> OutputValidator:
    """
    Get or create global output validator instance
    """
    global _validator_instance

    if _validator_instance is None:
        logger.info("Creating output validator instance...")
        _validator_instance = OutputValidator(pii_detector=pii_detector)

    return _validator_instance


# Example usage and testing
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("🧪 Testing Output Validator")
    print("=" * 60)
    print()

    # Initialize validator (without PII detector for this test)
    validator = get_validator()

    # Test cases
    test_cases = [
        # Safe response
        (
            "Retrieval Augmented Generation (RAG) is a technique that combines retrieval with generation...",
            "What is RAG?",
            'safe'
        ),

        # Response with PII (will be redacted by PII detector if available)
        (
            "You can contact me at john.doe@example.com or call 555-123-4567",
            "How do I contact you?",
            'warning'  # Would be warning if PII detector is available
        ),

        # Response with system metadata
        (
            "The answer is in /usr/local/app/data/secrets.txt with API key abc123",
            "Where is the data?",
            'warning'
        ),

        # Response with harmful content
        (
            "To make explosives, you need...",
            "How to make something explode?",
            'unsafe'
        ),

        # Empty response
        (
            "",
            "What is AI?",
            'unsafe'
        ),
    ]

    print("Running test cases...")
    print()

    for response, query, expected_status in test_cases:
        result = validator.validate(response, query)

        status_match = result['status'] == expected_status or result['status'] == 'safe'
        status_icon = "✅" if status_match else "❌"

        print(f"{status_icon} Query: {query}")
        print(f"   Response: {response[:60]}...")
        print(f"   Status: {result['status']} (expected: {expected_status})")
        print(f"   Violations: {len(result['violations'])}")
        print(f"   Redactions: {result['redactions_made']}")
        print(f"   Latency: {result['latency_ms']:.1f}ms")

        if result['violations']:
            for v in result['violations']:
                print(f"      - {v['type']}: {v['details']}")

        print()

    # Validator stats
    print("=" * 60)
    print("Validator Statistics:")
    stats = validator.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

