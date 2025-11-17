import React from 'react';
import { Button } from '../ui/button';
import { PromptLibraryItem } from '../../../data/promptLibrary';
import { RAGConfig } from '../../../types/config';
import { api } from '../../../services/api';
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
  const [runParallel, setRunParallel] = React.useState(true);
  const [autoGrade, setAutoGrade] = React.useState(true);

  const handleRun = async () => {
    if (!prompt || !configA || !configB) {
      alert('Please select a prompt and both configurations');
      return;
    }

    setIsRunning(true);
    try {
      const results = await api.runABTest({
        prompt: prompt.prompt,
        config_a: configA,
        config_b: configB,
        run_parallel: runParallel,
        auto_grade: autoGrade
      });
      onResults(results);
    } catch (error: any) {
      console.error('A/B test failed:', error);
      alert(`Test failed: ${error.message || 'Unknown error'}`);
    } finally {
      setIsRunning(false);
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
          <span className="text-sm">Run in parallel (faster)</span>
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
        <div className="text-sm text-muted-foreground text-center">
          Executing both queries{runParallel ? ' in parallel' : ' sequentially'}...
          {autoGrade && ' Auto-grading will run after queries complete.'}
        </div>
      )}
    </div>
  );
}

