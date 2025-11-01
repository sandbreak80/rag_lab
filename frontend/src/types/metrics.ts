import { RAGConfig } from './config';

// Query Metrics
export interface QueryMetric {
  id: string;
  timestamp: Date;
  query: string;
  config: RAGConfig;
  results: {
    total_results: number;
    sources_count: number;
  };
  performance: {
    total_latency_ms: number;
    query_expansion_ms?: number;
    vector_search_ms?: number;
    bm25_search_ms?: number;
    hybrid_fusion_ms?: number;
    graph_expansion_ms?: number;
    reranking_ms?: number;
    web_search_ms?: number;
    llm_generation_ms?: number;
  };
  tokens: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  quality?: {
    precision?: number;
    recall?: number;
    ndcg?: number;
    mrr?: number;
  };
}

// Aggregated Metrics
export interface MetricsSummary {
  total_queries: number;
  avg_latency_ms: number;
  avg_token_count: number;
  avg_results_count: number;
  feature_usage: {
    [feature: string]: number;
  };
  model_usage: {
    [model: string]: number;
  };
}

