#!/bin/bash

# Script to pull recommended Ollama models for MacBook Pro M2 with 16GB RAM
# Container: ollama

echo "🚀 Starting Ollama model downloads..."
echo "================================================"
echo ""

# Core recommended models (7-9B parameters)
echo "📦 Pulling core models..."
echo ""

echo "1/8 Pulling llama3.1:8b (Best all-around model)..."
docker exec ollama ollama pull llama3.1:8b
echo ""

echo "2/8 Pulling qwen2.5:7b (Great multilingual & coding)..."
docker exec ollama ollama pull qwen2.5:7b
echo ""

echo "3/8 Pulling deepseek-r1:7b (Advanced reasoning)..."
docker exec ollama ollama pull deepseek-r1:7b
echo ""

echo "4/8 Pulling gemma2:9b (High performance)..."
docker exec ollama ollama pull gemma2:9b
echo ""

# Lightweight models
echo "📦 Pulling lightweight models..."
echo ""

echo "5/8 Pulling llama3.2:3b (Fast & efficient)..."
docker exec ollama ollama pull llama3.2:3b
echo ""

echo "6/8 Pulling qwen3:4b (Latest generation)..."
docker exec ollama ollama pull qwen3:4b
echo ""

# Specialized models
echo "📦 Pulling specialized models..."
echo ""

echo "7/8 Pulling nomic-embed-text (Embeddings)..."
docker exec ollama ollama pull nomic-embed-text
echo ""

echo "8/8 Pulling llava:7b (Vision model)..."
docker exec ollama ollama pull llava:7b
echo ""

echo "================================================"
echo "✅ All models downloaded successfully!"
echo ""
echo "To list available models, run:"
echo "  docker exec ollama ollama list"
echo ""
echo "To test a model, run:"
echo "  docker exec -it ollama ollama run llama3.1:8b"

