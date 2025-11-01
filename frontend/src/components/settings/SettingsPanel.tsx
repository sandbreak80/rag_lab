import React from 'react';
import { useConfigStore } from '../../stores/configStore';
import { ModelSelector } from './ModelSelector';
import { RAGToggles } from './RAGToggles';
import { QuickPresets } from './QuickPresets';
import { MetadataFilters } from './MetadataFilters';
import { Slider } from '../ui/slider';
import { Label } from '../ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';

export function SettingsPanel() {
  const temperature = useConfigStore((state) => state.temperature);
  const setTemperature = useConfigStore((state) => state.setTemperature);
  const topK = useConfigStore((state) => state.topK);
  const setTopK = useConfigStore((state) => state.setTopK);
  const contextWindow = useConfigStore((state) => state.contextWindow);
  const setContextWindow = useConfigStore((state) => state.setContextWindow);
  const webSearchDocs = useConfigStore((state) => state.webSearchDocs);
  const setWebSearchDocs = useConfigStore((state) => state.setWebSearchDocs);
  const webSearchPages = useConfigStore((state) => state.webSearchPages);
  const setWebSearchPages = useConfigStore((state) => state.setWebSearchPages);
  const rerankTopK = useConfigStore((state) => state.rerankTopK);
  const setRerankTopK = useConfigStore((state) => state.setRerankTopK);
  const reset = useConfigStore((state) => state.reset);

  return (
    <div className="space-y-6">
      {/* Quick Presets */}
      <Card>
        <CardHeader>
          <CardTitle>⚡ Quick Presets</CardTitle>
          <CardDescription>
            Load predefined configurations for different use cases
          </CardDescription>
        </CardHeader>
        <CardContent>
          <QuickPresets />
        </CardContent>
      </Card>

      {/* Model Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>🤖 Model Configuration</CardTitle>
          <CardDescription>
            Configure LLM model and generation parameters
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <ModelSelector />

          {/* Temperature */}
          <div className="space-y-2">
            <div className="flex justify-between">
              <Label htmlFor="temperature">Temperature</Label>
              <span className="text-sm text-muted-foreground">{temperature}</span>
            </div>
            <Slider
              id="temperature"
              min={0}
              max={2}
              step={0.1}
              value={temperature}
              onValueChange={setTemperature}
            />
            <p className="text-xs text-muted-foreground">
              Higher = more creative, Lower = more focused
            </p>
          </div>

          {/* Context Window */}
          <div className="space-y-2">
            <div className="flex justify-between">
              <Label htmlFor="context">Context Window</Label>
              <span className="text-sm text-muted-foreground">{contextWindow}</span>
            </div>
            <Slider
              id="context"
              min={1024}
              max={128000}
              step={1024}
              value={contextWindow}
              onValueChange={setContextWindow}
            />
            <p className="text-xs text-muted-foreground">
              Maximum tokens for context
            </p>
          </div>
        </CardContent>
      </Card>

      {/* RAG Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>🔍 RAG Configuration</CardTitle>
          <CardDescription>
            Enable or disable RAG features to observe their impact
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <RAGToggles />

          {/* Top-K */}
          <div className="space-y-2">
            <div className="flex justify-between">
              <Label htmlFor="top-k">Top-K Results</Label>
              <span className="text-sm text-muted-foreground">{topK}</span>
            </div>
            <Slider
              id="top-k"
              min={1}
              max={20}
              step={1}
              value={topK}
              onValueChange={setTopK}
            />
            <p className="text-xs text-muted-foreground">
              Number of documents to retrieve
            </p>
          </div>

          {/* Web Search Config */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <div className="flex justify-between">
                <Label htmlFor="web-docs">Web: Max Results</Label>
                <span className="text-sm text-muted-foreground">{webSearchDocs}</span>
              </div>
              <Slider
                id="web-docs"
                min={1}
                max={10}
                step={1}
                value={webSearchDocs}
                onValueChange={setWebSearchDocs}
              />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between">
                <Label htmlFor="web-pages">Web: Pages/Result</Label>
                <span className="text-sm text-muted-foreground">{webSearchPages}</span>
              </div>
              <Slider
                id="web-pages"
                min={1}
                max={3}
                step={1}
                value={webSearchPages}
                onValueChange={setWebSearchPages}
              />
            </div>
          </div>

          {/* Reranker Top-K */}
          <div className="space-y-2">
            <div className="flex justify-between">
              <Label htmlFor="rerank-k">Reranker: Top-K</Label>
              <span className="text-sm text-muted-foreground">{rerankTopK}</span>
            </div>
            <Slider
              id="rerank-k"
              min={5}
              max={20}
              step={1}
              value={rerankTopK}
              onValueChange={setRerankTopK}
            />
            <p className="text-xs text-muted-foreground">
              Results to keep after reranking
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Metadata Filters */}
      <MetadataFilters />

      {/* Reset Button */}
      <div className="flex justify-end">
        <button
          onClick={reset}
          className="px-4 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          Reset to Defaults
        </button>
      </div>
    </div>
  );
}

