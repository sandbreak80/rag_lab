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

  const height = compact ? 300 : 400;
  const showLegend = !compact;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">⏱️ Performance Waterfall</h3>
        <div className="text-sm text-muted-foreground">
          Total: <span className="font-bold text-foreground font-mono">
            {(metrics.total_latency_ms / 1000).toFixed(2)}s
          </span>
          {' '}({data.length} stages)
        </div>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={height}>
        <BarChart
          data={data}
          layout="horizontal"
          margin={{ top: 5, right: 30, left: 10, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.2} />
          <XAxis
            type="number"
            label={{ value: 'Time (ms)', position: 'insideBottom', offset: -5 }}
            stroke="#9ca3af"
          />
          <YAxis
            type="category"
            dataKey="name"
            width={150}
            stroke="#9ca3af"
            style={{ fontSize: '12px' }}
          />
          <Tooltip
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
                      <p className="text-muted-foreground">
                        Start: <span className="font-mono text-foreground">
                          {(item.start || 0).toFixed(0)}ms
                        </span>
                      </p>
                      <p className="text-muted-foreground">
                        End: <span className="font-mono text-foreground">
                          {((item.start || 0) + (item.duration || 0)).toFixed(0)}ms
                        </span>
                      </p>
                    </div>
                  </div>
                );
              }
              return null;
            }}
          />
          <Bar dataKey="duration" radius={[0, 4, 4, 0]}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[entry.name]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Stage Breakdown */}
      {showLegend && (
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-muted-foreground">Stage Breakdown</h4>
          <div className="grid grid-cols-2 gap-2">
            {data.map((stage, idx) => (
              <div key={idx} className="flex items-center gap-2 text-xs">
                <div
                  className="w-3 h-3 rounded-sm flex-shrink-0"
                  style={{ backgroundColor: COLORS[stage.name] }}
                />
                <span className="text-muted-foreground truncate">{stage.name}:</span>
                <span className="font-mono font-semibold ml-auto">
                  {(stage.duration || 0).toFixed(0)}ms
                </span>
                <span className="text-muted-foreground">({stage.percentage || '0%'})</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Category Summaries */}
      {showLegend && (
        <div className="pt-2 border-t border-border">
          <div className="grid grid-cols-4 gap-4 text-xs">
            {['security', 'enhancement', 'search', 'generation'].map(category => {
              const categoryStages = data.filter(s => s.category === category);
              const categoryTotal = categoryStages.reduce((sum, s) => sum + (s.duration || 0), 0);
              const categoryPct = metrics.total_latency_ms ? ((categoryTotal / metrics.total_latency_ms) * 100).toFixed(1) : '0';

              if (categoryTotal === 0) return null;

              const categoryLabels: Record<string, string> = {
                security: '🔒 Security',
                enhancement: '✨ Enhancement',
                search: '🔍 Search',
                generation: '🤖 Generation',
              };

              return (
                <div key={category} className="space-y-1">
                  <p className="font-semibold text-muted-foreground">
                    {categoryLabels[category]}
                  </p>
                  <p className="font-mono font-bold">
                    {categoryTotal.toFixed(0)}ms
                  </p>
                  <p className="text-muted-foreground">
                    {categoryPct}% of total
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
