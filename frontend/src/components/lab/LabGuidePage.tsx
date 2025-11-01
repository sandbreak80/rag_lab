import React from 'react';
import { LabSection } from './LabSection';
import { ProgressTracker } from './ProgressTracker';

const LAB_SECTIONS = [
  {
    title: '📚 Introduction to RAG Systems',
    content: `
# What is RAG?

**RAG (Retrieval Augmented Generation)** combines information retrieval with large language model generation to create accurate, grounded responses.

## Key Benefits
- **Accuracy**: Responses are based on your actual documents
- **Up-to-date**: No need to retrain models with new information
- **Transparent**: You can see which documents were used
- **Cost-effective**: Cheaper than fine-tuning LLMs

## How It Works
1. **Index**: Documents are processed and embedded
2. **Retrieve**: Relevant chunks are found for a query
3. **Augment**: Context is added to the LLM prompt
4. **Generate**: LLM produces grounded response
    `,
  },
  {
    title: '🔧 Document Ingestion & Processing',
    content: `
# Ingestion Pipeline

The ingestion pipeline transforms raw documents into searchable chunks with embeddings.

## Steps
1. **Document Upload**: Accept PDF, Word, Excel, PowerPoint, Text
2. **Parsing**: Extract text using Docling (PDF) or native parsers
3. **Chunking**: Break into semantic chunks (agentic or fixed-size)
4. **Embedding**: Convert to vector representations
5. **Storage**: Save to ChromaDB with metadata

## Agentic Chunking
Uses an LLM to create semantically meaningful chunks instead of fixed sizes. This improves recall by 12% but adds latency.
    `,
  },
  {
    title: '🔍 Search: Vector vs BM25 vs Hybrid',
    content: `
# Search Strategies

## Vector Search
- **What**: Semantic similarity using embeddings
- **Best for**: Conceptual queries, synonyms
- **Pros**: Understands meaning, not just keywords
- **Cons**: Can miss exact matches

## BM25 (Keyword Search)
- **What**: Statistical ranking based on term frequency
- **Best for**: Exact matches, rare terms
- **Pros**: Fast, transparent, no ML needed
- **Cons**: Doesn't understand synonyms

## Hybrid Search
- **What**: Combines vector + BM25 with Reciprocal Rank Fusion
- **Best for**: Most production use cases
- **Impact**: +15% overall performance
- **How**: Merges ranked lists from both methods
    `,
  },
  {
    title: '🎯 Query Expansion',
    content: `
# Query Expansion

Enhance queries by adding related terms and synonyms.

## How It Works
1. Analyze the original query
2. Generate related terms/synonyms
3. Search with expanded query
4. Merge and deduplicate results

## Impact
- +5-10% recall
- Helps with sparse documents
- Useful for multi-language content

## Trade-offs
- Adds ~50-100ms latency
- May introduce some noise
    `,
  },
  {
    title: '🕸️ Knowledge Graph Integration',
    content: `
# Knowledge Graphs

Connect documents through relationships for multi-hop reasoning.

## What's Stored
- **Nodes**: Documents, tags, concepts, entities
- **Edges**: Links, mentions, related_to

## Use Cases
- Multi-hop questions ("Who did X work with?")
- Document discovery
- Concept mapping

## Impact
+25% accuracy on multi-hop questions

## How It Works
1. Extract entities and relationships
2. Build graph during ingestion
3. Expand search results via graph traversal
    `,
  },
  {
    title: '⚡ LLM Re-ranking',
    content: `
# LLM Re-ranking

Use an LLM to re-order search results for better precision.

## Process
1. Get initial results (vector/BM25/hybrid)
2. Score each result for query relevance
3. Re-order based on LLM scores
4. Return top-K after reranking

## Impact
- +12% precision
- Better handling of complex queries
- Reduces hallucination

## Trade-offs
- Adds 200-500ms latency
- Requires LLM API call
- Higher token usage
    `,
  },
  {
    title: '🌐 Web Search Integration',
    content: `
# Web Search via SearXNG

Extend RAG beyond your documents with web results.

## Features
- Privacy-focused metasearch engine
- No tracking or profiling
- Aggregates multiple search engines
- JSON API for integration

## Configuration
- **Max Results**: How many web results to fetch
- **Pages Per Result**: Depth of crawling

## Use Cases
- Current events
- External references
- Fact checking
    `,
  },
  {
    title: '📊 Evaluation Metrics',
    content: `
# Measuring RAG Performance

## Retrieval Metrics
- **Precision**: Relevant results / Total results
- **Recall**: Found relevant / All relevant
- **MRR**: Mean Reciprocal Rank
- **NDCG**: Normalized Discounted Cumulative Gain

## Generation Metrics
- **Faithfulness**: Response grounded in context
- **Answer Relevance**: Addresses the query
- **Hallucination Rate**: Made-up information

## System Metrics
- **Latency**: Total response time
- **Token Usage**: Cost estimation
- **Throughput**: Queries per second
    `,
  },
  {
    title: '🎓 Exercises',
    content: `
# Hands-On Lab Exercises

Complete these exercises to master RAG systems:

1. **Baseline Query**: Run with all features OFF
2. **Vector Search**: Enable vector search only
3. **Add BM25**: Enable keyword search
4. **Enable Hybrid**: Combine both search methods
5. **Query Expansion**: Add query expansion
6. **Re-ranking**: Enable LLM reranking
7. **Knowledge Graph**: Add graph expansion
8. **Web Search**: Include external results
9. **Metadata Filters**: Filter by document type
10. **Model Comparison**: Test different LLM models
11. **Temperature Tuning**: Adjust creativity
12. **Production Config**: Test the production preset

**Track your progress** using the Progress Tracker!
    `,
  },
];

export function LabGuidePage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold mb-2">🎓 RAG Systems Lab Guide</h1>
        <p className="text-muted-foreground">
          Learn how Retrieval Augmented Generation works through hands-on experimentation
        </p>
      </div>

      {/* Progress Tracker */}
      <ProgressTracker />

      {/* Lab Sections */}
      <div className="space-y-3">
        {LAB_SECTIONS.map((section, index) => (
          <LabSection
            key={index}
            title={section.title}
            content={section.content}
            defaultOpen={index === 0}
          />
        ))}
      </div>
    </div>
  );
}
