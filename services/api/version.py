"""
Version information for RAG API v1
"""

__version__ = "2.2.0-ab-testing"
__service__ = "rag-api-v1"
__build_date__ = "2025-11-17"

def get_version_info():
    """Return version information as a dictionary"""
    return {
        "service": __service__,
        "version": __version__,
        "build_date": __build_date__,
        "status": "healthy"
    }

