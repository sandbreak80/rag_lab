#!/bin/bash

# RAG Quality Test - Verify the system returns good answers

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   RAG QUALITY TEST - Verify Answer Quality${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

# Test questions about our documentation
QUERIES=(
    "What is agentic chunking?"
    "How does hybrid search work?"
    "What is the purpose of the knowledge graph?"
    "Explain query expansion"
    "What metrics are tracked?"
)

API_URL="http://localhost:5555/api/chat"

for i in "${!QUERIES[@]}"; do
    query="${QUERIES[$i]}"
    num=$((i+1))
    
    echo -e "\n${YELLOW}[${num}/${#QUERIES[@]}] Testing: ${query}${NC}"
    
    # Send query
    response=$(curl -s "$API_URL" \
        -H "Content-Type: application/json" \
        -d "{\"query\": \"${query}\", \"config\": {\"model\": \"llama3.2:3b\", \"temperature\": 0.7, \"topK\": 3}}")
    
    # Extract answer and sources
    answer=$(echo "$response" | jq -r '.answer')
    sources_count=$(echo "$response" | jq '.sources | length')
    
    # Check if answer is good (not empty, not error, contains actual content)
    if [[ -z "$answer" ]]; then
        echo -e "${RED}❌ FAIL: Empty answer${NC}"
        continue
    fi
    
    if [[ "$answer" == *"unable to provide"* ]] || [[ "$answer" == *"No relevant information"* ]]; then
        echo -e "${RED}❌ FAIL: No answer provided${NC}"
        echo -e "   Answer: ${answer:0:100}..."
        echo -e "   Sources: $sources_count"
        continue
    fi
    
    if [[ ${#answer} -lt 50 ]]; then
        echo -e "${RED}❌ FAIL: Answer too short (${#answer} chars)${NC}"
        echo -e "   Answer: $answer"
        continue
    fi
    
    # Success
    echo -e "${GREEN}✅ PASS: Quality answer (${#answer} chars, $sources_count sources)${NC}"
    echo -e "${GREEN}   Preview: ${answer:0:150}...${NC}"
done

echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}RAG Quality Test Complete${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

