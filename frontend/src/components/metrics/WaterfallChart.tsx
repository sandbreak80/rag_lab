import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, ResponsiveContainer } from 'recharts';
import { PerformanceMetrics } from '../../types/performance';

interface WaterfallChartProps {
  metrics: PerformanceMetrics;
  compact?: boolean;
}

interface ChartDataPoint {
  name: string;
  start: number;
  duration: number;
  percentage: string;
  category: string;
}

const COLORS: Record<string, string> = {
  'Security Validation': '#10b981',      // green-600
  'Prompt Enhancement': '#16a34a',      // green-600
  'Model Routing': '#f97316',           // orange-500
  'Query Decomposition': '#a855f7',     // purple-500
  'Query Expansion': '#eab308',         // yellow-500
  'Vector Search': '#ef4444',           // red-500
  'BM25 Search': '#ec4899',             // pink-500
  'Hybrid Fusion': '#06b6d4',           // cyan-500
  'Knowledge Graph': '#84cc16',         // lime-500
  'Re-ranking': '#f59e0b',              // amber-500
  'Web Search': '#dc2626',              // red-600
  'LLM Generation': '#6366f1',           // indigo-500
};

const STAGE_CATEGORIES: Record<string, string> = {
  'Security Validation': 'security',
  'Prompt Enhancement': 'enhancement',
  'Model Routing': 'routing',
  'Query Decomposition': 'decomposition',
  'Query Expansion': 'search',
  'Vector Search': 'search',
  'BM25 Search': 'search',
  'Hybrid Fusion': 'search',
  'Knowledge Graph': 'search',
  'Re-ranking': 'search',
  'Web Search': 'search',
  'LLM Generation': 'generation',
};

export function WaterfallChart({ metrics, compact = false }: WaterfallChartProps) {
  // Safety check
  if (!metrics || !metrics.total_latency_ms) {
    return (
      <div className="p-4 text-center text-muted-foreground">
        No timing data available
      </div>
    );
  }

  // Build data array with cumulative timing
  const data: ChartDataPoint[] = [];
  let cumulative = 0;

  const stages = [
    { name: 'Security Validation', ms: metrics.security_validation_ms },
    { name: 'Prompt Enhancement', ms: metrics.prompt_enhancement_ms },
    { name: 'Model Routing', ms: metrics.model_routing_ms },
    { name: 'Query Decomposition', ms: metrics.query_decomposition_ms },
    { name: 'Query Expansion', ms: metrics.query_expansion_ms },
    { name: 'Vector Search', ms: metrics.vector_search_ms },
    { name: 'BM25 Search', ms: metrics.bm25_search_ms },
    { name: 'Hybrid Fusion', ms: metrics.hybrid_fusion_ms },
    { name: 'Knowledge Graph', ms: metrics.graph_expansion_ms },
    { name: 'Re-ranking', ms: metrics.reranking_ms },
    { name: 'Web Search', ms: metrics.web_search_ms },
    { name: 'LLM Generation', ms: metrics.llm_generation_ms },
  ];

  stages.forEach(stage => {
    if (stage.ms && stage.ms > 0) {
      const percentage = ((stage.ms / metrics.total_latency_ms!) * 100).toFixed(1);
      data.push({
        name: stage.name,
        start: cumulative,
        duration: stage.ms,
        percentage: `${percentage}%`,
        category: STAGE_CATEGORIES[stage.name] || 'other',
      });
      cumulative += stage.ms;
    }
  });

  if (data.length === 0) {
    return (
      <div className="p-4 text-center text-muted-foreground">
        No timing data available
      </div>
    );
  }

  // Calculate max value for chart scale with 10% padding
  const maxValue = Math.max(...data.map(d => d.start + d.duration)) * 1.1;

  const height = compact ? 180 : 250;
  const showLegend = !compact;

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h3 className="text-sm font-semibold">⏱️ Performance Breakdown</h3>
        <div className="text-xs text-muted-foreground">
          Total: <span className="font-bold text-foreground font-mono">
            {(metrics.total_latency_ms / 1000).toFixed(2)}s
          </span>
          {' '}({data.length} stages)
        </div>
      </div>

      {/* Chart - Simple Duration Bars */}
      <ResponsiveContainer width="100%" height={height}>
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 10, right: 30, left: 120, bottom: 20 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.1} />
          <XAxis
            type="number"
            domain={[0, 'dataMax']}
            label={{ value: 'Duration (ms)', position: 'insideBottom', offset: -10, style: { fontSize: '11px', fill: '#9ca3af' } }}
            stroke="#9ca3af"
            tick={{ fontSize: 10 }}
          />
          <YAxis
            type="category"
            dataKey="name"
            width={115}
            stroke="#9ca3af"
            tick={{ fontSize: 10 }}
          />
          <Tooltip
            cursor={{ fill: 'rgba(255, 255, 255, 0.05)' }}
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const item = payload[0].payload as ChartDataPoint;
                if (!item || !item.duration) return null;

                return (
                  <div className="bg-card border border-border rounded-lg p-3 shadow-xl">
                    <p className="font-semibold text-sm mb-1">{item.name}</p>
                    <div className="space-y-1 text-xs">
                      <p className="text-muted-foreground">
                        Duration: <span className="font-mono text-foreground font-semibold">
                          {(item.duration || 0).toFixed(0)}ms
                        </span>
                      </p>
                      <p className="text-muted-foreground">
                        Percentage: <span className="text-foreground font-semibold">
                          {item.percentage || '0%'}
                        </span>
                      </p>
                    </div>
                  </div>
                );
              }
              return null;
            }}
          />
          {/* Simple bars showing duration only */}
          <Bar
            dataKey="duration"
            radius={[0, 4, 4, 0]}
            minPointSize={2}
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[entry.name]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Compact Stage List */}
      {showLegend && (
        <div className="border-t border-border pt-2">
          <div className="grid grid-cols-3 gap-x-3 gap-y-1 text-xs">
            {data.map((stage, idx) => (
              <div key={idx} className="flex items-center gap-1.5">
                <div
                  className="w-2 h-2 rounded-sm flex-shrink-0"
                  style={{ backgroundColor: COLORS[stage.name] }}
                />
                <span className="text-muted-foreground truncate text-[10px]">{stage.name}</span>
                <span className="font-mono font-semibold ml-auto text-[10px]">
                  {(stage.duration || 0).toFixed(0)}ms
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
