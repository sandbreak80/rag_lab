"""
A/B Grader for RAG answer quality evaluation
"""
from dataclasses import dataclass
from typing import Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class GradeResult:
    """Result from grading a RAG answer"""
    dimensions: dict[str, float]
    overall_score: float
    passed_dimensions: list[str]
    failed_dimensions: list[str]


class ABGrader:
    """
    7-dimension A/B grader for RAG answers.
    
    Dimensions:
    1. Coverage - How well the answer addresses the query
    2. Grounding - Citations and evidence support
    3. Recency - Freshness of sources
    4. Retrieval Quality - Deduplication, filtering effectiveness
    5. Decision Adherence - Budget compliance
    6. Structure - Answer organization
    7. Conciseness - Appropriate length
    """
    
    def __init__(self):
        self.dimensions = {
            "coverage": {"weight": 0.15, "threshold": 0.7},
            "grounding": {"weight": 0.25, "threshold": 0.9},
            "recency": {"weight": 0.15, "threshold": 0.8},
            "retrieval_quality": {"weight": 0.15, "threshold": 0.75},
            "decision_adherence": {"weight": 0.1, "threshold": 0.9},
            "structure": {"weight": 0.1, "threshold": 0.8},
            "conciseness": {"weight": 0.1, "threshold": 0.7}
        }
    
    def grade(
        self,
        query: str,
        answer: str,
        evidence_list: list,
        ungrounded_claims: list,
        recency_passed: bool,
        recency_notes: str,
        total_retrieved: int,
        total_deduped: int,
        domains_filtered: list,
        budget_use: dict,
        budgets_applied: dict
    ) -> GradeResult:
        """Grade a RAG answer across all dimensions"""
        
        passed_dims = []
        failed_dims = []
        dim_scores = {}
        
        # 1. Coverage (mock - check if answer contains keywords from query)
        coverage_score = 0.8 if any(word.lower() in answer.lower() for word in query.split()) else 0.5
        dim_scores["coverage"] = coverage_score
        if coverage_score >= self.dimensions["coverage"]["threshold"]:
            passed_dims.append("coverage")
        else:
            failed_dims.append("coverage")
        
        # 2. Grounding (mock - check for citation markers)
        import re
        citations = len(re.findall(r'\[\d+\]', answer))
        grounding_score = min(1.0, citations / 3.0) if citations > 0 else 0.0
        dim_scores["grounding"] = grounding_score
        if grounding_score >= self.dimensions["grounding"]["threshold"]:
            passed_dims.append("grounding")
        else:
            failed_dims.append("grounding")
        
        # 3. Recency
        recency_score = 1.0 if recency_passed else 0.0
        dim_scores["recency"] = recency_score
        if recency_score >= self.dimensions["recency"]["threshold"]:
            passed_dims.append("recency")
        else:
            failed_dims.append("recency")
        
        # 4. Retrieval Quality
        retrieval_score = 0.9  # Mock
        dim_scores["retrieval_quality"] = retrieval_score
        if retrieval_score >= self.dimensions["retrieval_quality"]["threshold"]:
            passed_dims.append("retrieval_quality")
        else:
            failed_dims.append("retrieval_quality")
        
        # 5. Decision Adherence
        adherence_score = 1.0  # Mock - assume budgets followed
        dim_scores["decision_adherence"] = adherence_score
        if adherence_score >= self.dimensions["decision_adherence"]["threshold"]:
            passed_dims.append("decision_adherence")
        else:
            failed_dims.append("decision_adherence")
        
        # 6. Structure
        structure_score = 0.85  # Mock
        dim_scores["structure"] = structure_score
        if structure_score >= self.dimensions["structure"]["threshold"]:
            passed_dims.append("structure")
        else:
            failed_dims.append("structure")
        
        # 7. Conciseness
        word_count = len(answer.split())
        conciseness_score = 1.0 if 50 < word_count < 300 else 0.7
        dim_scores["conciseness"] = conciseness_score
        if conciseness_score >= self.dimensions["conciseness"]["threshold"]:
            passed_dims.append("conciseness")
        else:
            failed_dims.append("conciseness")
        
        # Calculate overall weighted score
        overall = sum(
            dim_scores[dim] * self.dimensions[dim]["weight"]
            for dim in dim_scores
        )
        
        return GradeResult(
            dimensions=dim_scores,
            overall_score=round(overall, 3),
            passed_dimensions=passed_dims,
            failed_dimensions=failed_dims
        )

