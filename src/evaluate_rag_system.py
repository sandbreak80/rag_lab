#!/usr/bin/env python3
"""
RAG System Evaluation Script
Calculates precision, recall, MRR, NDCG and other RAG metrics
"""
import json
import sys
import requests
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict
import math

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

class RAGEvaluator:
    """Evaluate RAG system performance"""

    def __init__(self, test_file: str = "tests/evaluation_questions.json"):
        self.test_file = Path(test_file)
        self.questions = self._load_questions()

    def _load_questions(self) -> List[Dict]:
        """Load test questions"""
        with open(self.test_file, 'r') as f:
            data = json.load(f)
        return data['questions']

    def evaluate_query(self, query: str, results: List[Dict],
                       relevant_docs: List[str]) -> Dict[str, float]:
        """
        Evaluate a single query

        Returns:
            metrics: {
                'precision': float,
                'recall': float,
                'mrr': float,
                'ndcg': float,
                'avg_precision': float
            }
        """
        if not results:
            return {
                'precision': 0.0,
                'recall': 0.0,
                'mrr': 0.0,
                'ndcg': 0.0,
                'avg_precision': 0.0
            }

        # Extract filenames from results
        retrieved_docs = []
        for result in results:
            if 'metadata' in result:
                doc_name = result['metadata'].get('file_name', '')
                if doc_name:
                    retrieved_docs.append(doc_name)

        # Calculate metrics
        precision = self._calculate_precision(retrieved_docs, relevant_docs)
        recall = self._calculate_recall(retrieved_docs, relevant_docs)
        mrr = self._calculate_mrr(retrieved_docs, relevant_docs)
        ndcg = self._calculate_ndcg(retrieved_docs, relevant_docs)
        avg_precision = self._calculate_average_precision(retrieved_docs, relevant_docs)

        return {
            'precision': precision,
            'recall': recall,
            'mrr': mrr,
            'ndcg': ndcg,
            'avg_precision': avg_precision,
            'retrieved_count': len(retrieved_docs),
            'relevant_count': len(relevant_docs)
        }

    def _calculate_precision(self, retrieved: List[str], relevant: List[str]) -> float:
        """Precision: relevant retrieved / total retrieved"""
        if not retrieved:
            return 0.0
        relevant_retrieved = sum(1 for doc in retrieved if doc in relevant)
        return relevant_retrieved / len(retrieved)

    def _calculate_recall(self, retrieved: List[str], relevant: List[str]) -> float:
        """Recall: relevant retrieved / total relevant"""
        if not relevant:
            return 0.0
        relevant_retrieved = sum(1 for doc in retrieved if doc in relevant)
        return relevant_retrieved / len(relevant)

    def _calculate_mrr(self, retrieved: List[str], relevant: List[str]) -> float:
        """Mean Reciprocal Rank: 1/rank of first relevant document"""
        for i, doc in enumerate(retrieved, start=1):
            if doc in relevant:
                return 1.0 / i
        return 0.0

    def _calculate_ndcg(self, retrieved: List[str], relevant: List[str], k: int = 10) -> float:
        """Normalized Discounted Cumulative Gain"""
        # DCG: sum of (relevance / log2(rank+1))
        dcg = 0.0
        for i, doc in enumerate(retrieved[:k], start=1):
            relevance = 1.0 if doc in relevant else 0.0
            dcg += relevance / math.log2(i + 1)

        # IDCG: DCG of perfect ranking
        idcg = 0.0
        for i in range(1, min(len(relevant), k) + 1):
            idcg += 1.0 / math.log2(i + 1)

        return dcg / idcg if idcg > 0 else 0.0

    def _calculate_average_precision(self, retrieved: List[str], relevant: List[str]) -> float:
        """Average Precision: average of precision@k for each relevant doc"""
        if not relevant:
            return 0.0

        precisions = []
        relevant_count = 0

        for i, doc in enumerate(retrieved, start=1):
            if doc in relevant:
                relevant_count += 1
                precision_at_i = relevant_count / i
                precisions.append(precision_at_i)

        return sum(precisions) / len(relevant) if precisions else 0.0

    def evaluate_search_endpoint(self, endpoint_url: str,
                                 config: Dict = None) -> Dict[str, Any]:
        """
        Evaluate search endpoint on test set

        Args:
            endpoint_url: URL of search endpoint
            config: Search configuration

        Returns:
            results: {
                'overall': {...},
                'per_difficulty': {...},
                'per_type': {...},
                'failed_queries': [...]
            }
        """
        print(f"\n🧪 Evaluating search endpoint: {endpoint_url}")
        print(f"📋 Test questions: {len(self.questions)}")
        if config:
            print(f"⚙️  Configuration: {config}")
        print("\n" + "="*60)

        all_metrics = []
        failed_queries = []
        by_difficulty = defaultdict(list)
        by_type = defaultdict(list)

        for i, question in enumerate(self.questions, start=1):
            query = question['query']
            relevant_docs = question['relevant_docs']
            difficulty = question.get('difficulty', 'unknown')
            qtype = question.get('type', 'unknown')

            print(f"\n[{i}/{len(self.questions)}] {query}")
            print(f"     Difficulty: {difficulty} | Type: {qtype}")
            print(f"     Expected docs: {len(relevant_docs)}")

            try:
                # Query search endpoint
                payload = {'query': query, 'limit': 10}
                if config:
                    payload.update(config)

                response = requests.post(endpoint_url, json=payload, timeout=30)

                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])

                    # Evaluate
                    metrics = self.evaluate_query(query, results, relevant_docs)
                    all_metrics.append(metrics)
                    by_difficulty[difficulty].append(metrics)
                    by_type[qtype].append(metrics)

                    print(f"     ✅ Precision: {metrics['precision']:.2f} | Recall: {metrics['recall']:.2f} | MRR: {metrics['mrr']:.2f}")
                else:
                    print(f"     ❌ HTTP {response.status_code}")
                    failed_queries.append({
                        'query': query,
                        'error': f"HTTP {response.status_code}"
                    })

            except Exception as e:
                print(f"     ❌ Error: {e}")
                failed_queries.append({
                    'query': query,
                    'error': str(e)
                })

        # Calculate overall metrics
        overall = self._aggregate_metrics(all_metrics)

        # Calculate by difficulty
        per_difficulty = {
            diff: self._aggregate_metrics(metrics)
            for diff, metrics in by_difficulty.items()
        }

        # Calculate by type
        per_type = {
            qtype: self._aggregate_metrics(metrics)
            for qtype, metrics in by_type.items()
        }

        return {
            'overall': overall,
            'per_difficulty': per_difficulty,
            'per_type': per_type,
            'failed_queries': failed_queries,
            'total_questions': len(self.questions),
            'successful_queries': len(all_metrics)
        }

    def _aggregate_metrics(self, metrics_list: List[Dict]) -> Dict[str, float]:
        """Aggregate metrics across multiple queries"""
        if not metrics_list:
            return {}

        aggregated = {
            'precision': sum(m['precision'] for m in metrics_list) / len(metrics_list),
            'recall': sum(m['recall'] for m in metrics_list) / len(metrics_list),
            'mrr': sum(m['mrr'] for m in metrics_list) / len(metrics_list),
            'ndcg': sum(m['ndcg'] for m in metrics_list) / len(metrics_list),
            'avg_precision': sum(m['avg_precision'] for m in metrics_list) / len(metrics_list),
            'count': len(metrics_list)
        }

        # Calculate F1 score
        if aggregated['precision'] + aggregated['recall'] > 0:
            aggregated['f1'] = 2 * (aggregated['precision'] * aggregated['recall']) / \
                               (aggregated['precision'] + aggregated['recall'])
        else:
            aggregated['f1'] = 0.0

        return aggregated

    def print_results(self, results: Dict[str, Any]):
        """Pretty print evaluation results"""
        print("\n" + "="*60)
        print("📊 EVALUATION RESULTS")
        print("="*60)

        overall = results['overall']

        print(f"\n✅ Overall Performance:")
        print(f"   Precision:    {overall['precision']:.2%}")
        print(f"   Recall:       {overall['recall']:.2%}")
        print(f"   F1 Score:     {overall['f1']:.2%}")
        print(f"   MRR:          {overall['mrr']:.3f}")
        print(f"   NDCG:         {overall['ndcg']:.3f}")
        print(f"   Avg Precision:{overall['avg_precision']:.3f}")

        print(f"\n📈 Coverage:")
        print(f"   Successful:   {results['successful_queries']}/{results['total_questions']}")
        print(f"   Failed:       {len(results['failed_queries'])}")

        if results['per_difficulty']:
            print(f"\n📊 By Difficulty:")
            for difficulty, metrics in results['per_difficulty'].items():
                print(f"   {difficulty.capitalize():12} - P: {metrics['precision']:.2%}, R: {metrics['recall']:.2%}, F1: {metrics['f1']:.2%}")

        if results['per_type']:
            print(f"\n📋 By Question Type:")
            for qtype, metrics in results['per_type'].items():
                print(f"   {qtype.capitalize():12} - P: {metrics['precision']:.2%}, R: {metrics['recall']:.2%}, F1: {metrics['f1']:.2%}")

        # Grading
        avg_score = (overall['precision'] + overall['recall'] + overall['f1']) / 3
        if avg_score >= 0.90:
            grade = "🥇 Excellent"
        elif avg_score >= 0.80:
            grade = "🥈 Very Good"
        elif avg_score >= 0.70:
            grade = "🥉 Good"
        elif avg_score >= 0.60:
            grade = "⚠️  Fair"
        else:
            grade = "❌ Needs Improvement"

        print(f"\n🏆 Grade: {grade} (avg: {avg_score:.1%})")

        if results['failed_queries']:
            print(f"\n❌ Failed Queries:")
            for failed in results['failed_queries']:
                print(f"   - {failed['query'][:60]}... ({failed['error']})")

def main():
    """Run evaluation"""
    import argparse

    parser = argparse.ArgumentParser(description='Evaluate RAG system')
    parser.add_argument('--endpoint',
                       default='http://localhost:8002/search',
                       help='Search endpoint URL')
    parser.add_argument('--config',
                       type=json.loads,
                       help='Search configuration as JSON')
    parser.add_argument('--output',
                       help='Output file for results (JSON)')

    args = parser.parse_args()

    # Run evaluation
    evaluator = RAGEvaluator()
    results = evaluator.evaluate_search_endpoint(args.endpoint, args.config)

    # Print results
    evaluator.print_results(results)

    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to: {args.output}")

if __name__ == '__main__':
    main()

