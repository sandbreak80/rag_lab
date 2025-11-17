/**
 * Standard Prompt Library for A/B Testing
 * 20 diverse prompts covering different categories, complexities, and use cases
 */

export interface PromptLibraryItem {
  id: string;
  category: 'factual' | 'analytical' | 'multi-hop' | 'temporal' | 'creative';
  title: string;
  prompt: string;
  complexity: 'simple' | 'medium' | 'complex';
  expectedLength: 'short' | 'medium' | 'long';
  tags: string[];
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  expectedSources: number;
  expectedLatency: string;
  description?: string;
}

export const PROMPT_LIBRARY: PromptLibraryItem[] = [
  // ============================================================================
  // FACTUAL QUERIES (5 prompts)
  // ============================================================================
  {
    id: 'factual-1',
    category: 'factual',
    title: 'What is RAG?',
    prompt: 'What is Retrieval-Augmented Generation (RAG)? Explain the core concept and how it works.',
    complexity: 'simple',
    expectedLength: 'short',
    tags: ['RAG', 'basics', 'concepts'],
    difficulty: 'beginner',
    expectedSources: 3,
    expectedLatency: '50-100ms',
    description: 'Simple factual question requiring basic RAG knowledge'
  },
  {
    id: 'factual-2',
    category: 'factual',
    title: 'Vector Search vs Keyword Search',
    prompt: 'What is the difference between vector search and keyword search? When would you use each?',
    complexity: 'simple',
    expectedLength: 'medium',
    tags: ['search', 'vector', 'keyword', 'comparison'],
    difficulty: 'beginner',
    expectedSources: 4,
    expectedLatency: '100-150ms',
    description: 'Comparison question requiring understanding of search methods'
  },
  {
    id: 'factual-3',
    category: 'factual',
    title: 'Context Window Limits',
    prompt: 'What is the context window limit for llama3.1:8b? How does this affect RAG system design?',
    complexity: 'simple',
    expectedLength: 'short',
    tags: ['models', 'context-window', 'llama'],
    difficulty: 'beginner',
    expectedSources: 2,
    expectedLatency: '50-100ms',
    description: 'Specific technical fact about model capabilities'
  },
  {
    id: 'factual-4',
    category: 'factual',
    title: 'Embedding Models',
    prompt: 'What embedding models are available in this lab? What are their key characteristics?',
    complexity: 'simple',
    expectedLength: 'medium',
    tags: ['embeddings', 'models', 'nomic'],
    difficulty: 'beginner',
    expectedSources: 3,
    expectedLatency: '100-150ms',
    description: 'Factual question about available tools'
  },
  {
    id: 'factual-5',
    category: 'factual',
    title: 'Chunking Strategies',
    prompt: 'What are the different chunking strategies available? Explain fixed, regex, and agentic chunking.',
    complexity: 'medium',
    expectedLength: 'medium',
    tags: ['chunking', 'processing', 'agentic'],
    difficulty: 'intermediate',
    expectedSources: 5,
    expectedLatency: '150-200ms',
    description: 'Requires understanding of multiple chunking approaches'
  },

  // ============================================================================
  // ANALYTICAL QUERIES (5 prompts)
  // ============================================================================
  {
    id: 'analytical-1',
    category: 'analytical',
    title: 'RAG Architecture Comparison',
    prompt: 'Compare and contrast naive RAG, advanced RAG with reranking, and agentic RAG systems. Analyze the trade-offs between retrieval precision, computational cost, and response quality. Include specific examples of when each architecture would be most appropriate.',
    complexity: 'complex',
    expectedLength: 'long',
    tags: ['RAG', 'architecture', 'comparison', 'trade-offs'],
    difficulty: 'advanced',
    expectedSources: 8,
    expectedLatency: '500-1000ms',
    description: 'Complex analytical question requiring deep understanding and comparison'
  },
  {
    id: 'analytical-2',
    category: 'analytical',
    title: 'Model Size Trade-offs',
    prompt: 'What are the trade-offs between using a 3B model vs 8B model for RAG? Consider speed, quality, memory usage, and cost.',
    complexity: 'medium',
    expectedLength: 'medium',
    tags: ['models', 'trade-offs', 'performance', 'quality'],
    difficulty: 'intermediate',
    expectedSources: 6,
    expectedLatency: '200-400ms',
    description: 'Analytical question about model selection trade-offs'
  },
  {
    id: 'analytical-3',
    category: 'analytical',
    title: 'Chunk Size Impact',
    prompt: 'Analyze the impact of chunk size on retrieval quality. How does chunk size affect precision, recall, and context preservation? What is the optimal chunk size for technical documentation?',
    complexity: 'complex',
    expectedLength: 'long',
    tags: ['chunking', 'optimization', 'quality', 'precision', 'recall'],
    difficulty: 'advanced',
    expectedSources: 7,
    expectedLatency: '400-800ms',
    description: 'Deep analytical question about chunking optimization'
  },
  {
    id: 'analytical-4',
    category: 'analytical',
    title: 'Hybrid Search Benefits',
    prompt: 'Why is hybrid search (combining vector and BM25) better than using either method alone? What are the specific benefits and when does it matter most?',
    complexity: 'medium',
    expectedLength: 'medium',
    tags: ['hybrid', 'search', 'vector', 'BM25', 'fusion'],
    difficulty: 'intermediate',
    expectedSources: 5,
    expectedLatency: '200-400ms',
    description: 'Analytical question about search strategy benefits'
  },
  {
    id: 'analytical-5',
    category: 'analytical',
    title: 'Context Window Optimization',
    prompt: 'How does context window size affect RAG system performance? Analyze the relationship between context size, model quality, latency, and cost. What is the optimal context window for different use cases?',
    complexity: 'complex',
    expectedLength: 'long',
    tags: ['context-window', 'optimization', 'performance', 'cost'],
    difficulty: 'advanced',
    expectedSources: 8,
    expectedLatency: '500-1000ms',
    description: 'Complex analysis of context window optimization'
  },

  // ============================================================================
  // MULTI-HOP QUERIES (4 prompts)
  // ============================================================================
  {
    id: 'multi-hop-1',
    category: 'multi-hop',
    title: 'Query Expansion Impact',
    prompt: 'How does query expansion improve recall, and what are the latency costs? Trace through the entire pipeline to show where query expansion fits and how it affects downstream components.',
    complexity: 'complex',
    expectedLength: 'long',
    tags: ['query-expansion', 'recall', 'latency', 'pipeline'],
    difficulty: 'advanced',
    expectedSources: 7,
    expectedLatency: '400-800ms',
    description: 'Multi-hop question requiring understanding of pipeline flow'
  },
  {
    id: 'multi-hop-2',
    category: 'multi-hop',
    title: 'Data Flow Trace',
    prompt: 'Trace the complete data flow from document upload to final RAG response. Include all services involved, data transformations, and decision points in the pipeline.',
    complexity: 'complex',
    expectedLength: 'long',
    tags: ['pipeline', 'data-flow', 'architecture', 'services'],
    difficulty: 'advanced',
    expectedSources: 10,
    expectedLatency: '600-1200ms',
    description: 'Complex multi-hop question requiring system architecture knowledge'
  },
  {
    id: 'multi-hop-3',
    category: 'multi-hop',
    title: 'Security & Quality Trade-off',
    prompt: 'What security measures are in place in this RAG system, and how do they affect response quality? Analyze the trade-offs between security guardrails and answer completeness.',
    complexity: 'complex',
    expectedLength: 'medium',
    tags: ['security', 'guardrails', 'quality', 'trade-offs'],
    difficulty: 'advanced',
    expectedSources: 6,
    expectedLatency: '300-600ms',
    description: 'Multi-hop question connecting security and quality'
  },
  {
    id: 'multi-hop-4',
    category: 'multi-hop',
    title: 'Knowledge Graph Integration',
    prompt: 'How does knowledge graph search enhance RAG retrieval? Explain how graph traversal finds related documents and improves multi-hop query answering.',
    complexity: 'complex',
    expectedLength: 'medium',
    tags: ['knowledge-graph', 'graph-search', 'multi-hop', 'retrieval'],
    difficulty: 'advanced',
    expectedSources: 6,
    expectedLatency: '300-600ms',
    description: 'Multi-hop question about graph-based retrieval'
  },

  // ============================================================================
  // TEMPORAL/RECENCY QUERIES (3 prompts)
  // ============================================================================
  {
    id: 'temporal-1',
    category: 'temporal',
    title: 'Latest RAG Developments',
    prompt: 'What are the latest developments in RAG architecture? Include recent research papers and industry best practices from the past year.',
    complexity: 'medium',
    expectedLength: 'medium',
    tags: ['RAG', 'research', 'recent', 'developments'],
    difficulty: 'intermediate',
    expectedSources: 8,
    expectedLatency: '400-800ms',
    description: 'Temporal query requiring recent information'
  },
  {
    id: 'temporal-2',
    category: 'temporal',
    title: 'Agentic Chunking Research',
    prompt: 'What recent research papers discuss agentic chunking? Summarize the key findings and how they improve upon traditional chunking methods.',
    complexity: 'medium',
    expectedLength: 'medium',
    tags: ['agentic-chunking', 'research', 'papers', 'recent'],
    difficulty: 'intermediate',
    expectedSources: 6,
    expectedLatency: '300-600ms',
    description: 'Temporal query about recent research'
  },
  {
    id: 'temporal-3',
    category: 'temporal',
    title: 'Current Best Practices',
    prompt: 'What are the current best practices for production RAG systems? Include recommendations for deployment, monitoring, and optimization based on recent industry experience.',
    complexity: 'complex',
    expectedLength: 'long',
    tags: ['production', 'best-practices', 'deployment', 'recent'],
    difficulty: 'advanced',
    expectedSources: 9,
    expectedLatency: '500-1000ms',
    description: 'Temporal query requiring up-to-date best practices'
  },

  // ============================================================================
  // CREATIVE/SYNTHESIS QUERIES (3 prompts)
  // ============================================================================
  {
    id: 'creative-1',
    category: 'creative',
    title: 'Design Customer Support RAG',
    prompt: 'Design an optimal RAG pipeline for a customer support chatbot. Consider response time requirements, accuracy needs, and cost constraints. Provide a step-by-step architecture with justification for each component choice.',
    complexity: 'complex',
    expectedLength: 'long',
    tags: ['design', 'architecture', 'customer-support', 'optimization'],
    difficulty: 'advanced',
    expectedSources: 10,
    expectedLatency: '600-1200ms',
    description: 'Creative design question requiring synthesis of multiple concepts'
  },
  {
    id: 'creative-2',
    category: 'creative',
    title: 'GPU Optimization Guide',
    prompt: 'How would you optimize this RAG system for a 16GB GPU? Provide specific recommendations for model selection, context window sizing, and feature toggles to maximize quality while staying within memory constraints.',
    complexity: 'complex',
    expectedLength: 'long',
    tags: ['optimization', 'GPU', 'memory', 'performance'],
    difficulty: 'advanced',
    expectedSources: 8,
    expectedLatency: '500-1000ms',
    description: 'Creative optimization question'
  },
  {
    id: 'creative-3',
    category: 'creative',
    title: 'RAG Quality Evaluation Guide',
    prompt: 'Create a comprehensive step-by-step guide for evaluating RAG quality. Include metrics to measure, test cases to run, and how to interpret results. Provide examples of good vs poor RAG responses.',
    complexity: 'complex',
    expectedLength: 'long',
    tags: ['evaluation', 'quality', 'metrics', 'testing', 'guide'],
    difficulty: 'advanced',
    expectedSources: 9,
    expectedLatency: '600-1200ms',
    description: 'Creative synthesis question requiring comprehensive guide creation'
  }
];

// Helper functions
export function getPromptsByCategory(category: PromptLibraryItem['category']): PromptLibraryItem[] {
  return PROMPT_LIBRARY.filter(p => p.category === category);
}

export function getPromptsByComplexity(complexity: PromptLibraryItem['complexity']): PromptLibraryItem[] {
  return PROMPT_LIBRARY.filter(p => p.complexity === complexity);
}

export function getPromptsByDifficulty(difficulty: PromptLibraryItem['difficulty']): PromptLibraryItem[] {
  return PROMPT_LIBRARY.filter(p => p.difficulty === difficulty);
}

export function searchPrompts(query: string): PromptLibraryItem[] {
  const lowerQuery = query.toLowerCase();
  return PROMPT_LIBRARY.filter(p =>
    p.title.toLowerCase().includes(lowerQuery) ||
    p.prompt.toLowerCase().includes(lowerQuery) ||
    p.tags.some(tag => tag.toLowerCase().includes(lowerQuery))
  );
}

export function getPromptById(id: string): PromptLibraryItem | undefined {
  return PROMPT_LIBRARY.find(p => p.id === id);
}

