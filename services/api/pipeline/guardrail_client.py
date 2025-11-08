"""
Guardrail client for safety checks - simplified mock version
"""
from typing import Any
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


def check_guardrails(content: str, context: Any) -> dict[str, Any]:
    """
    Mock guardrail check.

    In production, this would call a real security service.
    For now, returns a minimal report.
    """
    # Mock: check for obviously unsafe content
    detections = []

    if "confidential" in content.lower():
        detections.append({
            "severity": "medium",
            "details": "Potential confidential information detected",
            "action_taken": "flagged"
        })

    overall_safe = len(detections) == 0

    return {
        "detections": detections,
        "service_errors": [],
        "overall_safe": overall_safe
    }


def get_security_status(report: dict) -> str:
    """Determine security status from guardrail report"""
    if report.get("service_errors"):
        return "degraded"
    if any(d.get("action_taken") == "blocked" for d in report.get("detections", [])):
        return "blocked"
    if any(d.get("action_taken") == "flagged" for d in report.get("detections", [])):
        return "degraded"
    return "ok"

