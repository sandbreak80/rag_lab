"""
Input Validator - Basic input validation
"""

class InputValidator:
    """
    Validate basic input properties before processing
    """

    MAX_LENGTH = 10000  # 10K characters max
    MIN_LENGTH = 1

    def __init__(self):
        pass

    def validate(self, query: str) -> dict:
        """
        Validate input query

        Returns:
            {'valid': bool, 'error': str}
        """
        # Check if empty
        if not query or len(query.strip()) == 0:
            return {'valid': False, 'error': 'Query cannot be empty'}

        # Check length
        if len(query) < self.MIN_LENGTH:
            return {'valid': False, 'error': f'Query too short (min {self.MIN_LENGTH} chars)'}

        if len(query) > self.MAX_LENGTH:
            return {'valid': False, 'error': f'Query too long (max {self.MAX_LENGTH} chars)'}

        # Check encoding (must be valid UTF-8)
        try:
            query.encode('utf-8')
        except UnicodeEncodeError:
            return {'valid': False, 'error': 'Invalid encoding (must be UTF-8)'}

        # Check for null bytes
        if '\x00' in query:
            return {'valid': False, 'error': 'Invalid characters (null bytes not allowed)'}

        return {'valid': True, 'error': None}

