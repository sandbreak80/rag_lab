#!/bin/bash

# Re-ingest System Documentation
# Used after database reset to restore baseline RAG knowledge

set -e

echo "🔄 Re-ingesting System Documentation..."
echo ""

# Base directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCS_DIR="$PROJECT_ROOT/docs"

# Documents to ingest
SYSTEM_DOCS=(
    "$DOCS_DIR/lab/AI_FUNDAMENTALS_ADDENDUM.md"
    "$DOCS_DIR/lab/LAB_GUIDE.md"
    "$DOCS_DIR/lab/LAB_OBJECTIVES.md"
    "$DOCS_DIR/lab/LAB_VISION_2.0.md"
    "$DOCS_DIR/lab/MODEL_COMPARISON_EXERCISE.md"
    "$DOCS_DIR/lab/STUDENT_EXERCISES.md"
    "$DOCS_DIR/ARCHITECTURE.md"
    "$DOCS_DIR/PERFORMANCE.md"
    "$DOCS_DIR/RAG_FEATURES.md"
    "$DOCS_DIR/RAG_DEEP_DIVE.md"
    "$DOCS_DIR/QUICK_START.md"
)

# Ingest API endpoint
INGEST_URL="http://localhost:8000/api/upload"

total=${#SYSTEM_DOCS[@]}
count=0

for doc in "${SYSTEM_DOCS[@]}"; do
    count=$((count + 1))

    if [ ! -f "$doc" ]; then
        echo "⚠️  Skipping missing file: $doc"
        continue
    fi

    filename=$(basename "$doc")
    echo "[$count/$total] 📄 Ingesting: $filename"

    response=$(curl -s -X POST "$INGEST_URL" \
        -F "file=@$doc" \
        -w "\n%{http_code}")

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "200" ]; then
        echo "    ✅ Success"
    else
        echo "    ❌ Failed (HTTP $http_code)"
        echo "    Response: $body"
    fi

    # Small delay to avoid overwhelming the service
    sleep 0.5
done

echo ""
echo "✅ System documentation re-ingestion complete!"
echo "📊 Check /api/stats to verify document count"

