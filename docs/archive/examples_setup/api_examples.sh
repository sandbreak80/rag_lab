#!/bin/bash

# Simple bash examples for Ollama API
# Demonstrates basic API calls using curl

OLLAMA_URL="http://localhost:11434"

echo "🚀 Ollama API Examples (Bash/curl)"
echo "================================================"
echo ""

# 1. List all models
echo "1️⃣  List all models"
echo "Command: curl $OLLAMA_URL/api/tags"
echo ""
curl -s $OLLAMA_URL/api/tags | python3 -m json.tool | head -20
echo "... (truncated)"
echo ""
echo ""

# 2. Simple generation (non-streaming)
echo "2️⃣  Simple text generation"
echo "Command: curl $OLLAMA_URL/api/generate -d '{...}'"
echo ""
curl -s $OLLAMA_URL/api/generate -d '{
  "model": "llama3.2:3b",
  "prompt": "Why is the sky blue? Answer in one sentence.",
  "stream": false
}' | python3 -c "import sys, json; print(json.load(sys.stdin)['response'])"
echo ""
echo ""

# 3. Chat-style completion
echo "3️⃣  Chat completion"
echo "Command: curl $OLLAMA_URL/api/chat -d '{...}'"
echo ""
curl -s $OLLAMA_URL/api/chat -d '{
  "model": "llama3.1:8b",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant who answers in exactly 2 sentences."
    },
    {
      "role": "user",
      "content": "What is Docker?"
    }
  ],
  "stream": false
}' | python3 -c "import sys, json; print(json.load(sys.stdin)['message']['content'])"
echo ""
echo ""

# 4. Generate embeddings
echo "4️⃣  Generate embeddings (for RAG/semantic search)"
echo "Command: curl $OLLAMA_URL/api/embeddings -d '{...}'"
echo ""
EMBEDDING_RESULT=$(curl -s $OLLAMA_URL/api/embeddings -d '{
  "model": "nomic-embed-text",
  "prompt": "Docker containers are isolated environments"
}')
VECTOR_LENGTH=$(echo $EMBEDDING_RESULT | python3 -c "import sys, json; print(len(json.load(sys.stdin)['embedding']))")
echo "✅ Generated embedding vector of length: $VECTOR_LENGTH"
echo ""
echo ""

# 5. Streaming example (shows tokens as they're generated)
echo "5️⃣  Streaming response (real-time generation)"
echo "Command: curl $OLLAMA_URL/api/generate -d '{...}' (stream: true)"
echo ""
echo "Response: "
curl -s $OLLAMA_URL/api/generate -d '{
  "model": "qwen3:4b",
  "prompt": "Count from 1 to 5 with enthusiasm!",
  "stream": true
}' | while read -r line; do
  echo $line | python3 -c "import sys, json; chunk = json.loads(sys.stdin.read()); print(chunk.get('response', ''), end='', flush=True)"
done
echo ""
echo ""
echo ""

# 6. Model info
echo "6️⃣  Get model information"
echo "Command: curl $OLLAMA_URL/api/show -d '{...}'"
echo ""
curl -s $OLLAMA_URL/api/show -d '{
  "name": "llama3.1:8b"
}' | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"Model: {data.get('details', {}).get('family', 'N/A')}\")
print(f\"Parameters: {data.get('details', {}).get('parameter_size', 'N/A')}\")
print(f\"Quantization: {data.get('details', {}).get('quantization_level', 'N/A')}\")
"
echo ""
echo ""

echo "================================================"
echo "✅ All examples completed!"
echo ""
echo "API Documentation: https://github.com/ollama/ollama/blob/main/docs/api.md"

