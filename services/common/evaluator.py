"""
Minimal Evaluation Harness for RAG Quality Measurement

Supports:
- Offline evaluation (test sets)
- Online evaluation (live traffic sampling)
- Metrics: relevance, faithfulness, answer quality
- A/B testing support
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import json


class EvaluationMetric(str, Enum):
    """Evaluation metrics"""
    RELEVANCE = "relevance"  # Is retrieved context relevant?
    FAITHFULNESS = "faithfulness"  # Is answer grounded in context?
    ANSWER_QUALITY = "answer_quality"  # Is answer helpful/correct?
    CONTEXT_PRECISION = "context_precision"  # Are top results most relevant?
    CONTEXT_RECALL = "context_recall"  # Did we retrieve all relevant docs?


@dataclass
class EvaluationCase:
    """Single evaluation case"""
    query: str
    expected_answer: Optional[str] = None
    relevant_doc_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationResult:
    """Result of evaluation"""
    case: EvaluationCase
    retrieved_evidence: List[Any]  # Evidence objects
    generated_answer: str
    metrics: Dict[str, float]
    passed: bool
    feedback: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


class RAGEvaluator:
    """
    Minimal evaluation harness for RAG system.
    
    Usage:
        evaluator = RAGEvaluator()
        
        # Add test cases
        evaluator.add_case(EvaluationCase(
            query="What is RAG?",
            relevant_doc_ids=["doc_rag_overview"],
            expected_answer="RAG combines retrieval and generation..."
        ))
        
        # Run evaluation
        results = evaluator.evaluate(orchestrator, llm)
        
        # Get metrics
        print(evaluator.get_summary(results))
    """
    
    def __init__(self):
        self.test_cases: List[EvaluationCase] = []
    
    def add_case(self, case: EvaluationCase):
        """Add test case"""
        self.test_cases.append(case)
    
    def load_cases_from_file(self, filepath: str):
        """Load test cases from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
            for item in data:
                self.test_cases.append(EvaluationCase(**item))
    
    def evaluate(
        self,
        orchestrator,
        llm_generate_fn,
        retrieval_plan=None
    ) -> List[EvaluationResult]:
        """
        Run evaluation on all test cases.
        
        Args:
            orchestrator: RAGOrchestrator instance
            llm_generate_fn: fn(prompt) -> str
            retrieval_plan: Optional RetrievalPlan
        
        Returns:
            List of EvaluationResult
        """
        results = []
        
        for case in self.test_cases:
            # Retrieve
            retrieval_result = orchestrator.retrieve(
                query=case.query,
                plan=retrieval_plan
            )
            
            # Generate (simplified - actual implementation would use PromptAssembler)
            context = "\n\n".join([e.content for e in retrieval_result.evidence[:5]])
            prompt = f"Context:\n{context}\n\nQuestion: {case.query}\n\nAnswer:"
            answer = llm_generate_fn(prompt)
            
            # Calculate metrics
            metrics = self._calculate_metrics(
                case,
                retrieval_result.evidence,
                answer
            )
            
            # Determine pass/fail
            passed = self._is_passing(metrics)
            feedback = self._generate_feedback(metrics)
            
            results.append(EvaluationResult(
                case=case,
                retrieved_evidence=retrieval_result.evidence,
                generated_answer=answer,
                metrics=metrics,
                passed=passed,
                feedback=feedback
            ))
        
        return results
    
    def _calculate_metrics(
        self,
        case: EvaluationCase,
        evidence: List[Any],
        answer: str
    ) -> Dict[str, float]:
        """Calculate evaluation metrics"""
        metrics = {}
        
        # Context Recall: Did we retrieve relevant docs?
        if case.relevant_doc_ids:
            retrieved_doc_ids = set(
                e.doc_id for e in evidence if hasattr(e, 'doc_id') and e.doc_id
            )
            expected_doc_ids = set(case.relevant_doc_ids)
            
            if expected_doc_ids:
                recall = len(retrieved_doc_ids & expected_doc_ids) / len(expected_doc_ids)
                metrics[EvaluationMetric.CONTEXT_RECALL.value] = recall
        
        # Context Precision: Are top results relevant?
        if case.relevant_doc_ids and evidence:
            relevant_in_top_5 = sum(
                1 for e in evidence[:5]
                if hasattr(e, 'doc_id') and e.doc_id in case.relevant_doc_ids
            )
            metrics[EvaluationMetric.CONTEXT_PRECISION.value] = relevant_in_top_5 / min(5, len(evidence))
        
        # Faithfulness: Is answer grounded in context?
        # Simple heuristic: check if key terms from context appear in answer
        if evidence:
            context_text = " ".join([e.content for e in evidence[:5]])
            # Extract key terms (simplified)
            context_words = set(context_text.lower().split())
            answer_words = set(answer.lower().split())
            overlap = len(context_words & answer_words) / len(answer_words) if answer_words else 0
            metrics[EvaluationMetric.FAITHFULNESS.value] = min(overlap * 2, 1.0)  # Scale up
        
        # Answer Quality: Length and structure heuristics
        word_count = len(answer.split())
        has_structure = any(marker in answer.lower() for marker in ['because', 'however', 'therefore', 'first', 'second'])
        quality_score = min((word_count / 50.0) + (0.2 if has_structure else 0), 1.0)
        metrics[EvaluationMetric.ANSWER_QUALITY.value] = quality_score
        
        return metrics
    
    def _is_passing(self, metrics: Dict[str, float]) -> bool:
        """Determine if result passes quality threshold"""
        # Pass if:
        # - Context recall > 0.7 (if applicable)
        # - Faithfulness > 0.5
        # - Answer quality > 0.4
        
        thresholds = {
            EvaluationMetric.CONTEXT_RECALL.value: 0.7,
            EvaluationMetric.FAITHFULNESS.value: 0.5,
            EvaluationMetric.ANSWER_QUALITY.value: 0.4,
        }
        
        for metric, threshold in thresholds.items():
            if metric in metrics and metrics[metric] < threshold:
                return False
        
        return True
    
    def _generate_feedback(self, metrics: Dict[str, float]) -> str:
        """Generate human-readable feedback"""
        feedback_parts = []
        
        for metric_name, value in metrics.items():
            if value < 0.5:
                feedback_parts.append(f"{metric_name}: LOW ({value:.2f})")
            elif value < 0.7:
                feedback_parts.append(f"{metric_name}: MEDIUM ({value:.2f})")
            else:
                feedback_parts.append(f"{metric_name}: HIGH ({value:.2f})")
        
        return " | ".join(feedback_parts)
    
    def get_summary(self, results: List[EvaluationResult]) -> Dict[str, Any]:
        """
        Get evaluation summary statistics.
        
        Returns:
            Dict with pass rate, average metrics, etc.
        """
        if not results:
            return {"error": "No results"}
        
        passed = sum(1 for r in results if r.passed)
        pass_rate = passed / len(results)
        
        # Average metrics
        all_metrics = {}
        for result in results:
            for metric_name, value in result.metrics.items():
                if metric_name not in all_metrics:
                    all_metrics[metric_name] = []
                all_metrics[metric_name].append(value)
        
        avg_metrics = {
            name: sum(values) / len(values)
            for name, values in all_metrics.items()
        }
        
        return {
            'total_cases': len(results),
            'passed': passed,
            'failed': len(results) - passed,
            'pass_rate': pass_rate,
            'average_metrics': avg_metrics,
            'timestamp': datetime.utcnow().isoformat()
        }

