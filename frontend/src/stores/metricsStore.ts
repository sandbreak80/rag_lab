import { create } from 'zustand';
import { QueryMetric, MetricsSummary } from '../types/metrics';
import { saveToLocalStorage, loadFromLocalStorage } from '../utils/localStorage';

interface MetricsStore {
  queries: QueryMetric[];
  
  // Actions
  addQuery: (metric: QueryMetric) => void;
  clearMetrics: () => void;
  getSummary: () => MetricsSummary;
  exportCSV: () => string;
}

export const useMetricsStore = create<MetricsStore>((set, get) => {
  // Load initial metrics from localStorage
  const savedQueries = loadFromLocalStorage<QueryMetric[]>('query_metrics', []);

  return {
    queries: savedQueries,

    addQuery: (metric) => {
      const queries = [...get().queries, metric];
      set({ queries });
      saveToLocalStorage('query_metrics', queries);
    },

    clearMetrics: () => {
      set({ queries: [] });
      saveToLocalStorage('query_metrics', []);
    },

    getSummary: () => {
      const queries = get().queries;
      
      if (queries.length === 0) {
        return {
          total_queries: 0,
          avg_latency_ms: 0,
          avg_token_count: 0,
          avg_results_count: 0,
          feature_usage: {},
          model_usage: {},
        };
      }

      const totalLatency = queries.reduce((sum, q) => sum + q.performance.total_latency_ms, 0);
      const totalTokens = queries.reduce((sum, q) => sum + q.tokens.total_tokens, 0);
      const totalResults = queries.reduce((sum, q) => sum + q.results.total_results, 0);

      const featureUsage: { [key: string]: number } = {};
      const modelUsage: { [key: string]: number } = {};

      queries.forEach((query) => {
        // Count feature usage
        if (query.config.useQueryExpansion) featureUsage['Query Expansion'] = (featureUsage['Query Expansion'] || 0) + 1;
        if (query.config.useBM25) featureUsage['BM25'] = (featureUsage['BM25'] || 0) + 1;
        if (query.config.useHybrid) featureUsage['Hybrid Search'] = (featureUsage['Hybrid Search'] || 0) + 1;
        if (query.config.useGraph) featureUsage['Knowledge Graph'] = (featureUsage['Knowledge Graph'] || 0) + 1;
        if (query.config.useReranking) featureUsage['Reranking'] = (featureUsage['Reranking'] || 0) + 1;
        if (query.config.useWebSearch) featureUsage['Web Search'] = (featureUsage['Web Search'] || 0) + 1;
        if (query.config.useAgenticChunking) featureUsage['Agentic Chunking'] = (featureUsage['Agentic Chunking'] || 0) + 1;

        // Count model usage
        modelUsage[query.config.model] = (modelUsage[query.config.model] || 0) + 1;
      });

      return {
        total_queries: queries.length,
        avg_latency_ms: totalLatency / queries.length,
        avg_token_count: totalTokens / queries.length,
        avg_results_count: totalResults / queries.length,
        feature_usage: featureUsage,
        model_usage: modelUsage,
      };
    },

    exportCSV: () => {
      const queries = get().queries;
      
      const headers = [
        'Timestamp',
        'Query',
        'Model',
        'Temperature',
        'Top-K',
        'Total Latency (ms)',
        'Results',
        'Total Tokens',
        'Query Expansion',
        'BM25',
        'Hybrid',
        'Knowledge Graph',
        'Reranking',
        'Web Search',
      ];

      const rows = queries.map((q) => [
        new Date(q.timestamp).toISOString(),
        `"${q.query.replace(/"/g, '""')}"`,
        q.config.model,
        q.config.temperature,
        q.config.topK,
        q.performance.total_latency_ms,
        q.results.total_results,
        q.tokens.total_tokens,
        q.config.useQueryExpansion ? 'Yes' : 'No',
        q.config.useBM25 ? 'Yes' : 'No',
        q.config.useHybrid ? 'Yes' : 'No',
        q.config.useGraph ? 'Yes' : 'No',
        q.config.useReranking ? 'Yes' : 'No',
        q.config.useWebSearch ? 'Yes' : 'No',
      ]);

      const csv = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
      return csv;
    },
  };
});

