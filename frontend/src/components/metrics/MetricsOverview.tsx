import React, { useMemo } from 'react';
import { useMetricsStore } from '../../stores/metricsStore';
import { useConfigStore } from '../../stores/configStore';
import { Card, CardContent } from '../ui/card';
import { formatNumber, formatDuration } from '../../utils/formatting';
import { Activity, Clock, Hash, Zap, DollarSign } from 'lucide-react';
import { estimateTokenCost, formatCost } from '../../utils/tokenCost';

export function MetricsOverview() {
  const queries = useMetricsStore((state) => state.queries);
  const model = useConfigStore((state) => state.model);

  // Compute summary directly from queries - don't call getSummary()
  const summary = useMemo(() => {
    if (queries.length === 0) {
      return {
        total_queries: 0,
        avg_latency_ms: 0,
        avg_token_count: 0,
        avg_results_count: 0,
        total_cost_usd: 0,
      };
    }

    const totalLatency = queries.reduce((sum, q) => sum + q.performance.total_latency_ms, 0);
    const totalTokens = queries.reduce((sum, q) => sum + q.tokens.total_tokens, 0);
    const totalResults = queries.reduce((sum, q) => sum + q.results.total_results, 0);

    // Calculate total cost across all queries
    const totalCost = queries.reduce((sum, q) => {
      const cost = estimateTokenCost(
        q.tokens.prompt_tokens,
        q.tokens.completion_tokens,
        q.config.model
      );
      return sum + cost.estimated_cost_usd;
    }, 0);

    return {
      total_queries: queries.length,
      avg_latency_ms: totalLatency / queries.length,
      avg_token_count: totalTokens / queries.length,
      avg_results_count: totalResults / queries.length,
      total_cost_usd: totalCost,
    };
  }, [queries]);

  const metrics = [
    {
      icon: Hash,
      label: 'Total Queries',
      value: formatNumber(summary.total_queries),
      color: 'text-blue-500',
    },
    {
      icon: Clock,
      label: 'Avg Latency',
      value: formatDuration(summary.avg_latency_ms),
      color: 'text-green-500',
    },
    {
      icon: Activity,
      label: 'Avg Results',
      value: formatNumber(summary.avg_results_count, 1),
      color: 'text-purple-500',
    },
    {
      icon: Zap,
      label: 'Avg Tokens',
      value: formatNumber(summary.avg_token_count),
      color: 'text-orange-500',
    },
    {
      icon: DollarSign,
      label: 'Estimated Cost',
      value: formatCost(summary.total_cost_usd),
      color: 'text-yellow-500',
      subtitle: model.includes('llama') || model.includes('mistral') ? 'Free (Ollama)' : 'API calls',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4" data-testid="metrics-panel">
      {metrics.map((metric, index) => {
        const Icon = metric.icon;
        const testId = metric.label.toLowerCase().replace(/\s+/g, '-');
        return (
          <Card key={index} data-testid={`metrics-${testId}`}>
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className={`${metric.color}`}>
                  <Icon className="h-8 w-8" />
                </div>
                <div className="flex-1">
                  <p className="text-sm text-muted-foreground">{metric.label}</p>
                  <p className="text-2xl font-bold" data-testid={`metrics-${testId}-value`}>{metric.value}</p>
                  {metric.subtitle && (
                    <p className="text-xs text-muted-foreground mt-1">{metric.subtitle}</p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

