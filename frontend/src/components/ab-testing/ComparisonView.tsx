import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { RAGConfig } from '@/types/config';
import { MetricsComparisonTable } from './MetricsComparisonTable';
import { AutoGraderResults } from './AutoGraderResults';

interface ComparisonViewProps {
  testResults: any;
  configA: RAGConfig | null;
  configB: RAGConfig | null;
}

export function ComparisonView({
  testResults,
  configA,
  configB
}: ComparisonViewProps) {
  if (!testResults) return null;

  const { result_a, result_b, metrics_a, metrics_b, grader_result, winner } = testResults;

  return (
    <div className="space-y-6">
      {/* Side-by-Side Responses */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Configuration A</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <h4 className="font-semibold mb-2">Response</h4>
                <p className="text-sm whitespace-pre-wrap">{result_a.answer}</p>
              </div>
              <div>
                <h4 className="font-semibold mb-2">Sources ({result_a.sources?.length || 0})</h4>
                <div className="text-xs text-muted-foreground">
                  {result_a.sources?.slice(0, 5).map((s: any, i: number) => (
                    <div key={i} className="mb-1">
                      {i + 1}. {s.doc_id || s.title || 'Unknown'} (Score: {s.score?.toFixed(3)})
                    </div>
                  ))}
                  {result_a.sources && result_a.sources.length > 5 && (
                    <div>... and {result_a.sources.length - 5} more</div>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Configuration B</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <h4 className="font-semibold mb-2">Response</h4>
                <p className="text-sm whitespace-pre-wrap">{result_b.answer}</p>
              </div>
              <div>
                <h4 className="font-semibold mb-2">Sources ({result_b.sources?.length || 0})</h4>
                <div className="text-xs text-muted-foreground">
                  {result_b.sources?.slice(0, 5).map((s: any, i: number) => (
                    <div key={i} className="mb-1">
                      {i + 1}. {s.doc_id || s.title || 'Unknown'} (Score: {s.score?.toFixed(3)})
                    </div>
                  ))}
                  {result_b.sources && result_b.sources.length > 5 && (
                    <div>... and {result_b.sources.length - 5} more</div>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Metrics Comparison */}
      <MetricsComparisonTable
        metricsA={metrics_a}
        metricsB={metrics_b}
        configA={configA}
        configB={configB}
      />

      {/* Auto-Grader Results */}
      {grader_result && (
        <AutoGraderResults graderResult={grader_result} winner={winner} />
      )}
    </div>
  );
}

