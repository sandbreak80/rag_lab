"""
Guardrail Client with Graceful Fallback

Calls security guardrails service and handles failures gracefully:
- Returns Schema F (GuardrailReport) even on 4xx/5xx errors
- Adds service_errors to report
- Sets security_status to 'degraded' in footer
- Continues processing (doesn't block request)
"""

import logging
import requests
from typing import Dict, Any
from datetime import datetime, timezone

from services.common.artifact_base import OrchestrationContext
from services.api.app import GuardrailReport, GuardrailDetection

logger = logging.getLogger(__name__)


def check_guardrails(
    content: str,
    ctx: OrchestrationContext,
    timeout: float = 2.0
) -> GuardrailReport:
    """
    Call security guardrails service with graceful fallback.

    On success: Return GuardrailReport with detections
    On failure (4xx/5xx/timeout): Return GuardrailReport with service_errors

    Args:
        content: Content to check (query + answer)
        ctx: Orchestration context (for trace_id/request_id)
        timeout: Request timeout in seconds

    Returns:
        GuardrailReport (Schema F) with either detections or service_errors
    """
    detections = []
    service_errors = []
    overall_safe = True  # Optimistic default

    try:
        # Call guardrails service
        response = requests.post(
            "http://security-guardrails:5000/check",
            json={
                "content": content,
                "tenant": ctx.tenant,
                "trace_id": ctx.trace_id
            },
            timeout=timeout,
            headers={"X-Request-ID": ctx.request_id}
        )

        if response.status_code == 200:
            # Success - parse detections
            data = response.json()

            for finding in data.get('findings', []):
                detections.append(GuardrailDetection(
                    type=finding.get('type', 'unknown'),
                    severity=finding.get('severity', 'medium'),
                    details=finding.get('details', ''),
                    action_taken=finding.get('action', 'flagged')
                ))

            overall_safe = data.get('safe', True)
            logger.info(f"Guardrails check: safe={overall_safe}, detections={len(detections)}")

        else:
            # 4xx/5xx error - log and continue
            service_errors.append({
                "service": "security-guardrails",
                "error": f"HTTP {response.status_code}: {response.text[:200]}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            overall_safe = False  # Assume unsafe in degraded mode (conservative)
            logger.warning(
                f"Guardrail service error: {response.status_code}, "
                f"continuing with degraded security"
            )

    except requests.exceptions.Timeout:
        # Timeout - log and continue
        service_errors.append({
            "service": "security-guardrails",
            "error": f"Timeout after {timeout}s",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        overall_safe = False
        logger.error(f"Guardrail service timeout ({timeout}s), continuing with degraded security")

    except requests.exceptions.ConnectionError as e:
        # Connection error - log and continue
        service_errors.append({
            "service": "security-guardrails",
            "error": f"ConnectionError: {str(e)[:200]}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        overall_safe = False
        logger.error(f"Guardrail service connection error: {e}, continuing with degraded security")

    except Exception as e:
        # Unexpected error - log and continue
        service_errors.append({
            "service": "security-guardrails",
            "error": f"Unexpected error: {str(e)[:200]}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        overall_safe = False
        logger.error(f"Guardrail service unexpected error: {e}, continuing with degraded security", exc_info=True)

    # Build GuardrailReport (Schema F) with ID correlation
    return GuardrailReport(
        trace_id=ctx.trace_id,
        request_id=ctx.request_id,
        detections=detections,
        service_errors=service_errors,
        overall_safe=overall_safe
    )


def get_security_status(guardrail_report: GuardrailReport) -> str:
    """
    Determine security status for response footer.

    Args:
        guardrail_report: GuardrailReport (Schema F)

    Returns:
        "healthy" or "degraded"
    """
    if guardrail_report.service_errors:
        return "degraded"
    elif not guardrail_report.overall_safe:
        return "degraded"
    else:
        return "healthy"

