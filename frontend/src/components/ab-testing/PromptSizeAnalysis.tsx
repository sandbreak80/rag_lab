import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';

interface PromptSizeAnalysisProps {
  metricsA: any;
  metricsB: any;
}

export function PromptSizeAnalysis({
  metricsA,
  metricsB
}: PromptSizeAnalysisProps) {
  const promptSizeA = metricsA?.stage_timings?.prompt_size;
  const promptSizeB = metricsB?.stage_timings?.prompt_size;

  // Debug logging
  console.log('🔍 PromptSizeAnalysis - metricsA:', metricsA);
  console.log('🔍 PromptSizeAnalysis - metricsB:', metricsB);
  console.log('🔍 PromptSizeAnalysis - promptSizeA:', promptSizeA);
  console.log('🔍 PromptSizeAnalysis - promptSizeB:', promptSizeB);

  // Show component even if data is missing (so user knows it should be there)
  // But show a message if data is missing
  if (!promptSizeA && !promptSizeB) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>📊 Prompt Size Analysis</CardTitle>
          <CardDescription>
            Detailed breakdown of token usage and context window utilization
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-muted-foreground text-sm">
            Prompt size data not available. This may be because the test was run before this feature was added, or the metrics are not being captured.
          </div>
        </CardContent>
      </Card>
    );
  }

  const formatNumber = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return 'N/A';
    if (typeof value === 'number') {
      if (value > 1000) return `${(value / 1000).toFixed(1)}k`;
      return value.toFixed(0);
    }
    return String(value);
  };

  const getWarningClass = (utilization: number | null | undefined, fits: boolean | null | undefined): string => {
    if (fits === false) return 'text-red-600 font-bold';
    if (utilization && utilization > 90) return 'text-orange-600 font-semibold';
    if (utilization && utilization > 80) return 'text-yellow-600';
    return '';
  };

  const getWarningText = (utilization: number | null | undefined, fits: boolean | null | undefined): string => {
    if (fits === false) return ' ⚠️ EXCEEDS CONTEXT WINDOW!';
    if (utilization && utilization > 90) return ' ⚠️ >90% - Response may be severely truncated!';
    if (utilization && utilization > 80) return ' ⚠️ >80% - Response may be truncated!';
    return '';
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>📊 Prompt Size Analysis</CardTitle>
        <CardDescription>
          Detailed breakdown of token usage and context window utilization
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Configuration A */}
          <div>
            <h3 className="font-semibold mb-3 text-lg">Configuration A</h3>
            {promptSizeA ? (
              <div className="space-y-2 text-sm">
                <div>
                  <span className="text-muted-foreground">System prompt:</span>{' '}
                  <span className="font-mono">~{formatNumber(promptSizeA.system_prompt_tokens)} tokens</span>
                </div>
                <div>
                  <span className="text-muted-foreground">User query:</span>{' '}
                  <span className="font-mono">~{formatNumber(promptSizeA.user_query_tokens)} tokens</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Retrieved documents ({promptSizeA.retrieved_docs_count || 0} docs):</span>{' '}
                  <span className="font-mono">~{formatNumber(promptSizeA.retrieved_docs_tokens)} tokens</span>
                </div>
                <div className="pt-2 border-t">
                  <span className="text-muted-foreground">Total prompt:</span>{' '}
                  <span className="font-mono font-semibold">~{formatNumber(promptSizeA.prompt_tokens_estimated)} tokens</span>
                  {' '}
                  <span className={getWarningClass(promptSizeA.prompt_utilization_pct, promptSizeA.prompt_fits)}>
                    ({promptSizeA.prompt_utilization_pct?.toFixed(1) || 'N/A'}% of {formatNumber(promptSizeA.context_window)} context window)
                    {getWarningText(promptSizeA.prompt_utilization_pct, promptSizeA.prompt_fits)}
                  </span>
                </div>
                <div>
                  <span className="text-muted-foreground">Available for response:</span>{' '}
                  <span className="font-mono">~{formatNumber(promptSizeA.available_for_response)} tokens</span>
                  {' '}
                  <span className="text-muted-foreground">(max_tokens={formatNumber(promptSizeA.max_tokens)})</span>
                  {promptSizeA.response_fits === false && (
                    <span className="text-orange-600 ml-1">⚠️ Response will be truncated!</span>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-muted-foreground text-sm">No prompt size data available</div>
            )}
          </div>

          {/* Configuration B */}
          <div>
            <h3 className="font-semibold mb-3 text-lg">Configuration B</h3>
            {promptSizeB ? (
              <div className="space-y-2 text-sm">
                <div>
                  <span className="text-muted-foreground">System prompt:</span>{' '}
                  <span className="font-mono">~{formatNumber(promptSizeB.system_prompt_tokens)} tokens</span>
                </div>
                <div>
                  <span className="text-muted-foreground">User query:</span>{' '}
                  <span className="font-mono">~{formatNumber(promptSizeB.user_query_tokens)} tokens</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Retrieved documents ({promptSizeB.retrieved_docs_count || 0} docs):</span>{' '}
                  <span className="font-mono">~{formatNumber(promptSizeB.retrieved_docs_tokens)} tokens</span>
                </div>
                <div className="pt-2 border-t">
                  <span className="text-muted-foreground">Total prompt:</span>{' '}
                  <span className="font-mono font-semibold">~{formatNumber(promptSizeB.prompt_tokens_estimated)} tokens</span>
                  {' '}
                  <span className={getWarningClass(promptSizeB.prompt_utilization_pct, promptSizeB.prompt_fits)}>
                    ({promptSizeB.prompt_utilization_pct?.toFixed(1) || 'N/A'}% of {formatNumber(promptSizeB.context_window)} context window)
                    {getWarningText(promptSizeB.prompt_utilization_pct, promptSizeB.prompt_fits)}
                  </span>
                </div>
                <div>
                  <span className="text-muted-foreground">Available for response:</span>{' '}
                  <span className="font-mono">~{formatNumber(promptSizeB.available_for_response)} tokens</span>
                  {' '}
                  <span className="text-muted-foreground">(max_tokens={formatNumber(promptSizeB.max_tokens)})</span>
                  {promptSizeB.response_fits === false && (
                    <span className="text-orange-600 ml-1">⚠️ Response will be truncated!</span>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-muted-foreground text-sm">No prompt size data available</div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

