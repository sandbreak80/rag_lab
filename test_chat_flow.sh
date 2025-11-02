#!/bin/bash
# Test script to reproduce chat flow issues

echo "=== Testing Complete Chat Flow ==="
echo ""

# Test 1: API Gateway health
echo "1. Testing API Gateway health..."
curl -s http://localhost:8000/health | jq -r '.status' || echo "FAILED"
echo ""

# Test 2: Search Service
echo "2. Testing Search Service (should be fast)..."
time curl -s -X POST http://localhost:8002/search_with_config \
  -H "Content-Type: application/json" \
  -d '{"query":"test","config":{"top_k":5,"use_query_expansion":false,"use_bm25":false,"use_hybrid":false,"use_graph":false,"use_reranking":false,"use_web_search":false}}' > /dev/null
echo ""

# Test 3: Ollama
echo "3. Testing Ollama /api/generate..."
curl -s -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"llama3.2:3b","prompt":"test","stream":false}' | jq -r '.response[:50]'
echo ""

# Test 4: Chat Service directly
echo "4. Testing Chat Service directly..."
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST http://localhost:8003/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What is RAG?","num_contexts":5}')
HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
echo "Status: $HTTP_CODE"
if [ "$HTTP_CODE" != "200" ]; then
  echo "ERROR Response:"
  echo "$RESPONSE" | grep -v "HTTP_CODE" | jq '.'
fi
echo ""

# Test 5: Full flow through API Gateway
echo "5. Testing Full Flow (API Gateway -> Chat Service)..."
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"query":"What is RAG?","model":"llama3.2:3b","temperature":0.7,"topK":5,"useQueryExpansion":false,"useBM25":false,"useHybrid":false,"useGraph":false,"useReranking":false,"useWebSearch":false}')
HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
echo "Status: $HTTP_CODE"
if [ "$HTTP_CODE" != "200" ]; then
  echo "ERROR Response:"
  echo "$RESPONSE" | grep -v "HTTP_CODE" | jq '.'
else
  echo "SUCCESS - Answer length:" $(echo "$RESPONSE" | grep -v "HTTP_CODE" | jq -r '.answer | length')
fi
echo ""

echo "=== Checking Recent Logs ==="
echo "API Gateway:"
docker logs rag-api-gateway --tail 10 | grep -E "🌐|📤|📬|❌" || echo "No recent activity"
echo ""
echo "Chat Service:"
docker logs rag-chat-service --tail 10 | grep -E "📥|🔍|✅|🤖|❌" || echo "No recent activity"

