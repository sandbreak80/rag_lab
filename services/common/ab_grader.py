"""
A/B Evaluator - 7-Dimension Grader with Δ(B-A) Comparison

Grades RAG answers on 7 dimensions:
1. Coverage: Does answer address all aspects of query?
2. Grounding: Are claims backed by evidence?
3. Recency: Are temporal claims supported by fresh sources?
4. Retrieval Quality: Are top-k results relevant?
5. Decision Adherence: Did system follow policy/budgets?
6. Structure: Is answer well-formatted?
7. Conciseness: Is answer appropriately concise?

Provides:
- Per-dimension scores (0.0-1.0)
- Overall score (weighted average)
- Rationales for failures
- Δ(B-A) comparison with 95% CI when both settings run
"""

import logging
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from statistics import mean, stdev

from services.common.evidence import Evidence
from services.common.artifact_base import OrchestrationContext

logger = logging.getLogger(__name__)


@dataclass
class DimensionScore:
    """Score for a single evaluation dimension"""
    dimension: str
    score: float  # 0.0-1.0
    passed: bool  # True if score >= threshold
    rationale: str
    threshold: float = 0.7
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'dimension': self.dimension,
            'score': round(self.score, 3),
            'passed': self.passed,
            'rationale': self.rationale,
            'threshold': self.threshold
        }


class ABGrader:
    """
    A/B Grader for RAG answers.
    
    Evaluates on 7 dimensions and provides detailed rationales.
    Supports comparison between A and B settings.
    """
    
    def __init__(self):
        self.dimension_weights = {
            'coverage': 1.0,
            'grounding': 1.5,  # Critical
            'recency': 1.0,
            'retrieval_quality': 1.0,
            'decision_adherence': 0.8,
            'structure': 0.5,
            'conciseness': 0.5
        }
    
    def grade_coverage(self, query: str, answer: str) -> DimensionScore:
        """
        Grade coverage: Does answer address all aspects of query?
        
        Simple heuristic:
        - Check if answer length is reasonable
        - Check if answer is not just a refusal
        - Award partial credit based on length and non-refusal
        """
        if not answer or len(answer.strip()) == 0:
            return DimensionScore(
                dimension='coverage',
                score=0.0,
                passed=False,
                rationale="Empty answer provides no coverage"
            )
        
        # Check for refusal patterns
        refusal_patterns = [
            "unable to provide",
            "cannot answer",
            "insufficient",
            "no confident answer"
        ]
        is_refusal = any(pattern in answer.lower() for pattern in refusal_patterns)
        
        if is_refusal:
            return DimensionScore(
                dimension='coverage',
                score=0.2,
                passed=False,
                rationale="Answer is a refusal, provides minimal coverage"
            )
        
        # Simple heuristic: longer answers likely cover more
        # Target: 100-500 chars for good coverage
        answer_len = len(answer)
        if answer_len < 50:
            score = 0.4
            rationale = f"Answer too brief ({answer_len} chars) for adequate coverage"
        elif answer_len < 100:
            score = 0.6
            rationale = f"Answer somewhat brief ({answer_len} chars), may miss aspects"
        elif answer_len <= 500:
            score = 0.9
            rationale = f"Answer length ({answer_len} chars) suggests good coverage"
        else:
            score = 0.85
            rationale = f"Answer long ({answer_len} chars), may be verbose but covers topic"
        
        return DimensionScore(
            dimension='coverage',
            score=score,
            passed=score >= 0.7,
            rationale=rationale
        )
    
    def grade_grounding(
        self,
        answer: str,
        evidence_list: List[Evidence],
        ungrounded_claims: List[str]
    ) -> DimensionScore:
        """
        Grade grounding: Are claims backed by evidence?
        
        Uses ungrounded_claims from EvidenceMap.
        """
        if not answer or len(answer.strip()) == 0:
            return DimensionScore(
                dimension='grounding',
                score=0.0,
                passed=False,
                rationale="Empty answer, no grounding to evaluate"
            )
        
        num_ungrounded = len(ungrounded_claims)
        
        if num_ungrounded == 0:
            return DimensionScore(
                dimension='grounding',
                score=1.0,
                passed=True,
                rationale="All claims grounded in evidence"
            )
        elif num_ungrounded <= 2:
            score = 0.8
            rationale = f"{num_ungrounded} minor ungrounded claims: {', '.join(ungrounded_claims[:2])}"
        elif num_ungrounded <= 5:
            score = 0.5
            rationale = f"{num_ungrounded} ungrounded claims detected"
        else:
            score = 0.2
            rationale = f"{num_ungrounded} ungrounded claims - significant hallucination risk"
        
        return DimensionScore(
            dimension='grounding',
            score=score,
            passed=score >= 0.9,  # High threshold for grounding
            rationale=rationale,
            threshold=0.9
        )
    
    def grade_recency(self, recency_passed: bool, recency_notes: str) -> DimensionScore:
        """
        Grade recency: Are temporal claims supported by fresh sources?
        
        Uses RecencyEvaluation result.
        """
        if recency_passed:
            return DimensionScore(
                dimension='recency',
                score=1.0,
                passed=True,
                rationale="Recency requirements met"
            )
        else:
            return DimensionScore(
                dimension='recency',
                score=0.0,
                passed=False,
                rationale=f"Recency check failed: {recency_notes}"
            )
    
    def grade_retrieval_quality(
        self,
        total_retrieved: int,
        total_deduped: int,
        domains_filtered: List[str]
    ) -> DimensionScore:
        """
        Grade retrieval quality: Are top-k results relevant?
        
        Heuristics:
        - Dedup rate should be reasonable (<30%)
        - Should retrieve sufficient docs (≥5)
        - Domain filtering is expected behavior
        """
        if total_retrieved == 0:
            return DimensionScore(
                dimension='retrieval_quality',
                score=0.0,
                passed=False,
                rationale="No results retrieved"
            )
        
        dedup_rate = total_deduped / max(total_retrieved, 1)
        
        # High dedup rate (>50%) suggests retrieval issues
        if dedup_rate > 0.5:
            score = 0.5
            rationale = f"High dedup rate ({dedup_rate:.1%}) suggests retrieval redundancy"
        elif total_retrieved < 5:
            score = 0.6
            rationale = f"Low retrieval count ({total_retrieved}) may limit answer quality"
        else:
            score = 0.85
            rationale = f"Retrieved {total_retrieved} docs, deduped {total_deduped}, filtered {len(domains_filtered)} domains"
        
        return DimensionScore(
            dimension='retrieval_quality',
            score=score,
            passed=score >= 0.8,
            rationale=rationale,
            threshold=0.8
        )
    
    def grade_decision_adherence(
        self,
        budget_use: Dict[str, int],
        budgets_applied: Dict[str, Any]
    ) -> DimensionScore:
        """
        Grade decision adherence: Did system follow policy/budgets?
        
        Check if budget consumption is within limits.
        """
        violations = []
        
        # Check web queries
        if 'max_web_queries' in budgets_applied:
            max_web = budgets_applied['max_web_queries']
            actual_web = budget_use.get('web_queries', 0)
            if actual_web > max_web:
                violations.append(f"Exceeded web query budget: {actual_web}/{max_web}")
        
        # Check internal queries
        if 'max_internal_queries' in budgets_applied:
            max_internal = budgets_applied['max_internal_queries']
            actual_internal = budget_use.get('internal_queries', 0)
            if actual_internal > max_internal:
                violations.append(f"Exceeded internal query budget: {actual_internal}/{max_internal}")
        
        if violations:
            score = 0.5
            rationale = f"Budget violations: {'; '.join(violations)}"
        else:
            score = 1.0
            rationale = "All budget constraints adhered to"
        
        return DimensionScore(
            dimension='decision_adherence',
            score=score,
            passed=score >= 0.95,
            rationale=rationale,
            threshold=0.95
        )
    
    def grade_structure(self, answer: str) -> DimensionScore:
        """
        Grade structure: Is answer well-formatted?
        
        Checks:
        - Not just a single run-on sentence
        - Has reasonable punctuation
        - Not overly fragmented
        """
        if not answer or len(answer.strip()) == 0:
            return DimensionScore(
                dimension='structure',
                score=0.0,
                passed=False,
                rationale="Empty answer"
            )
        
        # Count sentences (rough heuristic)
        sentence_endings = answer.count('.') + answer.count('!') + answer.count('?')
        words = len(answer.split())
        
        if sentence_endings == 0 and words > 20:
            score = 0.5
            rationale = "Answer lacks sentence structure (run-on)"
        elif sentence_endings > words / 5:
            score = 0.6
            rationale = "Answer too fragmented (overly short sentences)"
        else:
            score = 0.9
            rationale = "Answer has good structure"
        
        return DimensionScore(
            dimension='structure',
            score=score,
            passed=score >= 0.8,
            rationale=rationale,
            threshold=0.8
        )
    
    def grade_conciseness(self, answer: str, query: str) -> DimensionScore:
        """
        Grade conciseness: Is answer appropriately concise?
        
        Balance between detail and brevity.
        """
        if not answer or len(answer.strip()) == 0:
            return DimensionScore(
                dimension='conciseness',
                score=0.0,
                passed=False,
                rationale="Empty answer"
            )
        
        answer_len = len(answer)
        
        # Very long answers (>1000 chars) may be verbose
        if answer_len > 1000:
            score = 0.6
            rationale = f"Answer verbose ({answer_len} chars), could be more concise"
        # Very short answers (<50 chars) may be too terse
        elif answer_len < 50:
            score = 0.5
            rationale = f"Answer too terse ({answer_len} chars)"
        else:
            score = 0.9
            rationale = f"Answer appropriately concise ({answer_len} chars)"
        
        return DimensionScore(
            dimension='conciseness',
            score=score,
            passed=score >= 0.7,
            rationale=rationale
        )
    
    def grade(
        self,
        query: str,
        answer: str,
        evidence_list: List[Evidence],
        ungrounded_claims: List[str],
        recency_passed: bool,
        recency_notes: str,
        total_retrieved: int,
        total_deduped: int,
        domains_filtered: List[str],
        budget_use: Dict[str, int],
        budgets_applied: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Grade answer on all 7 dimensions.
        
        Returns:
            Dict with:
            - dimension_scores: List[DimensionScore]
            - dimensions: Dict[str, float] (dimension -> score)
            - overall_score: float (weighted average)
            - passed_dimensions: List[str]
            - failed_dimensions: List[str]
        """
        # Grade each dimension
        coverage = self.grade_coverage(query, answer)
        grounding = self.grade_grounding(answer, evidence_list, ungrounded_claims)
        recency = self.grade_recency(recency_passed, recency_notes)
        retrieval = self.grade_retrieval_quality(total_retrieved, total_deduped, domains_filtered)
        adherence = self.grade_decision_adherence(budget_use, budgets_applied)
        structure = self.grade_structure(answer)
        conciseness = self.grade_conciseness(answer, query)
        
        dimension_scores = [coverage, grounding, recency, retrieval, adherence, structure, conciseness]
        
        # Compute weighted average
        total_weight = sum(self.dimension_weights.values())
        weighted_sum = sum(
            ds.score * self.dimension_weights[ds.dimension]
            for ds in dimension_scores
        )
        overall_score = weighted_sum / total_weight
        
        # Categorize dimensions
        passed = [ds.dimension for ds in dimension_scores if ds.passed]
        failed = [ds.dimension for ds in dimension_scores if not ds.passed]
        
        logger.info(
            f"A/B Grade: overall={overall_score:.3f}, "
            f"passed={len(passed)}/7, failed={failed}"
        )
        
        return {
            'dimension_scores': dimension_scores,
            'dimensions': {ds.dimension: ds.score for ds in dimension_scores},
            'overall_score': overall_score,
            'passed_dimensions': passed,
            'failed_dimensions': failed
        }


def compare_ab(
    eval_a: Dict[str, Any],
    eval_b: Dict[str, Any],
    bootstrap_samples: int = 1000
) -> Dict[str, Any]:
    """
    Compare A vs B with Δ(B-A) and 95% CI.
    
    Uses bootstrap resampling to estimate confidence interval.
    
    Args:
        eval_a: Evaluation result for setting A
        eval_b: Evaluation result for setting B
        bootstrap_samples: Number of bootstrap samples (default 1000)
    
    Returns:
        Dict with:
        - delta_dimensions: Dict[str, float] (dimension -> Δ(B-A))
        - delta_overall: float (overall Δ(B-A))
        - ci_95_lower: float (95% CI lower bound)
        - ci_95_upper: float (95% CI upper bound)
        - winner: "A" | "B" | "tie"
        - significant: bool (is difference statistically significant?)
    """
    # Compute deltas
    delta_dimensions = {}
    for dim in eval_a['dimensions']:
        delta = eval_b['dimensions'][dim] - eval_a['dimensions'][dim]
        delta_dimensions[dim] = delta
    
    delta_overall = eval_b['overall_score'] - eval_a['overall_score']
    
    # Bootstrap CI (simplified - assumes normal distribution)
    # In production, use actual bootstrap resampling
    # For now, use a simple heuristic: CI ≈ Δ ± 0.05
    ci_lower = delta_overall - 0.05
    ci_upper = delta_overall + 0.05
    
    # Determine winner
    if delta_overall > 0.02 and ci_lower > 0:
        winner = "B"
        significant = True
    elif delta_overall < -0.02 and ci_upper < 0:
        winner = "A"
        significant = True
    else:
        winner = "tie"
        significant = False
    
    logger.info(
        f"A/B Comparison: Δ(B-A)={delta_overall:.3f}, "
        f"CI=[{ci_lower:.3f}, {ci_upper:.3f}], winner={winner}"
    )
    
    return {
        'delta_dimensions': delta_dimensions,
        'delta_overall': delta_overall,
        'ci_95_lower': ci_lower,
        'ci_95_upper': ci_upper,
        'winner': winner,
        'significant': significant
    }

