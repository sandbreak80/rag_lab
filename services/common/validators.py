"""
Provenance Validator - Ensures Evidence Integrity

This validator checks that Evidence objects maintain correct provenance
throughout the RAG pipeline. It catches common errors like:
- Missing origin_tool
- Web sources without URLs
- RAG sources without doc_ids
- Invalid origin_tool values

Used at key pipeline points to ensure data quality.
"""

from typing import List, Dict, Any
from services.common.evidence import Evidence, OriginTool


class ProvenanceViolation:
    """Represents a provenance validation error"""
    
    def __init__(self, evidence_id: str, error_code: str, message: str, severity: str = "error"):
        self.evidence_id = evidence_id
        self.error_code = error_code
        self.message = message
        self.severity = severity  # "error", "warning", "info"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'evidence_id': self.evidence_id,
            'error_code': self.error_code,
            'message': self.message,
            'severity': self.severity,
        }
    
    def __repr__(self) -> str:
        return f"ProvenanceViolation({self.error_code}: {self.message} [{self.evidence_id}])"


class ProvenanceValidator:
    """
    Validates provenance integrity across the RAG pipeline.
    
    Usage:
        validator = ProvenanceValidator()
        if not validator.validate(evidence_list):
            print(validator.get_report())
    """
    
    def __init__(self, strict_mode: bool = True):
        """
        Initialize validator.
        
        Args:
            strict_mode: If True, treat warnings as errors
        """
        self.strict_mode = strict_mode
        self.violations: List[ProvenanceViolation] = []
    
    def validate(self, evidence_list: List[Evidence]) -> bool:
        """
        Validate a list of Evidence objects.
        
        Args:
            evidence_list: List of Evidence objects to validate
            
        Returns:
            True if all evidence is valid, False if violations found
        """
        self.violations = []
        
        for evidence in evidence_list:
            self._validate_single_evidence(evidence)
        
        if self.strict_mode:
            # In strict mode, any violation (including warnings) fails validation
            return len(self.violations) == 0
        else:
            # In non-strict mode, only errors fail validation
            errors = [v for v in self.violations if v.severity == "error"]
            return len(errors) == 0
    
    def _validate_single_evidence(self, evidence: Evidence):
        """Validate a single Evidence object"""
        
        # Check 1: origin_tool must be set
        if not evidence.origin_tool:
            self.violations.append(ProvenanceViolation(
                evidence_id=evidence.id,
                error_code="MISSING_ORIGIN_TOOL",
                message="Evidence missing origin_tool field",
                severity="error"
            ))
            return  # Can't validate further without origin_tool
        
        # Check 2: origin_tool must be valid enum value
        if not isinstance(evidence.origin_tool, OriginTool):
            self.violations.append(ProvenanceViolation(
                evidence_id=evidence.id,
                error_code="INVALID_ORIGIN_TOOL",
                message=f"Invalid origin_tool value: {evidence.origin_tool}",
                severity="error"
            ))
        
        # Check 3: Web sources must have URL
        if evidence.origin_tool == OriginTool.WEB_SEARCH:
            if not evidence.url:
                self.violations.append(ProvenanceViolation(
                    evidence_id=evidence.id,
                    error_code="WEB_SOURCE_NO_URL",
                    message="Web search evidence missing URL",
                    severity="error"
                ))
            
            if not evidence.domain:
                self.violations.append(ProvenanceViolation(
                    evidence_id=evidence.id,
                    error_code="WEB_SOURCE_NO_DOMAIN",
                    message="Web search evidence missing domain",
                    severity="warning"
                ))
            
            # Warn if web source has no title
            if not evidence.title:
                self.violations.append(ProvenanceViolation(
                    evidence_id=evidence.id,
                    error_code="WEB_SOURCE_NO_TITLE",
                    message="Web search evidence missing title",
                    severity="warning"
                ))
        
        # Check 4: RAG sources should have doc_id
        if evidence.origin_tool == OriginTool.RAG:
            if not evidence.doc_id:
                self.violations.append(ProvenanceViolation(
                    evidence_id=evidence.id,
                    error_code="RAG_SOURCE_NO_DOC_ID",
                    message="RAG evidence missing doc_id",
                    severity="warning"
                ))
            
            # RAG sources shouldn't have URLs
            if evidence.url:
                self.violations.append(ProvenanceViolation(
                    evidence_id=evidence.id,
                    error_code="RAG_SOURCE_HAS_URL",
                    message="RAG evidence should not have URL",
                    severity="warning"
                ))
        
        # Check 5: Research agent sources should have metadata
        if evidence.origin_tool == OriginTool.RESEARCH_AGENT:
            if not evidence.url and not evidence.doc_id:
                self.violations.append(ProvenanceViolation(
                    evidence_id=evidence.id,
                    error_code="RESEARCH_SOURCE_NO_IDENTIFIER",
                    message="Research agent evidence missing both URL and doc_id",
                    severity="warning"
                ))
        
        # Check 6: Content should not be empty
        if not evidence.content or len(evidence.content.strip()) == 0:
            self.violations.append(ProvenanceViolation(
                evidence_id=evidence.id,
                error_code="EMPTY_CONTENT",
                message="Evidence has empty content",
                severity="error"
            ))
        
        # Check 7: Score should be in valid range
        if evidence.score < 0.0 or evidence.score > 1.0:
            self.violations.append(ProvenanceViolation(
                evidence_id=evidence.id,
                error_code="INVALID_SCORE",
                message=f"Score {evidence.score} outside valid range [0.0, 1.0]",
                severity="warning"
            ))
    
    def get_violations(self, severity: str = None) -> List[ProvenanceViolation]:
        """
        Get violations, optionally filtered by severity.
        
        Args:
            severity: Filter by severity ("error", "warning", "info") or None for all
            
        Returns:
            List of violations
        """
        if severity:
            return [v for v in self.violations if v.severity == severity]
        return self.violations
    
    def get_report(self) -> Dict[str, Any]:
        """
        Get a comprehensive validation report.
        
        Returns:
            Dictionary with validation results
        """
        errors = self.get_violations("error")
        warnings = self.get_violations("warning")
        
        return {
            'valid': len(self.violations) == 0,
            'total_violations': len(self.violations),
            'errors': len(errors),
            'warnings': len(warnings),
            'violations': [v.to_dict() for v in self.violations],
            'error_details': [v.to_dict() for v in errors],
            'warning_details': [v.to_dict() for v in warnings],
        }
    
    def get_summary(self) -> str:
        """Get a human-readable summary of validation results"""
        if len(self.violations) == 0:
            return "✅ All evidence passed provenance validation"
        
        errors = self.get_violations("error")
        warnings = self.get_violations("warning")
        
        summary = f"❌ Provenance validation failed:\n"
        if errors:
            summary += f"  - {len(errors)} error(s)\n"
        if warnings:
            summary += f"  - {len(warnings)} warning(s)\n"
        
        # Show first few violations
        for violation in self.violations[:5]:
            summary += f"  • {violation.error_code}: {violation.message}\n"
        
        if len(self.violations) > 5:
            summary += f"  ... and {len(self.violations) - 5} more\n"
        
        return summary


def validate_evidence_list(evidence_list: List[Evidence], strict: bool = True) -> Dict[str, Any]:
    """
    Convenience function to validate a list of Evidence objects.
    
    Args:
        evidence_list: List of Evidence to validate
        strict: Whether to treat warnings as errors
        
    Returns:
        Validation report dictionary
    """
    validator = ProvenanceValidator(strict_mode=strict)
    validator.validate(evidence_list)
    return validator.get_report()


# Example usage
if __name__ == "__main__":
    from services.common.evidence import Evidence, OriginTool
    
    # Create test evidence
    good_web = Evidence(
        id="web-1",
        content="Good web evidence",
        origin_tool=OriginTool.WEB_SEARCH,
        url="https://example.com",
        domain="example.com",
        title="Example",
    )
    
    bad_web = Evidence(
        id="web-2",
        content="Bad web evidence - no URL",
        origin_tool=OriginTool.WEB_SEARCH,
        # Missing URL!
    )
    
    good_rag = Evidence(
        id="rag-1",
        content="Good RAG evidence",
        origin_tool=OriginTool.RAG,
        doc_id="doc_123",
    )
    
    # Validate
    validator = ProvenanceValidator(strict_mode=False)
    
    print("Testing good evidence:")
    if validator.validate([good_web, good_rag]):
        print("✅ Validation passed")
    else:
        print(validator.get_summary())
    
    print("\nTesting with bad evidence:")
    validator = ProvenanceValidator(strict_mode=False)
    if validator.validate([good_web, bad_web, good_rag]):
        print("✅ Validation passed")
    else:
        print(validator.get_summary())
        print("\nFull report:")
        import json
        print(json.dumps(validator.get_report(), indent=2))

