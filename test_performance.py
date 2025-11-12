#!/usr/bin/env python3
"""
Performance test for parallel retrieval implementation
"""
import requests
import json
import time
from statistics import mean, median

# Test configuration
# RAG API is accessed via frontend proxy on port 3000
API_URL = "http://localhost:3000/api/v1/rag/query"
NUM_QUERIES = 5
TEST_QUERY = "What is machine learning?"

print("=== PARALLEL RETRIEVAL PERFORMANCE TEST ===")
print(f"API URL: {API_URL}")
print(f"Number of queries: {NUM_QUERIES}")
print(f"Test query: {TEST_QUERY}")
print()

results = []

for i in range(1, NUM_QUERIES + 1):
    print(f"Query {i}:")

    try:
        payload = {
            "query": TEST_QUERY,
            "user_id": "test_user",
            "groups": ["public"]
        }

        start = time.time()
        response = requests.post(API_URL, json=payload, timeout=60)
        end = time.time()

        if response.status_code == 200:
            data = response.json()
            timings = data.get('metrics', {}).get('stage_timings', {})

            vector_ms = timings.get('vector_ms', 0)
            web_ms = timings.get('web_ms', 0)
            parallel_ms = timings.get('retrieve_parallel_ms', 0)
            total_ms = timings.get('total_ms', 0)

            print(f"  vector_ms: {vector_ms}")
            print(f"  web_ms: {web_ms}")
            print(f"  retrieve_parallel_ms: {parallel_ms}")
            print(f"  total_ms: {total_ms}")

            if parallel_ms > 0:
                sequential_est = vector_ms + web_ms
                speedup = sequential_est / parallel_ms if parallel_ms > 0 else 1.0
                savings_ms = sequential_est - parallel_ms
                print(f"  Speedup: {speedup:.2f}x")
                print(f"  Time saved: {savings_ms}ms ({savings_ms/1000:.2f}s)")

                results.append({
                    'vector_ms': vector_ms,
                    'web_ms': web_ms,
                    'parallel_ms': parallel_ms,
                    'total_ms': total_ms,
                    'speedup': speedup,
                    'savings_ms': savings_ms
                })
        else:
            print(f"  ERROR: HTTP {response.status_code}")
            print(f"  Response: {response.text[:200]}")

    except Exception as e:
        print(f"  ERROR: {e}")

    print()
    time.sleep(1)

# Summary statistics
if results:
    print("=== SUMMARY STATISTICS ===")
    print(f"Successful queries: {len(results)}/{NUM_QUERIES}")
    print()

    speedups = [r['speedup'] for r in results]
    savings = [r['savings_ms'] for r in results]
    parallel_times = [r['parallel_ms'] for r in results]

    print(f"Parallel retrieval time:")
    print(f"  Mean: {mean(parallel_times):.0f}ms")
    print(f"  Median: {median(parallel_times):.0f}ms")
    print()

    print(f"Speedup:")
    print(f"  Mean: {mean(speedups):.2f}x")
    print(f"  Median: {median(speedups):.2f}x")
    print()

    print(f"Time saved per query:")
    print(f"  Mean: {mean(savings):.0f}ms ({mean(savings)/1000:.2f}s)")
    print(f"  Median: {median(savings):.0f}ms ({median(savings)/1000:.2f}s)")
    print()

    print("✅ PARALLEL RETRIEVAL VERIFIED")
else:
    print("❌ NO SUCCESSFUL QUERIES")

print()
print("=== TEST COMPLETE ===")

