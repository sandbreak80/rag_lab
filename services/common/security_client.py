"""
Security Client - Client library for security-guardrails service
"""

import requests
from typing import Dict, Optional

class SecurityClient:
    """
    Client for interacting with security-guardrails service
    """

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.timeout = 5.0  # 5 second timeout

    def validate_input(
        self,
        query: str,
        use_case: str = 'educational',
        user_id: Optional[str] = None,
        config: Optional[Dict] = None
    ) -> Dict:
        """
        Validate user input through security pipeline

        Args:
            query: User input query
            use_case: Use case policy to apply (educational, demo, production)
            user_id: Optional user identifier
            config: Optional configuration overrides

        Returns:
            {
                'status': 'allowed'|'blocked'|'warning',
                'cleaned_query': str,
                'violations': List[Dict],
                'topics': List[str],
                'confidence': float,
                'latency_ms': float
            }
        """
        try:
            response = requests.post(
                f"{self.base_url}/validate_input",
                json={
                    'query': query,
                    'use_case': use_case,
                    'user_id': user_id,
                    'config': config or {
                        'check_pii': True,
                        'check_injection': True,
                        'check_topics': True,
                        'check_unicode': True,
                        'block_on_violation': False  # Warn instead of block by default
                    }
                },
                timeout=self.timeout
            )

            if response.status_code == 200:
                return response.json()
            else:
                # Security service error - fail open (allow request with warning)
                return {
                    'status': 'warning',
                    'cleaned_query': query,
                    'violations': [{
                        'type': 'security_service_error',
                        'severity': 'medium',
                        'details': f'Security service returned {response.status_code}'
                    }],
                    'topics': [],
                    'confidence': 0.0,
                    'latency_ms': 0
                }
        except Exception as e:
            # Security service unreachable - fail open (allow request with warning)
            print(f"⚠️  Security service error: {e}")
            return {
                'status': 'warning',
                'cleaned_query': query,
                'violations': [{
                    'type': 'security_service_unreachable',
                    'severity': 'medium',
                    'details': str(e)
                }],
                'topics': [],
                'confidence': 0.0,
                'latency_ms': 0
            }

    def validate_output(
        self,
        response: str,
        original_query: str,
        config: Optional[Dict] = None
    ) -> Dict:
        """
        Validate LLM output for safety and PII

        Args:
            response: LLM generated response
            original_query: Original user query
            config: Optional configuration overrides

        Returns:
            {
                'status': 'safe'|'unsafe',
                'cleaned_response': str,
                'violations': List[Dict],
                'latency_ms': float
            }
        """
        try:
            resp = requests.post(
                f"{self.base_url}/validate_output",
                json={
                    'response': response,
                    'original_query': original_query,
                    'config': config or {
                        'check_pii': True,
                        'check_safety': True
                    }
                },
                timeout=self.timeout
            )

            if resp.status_code == 200:
                return resp.json()
            else:
                # Security service error - return original response
                return {
                    'status': 'safe',
                    'cleaned_response': response,
                    'violations': [],
                    'latency_ms': 0
                }
        except Exception as e:
            # Security service unreachable - return original response
            print(f"⚠️  Security service error: {e}")
            return {
                'status': 'safe',
                'cleaned_response': response,
                'violations': [],
                'latency_ms': 0
            }

    def health_check(self) -> bool:
        """Check if security service is healthy"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=2.0)
            return response.status_code == 200
        except:
            return False


class EnhancementClient:
    """
    Client for interacting with prompt-enhancement service
    """

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.timeout = 5.0

    def enhance(
        self,
        query: str,
        context: Optional[Dict] = None,
        config: Optional[Dict] = None
    ) -> Dict:
        """
        Enhance user prompt for better LLM responses

        Args:
            query: User input query
            context: Optional context (documents, history, user profile)
            config: Optional configuration overrides

        Returns:
            {
                'original_query': str,
                'enhanced_prompt': str,
                'enhancements_applied': List[str],
                'estimated_improvement': float,
                'latency_ms': float
            }
        """
        try:
            response = requests.post(
                f"{self.base_url}/enhance",
                json={
                    'query': query,
                    'context': context or {},
                    'config': config or {
                        'enhancement_level': 'standard',
                        'output_format': 'markdown',
                        'query_type': 'default',
                        'add_safety_instructions': True
                    }
                },
                timeout=self.timeout
            )

            if response.status_code == 200:
                return response.json()
            else:
                # Enhancement service error - return original query
                return {
                    'original_query': query,
                    'enhanced_prompt': query,
                    'enhancements_applied': [],
                    'estimated_improvement': 0.0,
                    'latency_ms': 0
                }
        except Exception as e:
            # Enhancement service unreachable - return original query
            print(f"⚠️  Enhancement service error: {e}")
            return {
                'original_query': query,
                'enhanced_prompt': query,
                'enhancements_applied': [],
                'estimated_improvement': 0.0,
                'latency_ms': 0
            }

    def health_check(self) -> bool:
        """Check if enhancement service is healthy"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=2.0)
            return response.status_code == 200
        except:
            return False

