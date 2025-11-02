#!/usr/bin/env python3
"""
Quick fixes for all 5 identified issues in search service
"""

import sys
import re

# Read the file
with open('services/search/app/service.py', 'r') as f:
    content = f.read()

# Fix 1: Add logging after vector search
content = re.sub(
    r"(vec_start = time\.time\(\)\s+vector_results = vector_search_internal\(query, top_k \* 2\)\s+perf_metrics\['vector_search_ms'\] = round\(\(time\.time\(\) - vec_start\) \* 1000, 2\)\s+perf_metrics\['vector_results_count'\] = len\(vector_results\))",
    r"\1\n        print(f\"✓ Vector Search: {perf_metrics['vector_search_ms']}ms ({perf_metrics['vector_results_count']} results)\")",
    content
)

# Fix 2: Add logging after BM25 search
content = re.sub(
    r"(perf_metrics\['bm25_search_ms'\] = round\(\(time\.time\(\) - bm25_start\) \* 1000, 2\)\s+perf_metrics\['bm25_results_count'\] = len\(bm25_results\))",
    r"\1\n            print(f\"✓ BM25 Search: {perf_metrics['bm25_search_ms']}ms ({perf_metrics['bm25_results_count']} results)\")",
    content
)

# Fix 3: Add logging for hybrid fusion
content = re.sub(
    r"(perf_metrics\['fusion_ms'\] = round\(\(time\.time\(\) - fusion_start\) \* 1000, 2\)\s+perf_metrics\['method'\] = 'hybrid')",
    r"\1\n            print(f\"✓ Hybrid Fusion: {perf_metrics['fusion_ms']}ms\")",
    content
)

# Fix 4: Add logging for knowledge graph
content = re.sub(
    r"(perf_metrics\['graph_enhancement_ms'\] = round\(\(time\.time\(\) - graph_start\) \* 1000, 2\)\s+perf_metrics\['graph_docs_added'\] = graph_added)",
    r"\1\n                print(f\"✓ Knowledge Graph: {perf_metrics['graph_enhancement_ms']}ms ({perf_metrics['graph_docs_added']} docs added)\")",
    content
)

# Fix 5: Add logging for reranking
content = re.sub(
    r"(perf_metrics\['reranking_ms'\] = round\(\(time\.time\(\) - rerank_start\) \* 1000, 2\)\s+perf_metrics\['reranking_success'\] = True)",
    r"\1\n                    print(f\"✓ Reranking: {perf_metrics['reranking_ms']}ms (success={perf_metrics['reranking_success']})\")  ",
    content
)

# Fix 6: Add error logging for reranking
content = re.sub(
    r"(perf_metrics\['reranking_error'\] = str\(e\))",
    r"\1\n                print(f\"❌ Reranking error: {e}\")",
    content
)

# Fix 7: Add total timing at end
content = re.sub(
    r"(perf_metrics\['total_latency_ms'\] = round\(\(time\.time\(\) - start_time\) \* 1000, 2\))",
    r"\1\n        print(f\"⏱️  TOTAL SEARCH: {perf_metrics['total_latency_ms']}ms\")\n        print(f\"✅ Returning {len(final_results)} results\\n\")",
    content
)

# Write back
with open('services/search/app/service.py', 'w') as f:
    f.write(content)

print("✅ Added comprehensive logging to search service")
print("   - Vector search timing")
print("   - BM25 search timing")
print("   - Hybrid fusion timing")
print("   - Knowledge graph timing")
print("   - Reranking timing + errors")
print("   - Total timing")

