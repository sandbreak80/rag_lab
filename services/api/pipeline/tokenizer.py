"""
Simple tokenizer for chunk size estimation
"""

def count_tokens(text: str) -> int:
    """
    Estimate token count using simple whitespace splitting.

    This is a rough approximation. For production, consider using
    tiktoken or the actual model's tokenizer.

    Args:
        text: Input text

    Returns:
        Estimated token count
    """
    if not text:
        return 0

    # Simple approximation: split on whitespace
    # Real tokens are usually ~1.3x words for English
    words = len(text.split())
    return int(words * 1.3)

