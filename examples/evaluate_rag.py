#!/usr/bin/env python3
"""
Evaluate RAG system performance with test questions
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from search import VaultSearcher
from ask_questions import ask_question
import json


def evaluate_retrieval(searcher: VaultSearcher):
    """
    Evaluate retrieval quality with test questions
    
    Tests:
    1. Retrieval accuracy (does it find relevant docs?)
    2. Score distribution (are relevant docs scored higher?)
    3. Coverage (how many queries return results?)
    """
    print("="*60)
    print("📊 RAG EVALUATION - RETRIEVAL METRICS")
    print("="*60)
    
    # Test queries with expected relevant terms
    test_queries = [
        {
            "query": "AI prompting best practices",
            "expected_keywords": ["prompt", "ai", "engineering"],
            "expected_relevance": 0.6  # Minimum score threshold
        },
        {
            "query": "AppDynamics observability features",
            "expected_keywords": ["appdynamics", "observability", "monitoring"],
            "expected_relevance": 0.6
        },
        {
            "query": "transformer architecture and attention mechanism",
            "expected_keywords": ["transformer", "attention", "architecture"],
            "expected_relevance": 0.6
        },
        {
            "query": "LangChain framework usage",
            "expected_keywords": ["langchain", "framework"],
            "expected_relevance": 0.5
        },
        {
            "query": "Cisco AI principles and responsible AI",
            "expected_keywords": ["cisco", "ai", "responsible"],
            "expected_relevance": 0.5
        },
        {
            "query": "How to fine-tune LLMs with HuggingFace",
            "expected_keywords": ["huggingface", "fine-tun", "llm"],
            "expected_relevance": 0.5
        },
        {
            "query": "Splunk case studies and customer success",
            "expected_keywords": ["splunk", "customer", "case"],
            "expected_relevance": 0.5
        },
    ]
    
    results = []
    total_queries = len(test_queries)
    successful_retrievals = 0
    high_relevance_count = 0
    
    print(f"\nRunning {total_queries} test queries...\n")
    
    for i, test in enumerate(test_queries, 1):
        query = test["query"]
        print(f"Test {i}/{total_queries}: {query}")
        
        # Search
        search_results = searcher.search(query, limit=5)
        
        if not search_results:
            print("  ❌ No results")
            results.append({
                "query": query,
                "found": False,
                "top_score": 0,
                "avg_score": 0,
                "has_expected_keywords": False
            })
            continue
        
        successful_retrievals += 1
        
        # Calculate metrics
        scores = [r['score'] for r in search_results]
        top_score = scores[0]
        avg_score = sum(scores) / len(scores)
        
        # Check for expected keywords in top result
        top_content = search_results[0]['content'].lower()
        top_title = search_results[0]['metadata']['title'].lower()
        has_keywords = any(kw.lower() in top_content or kw.lower() in top_title 
                          for kw in test["expected_keywords"])
        
        # Check if top score meets threshold
        meets_threshold = top_score >= test["expected_relevance"]
        
        if meets_threshold:
            high_relevance_count += 1
        
        status = "✅" if (has_keywords and meets_threshold) else "⚠️"
        print(f"  {status} Top: {search_results[0]['metadata']['title'][:50]}")
        print(f"     Score: {top_score:.3f} | Avg: {avg_score:.3f} | Keywords: {has_keywords}")
        
        results.append({
            "query": query,
            "found": True,
            "top_score": top_score,
            "avg_score": avg_score,
            "has_expected_keywords": has_keywords,
            "meets_threshold": meets_threshold,
            "top_result": search_results[0]['metadata']['title']
        })
    
    # Calculate overall metrics
    print("\n" + "="*60)
    print("📈 RETRIEVAL METRICS")
    print("="*60)
    
    coverage = (successful_retrievals / total_queries) * 100
    precision = (high_relevance_count / total_queries) * 100 if total_queries > 0 else 0
    
    avg_top_score = sum(r['top_score'] for r in results) / len(results)
    avg_all_scores = sum(r['avg_score'] for r in results if r['found']) / successful_retrievals if successful_retrievals > 0 else 0
    
    keyword_matches = sum(1 for r in results if r.get('has_expected_keywords', False))
    keyword_precision = (keyword_matches / total_queries) * 100
    
    print(f"\n✅ Coverage: {coverage:.1f}%")
    print(f"   ({successful_retrievals}/{total_queries} queries returned results)")
    
    print(f"\n🎯 High Relevance Retrieval: {precision:.1f}%")
    print(f"   ({high_relevance_count}/{total_queries} queries had top score ≥ threshold)")
    
    print(f"\n🔍 Keyword Match Precision: {keyword_precision:.1f}%")
    print(f"   ({keyword_matches}/{total_queries} top results contained expected keywords)")
    
    print(f"\n📊 Average Scores:")
    print(f"   Top result: {avg_top_score:.3f}")
    print(f"   All results: {avg_all_scores:.3f}")
    
    print(f"\n💡 Score Interpretation:")
    print(f"   0.8-1.0  = Excellent match")
    print(f"   0.6-0.8  = Good match")
    print(f"   0.4-0.6  = Fair match")
    print(f"   0.0-0.4  = Poor match")
    
    return {
        "coverage": coverage,
        "precision": precision,
        "keyword_precision": keyword_precision,
        "avg_top_score": avg_top_score,
        "avg_all_scores": avg_all_scores,
        "results": results
    }


def evaluate_qa(searcher: VaultSearcher):
    """
    Evaluate Q&A quality (subjective - requires human review)
    """
    print("\n" + "="*60)
    print("💬 RAG EVALUATION - Q&A QUALITY")
    print("="*60)
    
    test_questions = [
        "What are the key principles of prompt engineering?",
        "What observability features does AppDynamics provide?",
        "How does the attention mechanism work in transformers?",
    ]
    
    print(f"\nGenerating answers for {len(test_questions)} questions...\n")
    
    qa_results = []
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n--- Question {i}/{len(test_questions)} ---")
        result = ask_question(searcher, question, num_contexts=3)
        
        qa_results.append({
            "question": question,
            "answer": result['answer'],
            "num_sources": len(result['sources']),
            "top_source_score": result['sources'][0]['score'] if result['sources'] else 0
        })
        
        print(f"\n📝 Answer (first 200 chars):")
        print(result['answer'][:200] + "...")
        print(f"\n📚 Sources: {len(result['sources'])}")
    
    print("\n" + "="*60)
    print("✅ Q&A Evaluation Complete")
    print("="*60)
    print("\n💡 Note: Q&A quality requires human evaluation.")
    print("   Please review the answers above for:")
    print("   - Factual accuracy")
    print("   - Relevance to question")
    print("   - Use of sources")
    print("   - Clarity and completeness")
    
    return qa_results


def main():
    """Run full RAG evaluation"""
    print("\n" + "="*60)
    print("🔬 RAG SYSTEM EVALUATION")
    print("="*60)
    
    searcher = VaultSearcher()
    
    if not searcher.collection:
        print("❌ No index found. Please run: python src/indexer.py")
        return
    
    print(f"\n📚 Vault: {searcher.collection.count()} chunks indexed")
    
    # 1. Evaluate retrieval
    retrieval_metrics = evaluate_retrieval(searcher)
    
    # 2. Evaluate Q&A
    qa_results = evaluate_qa(searcher)
    
    # 3. Summary
    print("\n" + "="*60)
    print("📊 FINAL SUMMARY")
    print("="*60)
    
    print(f"\n🎯 RETRIEVAL PERFORMANCE:")
    print(f"   Coverage:          {retrieval_metrics['coverage']:.1f}%")
    print(f"   Precision:         {retrieval_metrics['precision']:.1f}%")
    print(f"   Keyword Match:     {retrieval_metrics['keyword_precision']:.1f}%")
    print(f"   Avg Top Score:     {retrieval_metrics['avg_top_score']:.3f}")
    
    print(f"\n💬 Q&A PERFORMANCE:")
    print(f"   Questions tested:  {len(qa_results)}")
    print(f"   Avg sources used:  {sum(r['num_sources'] for r in qa_results) / len(qa_results):.1f}")
    
    print(f"\n✅ Overall: Your RAG system is operational!")
    print(f"   - {retrieval_metrics['coverage']:.0f}% of queries return results")
    print(f"   - {retrieval_metrics['precision']:.0f}% have high relevance scores")
    print(f"   - Avg relevance score: {retrieval_metrics['avg_top_score']:.3f}")
    
    if retrieval_metrics['avg_top_score'] >= 0.7:
        grade = "🥇 Excellent"
    elif retrieval_metrics['avg_top_score'] >= 0.6:
        grade = "🥈 Good"
    elif retrieval_metrics['avg_top_score'] >= 0.5:
        grade = "🥉 Fair"
    else:
        grade = "⚠️  Needs Improvement"
    
    print(f"\n🏆 Grade: {grade}")
    
    # Save results
    output_file = Path(__file__).parent.parent / "indices" / "evaluation_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            "retrieval": retrieval_metrics,
            "qa_summary": {
                "questions_tested": len(qa_results),
                "avg_sources": sum(r['num_sources'] for r in qa_results) / len(qa_results)
            }
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")


if __name__ == "__main__":
    main()
