#!/bin/bash

# Script to check for and optionally update Ollama models

echo "🔍 Checking for model updates..."
echo "================================================"
echo ""

# Get list of installed models (excluding duplicates with :latest)
MODELS=$(docker exec ollama ollama list | tail -n +2 | grep -v ":latest" | awk '{print $1}' | sort -u)

echo "📦 Current models:"
docker exec ollama ollama list
echo ""

echo "🔄 Checking for updates..."
echo ""

UPDATE_AVAILABLE=0

for model in $MODELS; do
    echo "Checking $model..."
    
    # Pull the model to check for updates (this will only download if there's a new version)
    docker exec ollama ollama pull $model 2>&1 | grep -q "already up to date" || UPDATE_AVAILABLE=1
    
    echo ""
done

echo "================================================"

if [ $UPDATE_AVAILABLE -eq 1 ]; then
    echo "✅ Some models were updated!"
else
    echo "✅ All models are up to date!"
fi

echo ""
echo "Current models after update check:"
docker exec ollama ollama list
echo ""

