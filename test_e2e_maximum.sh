#!/bin/bash
# End-to-End Test with Maximum RAG Configuration
# Tests all features: Query Expansion, BM25, Hybrid, Graph, Reranking, Web Search

echo "════════════════════════════════════════════════════════════════"
echo "  🧪 NEURAL VAULT RAG LAB - END-TO-END TEST (MAXIMUM CONFIG)"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Test query
QUERY="What are the key features of RAG?"
echo "📝 Test Query: $QUERY"
echo ""

# Maximum configuration (everything enabled)
echo "⚙️  Configuration: MAXIMUM (all features enabled)"
echo "   ✓ Query Expansion"
echo "   ✓ BM25 Search"
echo "   ✓ Hybrid Fusion"
echo "   ✓ Knowledge Graph"
echo "   ✓ LLM Re-ranking"
echo "   ✓ Web Search"
echo "   ✓ Top-K: 10"
echo ""

# Pre-flight checks
echo "────────────────────────────────────────────────────────────────"
echo "🔍 PRE-FLIGHT CHECKS"
echo "────────────────────────────────────────────────────────────────"

check_service() {
    local name=$1
    local url=$2
    local status=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    if [ "$status" = "200" ]; then
        echo "   ✅ $name: HEALTHY"
        return 0
    else
        echo "   ❌ $name: UNHEALTHY (HTTP $status)"
        return 1
    fi
}

check_service "API Gateway      " "http://localhost:8000/health"
check_service "Search Service   " "http://localhost:8002/health"
check_service "Chat Service     " "http://localhost:8003/health"
check_service "Vector DB        " "http://localhost:8005/health"
check_service "Embedding Service" "http://localhost:8006/health"
check_service "Knowledge Graph  " "http://localhost:8007/health"
check_service "Reranker Service " "http://localhost:8008/health"
check_service "Ollama           " "http://localhost:11434/api/tags"

echo ""

# Main test
echo "────────────────────────────────────────────────────────────────"
echo "🚀 RUNNING END-TO-END TEST"
echo "────────────────────────────────────────────────────────────────"

START_TIME=$(date +%s.%N)

# Make the request
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}\nTOTAL_TIME:%{time_total}" \
  -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "'"$QUERY"'",
    "model": "llama3.2:3b",
    "temperature": 0.7,
    "topK": 10,
    "useQueryExpansion": true,
    "useBM25": true,
    "useHybrid": true,
    "useGraph": true,
    "useReranking": true,
    "useWebSearch": true,
    "webSearchDocs": 5,
    "webSearchPages": 1,
    "rerankTopK": 10
  }')

END_TIME=$(date +%s.%N)
TOTAL_SECONDS=$(echo "$END_TIME - $START_TIME" | bc)

# Extract HTTP code and timing
HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
CURL_TIME=$(echo "$RESPONSE" | grep "TOTAL_TIME" | cut -d: -f2)

# Remove metadata lines
RESPONSE_BODY=$(echo "$RESPONSE" | grep -v "HTTP_CODE" | grep -v "TOTAL_TIME")

echo ""
echo "⏱️  TIMING:"
echo "   Total Time: ${TOTAL_SECONDS} seconds"
echo "   HTTP Status: $HTTP_CODE"
echo ""

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ SUCCESS!"
    echo ""
    echo "────────────────────────────────────────────────────────────────"
    echo "📊 RESPONSE ANALYSIS"
    echo "────────────────────────────────────────────────────────────────"

    # Parse response
    ANSWER_LENGTH=$(echo "$RESPONSE_BODY" | jq -r '.answer | length' 2>/dev/null)
    SOURCES_COUNT=$(echo "$RESPONSE_BODY" | jq -r '.sources | length' 2>/dev/null)

    echo "$RESPONSE_BODY" | jq -r '
    "
📝 Answer:
   Length: \(.answer | length) characters
   Preview: \(.answer[:200])...

📚 Sources: \(.sources | length) documents

⚙️  RAG PIPELINE METRICS:
" +
    if .metrics then
        "   Method: \(.metrics.method // "N/A")
   Query Expanded: \(.metrics.query_expanded // false)

   🔍 SEARCH TIMING:
   • Query Expansion: \(.metrics.query_expansion_ms // 0)ms
   • Vector Search:   \(.metrics.vector_search_ms // 0)ms (\(.metrics.vector_results_count // 0) results)
   • BM25 Search:     \(.metrics.bm25_search_ms // 0)ms (\(.metrics.bm25_results_count // 0) results)
   • Hybrid Fusion:   \(.metrics.fusion_ms // 0)ms
   • Knowledge Graph: \(.metrics.graph_enhancement_ms // 0)ms (\(.metrics.graph_docs_added // 0) docs added)
   • Reranking:       \(.metrics.reranking_ms // 0)ms (success: \(.metrics.reranking_success // false))
   • Web Search:      \(.metrics.web_search_ms // 0)ms

   📊 TOTAL SEARCH:   \(.metrics.total_latency_ms // 0)ms

   🎯 RESULTS:
   • Context Chunks: \(.metrics.context_chunks // 0)
   • Model: \(.metrics.model // "N/A")
   • Temperature: \(.metrics.temperature // 0)

   ⚡ BREAKDOWN:
" +
        if .metrics.breakdown_percent then
            (.metrics.breakdown_percent | to_entries | map("   • " + .key + ": " + (.value | tostring) + "%") | join("\n"))
        else
            "   (No breakdown available)"
        end
    else
        "   (No metrics available)"
    end
    ' 2>/dev/null

    echo ""

else
    echo "❌ FAILED!"
    echo ""
    echo "────────────────────────────────────────────────────────────────"
    echo "🔴 ERROR DETAILS"
    echo "────────────────────────────────────────────────────────────────"
    echo "$RESPONSE_BODY" | jq '.' 2>/dev/null || echo "$RESPONSE_BODY"
    echo ""
fi

# Check recent logs
echo "────────────────────────────────────────────────────────────────"
echo "📋 RECENT SERVICE LOGS"
echo "────────────────────────────────────────────────────────────────"

echo ""
echo "🌐 API Gateway:"
docker logs rag-api-gateway --since 30s --tail 20 2>&1 | grep -E "🌐|📤|📬|❌|Error" | tail -5

echo ""
echo "💬 Chat Service:"
docker logs rag-chat-service --since 30s --tail 20 2>&1 | grep -E "📥|🔍|✅|🤖|❌|Error" | tail -5

echo ""
echo "🔎 Search Service:"
docker logs rag-search-service --since 30s --tail 20 2>&1 | grep -E "search_with_config|Error" | tail -5

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  TEST COMPLETE"
echo "════════════════════════════════════════════════════════════════"

