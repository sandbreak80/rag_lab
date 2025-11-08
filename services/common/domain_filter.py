"""
Domain Filtering with Audit Trail

Filters evidence by domain allow/deny rules while maintaining audit trail
for Schema B (RetrievalLog).

Supports:
- Denylist (block specific domains)
- Allowlist (only allow specific domains)
- Pattern matching (e.g., *.internal.example.com)
"""

import logging
import re
from typing import List, Tuple, Dict, Any, Set, Optional
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse

from services.common.evidence import Evidence, extract_domain

logger = logging.getLogger(__name__)


class DomainFilterAction(str, Enum):
    """Action taken during domain filtering"""
    ALLOWED = "allowed"
    DROPPED = "dropped"


@dataclass
class DomainFilterAuditEntry:
    """Audit entry for a single domain filtering decision"""
    action: DomainFilterAction
    doc_id: str
    domain: str
    reason: str
    url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'action': self.action.value,
            'doc_id': self.doc_id,
            'domain': self.domain,
            'reason': self.reason,
            'url': self.url
        }


class DomainFilter:
    """
    Domain filtering with configurable allow/deny rules.

    Example:
        filter = DomainFilter(
            denylist=["asana.com", "jira.internal.example.com"],
            allowlist=None  # Allow all except denylist
        )

        filtered, audit = filter.filter_evidence(evidence_list)
    """

    def __init__(
        self,
        denylist: Optional[List[str]] = None,
        allowlist: Optional[List[str]] = None,
        deny_unknown_domain: bool = False
    ):
        """
        Initialize domain filter.

        Args:
            denylist: List of domains to block (e.g., ["asana.com", "jira.internal.example.com"])
            allowlist: List of domains to allow (if set, all others are blocked)
            deny_unknown_domain: Block evidence with unknown/missing domains
        """
        self.denylist: Set[str] = set(denylist or [])
        self.allowlist: Set[str] = set(allowlist or [])
        self.deny_unknown_domain = deny_unknown_domain

        logger.info(f"DomainFilter initialized: denylist={len(self.denylist)}, allowlist={len(self.allowlist)}, deny_unknown={deny_unknown_domain}")

    def _domain_matches(self, domain: str, pattern: str) -> bool:
        """
        Check if domain matches pattern.

        Supports:
        - Exact match: "example.com" matches "example.com"
        - Wildcard subdomain: "*.example.com" matches "sub.example.com", "deep.sub.example.com"

        Args:
            domain: Domain to check (e.g., "sub.example.com")
            pattern: Pattern to match (e.g., "*.example.com")

        Returns:
            True if match
        """
        # Exact match
        if domain == pattern:
            return True

        # Wildcard subdomain match
        if pattern.startswith("*."):
            # *.example.com should match sub.example.com but not example.com
            base_domain = pattern[2:]  # Remove "*."
            return domain.endswith(f".{base_domain}")

        return False

    def _is_allowed(self, domain: str) -> Tuple[bool, str]:
        """
        Check if domain is allowed.

        Returns:
            Tuple of (is_allowed, reason)
        """
        # Unknown domain handling
        if not domain or domain == "unknown":
            if self.deny_unknown_domain:
                return False, "unknown_domain_blocked_by_policy"
            else:
                return True, "unknown_domain_allowed_by_policy"

        # Allowlist takes precedence (if set)
        if self.allowlist:
            for pattern in self.allowlist:
                if self._domain_matches(domain, pattern):
                    return True, f"allowlist: {pattern}"
            return False, f"not_on_allowlist"

        # Denylist check
        for pattern in self.denylist:
            if self._domain_matches(domain, pattern):
                return False, f"denylist: {pattern}"

        return True, "not_on_denylist"

    def filter_evidence(
        self,
        evidence_list: List[Evidence]
    ) -> Tuple[List[Evidence], List[DomainFilterAuditEntry]]:
        """
        Filter evidence by domain rules.

        CRITICAL: This function NEVER modifies Evidence objects.
        It only selects which Evidence objects to keep/drop.

        Args:
            evidence_list: List of Evidence objects

        Returns:
            Tuple of (filtered_list, audit_trail)
        """
        kept: List[Evidence] = []
        audit_trail: List[DomainFilterAuditEntry] = []

        for evidence in evidence_list:
            # Extract domain from URL or metadata
            domain = evidence.metadata.get('domain')
            url = evidence.url

            if not domain and url:
                domain = extract_domain(url)

            if not domain:
                domain = "unknown"

            # Check if allowed
            is_allowed, reason = self._is_allowed(domain)

            if is_allowed:
                kept.append(evidence)
                audit_trail.append(DomainFilterAuditEntry(
                    action=DomainFilterAction.ALLOWED,
                    doc_id=evidence.id,
                    domain=domain,
                    reason=reason,
                    url=url
                ))
            else:
                audit_trail.append(DomainFilterAuditEntry(
                    action=DomainFilterAction.DROPPED,
                    doc_id=evidence.id,
                    domain=domain,
                    reason=reason,
                    url=url
                ))

                logger.debug(f"Domain filter: Dropped {evidence.id} from {domain} ({reason})")

        dropped_count = len(evidence_list) - len(kept)
        if dropped_count > 0:
            logger.info(f"Domain filtering: {len(evidence_list)} input → {len(kept)} kept, {dropped_count} dropped")

        return kept, audit_trail

    def get_filtered_domains(self, audit_trail: List[DomainFilterAuditEntry]) -> List[str]:
        """
        Extract list of unique domains that were filtered out.

        Args:
            audit_trail: Audit trail from filter_evidence()

        Returns:
            List of unique domains that were dropped
        """
        dropped_domains = set()
        for entry in audit_trail:
            if entry.action == DomainFilterAction.DROPPED:
                dropped_domains.add(entry.domain)
        return sorted(list(dropped_domains))


# Default filter (commonly blocked domains)
DEFAULT_DENYLIST = [
    # Internal tracking/project management (often noisy, low quality for RAG)
    "asana.com",
    "*.asana.com",
    "jira.atlassian.com",
    "*.jira.com",

    # Social media (often off-topic, low quality)
    # Uncomment if needed:
    # "facebook.com",
    # "twitter.com",
    # "instagram.com",
]


def create_default_filter() -> DomainFilter:
    """
    Create a DomainFilter with sensible defaults.

    Returns:
        DomainFilter with default denylist
    """
    return DomainFilter(
        denylist=DEFAULT_DENYLIST,
        allowlist=None,
        deny_unknown_domain=False
    )

