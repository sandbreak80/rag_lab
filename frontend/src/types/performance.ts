// Performance Metrics Types
// Single source of truth for all performance-related metrics

/**
 * Performance metrics for RAG pipeline execution
 * Includes timing for all components: search, LLM, and service overhead
 */
export interface PerformanceMetrics {
  // Search Service Components
  query_expansion_ms?: number;
  vector_search_ms?: number;
  bm25_search_ms?: number;
  hybrid_fusion_ms?: number;
  graph_expansion_ms?: number;
  reranking_ms?: number;
  web_search_ms?: number;

  // LLM Components (from Ollama)
  llm_generation_ms?: number;
  llm_prompt_eval_duration_ms?: number;  // Time to process prompt
  llm_eval_duration_ms?: number;         // Time to generate tokens
  llm_tokens_generated?: number;
  llm_tokens_prompt?: number;
  llm_tokens_per_second?: number;

  // Service Latencies
  search_service_latency_ms?: number;
  chat_service_overhead_ms?: number;

  // Total
  total_latency_ms?: number;
}

