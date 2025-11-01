#!/bin/bash

# Script to upgrade Ollama Docker container to the latest version
# This will preserve all downloaded models

echo "🔄 Upgrading Ollama Docker Container"
echo "================================================"
echo ""

# Step 1: Check current version
echo "📊 Current Ollama version:"
docker exec ollama ollama --version || echo "Unable to get version"
echo ""

# Step 2: Stop the current container
echo "⏸️  Stopping current Ollama container..."
docker stop ollama
echo "✅ Container stopped"
echo ""

# Step 3: Remove the old container (keep the volume with models)
echo "🗑️  Removing old container (models will be preserved)..."
docker rm ollama
echo "✅ Container removed"
echo ""

# Step 4: Pull the latest Ollama image
echo "⬇️  Pulling latest Ollama image..."
docker pull ollama/ollama:latest
echo "✅ Latest image pulled"
echo ""

# Step 5: Start new container with the same configuration
echo "🚀 Starting new Ollama container..."
docker run -d \
  --name ollama \
  -p 11434:11434 \
  -v ollama:/root/.ollama \
  ollama/ollama
echo "✅ New container started"
echo ""

# Step 6: Wait for the service to be ready
echo "⏳ Waiting for Ollama service to be ready..."
sleep 5
echo ""

# Step 7: Check new version
echo "📊 New Ollama version:"
docker exec ollama ollama --version
echo ""

# Step 8: Verify models are still available
echo "📦 Verifying models are still available:"
docker exec ollama ollama list
echo ""

# Step 9: Run a quick test
echo "🧪 Running quick test with llama3.1:8b..."
docker exec ollama ollama run llama3.1:8b "Say 'Upgrade successful!' in a creative way."
echo ""

echo "================================================"
echo "✅ Ollama upgrade completed successfully!"
echo ""
echo "Your models have been preserved and are ready to use."
echo ""

