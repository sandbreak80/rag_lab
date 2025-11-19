import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Button } from '../ui/button';
import { Loader2 } from 'lucide-react';
import { RAGConfig } from '@/types/config';
import { MetricsComparisonTable } from './MetricsComparisonTable';
import { AutoGraderResults } from './AutoGraderResults';
import { CostComparisonTable } from './CostComparisonTable';
import { PromptSizeAnalysis } from './PromptSizeAnalysis';
import { api } from '@/services/api';

interface ComparisonViewProps {
  testResults: any;
  configA: RAGConfig | null;
  configB: RAGConfig | null;
  onResultsUpdate?: (updatedResults: any) => void;
}

export function ComparisonView({
  testResults,
  configA,
  configB,
  onResultsUpdate
}: ComparisonViewProps) {
  const [isGrading, setIsGrading] = React.useState(false);
  const [gradingStatus, setGradingStatus] = React.useState<string>('');

  console.log('🔍 ComparisonView: testResults:', testResults);

  if (!testResults) {
    console.log('⚠️ ComparisonView: testResults is null/undefined');
    return <div className="text-muted-foreground">No results to display</div>;
  }

  const { result_a, result_b, metrics_a, metrics_b, grader_result, winner, grading_duration_ms, test_id } = testResults;

  // Validate that we have the required data
  if (!result_a || !result_b) {
    console.error('⚠️ ComparisonView: Missing result_a or result_b', { result_a: !!result_a, result_b: !!result_b });
    return (
      <div className="text-muted-foreground p-4">
        <p>Results are still loading or incomplete.</p>
        <p className="text-xs mt-2">result_a: {result_a ? 'present' : 'missing'}, result_b: {result_b ? 'present' : 'missing'}</p>
        {test_id && <p className="text-xs">Test ID: {test_id}</p>}
      </div>
    );
  }

  const handleRunComparison = async () => {
    if (!test_id) {
      alert('Test ID not found');
      return;
    }

    setIsGrading(true);
    setGradingStatus('Starting comparison...');

    try {
      // Start grading
      const gradeResponse = await api.gradeABTest(test_id);
      setGradingStatus(gradeResponse.message || 'Grading started...');

      // Poll for results
      const pollInterval = setInterval(async () => {
        try {
          const result = await api.getABTestResult(test_id);
          console.log('🔍 Polling result:', { status: result.status, has_grader_result: !!result.grader_result });

          // Check if grading is complete (has grader_result or status is 'graded')
          if (result.grader_result || result.status === 'graded') {
            // Grading completed
            clearInterval(pollInterval);
            setIsGrading(false);
            setGradingStatus('');
            console.log('✅ Grading completed, updating results...');

            // Update the parent component with new results
            if (onResultsUpdate) {
              onResultsUpdate(result);
            } else {
              // Fallback: reload if no callback provided
              console.warn('⚠️ No onResultsUpdate callback, reloading page...');
              window.location.reload();
            }
            return;
          }

          // Check if grading failed
          if (result.status === 'grading_failed' || (result.grader_result && result.grader_result.error)) {
            clearInterval(pollInterval);
            setIsGrading(false);
            setGradingStatus('');
            const errorMsg = result.grader_result?.error || result.error || 'Grading failed';
            alert(`Grading failed: ${errorMsg}`);
            return;
          }

          // Still grading - update status
          if (result.status === 'grading' || result.status === 'running') {
            setGradingStatus(result.message || 'Grading in progress...');
            return;
          }

          // If status is 'completed' but no grader_result yet, we're still waiting
          if (result.status === 'completed' && !result.grader_result) {
            setGradingStatus('Grading in progress...');
            return;
          }

          // If we have a status but it's not one we recognize, log it
          console.log('⚠️ Unknown status:', result.status);
        } catch (error: any) {
          console.error('Error polling for grading results:', error);
          clearInterval(pollInterval);
          setIsGrading(false);
          setGradingStatus('');
          alert(`Grading failed: ${error?.message || 'Unknown error'}`);
        }
      }, 2000); // Poll every 2 seconds

      // Cleanup on unmount
      return () => clearInterval(pollInterval);
    } catch (error: any) {
      console.error('Failed to start grading:', error);
      setIsGrading(false);
      setGradingStatus('');
      alert(`Failed to start grading: ${error?.message || 'Unknown error'}`);
    }
  };

  console.log('🔍 ComparisonView: Extracted values:', {
    has_result_a: !!result_a,
    has_result_b: !!result_b,
    has_metrics_a: !!metrics_a,
    has_metrics_b: !!metrics_b,
    has_grader_result: !!grader_result,
    winner
  });

  return (
    <div className="space-y-6">
      {/* Side-by-Side Responses */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Configuration A</CardTitle>
          </CardHeader>
          <CardContent className="overflow-visible">
            <div className="space-y-4">
              <div className="overflow-visible">
                <h4 className="font-semibold mb-2">Response</h4>
                <div className="max-h-none overflow-visible min-h-0">
                  <p className="text-sm whitespace-pre-wrap break-words overflow-visible">{result_a.answer}</p>
                </div>
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

        <Card className="overflow-visible">
          <CardHeader>
            <CardTitle>Configuration B</CardTitle>
          </CardHeader>
          <CardContent className="overflow-visible">
            <div className="space-y-4">
              <div className="overflow-visible">
                <h4 className="font-semibold mb-2">Response</h4>
                <div className="max-h-none overflow-visible min-h-0">
                  <p className="text-sm whitespace-pre-wrap break-words overflow-visible">{result_b.answer}</p>
                </div>
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

      {/* Prompt Size Analysis */}
      <PromptSizeAnalysis
        metricsA={metrics_a}
        metricsB={metrics_b}
      />

      {/* Metrics Comparison */}
      <MetricsComparisonTable
        metricsA={metrics_a}
        metricsB={metrics_b}
        configA={configA}
        configB={configB}
      />

      {/* Cost Comparison */}
      <CostComparisonTable
        metricsA={metrics_a}
        metricsB={metrics_b}
      />

      {/* Auto-Grader Results */}
      {grader_result ? (
        <div>
          {grading_duration_ms && (
            <div className="mb-4 p-3 bg-muted rounded-lg">
              <p className="text-sm text-muted-foreground">
                <strong>Comparison Duration:</strong> {(grading_duration_ms / 1000).toFixed(1)} seconds
                <br />
                <span className="text-xs">
                  (Unloading large models: ~0.1s, Loading mistral:7b: ~1-2s, Generating evaluation: ~{((grading_duration_ms - 2000) / 1000).toFixed(1)}s)
                </span>
              </p>
            </div>
          )}
          <AutoGraderResults graderResult={grader_result} winner={winner} />
        </div>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Comparison Not Run</CardTitle>
            <CardDescription>
              Run the comparison to see detailed evaluation scores and winner determination
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button
              onClick={handleRunComparison}
              disabled={isGrading}
              className="w-full"
            >
              {isGrading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {gradingStatus || 'Running Comparison...'}
                </>
              ) : (
                'Run Comparison'
              )}
            </Button>
            {gradingStatus && (
              <p className="mt-2 text-sm text-muted-foreground">{gradingStatus}</p>
            )}
            <p className="mt-4 text-xs text-muted-foreground">
              <strong>Why does this take time?</strong>
              <br />
              • Unloading large models (qwen2.5:14b) to free GPU memory: ~0.1s
              <br />
              • Loading mistral:7b for evaluation: ~1-2s
              <br />
              • Generating detailed evaluation (2 responses + sources): ~15-20s
              <br />
              <strong>Total: ~16-22 seconds</strong>
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

