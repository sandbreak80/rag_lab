import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { RAGConfig } from '../../../types/config';

interface MetricsComparisonTableProps {
  metricsA: any;
  metricsB: any;
  configA: RAGConfig | null;
  configB: RAGConfig | null;
}

export function MetricsComparisonTable({
  metricsA,
  metricsB,
  configA,
  configB
}: MetricsComparisonTableProps) {
  if (!metricsA || !metricsB) return null;

  const getMetricValue = (metrics: any, key: string): number | string => {
    return metrics[key] ?? metrics[key.replace(/_/g, '.')] ?? 'N/A';
  };

  const formatValue = (value: any): string => {
    if (typeof value === 'number') {
      if (value > 1000) return `${(value / 1000).toFixed(1)}k`;
      return value.toFixed(2);
    }
    return String(value);
  };

  const getWinner = (valA: number, valB: number, higherIsBetter: boolean = true): string => {
    if (typeof valA !== 'number' || typeof valB !== 'number') return '';
    if (Math.abs(valA - valB) < 0.01) return 'tie';
    const aWins = higherIsBetter ? valA > valB : valA < valB;
    return aWins ? 'A' : 'B';
  };

  const metrics = [
    { key: 'latency_ms', label: 'Total Latency (ms)', higherIsBetter: false },
    { key: 'tokens_in', label: 'Tokens In', higherIsBetter: false },
    { key: 'tokens_out', label: 'Tokens Out', higherIsBetter: false },
    { key: 'total_tokens', label: 'Total Tokens', higherIsBetter: false },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Metrics Comparison</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left p-2">Metric</th>
                <th className="text-right p-2">Configuration A</th>
                <th className="text-right p-2">Configuration B</th>
                <th className="text-center p-2">Winner</th>
              </tr>
            </thead>
            <tbody>
              {metrics.map((metric) => {
                const valA = getMetricValue(metricsA, metric.key);
                const valB = getMetricValue(metricsB, metric.key);
                const winner = typeof valA === 'number' && typeof valB === 'number'
                  ? getWinner(valA, valB, metric.higherIsBetter)
                  : '';

                return (
                  <tr key={metric.key} className="border-b">
                    <td className="p-2">{metric.label}</td>
                    <td className="text-right p-2">{formatValue(valA)}</td>
                    <td className="text-right p-2">{formatValue(valB)}</td>
                    <td className="text-center p-2">
                      {winner && (
                        <span className={`px-2 py-1 rounded text-xs ${
                          winner === 'A' ? 'bg-green-100 text-green-800' :
                          winner === 'B' ? 'bg-blue-100 text-blue-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {winner === 'tie' ? 'Tie' : `Winner: ${winner}`}
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}

