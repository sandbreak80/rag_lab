"""
Deduplication with Audit Trail

Deduplicates evidence by content hash while maintaining audit trail
for Schema B (RetrievalLog).

Preserves highest-scored duplicate and logs all decisions.
"""

import hashlib
import logging
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass
from enum import Enum

from services.common.evidence import Evidence

logger = logging.getLogger(__name__)


class DedupAction(str, Enum):
    """Action taken during deduplication"""
    KEPT = "kept"
    DROPPED = "dropped"


@dataclass
class DedupAuditEntry:
    """Audit entry for a single deduplication decision"""
    action: DedupAction
    doc_id: str
    reason: str
    duplicate_of: str = None
    original_score: float = 0.0
    kept_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'action': self.action.value,
            'doc_id': self.doc_id,
            'reason': self.reason,
            'duplicate_of': self.duplicate_of,
            'original_score': round(self.original_score, 3) if self.original_score else None,
            'kept_score': round(self.kept_score, 3) if self.kept_score else None
        }


def compute_content_hash(content: str, length: int = 16) -> str:
    """
    Compute SHA-256 hash of content.

    Args:
        content: Text content to hash
        length: Hash length (default 16 chars)

    Returns:
        Hex hash string
    """
    return hashlib.sha256(content.encode('utf-8')).hexdigest()[:length]


def deduplicate_evidence(
    evidence_list: List[Evidence],
    preserve_highest_score: bool = True
) -> Tuple[List[Evidence], List[DedupAuditEntry]]:
    """
    Deduplicate evidence by content hash, preserving highest score.

    CRITICAL: This function NEVER modifies origin_tool or other Evidence fields.
    It only selects which Evidence objects to keep/drop.

    Args:
        evidence_list: List of Evidence objects
        preserve_highest_score: Keep highest-scored duplicate (default True)

    Returns:
        Tuple of (deduplicated_list, audit_trail)

    Example:
        evidence = [
            Evidence(id="1", content="foo", score=0.9, origin_tool="rag"),
            Evidence(id="2", content="foo", score=0.95, origin_tool="web_search"),  # duplicate, higher score
            Evidence(id="3", content="bar", score=0.8, origin_tool="rag")
        ]

        deduplicated, audit = deduplicate_evidence(evidence)
        # deduplicated = [Evidence(id="2", ...), Evidence(id="3", ...)]
        # audit = [
        #   DedupAuditEntry(action="dropped", doc_id="1", duplicate_of="2"),
        #   DedupAuditEntry(action="kept", doc_id="2"),
        #   DedupAuditEntry(action="kept", doc_id="3")
        # ]
    """
    seen_hashes: Dict[str, Evidence] = {}
    kept: List[Evidence] = []
    audit_trail: List[DedupAuditEntry] = []

    for evidence in evidence_list:
        content_hash = compute_content_hash(evidence.content)
        score = evidence.metadata.get('score', 0.0)

        if content_hash in seen_hashes:
            # Duplicate found
            original = seen_hashes[content_hash]
            original_score = original.metadata.get('score', 0.0)

            if preserve_highest_score and score > original_score:
                # Replace original with this higher-scored duplicate
                kept.remove(original)
                kept.append(evidence)
                seen_hashes[content_hash] = evidence

                # Audit: dropped original, kept new
                audit_trail.append(DedupAuditEntry(
                    action=DedupAction.DROPPED,
                    doc_id=original.id,
                    reason=f"duplicate_content_hash={content_hash}, lower_score",
                    duplicate_of=evidence.id,
                    original_score=original_score,
                    kept_score=score
                ))
                audit_trail.append(DedupAuditEntry(
                    action=DedupAction.KEPT,
                    doc_id=evidence.id,
                    reason=f"unique_or_highest_score (replaced {original.id})",
                    original_score=score
                ))

                logger.debug(f"Dedup: Replaced {original.id} (score={original_score:.3f}) with {evidence.id} (score={score:.3f})")
            else:
                # Keep original, drop this duplicate
                audit_trail.append(DedupAuditEntry(
                    action=DedupAction.DROPPED,
                    doc_id=evidence.id,
                    reason=f"duplicate_content_hash={content_hash}",
                    duplicate_of=original.id,
                    original_score=score,
                    kept_score=original_score
                ))

                logger.debug(f"Dedup: Dropped {evidence.id} (score={score:.3f}), kept {original.id} (score={original_score:.3f})")
        else:
            # Unique content
            seen_hashes[content_hash] = evidence
            kept.append(evidence)
            audit_trail.append(DedupAuditEntry(
                action=DedupAction.KEPT,
                doc_id=evidence.id,
                reason="unique_content",
                original_score=score
            ))

    logger.info(f"Deduplication: {len(evidence_list)} input → {len(kept)} kept, {len(evidence_list) - len(kept)} dropped")

    return kept, audit_trail


def merge_dedup_audits(audits: List[List[DedupAuditEntry]]) -> List[DedupAuditEntry]:
    """
    Merge multiple deduplication audit trails.

    Useful when deduplicating results from multiple retrievers.

    Args:
        audits: List of audit trails to merge

    Returns:
        Merged audit trail
    """
    merged = []
    for audit_list in audits:
        merged.extend(audit_list)
    return merged

