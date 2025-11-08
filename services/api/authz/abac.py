"""
Attribute-Based Access Control (ABAC) for permission-aware retrieval
"""
from dataclasses import dataclass
from typing import Any
import hashlib


@dataclass
class ACLPredicate:
    """ACL predicate for pre-filtering at index level"""
    user_id: str
    groups: list[str]
    dept: str | None
    tag: str  # Compact representation for spans
    filter_expr: dict[str, Any]  # Vector DB filter expression

    def to_filter(self) -> dict[str, Any]:
        """Convert to vector DB filter format"""
        return self.filter_expr


def build_acl_predicate(user_id: str, groups: list[str], dept: str | None) -> ACLPredicate:
    """
    Build ACL predicate from user attributes.

    Pre-filter logic:
    - User can access docs tagged with their dept
    - User can access docs tagged with any of their groups
    - User can access public docs

    This is a LOCAL computation (no remote call).
    """
    # Build filter expression for vector DB
    # Format: { "access_control": { "$in": [allowed_tags] } }
    allowed_tags = ["public"]  # Always include public

    if dept:
        allowed_tags.append(f"dept:{dept}")

    for group in groups:
        allowed_tags.append(f"group:{group}")

    allowed_tags.append(f"user:{user_id}")  # User-specific docs

    filter_expr = {
        "$or": [
            {"access_control": {"$in": allowed_tags}},
            {"access_control": {"$exists": False}}  # Docs without ACL are public
        ]
    }

    # Generate compact tag for observability (no PII)
    tag_hash = hashlib.md5(f"{dept}:{','.join(sorted(groups))}".encode()).hexdigest()[:8]
    tag = f"dept={dept or 'none'},groups={len(groups)},hash={tag_hash}"

    return ACLPredicate(
        user_id=user_id,
        groups=groups,
        dept=dept,
        tag=tag,
        filter_expr=filter_expr
    )


def check_acl_pass(doc_metadata: dict[str, Any], acl_pred: ACLPredicate) -> bool:
    """
    Check if a document passes ACL predicate (for post-hoc validation).

    Used for testing and audit, not for primary filtering.
    """
    access_control = doc_metadata.get("access_control", [])

    # If no ACL, it's public
    if not access_control:
        return True

    # Check if any of our allowed tags match
    allowed_tags = []
    if acl_pred.dept:
        allowed_tags.append(f"dept:{acl_pred.dept}")
    for group in acl_pred.groups:
        allowed_tags.append(f"group:{group}")
    allowed_tags.append(f"user:{acl_pred.user_id}")
    allowed_tags.append("public")

    return any(tag in access_control for tag in allowed_tags)

