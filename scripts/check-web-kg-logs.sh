#!/bin/bash
# Check logs for web/KG result inclusion debugging
# Run this after running the feature tests

echo "Checking logs for web/KG result inclusion..."
echo "=========================================="
echo ""

# Get recent logs and filter for relevant messages
docker compose logs rag-api-v1 --tail=500 | grep -E '(Web search|KG search|origin_tool|Top results|Auto-added|Cited|Web results|KG results|Final top_results|Forced)' | tail -50

echo ""
echo "=========================================="
echo "Key things to look for:"
echo "1. 'Web results origin_tools: [...]' - shows what origin_tool values web results have"
echo "2. 'KG results origin_tools: [...]' - shows what origin_tool values KG results have"
echo "3. 'Top results for LLM prompt: ... origin_tools: [...]' - shows what's in top_results"
echo "4. 'Final top_results: X results, web: X, kg: X' - final state before LLM"
echo "5. 'Cited origin_tools: {...}' - what the LLM actually cited"
echo "6. 'Auto-added web/KG result to citations' - confirmation auto-add worked"
echo "7. 'Web search enabled but no web results available' - indicates a problem"

