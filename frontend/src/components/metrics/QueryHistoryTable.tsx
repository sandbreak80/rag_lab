import React, { useState } from 'react';
import { useMetricsStore } from '../../stores/metricsStore';
import { QueryMetric } from '../../types/metrics';
import { formatDate, formatDuration, formatNumber, truncate } from '../../utils/formatting';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Card, CardContent } from '../ui/card';
import { Eye } from 'lucide-react';

interface QueryHistoryTableProps {
  onViewDetails?: (metric: QueryMetric) => void;
}

export function QueryHistoryTable({ onViewDetails }: QueryHistoryTableProps) {
  const queries = useMetricsStore((state) => state.queries);
  const [sortBy, setSortBy] = useState<'timestamp' | 'latency'>('timestamp');

  const sortedQueries = [...queries].sort((a, b) => {
    if (sortBy === 'timestamp') {
      // Safely parse timestamps
      const timeA = new Date(a.timestamp).getTime();
      const timeB = new Date(b.timestamp).getTime();
      
      // Handle invalid dates
      if (isNaN(timeA) && isNaN(timeB)) return 0;
      if (isNaN(timeA)) return 1; // Push invalid dates to end
      if (isNaN(timeB)) return -1; // Push invalid dates to end
      
      return timeB - timeA;
    }
    return b.performance.total_latency_ms - a.performance.total_latency_ms;
  });

  if (queries.length === 0) {
    return (
      <Card>
        <CardContent className="p-12 text-center">
          <p className="text-muted-foreground">
            No queries yet. Start chatting to see metrics here!
          </p>
        </CardContent>
      </Card>
    );
  }

  const getFeatureBadges = (metric: QueryMetric) => {
    const features = [];
    if (metric.config.useQueryExpansion) features.push('Query Exp');
    if (metric.config.useBM25) features.push('BM25');
    if (metric.config.useHybrid) features.push('Hybrid');
    if (metric.config.useGraph) features.push('Graph');
    if (metric.config.useReranking) features.push('Rerank');
    if (metric.config.useWebSearch) features.push('Web');
    return features;
  };

  return (
    <div className="space-y-4">
      {/* Sort controls */}
      <div className="flex gap-2">
        <Button
          variant={sortBy === 'timestamp' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setSortBy('timestamp')}
        >
          Sort by Time
        </Button>
        <Button
          variant={sortBy === 'latency' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setSortBy('latency')}
        >
          Sort by Latency
        </Button>
      </div>

      {/* Table */}
      <div className="space-y-2">
        {sortedQueries.map((metric, index) => {
          const features = getFeatureBadges(metric);
          return (
            <Card key={metric.id}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    {/* Query */}
                    <p className="font-medium mb-2">
                      {truncate(metric.query, 100)}
                    </p>

                    {/* Metadata */}
                    <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
                      <span>{formatDate(metric.timestamp)}</span>
                      <span>•</span>
                      <span>{formatDuration(metric.performance.total_latency_ms)}</span>
                      <span>•</span>
                      <span>{metric.results.total_results} results</span>
                      <span>•</span>
                      <span>{formatNumber(metric.tokens.total_tokens)} tokens</span>
                      <span>•</span>
                      <span className="font-medium">{metric.config.model}</span>
                    </div>

                    {/* Features */}
                    {features.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {features.map((feature) => (
                          <Badge key={feature} variant="secondary">
                            {feature}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* View button */}
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => onViewDetails?.(metric)}
                  >
                    <Eye className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}

