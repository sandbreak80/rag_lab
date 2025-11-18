import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { RAGConfig } from '@/types/config';

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
    // Handle nested keys like 'ollama.total_duration_ms'
    if (key.includes('.')) {
      const parts = key.split('.');
      let value = metrics;
      for (const part of parts) {
        if (value && typeof value === 'object') {
          value = value[part];
        } else {
          return 'N/A';
        }
      }
      return value ?? 'N/A';
    }
    return metrics[key] ?? metrics[key.replace(/_/g, '.')] ?? 'N/A';
  };

  const formatValue = (value: any, metricKey?: string): string => {
    if (value === null || value === undefined) {
      // For timing metrics, show "Disabled" instead of "N/A" to indicate feature was off
      if (metricKey && (metricKey.includes('_ms') || metricKey.includes('Timing'))) {
        return 'Disabled';
      }
      return 'N/A';
    }
    if (typeof value === 'number') {
      if (value === 0) return '0.00';  // Show 0.00 instead of just 0
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
    // Prompt size metrics (critical for context window validation)
    { key: 'stage_timings.prompt_size.prompt_tokens_estimated', label: 'Prompt Tokens (Estimated)', higherIsBetter: false, nested: true },
    { key: 'stage_timings.prompt_size.system_prompt_tokens', label: 'System Prompt Tokens', higherIsBetter: false, nested: true },
    { key: 'stage_timings.prompt_size.retrieved_docs_tokens', label: 'Retrieved Docs Tokens', higherIsBetter: false, nested: true },
    { key: 'stage_timings.prompt_size.retrieved_docs_count', label: 'Retrieved Docs Count', higherIsBetter: false, nested: true },
    { key: 'stage_timings.prompt_size.context_window', label: 'Context Window', higherIsBetter: true, nested: true },
    { key: 'stage_timings.prompt_size.max_tokens', label: 'Max Tokens', higherIsBetter: true, nested: true },
    { key: 'stage_timings.prompt_size.available_for_response', label: 'Available for Response', higherIsBetter: true, nested: true },
    { key: 'stage_timings.prompt_size.prompt_utilization_pct', label: 'Prompt Utilization (%)', higherIsBetter: false, nested: true },
    // Service timings
    { key: 'stage_timings.acl_ms', label: 'ACL/Authorization (ms)', higherIsBetter: false, nested: true },
    { key: 'stage_timings.embedding_ms', label: 'Embedding Generation (ms)', higherIsBetter: false, nested: true },
    { key: 'stage_timings.vector_db_ms', label: 'Vector DB Search (ms)', higherIsBetter: false, nested: true },
    { key: 'stage_timings.vector_ms', label: 'Vector Search Total (ms)', higherIsBetter: false, nested: true },
    { key: 'stage_timings.web_ms', label: 'Web Search (ms)', higherIsBetter: false, nested: true },
    { key: 'stage_timings.kg_ms', label: 'Knowledge Graph (ms)', higherIsBetter: false, nested: true },
    { key: 'stage_timings.query_expansion_ms', label: 'Query Expansion (ms)', higherIsBetter: false, nested: true },
    { key: 'stage_timings.bm25_ms', label: 'BM25 Search (ms)', higherIsBetter: false, nested: true },
    { key: 'stage_timings.hybrid_fusion_ms', label: 'Hybrid Fusion (ms)', higherIsBetter: false, nested: true },
    { key: 'stage_timings.recency_gate_ms', label: 'Recency Gate (ms)', higherIsBetter: false, nested: true },
    { key: 'stage_timings.rerank_ms', label: 'Reranking (ms)', higherIsBetter: false, nested: true },
    { key: 'stage_timings.llm_ms', label: 'LLM Generation (ms)', higherIsBetter: false, nested: true },
    { key: 'stage_timings.guardrails_ms', label: 'Security Guardrails (ms)', higherIsBetter: false, nested: true },
    // Ollama verbose metrics
    { key: 'ollama.total_duration_ms', label: 'Ollama: Total Duration (ms)', higherIsBetter: false, nested: true },
    { key: 'ollama.load_duration_ms', label: 'Ollama: Load Duration (ms)', higherIsBetter: false, nested: true },
    { key: 'ollama.prompt_eval_duration_ms', label: 'Ollama: Prompt Eval Duration (ms)', higherIsBetter: false, nested: true },
    { key: 'ollama.prompt_eval_rate', label: 'Ollama: Prompt Eval Rate (tok/s)', higherIsBetter: true, nested: true },
    { key: 'ollama.eval_duration_ms', label: 'Ollama: Eval Duration (ms)', higherIsBetter: false, nested: true },
    { key: 'ollama.eval_rate', label: 'Ollama: Eval Rate (tok/s)', higherIsBetter: true, nested: true },
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

                // Check for prompt size warnings
                const isPromptSizeMetric = metric.key.includes('prompt_size');
                const promptSizeA = metricsA?.stage_timings?.prompt_size;
                const promptSizeB = metricsB?.stage_timings?.prompt_size;
                
                // Show warning if prompt doesn't fit
                let warningA = '';
                let warningB = '';
                if (isPromptSizeMetric && metric.key.includes('prompt_utilization_pct')) {
                  if (promptSizeA && !promptSizeA.prompt_fits) {
                    warningA = ' ⚠️ Exceeds context window!';
                  } else if (promptSizeA && promptSizeA.prompt_utilization_pct > 90) {
                    warningA = ' ⚠️ >90%';
                  } else if (promptSizeA && promptSizeA.prompt_utilization_pct > 80) {
                    warningA = ' ⚠️ >80%';
                  }
                  if (promptSizeB && !promptSizeB.prompt_fits) {
                    warningB = ' ⚠️ Exceeds context window!';
                  } else if (promptSizeB && promptSizeB.prompt_utilization_pct > 90) {
                    warningB = ' ⚠️ >90%';
                  } else if (promptSizeB && promptSizeB.prompt_utilization_pct > 80) {
                    warningB = ' ⚠️ >80%';
                  }
                }

                return (
                  <tr key={metric.key} className="border-b">
                    <td className="p-2">{metric.label}</td>
                    <td className="text-right p-2">
                      {formatValue(valA, metric.key)}
                      {warningA && <span className="text-orange-600 text-xs ml-1">{warningA}</span>}
                    </td>
                    <td className="text-right p-2">
                      {formatValue(valB, metric.key)}
                      {warningB && <span className="text-orange-600 text-xs ml-1">{warningB}</span>}
                    </td>
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

