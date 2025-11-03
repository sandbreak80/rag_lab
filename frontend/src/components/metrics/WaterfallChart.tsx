import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';

interface PerformanceMetrics {
  query_expansion_ms?: number;
  vector_search_ms?: number;
  bm25_search_ms?: number;
  hybrid_fusion_ms?: number;
  graph_expansion_ms?: number;
  reranking_ms?: number;
  web_search_ms?: number;
  llm_generation_ms?: number;
  total_latency_ms?: number;
}

interface WaterfallChartProps {
  metrics: PerformanceMetrics;
  compact?: boolean;
}

// Color palette for each RAG component
const COLORS = {
  'Query Expansion': '#10b981', // green
  'Vector Search': '#3b82f6', // blue
  'BM25 Search': '#8b5cf6', // purple
  'Hybrid Fusion': '#f59e0b', // amber
  'Graph Expansion': '#ec4899', // pink
  'Re-ranking': '#ef4444', // red
  'Web Search': '#06b6d4', // cyan
  'LLM Generation': '#6366f1', // indigo
};

export function WaterfallChart({ metrics, compact = false }: WaterfallChartProps) {
  // Transform metrics into chart data
  const data = [
    {
      name: 'Query Expansion',
      time: metrics.query_expansion_ms || 0,
      enabled: (metrics.query_expansion_ms || 0) > 0,
    },
    {
      name: 'Vector Search',
      time: metrics.vector_search_ms || 0,
      enabled: (metrics.vector_search_ms || 0) > 0,
    },
    {
      name: 'BM25 Search',
      time: metrics.bm25_search_ms || 0,
      enabled: (metrics.bm25_search_ms || 0) > 0,
    },
    {
      name: 'Hybrid Fusion',
      time: metrics.hybrid_fusion_ms || 0,
      enabled: (metrics.hybrid_fusion_ms || 0) > 0,
    },
    {
      name: 'Graph Expansion',
      time: metrics.graph_expansion_ms || 0,
      enabled: (metrics.graph_expansion_ms || 0) > 0,
    },
    {
      name: 'Re-ranking',
      time: metrics.reranking_ms || 0,
      enabled: (metrics.reranking_ms || 0) > 0,
    },
    {
      name: 'Web Search',
      time: metrics.web_search_ms || 0,
      enabled: (metrics.web_search_ms || 0) > 0,
    },
    {
      name: 'LLM Generation',
      time: metrics.llm_generation_ms || 0,
      enabled: (metrics.llm_generation_ms || 0) > 0,
    },
  ].filter(item => item.enabled); // Only show enabled features

  const totalTime = metrics.total_latency_ms || data.reduce((sum, item) => sum + item.time, 0);

  // Format time for display
  const formatTime = (ms: number) => {
    if (ms < 1000) return `${ms.toFixed(0)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      const percentage = totalTime > 0 ? ((data.time / totalTime) * 100).toFixed(1) : '0.0';
      return (
        <div className="bg-card border rounded-lg shadow-lg p-3">
          <p className="font-semibold">{data.name}</p>
          <p className="text-sm text-muted-foreground">
            Time: <span className="text-foreground font-medium">{formatTime(data.time)}</span>
          </p>
          <p className="text-sm text-muted-foreground">
            Percentage: <span className="text-foreground font-medium">{percentage}%</span>
          </p>
        </div>
      );
    }
    return null;
  };

  if (data.length === 0) {
    return (
      <div className="text-center text-muted-foreground py-8">
        No performance data available
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {!compact && (
        <div className="text-sm text-muted-foreground">
          Total Response Time: <span className="text-foreground font-semibold">{formatTime(totalTime)}</span>
        </div>
      )}
      
      <ResponsiveContainer width="100%" height={compact ? 200 : 300}>
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 120, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
          <XAxis
            type="number"
            tickFormatter={formatTime}
            label={!compact ? { value: 'Time', position: 'insideBottom', offset: -5 } : undefined}
          />
          <YAxis type="category" dataKey="name" width={110} />
          <Tooltip content={<CustomTooltip />} />
          {!compact && <Legend />}
          <Bar dataKey="time" name="Time (ms)" radius={[0, 4, 4, 0]}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[entry.name as keyof typeof COLORS] || '#888'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {!compact && (
        <div className="grid grid-cols-2 gap-2 mt-4 text-xs">
          {data.map((item) => (
            <div key={item.name} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded"
                style={{ backgroundColor: COLORS[item.name as keyof typeof COLORS] || '#888' }}
              />
              <span className="text-muted-foreground">{item.name}:</span>
              <span className="font-medium">{formatTime(item.time)}</span>
              <span className="text-muted-foreground">
                ({totalTime > 0 ? ((item.time / totalTime) * 100).toFixed(1) : '0'}%)
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

