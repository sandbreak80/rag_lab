import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';

interface CostComparisonTableProps {
  metricsA: any;
  metricsB: any;
}

// Cost per million tokens (from cost_calculation_gpt.md)
const COST_INPUT_TOKENS_PER_M = 0.04;   // $0.04 per 1M input tokens
const COST_OUTPUT_TOKENS_PER_M = 1.50;  // $1.50 per 1M output tokens
const COST_EMBEDDING_TOKENS_PER_M = 0.05; // $0.05 per 1M embedding tokens

// Average chunk size for embedding token estimation
const AVG_CHUNK_SIZE_TOKENS = 450;

/**
 * Calculate cost based on token counts
 * Formula: (input_tokens / 1M) * 0.04 + (output_tokens / 1M) * 1.50 + (embedding_tokens / 1M) * 0.05
 */
function calculateCost(
  inputTokens: number | null | undefined,
  outputTokens: number | null | undefined,
  embeddingTokens: number | null | undefined
): number | null {
  if (inputTokens === null || inputTokens === undefined ||
      outputTokens === null || outputTokens === undefined ||
      embeddingTokens === null || embeddingTokens === undefined) {
    return null;
  }

  const inputCost = (inputTokens / 1_000_000) * COST_INPUT_TOKENS_PER_M;
  const outputCost = (outputTokens / 1_000_000) * COST_OUTPUT_TOKENS_PER_M;
  const embeddingCost = (embeddingTokens / 1_000_000) * COST_EMBEDDING_TOKENS_PER_M;

  return inputCost + outputCost + embeddingCost;
}

/**
 * Estimate embedding tokens from retrieved docs count
 * This is an approximation: retrieved_docs_count × average_chunk_size
 */
function estimateEmbeddingTokens(
  retrievedDocsCount: number | null | undefined,
  retrievedDocsTokens: number | null | undefined
): number | null {
  // If we have retrieved_docs_tokens, use that (more accurate)
  if (retrievedDocsTokens !== null && retrievedDocsTokens !== undefined) {
    return retrievedDocsTokens;
  }

  // Otherwise, estimate from count × average chunk size
  if (retrievedDocsCount !== null && retrievedDocsCount !== undefined) {
    return retrievedDocsCount * AVG_CHUNK_SIZE_TOKENS;
  }

  return null;
}

function formatCurrency(value: number | null): string {
  if (value === null || value === undefined) {
    return 'N/A';
  }
  if (value < 0.0001) {
    return `$${value.toFixed(6)}`;
  }
  return `$${value.toFixed(6)}`;
}

function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return 'N/A';
  }
  if (value > 1000) {
    return `${(value / 1000).toFixed(1)}k`;
  }
  return value.toFixed(0);
}

export function CostComparisonTable({
  metricsA,
  metricsB
}: CostComparisonTableProps) {
  if (!metricsA || !metricsB) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>💰 Cost Comparison</CardTitle>
          <CardDescription>
            Cost breakdown per query based on token usage
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-muted-foreground text-sm">
            Cost data not available. Run a test to see cost breakdown.
          </div>
        </CardContent>
      </Card>
    );
  }

  // Extract token counts
  const inputTokensA = metricsA.tokens_in ?? metricsA.prompt_tokens;
  const outputTokensA = metricsA.tokens_out ?? metricsA.completion_tokens;
  const retrievedDocsCountA = metricsA.stage_timings?.prompt_size?.retrieved_docs_count;
  const retrievedDocsTokensA = metricsA.stage_timings?.prompt_size?.retrieved_docs_tokens;
  // Use embedding_tokens_estimated if available, otherwise estimate
  const embeddingTokensA = metricsA.stage_timings?.prompt_size?.embedding_tokens_estimated ??
                           estimateEmbeddingTokens(retrievedDocsCountA, retrievedDocsTokensA);

  const inputTokensB = metricsB.tokens_in ?? metricsB.prompt_tokens;
  const outputTokensB = metricsB.tokens_out ?? metricsB.completion_tokens;
  const retrievedDocsCountB = metricsB.stage_timings?.prompt_size?.retrieved_docs_count;
  const retrievedDocsTokensB = metricsB.stage_timings?.prompt_size?.retrieved_docs_tokens;
  // Use embedding_tokens_estimated if available, otherwise estimate
  const embeddingTokensB = metricsB.stage_timings?.prompt_size?.embedding_tokens_estimated ??
                           estimateEmbeddingTokens(retrievedDocsCountB, retrievedDocsTokensB);

  // Calculate costs
  const costA = calculateCost(inputTokensA, outputTokensA, embeddingTokensA);
  const costB = calculateCost(inputTokensB, outputTokensB, embeddingTokensB);

  // Calculate component costs
  const inputCostA = inputTokensA ? (inputTokensA / 1_000_000) * COST_INPUT_TOKENS_PER_M : null;
  const outputCostA = outputTokensA ? (outputTokensA / 1_000_000) * COST_OUTPUT_TOKENS_PER_M : null;
  const embeddingCostA = embeddingTokensA ? (embeddingTokensA / 1_000_000) * COST_EMBEDDING_TOKENS_PER_M : null;

  const inputCostB = inputTokensB ? (inputTokensB / 1_000_000) * COST_INPUT_TOKENS_PER_M : null;
  const outputCostB = outputTokensB ? (outputTokensB / 1_000_000) * COST_OUTPUT_TOKENS_PER_M : null;
  const embeddingCostB = embeddingTokensB ? (embeddingTokensB / 1_000_000) * COST_EMBEDDING_TOKENS_PER_M : null;

  // Determine winner (lower cost is better)
  const getWinner = (costA: number | null, costB: number | null): string => {
    if (costA === null || costB === null) return '';
    if (Math.abs(costA - costB) < 0.000001) return 'tie';
    return costA < costB ? 'A' : 'B';
  };

  const winner = getWinner(costA, costB);

  return (
    <Card>
      <CardHeader>
        <CardTitle>💰 Cost Comparison</CardTitle>
        <CardDescription>
          Cost breakdown per query based on token usage. Costs are calculated using:
          <br />
          <span className="text-xs">
            Input: ${COST_INPUT_TOKENS_PER_M}/1M tokens |
            Output: ${COST_OUTPUT_TOKENS_PER_M}/1M tokens |
            Embedding: ${COST_EMBEDDING_TOKENS_PER_M}/1M tokens
          </span>
        </CardDescription>
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
              {/* Token Counts */}
              <tr className="border-b bg-muted/30">
                <td colSpan={4} className="p-2 font-semibold">Token Counts</td>
              </tr>
              <tr className="border-b">
                <td className="p-2">Input Tokens</td>
                <td className="text-right p-2 font-mono">{formatNumber(inputTokensA)}</td>
                <td className="text-right p-2 font-mono">{formatNumber(inputTokensB)}</td>
                <td className="text-center p-2">
                  {inputTokensA && inputTokensB && (
                    <span className={`px-2 py-1 rounded text-xs ${
                      inputTokensA < inputTokensB ? 'bg-green-100 text-green-800' :
                      inputTokensA > inputTokensB ? 'bg-blue-100 text-blue-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {inputTokensA < inputTokensB ? 'A (Lower)' : inputTokensA > inputTokensB ? 'B (Lower)' : 'Tie'}
                    </span>
                  )}
                </td>
              </tr>
              <tr className="border-b">
                <td className="p-2">Output Tokens</td>
                <td className="text-right p-2 font-mono">{formatNumber(outputTokensA)}</td>
                <td className="text-right p-2 font-mono">{formatNumber(outputTokensB)}</td>
                <td className="text-center p-2">
                  {outputTokensA && outputTokensB && (
                    <span className={`px-2 py-1 rounded text-xs ${
                      outputTokensA < outputTokensB ? 'bg-green-100 text-green-800' :
                      outputTokensA > outputTokensB ? 'bg-blue-100 text-blue-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {outputTokensA < outputTokensB ? 'A (Lower)' : outputTokensA > outputTokensB ? 'B (Lower)' : 'Tie'}
                    </span>
                  )}
                </td>
              </tr>
              <tr className="border-b">
                <td className="p-2">Embedding Tokens (est.)</td>
                <td className="text-right p-2 font-mono">{formatNumber(embeddingTokensA)}</td>
                <td className="text-right p-2 font-mono">{formatNumber(embeddingTokensB)}</td>
                <td className="text-center p-2">
                  {embeddingTokensA && embeddingTokensB && (
                    <span className={`px-2 py-1 rounded text-xs ${
                      embeddingTokensA < embeddingTokensB ? 'bg-green-100 text-green-800' :
                      embeddingTokensA > embeddingTokensB ? 'bg-blue-100 text-blue-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {embeddingTokensA < embeddingTokensB ? 'A (Lower)' : embeddingTokensA > embeddingTokensB ? 'B (Lower)' : 'Tie'}
                    </span>
                  )}
                </td>
              </tr>

              {/* Cost Breakdown */}
              <tr className="border-b bg-muted/30">
                <td colSpan={4} className="p-2 font-semibold">Cost Breakdown</td>
              </tr>
              <tr className="border-b">
                <td className="p-2">Input Cost</td>
                <td className="text-right p-2 font-mono">{formatCurrency(inputCostA)}</td>
                <td className="text-right p-2 font-mono">{formatCurrency(inputCostB)}</td>
                <td className="text-center p-2">
                  {inputCostA !== null && inputCostB !== null && (
                    <span className={`px-2 py-1 rounded text-xs ${
                      inputCostA < inputCostB ? 'bg-green-100 text-green-800' :
                      inputCostA > inputCostB ? 'bg-blue-100 text-blue-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {inputCostA < inputCostB ? 'A' : inputCostA > inputCostB ? 'B' : 'Tie'}
                    </span>
                  )}
                </td>
              </tr>
              <tr className="border-b">
                <td className="p-2">Output Cost</td>
                <td className="text-right p-2 font-mono">{formatCurrency(outputCostA)}</td>
                <td className="text-right p-2 font-mono">{formatCurrency(outputCostB)}</td>
                <td className="text-center p-2">
                  {outputCostA !== null && outputCostB !== null && (
                    <span className={`px-2 py-1 rounded text-xs ${
                      outputCostA < outputCostB ? 'bg-green-100 text-green-800' :
                      outputCostA > outputCostB ? 'bg-blue-100 text-blue-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {outputCostA < outputCostB ? 'A' : outputCostA > outputCostB ? 'B' : 'Tie'}
                    </span>
                  )}
                </td>
              </tr>
              <tr className="border-b">
                <td className="p-2">Embedding Cost</td>
                <td className="text-right p-2 font-mono">{formatCurrency(embeddingCostA)}</td>
                <td className="text-right p-2 font-mono">{formatCurrency(embeddingCostB)}</td>
                <td className="text-center p-2">
                  {embeddingCostA !== null && embeddingCostB !== null && (
                    <span className={`px-2 py-1 rounded text-xs ${
                      embeddingCostA < embeddingCostB ? 'bg-green-100 text-green-800' :
                      embeddingCostA > embeddingCostB ? 'bg-blue-100 text-blue-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {embeddingCostA < embeddingCostB ? 'A' : embeddingCostA > embeddingCostB ? 'B' : 'Tie'}
                    </span>
                  )}
                </td>
              </tr>

              {/* Total Cost */}
              <tr className="border-t-2 border-primary bg-primary/5">
                <td className="p-2 font-semibold">Total Cost per Query</td>
                <td className="text-right p-2 font-mono font-semibold text-lg">{formatCurrency(costA)}</td>
                <td className="text-right p-2 font-mono font-semibold text-lg">{formatCurrency(costB)}</td>
                <td className="text-center p-2">
                  {winner && (
                    <span className={`px-3 py-1 rounded text-sm font-semibold ${
                      winner === 'A' ? 'bg-green-200 text-green-900' :
                      winner === 'B' ? 'bg-blue-200 text-blue-900' :
                      'bg-gray-200 text-gray-900'
                    }`}>
                      {winner === 'tie' ? 'Tie' : `Winner: ${winner}`}
                    </span>
                  )}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Cost Savings Calculation */}
        {costA !== null && costB !== null && costA !== costB && (
          <div className="mt-4 p-3 bg-muted rounded-lg">
            <p className="text-sm">
              <strong>Cost Difference:</strong>{' '}
              {costA < costB ? (
                <>
                  Configuration A is <span className="text-green-600 font-semibold">
                    ${(costB - costA).toFixed(6)} cheaper
                  </span> per query
                  {' '}({((1 - costA / costB) * 100).toFixed(1)}% savings)
                </>
              ) : (
                <>
                  Configuration B is <span className="text-green-600 font-semibold">
                    ${(costA - costB).toFixed(6)} cheaper
                  </span> per query
                  {' '}({((1 - costB / costA) * 100).toFixed(1)}% savings)
                </>
              )}
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              At 1,000 queries: {costA < costB
                ? `$${((costB - costA) * 1000).toFixed(3)} savings with A`
                : `$${((costA - costB) * 1000).toFixed(3)} savings with B`
              }
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

