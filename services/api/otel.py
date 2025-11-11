"""
OpenTelemetry helper utilities
"""
from contextlib import contextmanager
from opentelemetry import trace
import logging

logger = logging.getLogger(__name__)

tracer = trace.get_tracer(__name__)


@contextmanager
def span(name: str, attributes: dict | None = None):
    """
    Context manager for creating OTel spans with attributes.

    Usage:
        with span("my_operation", {"key": "value"}) as sp:
            # do work
            sp.set_attribute("result", "success")

    Args:
        name: Span name
        attributes: Optional dict of attributes to set on span

    Yields:
        Span object
    """
    with tracer.start_as_current_span(name) as sp:
        if attributes:
            for k, v in attributes.items():
                try:
                    sp.set_attribute(k, v)
                except Exception as e:
                    logger.warning(f"Failed to set span attribute {k}: {e}")
        yield sp

