#!/bin/bash
# Performance test for parallel retrieval

echo "=== PARALLEL RETRIEVAL PERFORMANCE TEST ==="
echo "Testing RAG API with parallel vector + web search"
echo ""

# Find the correct RAG API port
RAG_PORT=$(docker compose port rag-api-v1 8080 2>/dev/null | cut -d: -f2)
if [ -z "$RAG_PORT" ]; then
    echo "ERROR: Could not find RAG API port mapping"
    echo "Trying direct container access..."
    RAG_URL="http://rag-api-v1:8080"
else
    RAG_URL="http://localhost:$RAG_PORT"
fi

echo "RAG API URL: $RAG_URL/v1/rag/query"
echo ""

# Run 5 test queries
for i in {1..5}; do
    echo "Query $i:"
    
    # Execute query and capture response
    response=$(docker compose exec -T rag-api-v1 curl -s -X POST http://localhost:8080/v1/rag/query \
        -H "Content-Type: application/json" \
        -d '{"query":"What is RAG?","user_id":"test_user","groups":["public"]}')
    
    # Extract timing metrics
    echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    timings = data.get('metrics', {}).get('stage_timings', {})
    print(f\"  vector_ms: {timings.get('vector_ms', 'N/A')}\")
    print(f\"  web_ms: {timings.get('web_ms', 'N/A')}\")
    print(f\"  retrieve_parallel_ms: {timings.get('retrieve_parallel_ms', 'N/A')}\")
    print(f\"  total_ms: {timings.get('total_ms', 'N/A')}\")
    
    # Calculate speedup
    vector_ms = timings.get('vector_ms', 0)
    web_ms = timings.get('web_ms', 0)
    parallel_ms = timings.get('retrieve_parallel_ms', 0)
    if parallel_ms > 0:
        sequential_est = vector_ms + web_ms
        speedup = sequential_est / parallel_ms if parallel_ms > 0 else 1.0
        print(f\"  Speedup: {speedup:.2f}x (sequential est: {sequential_est}ms vs parallel: {parallel_ms}ms)\")
except Exception as e:
    print(f\"  ERROR: {e}\")
"
    echo ""
    sleep 1
done

echo "=== TEST COMPLETE ==="

