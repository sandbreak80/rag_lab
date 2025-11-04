import { RAGConfig } from './config';
import { PerformanceMetrics } from './performance';

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
  performance: PerformanceMetrics & {
    total_latency_ms: number;  // Required for QueryMetric
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

