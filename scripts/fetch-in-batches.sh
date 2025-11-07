#!/bin/bash
#
# Fetch Research Agent Sources in Batches
# Prevents timeouts by chunking requests
#
# Usage:
#   ./scripts/fetch-in-batches.sh [batch_size]
#   ./scripts/fetch-in-batches.sh 5  # Default: 5 sources per batch

set -e

BATCH_SIZE="${1:-5}"
RESEARCH_AGENT_URL="${2:-http://localhost:8015}"

echo "🚀 Batch Fetcher for Research Agent"
echo "====================================="
echo "Batch Size: $BATCH_SIZE sources per request"
echo "Target: $RESEARCH_AGENT_URL"
echo ""

# Get total sources
echo "📊 Getting source count..."
TOTAL=$(curl -s "$RESEARCH_AGENT_URL/sources" | jq '.sources | length')
echo "Total sources: $TOTAL"
echo ""

if [ "$TOTAL" -eq 0 ]; then
    echo "❌ No sources found!"
    exit 1
fi

# Calculate number of batches
BATCHES=$(( (TOTAL + BATCH_SIZE - 1) / BATCH_SIZE ))
echo "Will process $BATCHES batches"
echo ""

# Process each batch
OFFSET=0
BATCH_NUM=1
TOTAL_PROCESSED=0

while [ $OFFSET -lt $TOTAL ]; do
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📦 Batch $BATCH_NUM/$BATCHES (offset: $OFFSET)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Trigger batch fetch
    RESPONSE=$(curl -s -X POST "$RESEARCH_AGENT_URL/trigger/batch?batch_size=$BATCH_SIZE&offset=$OFFSET")

    # Parse response
    SUCCESS=$(echo "$RESPONSE" | jq -r '.success')
    PROCESSED=$(echo "$RESPONSE" | jq -r '.processed')
    MESSAGE=$(echo "$RESPONSE" | jq -r '.message')
    PROGRESS=$(echo "$RESPONSE" | jq -r '.progress')
    HAS_MORE=$(echo "$RESPONSE" | jq -r '.has_more')

    echo "Status: $MESSAGE"
    echo "Progress: $PROGRESS"

    # Check for errors
    ERRORS=$(echo "$RESPONSE" | jq -r '.errors | length')
    if [ "$ERRORS" -gt 0 ]; then
        echo "⚠️  Errors encountered:"
        echo "$RESPONSE" | jq -r '.errors[]' | while read -r error; do
            echo "  - $error"
        done
    fi

    TOTAL_PROCESSED=$((TOTAL_PROCESSED + PROCESSED))

    echo "Processed in this batch: $PROCESSED"
    echo "Total processed so far: $TOTAL_PROCESSED"
    echo ""

    # Check if more batches
    if [ "$HAS_MORE" = "false" ]; then
        echo "✅ All batches complete!"
        break
    fi

    # Move to next batch
    OFFSET=$((OFFSET + BATCH_SIZE))
    BATCH_NUM=$((BATCH_NUM + 1))

    # Small delay between batches
    echo "⏳ Waiting 2 seconds before next batch..."
    sleep 2
    echo ""
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ FETCH COMPLETE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Total sources: $TOTAL"
echo "Total processed: $TOTAL_PROCESSED"
echo ""

# Get final stats
echo "📊 Final Statistics:"
curl -s "$RESEARCH_AGENT_URL/status" | jq '.stats'

echo ""
echo "🎉 Done! Check status at: $RESEARCH_AGENT_URL/status"

