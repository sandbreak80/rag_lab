#!/bin/bash
# Pull Ollama Models for RAG Lab
# This script pulls all required Ollama models for the project

set -e

echo "🤖 Pulling Ollama Models for RAG Lab"
echo "======================================"
echo ""

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "❌ ERROR: Ollama is not running or not accessible at localhost:11434"
    echo "   Please start Ollama first:"
    echo "   docker-compose up -d ollama"
    echo "   OR"
    echo "   ollama serve (if running locally)"
    exit 1
fi

echo "✅ Ollama is running"
echo ""

# Define required models (optimized for 16GB GPU)
CHAT_MODEL="llama3.1:8b"
EMBEDDING_MODEL="nomic-embed-text"  # Changed: mxbai-embed-large has 500 errors

# Optional models (for lab exercises and comparison)
OPTIONAL_MODELS=(
    # Small models (fast, large context) - Lab: Speed vs Quality
    "llama3.2:1b"      # Smallest (1GB) - 128K context, 100+ tok/s
    "llama3.2:3b"      # Small (2GB) - 128K context, 60 tok/s
    "gemma2:2b"        # Google efficient (2GB) - High quality for size
    
    # Medium models (production sweet spot)
    "gemma2:9b"        # Google high-performance (5.5GB) - Excellent quality
    "mistral:7b"       # Fast alternative (4GB) - 32K context
    
    # Large models (best quality) - Lab: Quality vs Memory
    "qwen2.5:14b"      # Best for 16GB GPU (9GB) - Top quality
    
    # Embedding alternatives (if mxbai fails)
    "mxbai-embed-large"  # Keep as option (335MB) - Best retrieval
    "all-minilm"       # Tiny, fast (23MB) - Good for demos
)

# Function to pull a model
pull_model() {
    local model=$1
    local description=$2

    echo "📥 Pulling $model ($description)..."

    if docker exec rag-ollama ollama pull "$model"; then
        echo "✅ Successfully pulled $model"
    else
        echo "⚠️  Failed to pull $model (may already exist or network issue)"
    fi
    echo ""
}

# Pull required models
echo "📦 REQUIRED MODELS"
echo "=================="
pull_model "$CHAT_MODEL" "Chat/LLM model"
pull_model "$EMBEDDING_MODEL" "Embedding model"

# Ask if user wants optional models
echo ""
echo "📦 OPTIONAL MODELS (for testing)"
echo "================================="
echo "These models are optional and can be used for testing different model sizes."
echo "They will take additional disk space (~4-8GB each)."
echo ""
read -p "Do you want to pull optional models? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    for model in "${OPTIONAL_MODELS[@]}"; do
        pull_model "$model" "Optional test model"
    done
fi

# List all downloaded models
echo ""
echo "📋 Downloaded Models:"
echo "===================="
docker exec rag-ollama ollama list

echo ""
echo "✅ Model setup complete!"
echo ""
echo "💡 TIP: You can change the model in config.env:"
echo "   CHAT_MODEL=$CHAT_MODEL"
echo "   EMBEDDING_MODEL=$EMBEDDING_MODEL"
echo ""

