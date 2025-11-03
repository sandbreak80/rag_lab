import React, { useState } from 'react';
import { useMetricsStore } from '../../stores/metricsStore';
import { QueryMetric } from '../../types/metrics';
import { MetricsOverview } from './MetricsOverview';
import { QueryHistoryTable } from './QueryHistoryTable';
import { WaterfallChart } from './WaterfallChart';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Download, Trash2, X } from 'lucide-react';
import { formatDuration, formatDate } from '../../utils/formatting';

export function MetricsPage() {
  const clearMetrics = useMetricsStore((state) => state.clearMetrics);
  const exportCSV = useMetricsStore((state) => state.exportCSV);
  const [selectedMetric, setSelectedMetric] = useState<QueryMetric | null>(null);

  const handleExport = () => {
    const csv = exportCSV();
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `rag-metrics-${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleClear = () => {
    if (confirm('Are you sure you want to clear all metrics?')) {
      clearMetrics();
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2">📊 Performance Metrics</h1>
          <p className="text-muted-foreground">
            Track and analyze RAG pipeline performance
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleExport}>
            <Download className="h-4 w-4 mr-2" />
            Export CSV
          </Button>
          <Button variant="outline" onClick={handleClear}>
            <Trash2 className="h-4 w-4 mr-2" />
            Clear
          </Button>
        </div>
      </div>

      {/* Overview Cards */}
      <MetricsOverview />

      {/* Query History */}
      <Card>
        <CardHeader>
          <CardTitle>Query History</CardTitle>
          <CardDescription>
            All queries with configuration and performance metrics
          </CardDescription>
        </CardHeader>
        <CardContent>
          <QueryHistoryTable onViewDetails={setSelectedMetric} />
        </CardContent>
      </Card>

      {/* Detail Modal */}
      {selectedMetric && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle>Query Details</CardTitle>
                  <CardDescription>
                    {formatDate(selectedMetric.timestamp)}
                  </CardDescription>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setSelectedMetric(null)}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Query */}
              <div>
                <h4 className="text-sm font-medium mb-2">Query</h4>
                <p className="text-sm bg-muted p-3 rounded">{selectedMetric.query}</p>
              </div>

              {/* Configuration */}
              <div>
                <h4 className="text-sm font-medium mb-2">Configuration</h4>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="bg-muted p-2 rounded">
                    <span className="text-muted-foreground">Model:</span>{' '}
                    <span className="font-medium">{selectedMetric.config.model}</span>
                  </div>
                  <div className="bg-muted p-2 rounded">
                    <span className="text-muted-foreground">Temperature:</span>{' '}
                    <span className="font-medium">{selectedMetric.config.temperature}</span>
                  </div>
                  <div className="bg-muted p-2 rounded">
                    <span className="text-muted-foreground">Top-K:</span>{' '}
                    <span className="font-medium">{selectedMetric.config.topK}</span>
                  </div>
                  <div className="bg-muted p-2 rounded">
                    <span className="text-muted-foreground">Total Time:</span>{' '}
                    <span className="font-medium">
                      {formatDuration(selectedMetric.performance.total_latency_ms)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Performance Breakdown */}
              <div>
                <h4 className="text-sm font-medium mb-4">Performance Breakdown</h4>
                <WaterfallChart metrics={selectedMetric.performance} />
              </div>

              {/* Results & Tokens */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="text-sm font-medium mb-2">Results</h4>
                  <p className="text-2xl font-bold">{selectedMetric.results.total_results}</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium mb-2">Total Tokens</h4>
                  <p className="text-2xl font-bold">{selectedMetric.tokens.total_tokens}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
