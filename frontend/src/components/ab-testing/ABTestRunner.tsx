import React from 'react';
import { Button } from '../ui/button';
import { PromptLibraryItem } from '@/data/promptLibrary';
import { RAGConfig } from '@/types/config';
import { api } from '@/services/api';
import { Loader2, Play } from 'lucide-react';

interface ABTestRunnerProps {
  prompt: PromptLibraryItem | null;
  configA: RAGConfig | null;
  configB: RAGConfig | null;
  onResults: (results: any) => void;
  isRunning: boolean;
  setIsRunning: (running: boolean) => void;
}

export function ABTestRunner({
  prompt,
  configA,
  configB,
  onResults,
  isRunning,
  setIsRunning
}: ABTestRunnerProps) {
  const [runParallel, setRunParallel] = React.useState(false); // Default to sequential to avoid VRAM issues
  const [autoGrade, setAutoGrade] = React.useState(false); // Default to false to show responses immediately
  const [testId, setTestId] = React.useState<string | null>(null);
  const [statusMessage, setStatusMessage] = React.useState<string>('');

  // Poll for results when test is running
  React.useEffect(() => {
    if (!testId || !isRunning) return;

    const pollInterval = setInterval(async () => {
                  try {
                    const result = await api.getABTestResult(testId);

                    // Check for error status
                    if (result.status === 'error') {
                      clearInterval(pollInterval);
                      setIsRunning(false);
                      const errorMsg = result.error || result.message || 'Test failed with unknown error';
                      alert(`Test failed: ${errorMsg}`);
                      return;
                    }

                    // Check if results are ready (has result_a and result_b, or status is 'completed')
                    // Don't wait for grader_result - show responses immediately!
                    if (result.result_a && result.result_b) {
                      // Results are ready - show them immediately (grading may still be running)
                      clearInterval(pollInterval);
                      setIsRunning(false);
                      setStatusMessage('Responses ready!');
                      console.log('✅ A/B Test responses ready! Result:', result);
                      console.log('✅ Calling onResults with:', result);
                      onResults(result);
                      console.log('✅ onResults called');
                      return;
                    }

                    // Still running - update status message
                    if (result.status === 'running') {
                      setStatusMessage(result.message || 'Test is running...');
                      return;
                    }

                    // If we get here, results might not be ready yet
                    setStatusMessage('Waiting for responses...');
                  } catch (error: any) {
                    console.error('Error polling for results:', error);
                    const errorMessage = error?.response?.data?.detail || error?.response?.data?.error || error?.message || 'Unknown error';
                    if (errorMessage.includes('error') || error?.response?.status === 500) {
                      clearInterval(pollInterval);
                      setIsRunning(false);
                      alert(`Test failed: ${errorMessage}`);
                    }
                  }
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(pollInterval);
  }, [testId, isRunning, onResults]);

  const handleRun = async () => {
    if (!prompt || !configA || !configB) {
      alert('Please select a prompt and both configurations');
      return;
    }

    setIsRunning(true);
    setStatusMessage('Starting test...');
    setTestId(null);

    try {
      // Debug: Log what we're sending
      console.log('🔍 A/B Test Config A:', {
        model: configA?.model,
        temperature: configA?.temperature,
        maxTokens: configA?.maxTokens,
        contextWindow: configA?.contextWindow,
        topK: configA?.topK,
        useWebSearch: configA?.useWebSearch
      });
      console.log('🔍 A/B Test Config B:', {
        model: configB?.model,
        temperature: configB?.temperature,
        maxTokens: configB?.maxTokens,
        contextWindow: configB?.contextWindow,
        topK: configB?.topK,
        useWebSearch: configB?.useWebSearch
      });

      const startResponse = await api.runABTest({
        prompt: prompt.prompt,
        config_a: configA,
        config_b: configB,
        run_parallel: runParallel,
        auto_grade: autoGrade
      });

      setTestId(startResponse.test_id);
      setStatusMessage(startResponse.message || 'Test started. Waiting for results...');
    } catch (error: any) {
      console.error('A/B test failed to start:', error);
      const errorMessage = error?.response?.data?.detail || error?.message || error?.toString() || 'Unknown error';
      console.error('Full error details:', {
        message: error?.message,
        response: error?.response?.data,
        status: error?.response?.status,
        code: error?.code
      });
      setIsRunning(false);
      alert(`Test failed to start: ${errorMessage}`);
    }
  };

  const canRun = prompt && configA && configB && !isRunning;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={runParallel}
            onChange={(e) => setRunParallel(e.target.checked)}
            disabled={isRunning}
          />
          <span className="text-sm">Run in parallel (faster, but may cause VRAM issues)</span>
        </label>

        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={autoGrade}
            onChange={(e) => setAutoGrade(e.target.checked)}
            disabled={isRunning}
          />
          <span className="text-sm">Auto-grade responses</span>
        </label>
      </div>

      <Button
        onClick={handleRun}
        disabled={!canRun}
        size="lg"
        className="w-full"
      >
        {isRunning ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Running Test...
          </>
        ) : (
          <>
            <Play className="mr-2 h-4 w-4" />
            Run A/B Test
          </>
        )}
      </Button>

      {isRunning && (
        <div className="text-sm text-muted-foreground text-center space-y-2">
          <div className="flex items-center justify-center gap-2">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>{statusMessage || 'Running test...'}</span>
          </div>
          <div className="text-xs">
            Executing both queries{runParallel ? ' in parallel' : ' sequentially'}...
            {autoGrade && ' Auto-grading will run after queries complete.'}
            {testId && ` (Test ID: ${testId.substring(0, 8)}...)`}
          </div>
        </div>
      )}
    </div>
  );
}

