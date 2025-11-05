"""
PII Detector - Detect and redact Personally Identifiable Information
Uses regex patterns as a lightweight alternative to Presidio for initial implementation
"""

import re
from typing import List, Dict

class PIIDetector:
    """
    Detect and redact PII using regex patterns

    Note: This is a simplified implementation. For production,
    consider using Microsoft Presidio for more accurate detection.
    """

    def __init__(self):
        # PII patterns
        self.patterns = {
            'EMAIL': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'PHONE': re.compile(r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b'),
            'SSN': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            'CREDIT_CARD': re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
            'IP_ADDRESS': re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
            'ZIP_CODE': re.compile(r'\b\d{5}(?:-\d{4})?\b'),
        }

    def detect(self, text: str) -> Dict:
        """
        Detect PII in text

        Returns:
            {
                'pii_found': bool,
                'entities': List[{'type': str, 'text': str, 'start': int, 'end': int}],
                'redacted_text': str
            }
        """
        entities = []
        redacted_text = text

        # Find all PII entities
        for pii_type, pattern in self.patterns.items():
            for match in pattern.finditer(text):
                entities.append({
                    'type': pii_type,
                    'text': match.group(),
                    'start': match.start(),
                    'end': match.end()
                })

        # Redact PII (replace with placeholder)
        # Sort by start position in reverse to maintain indices
        entities.sort(key=lambda x: x['start'], reverse=True)

        for entity in entities:
            redacted_text = (
                redacted_text[:entity['start']] +
                f"<{entity['type']}>" +
                redacted_text[entity['end']:]
            )

        return {
            'pii_found': len(entities) > 0,
            'entities': entities,
            'redacted_text': redacted_text
        }

    def get_supported_types(self) -> List[str]:
        """Get list of supported PII types"""
        return list(self.patterns.keys())

