import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { RAGConfig } from '@/types/config';
import { PROMPT_LIBRARY, PromptLibraryItem } from '@/data/promptLibrary';
import { useConfigStore } from '@/stores/configStore';
import { PromptLibraryBrowser } from '@/components/ab-testing/PromptLibraryBrowser';
import { ConfigurationSelector } from '@/components/ab-testing/ConfigurationSelector';
import { ABTestRunner } from '@/components/ab-testing/ABTestRunner';
import { ComparisonView } from '@/components/ab-testing/ComparisonView';

export function ABTestingPage() {
  const [selectedPrompt, setSelectedPrompt] = useState<PromptLibraryItem | null>(null);
  const [configA, setConfigA] = useState<RAGConfig | null>(null);
  const [configB, setConfigB] = useState<RAGConfig | null>(null);
  const [testResults, setTestResults] = useState<any>(null);
  const [isRunning, setIsRunning] = useState(false);

  // Debug: Log when testResults changes
  React.useEffect(() => {
    console.log('🔍 ABTestingPage: testResults changed:', testResults);
  }, [testResults]);

  const defaultConfig = useConfigStore((state) => state);

  // Initialize with default config if not set
  React.useEffect(() => {
    if (!configA) {
      setConfigA(defaultConfig);
    }
    if (!configB) {
      setConfigB(defaultConfig);
    }
  }, [defaultConfig, configA, configB]);

  const handleRunTest = async () => {
    if (!selectedPrompt || !configA || !configB) {
      alert('Please select a prompt and both configurations');
      return;
    }

    setIsRunning(true);
    try {
      // This will be implemented in ABTestRunner
      // For now, just set a placeholder
      setTestResults(null);
    } catch (error) {
      console.error('Test failed:', error);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="container mx-auto px-6 py-8 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">A/B Testing Lab</h1>
        <p className="text-muted-foreground">
          Compare different RAG configurations side-by-side to understand trade-offs
        </p>
      </div>

      {/* Step 1: Select Prompt */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Step 1: Select Test Prompt</CardTitle>
          <CardDescription>
            Choose a prompt from the library or use a custom prompt
          </CardDescription>
        </CardHeader>
        <CardContent>
          <PromptLibraryBrowser
            prompts={PROMPT_LIBRARY}
            selectedPrompt={selectedPrompt}
            onSelect={setSelectedPrompt}
          />
        </CardContent>
      </Card>

      {/* Step 2: Select Configurations */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Step 2: Select Configurations to Compare</CardTitle>
          <CardDescription>
            Choose two different configurations (presets or custom)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <ConfigurationSelector
              label="Configuration A"
              value={configA}
              onChange={setConfigA}
            />
            <ConfigurationSelector
              label="Configuration B"
              value={configB}
              onChange={setConfigB}
            />
          </div>
          {configA && configB && (
            <div className="mt-4 flex gap-2">
              <Button
                variant="outline"
                onClick={() => {
                  const temp = configA;
                  setConfigA(configB);
                  setConfigB(temp);
                }}
              >
                Swap Configurations
              </Button>
              <Button
                variant="outline"
                onClick={() => setConfigB(configA)}
              >
                Copy A to B
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Step 3: Run Test */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Step 3: Run Test</CardTitle>
          <CardDescription>
            Execute both queries and compare results
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ABTestRunner
            prompt={selectedPrompt}
            configA={configA}
            configB={configB}
            onResults={setTestResults}
            isRunning={isRunning}
            setIsRunning={setIsRunning}
          />
        </CardContent>
      </Card>

      {/* Step 4: Results */}
      {testResults ? (
        <Card>
          <CardHeader>
            <CardTitle>Results: Side-by-Side Comparison</CardTitle>
            <CardDescription>
              Compare responses, sources, and metrics
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ComparisonView
              testResults={testResults}
              configA={configA}
              configB={configB}
            />
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            {isRunning ? 'Test is running...' : 'No test results yet. Run a test to see results here.'}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

