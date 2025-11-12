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

  // New intelligence features
  const usePromptEnhancement = useConfigStore((state) => state.usePromptEnhancement);
  const useAutoModelRouting = useConfigStore((state) => state.useAutoModelRouting);
  const useQueryDecomposition = useConfigStore((state) => state.useQueryDecomposition);
  const useSelfRAG = useConfigStore((state) => state.useSelfRAG);
  const showReasoningProcess = useConfigStore((state) => state.showReasoningProcess);
  const useVectorDB = useConfigStore((state) => state.useVectorDB);
  const useResearchAgent = useConfigStore((state) => state.useResearchAgent);
  const useWebSearch = useConfigStore((state) => state.useWebSearch);
  const useGraph = useConfigStore((state) => state.useGraph);
  const toggleFeature = useConfigStore((state) => state.toggleFeature);

  // Debug logging
  console.log('🔍 SettingsPanel render - Intelligence Features:', {
    usePromptEnhancement,
    useAutoModelRouting,
    useQueryDecomposition,
    useVectorDB,
    useResearchAgent,
    useWebSearch,
    useGraph,
  });

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
          <div className="space-y-2" data-testid="settings-temperature-container">
            <div className="flex justify-between">
              <Label htmlFor="temperature">Temperature</Label>
              <span className="text-sm text-muted-foreground" data-testid="settings-temperature-value">{temperature}</span>
            </div>
            <Slider
              id="temperature"
              data-testid="settings-temperature"
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
          <div className="space-y-2" data-testid="settings-context-container">
            <div className="flex justify-between">
              <Label htmlFor="context">Context Window</Label>
              <span className="text-sm text-muted-foreground" data-testid="settings-context-value">{contextWindow}</span>
            </div>
            <Slider
              id="context"
              data-testid="settings-context"
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
          <div className="space-y-2" data-testid="settings-topk-container">
            <div className="flex justify-between">
              <Label htmlFor="top-k">Top-K Results</Label>
              <span className="text-sm text-muted-foreground" data-testid="settings-topk-value">{topK}</span>
            </div>
            <Slider
              id="top-k"
              data-testid="settings-topk"
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

      {/* Intelligence Features - NEW Nov 5, 2025 */}
      <Card>
        <CardHeader>
          <CardTitle>🧠 Intelligence Features</CardTitle>
          <CardDescription>
            Enable AI-powered query processing and optimization
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="prompt-enhancement" className="text-base font-medium">
                🔮 Prompt Enhancement
              </Label>
              <p className="text-sm text-muted-foreground">
                Automatically enhance queries using CoT, ReAct, or Few-Shot frameworks
              </p>
            </div>
            <button
              type="button"
              id="prompt-enhancement"
              data-testid="settings-prompt-enhancement"
              onClick={(e) => {
                e.preventDefault();
                console.log('🔍 Prompt Enhancement toggle clicked');
                toggleFeature('usePromptEnhancement');
              }}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors cursor-pointer ${
                usePromptEnhancement
                  ? 'bg-primary'
                  : 'bg-muted'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-background transition-transform pointer-events-none ${
                  usePromptEnhancement
                    ? 'translate-x-6'
                    : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="auto-routing" className="text-base font-medium">
                🎯 Auto Model Routing
              </Label>
              <p className="text-sm text-muted-foreground">
                Automatically select optimal LLM model based on query complexity
              </p>
            </div>
            <button
              type="button"
              id="auto-routing"
              onClick={(e) => {
                e.preventDefault();
                console.log('🔍 Auto Model Routing toggle clicked');
                toggleFeature('useAutoModelRouting');
              }}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors cursor-pointer ${
                useAutoModelRouting
                  ? 'bg-primary'
                  : 'bg-muted'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-background transition-transform pointer-events-none ${
                  useAutoModelRouting
                    ? 'translate-x-6'
                    : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="query-decomposition" className="text-base font-medium">
                🧩 Query Decomposition
              </Label>
              <p className="text-sm text-muted-foreground">
                Break complex questions into simpler sub-queries for better results
              </p>
            </div>
            <button
              type="button"
              id="query-decomposition"
              onClick={(e) => {
                e.preventDefault();
                console.log('🔍 Query Decomposition toggle clicked');
                toggleFeature('useQueryDecomposition');
              }}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors cursor-pointer ${
                useQueryDecomposition
                  ? 'bg-primary'
                  : 'bg-muted'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-background transition-transform pointer-events-none ${
                  useQueryDecomposition
                    ? 'translate-x-6'
                    : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="self-rag" className="text-base font-medium">
                🔍 Self-RAG
              </Label>
              <p className="text-sm text-muted-foreground">
                Self-reflective retrieval with quality assessment and automatic refinement
              </p>
            </div>
            <button
              type="button"
              id="self-rag"
              onClick={(e) => {
                e.preventDefault();
                console.log('🔍 Self-RAG toggle clicked');
                toggleFeature('useSelfRAG');
              }}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors cursor-pointer ${
                useSelfRAG
                  ? 'bg-primary'
                  : 'bg-muted'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-background transition-transform pointer-events-none ${
                  useSelfRAG
                    ? 'translate-x-6'
                    : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="show-reasoning" className="text-base font-medium">
                🔬 Show Reasoning Process
              </Label>
              <p className="text-sm text-muted-foreground">
                Display step-by-step thinking (CoT/ReAct scaffolding) in responses
              </p>
            </div>
            <button
              type="button"
              id="show-reasoning"
              onClick={(e) => {
                e.preventDefault();
                console.log('🔍 Show Reasoning toggle clicked');
                toggleFeature('showReasoningProcess');
              }}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors cursor-pointer ${
                showReasoningProcess
                  ? 'bg-primary'
                  : 'bg-muted'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-background transition-transform pointer-events-none ${
                  showReasoningProcess
                    ? 'translate-x-6'
                    : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Data Sources - NEW Nov 5, 2025 */}
      <Card>
        <CardHeader>
          <CardTitle>📚 Data Sources</CardTitle>
          <CardDescription>
            Control which data sources are used for retrieval
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="vector-db" className="text-base font-medium">
                📄 Vector Database
              </Label>
              <p className="text-sm text-muted-foreground">
                Search uploaded documents and ingested content
              </p>
            </div>
            <button
              type="button"
              id="vector-db"
              data-testid="settings-vector-db"
              onClick={(e) => {
                e.preventDefault();
                console.log('🔍 Vector DB toggle clicked');
                toggleFeature('useVectorDB');
              }}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors cursor-pointer ${
                useVectorDB
                  ? 'bg-primary'
                  : 'bg-muted'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-background transition-transform pointer-events-none ${
                  useVectorDB
                    ? 'translate-x-6'
                    : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="research-agent" className="text-base font-medium">
                🔬 Research Agent
              </Label>
              <p className="text-sm text-muted-foreground">
                Include auto-discovered research content (91 items, 6 sources)
              </p>
            </div>
            <button
              type="button"
              id="research-agent"
              onClick={(e) => {
                e.preventDefault();
                console.log('🔍 Research Agent toggle clicked');
                toggleFeature('useResearchAgent');
              }}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors cursor-pointer ${
                useResearchAgent
                  ? 'bg-primary'
                  : 'bg-muted'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-background transition-transform pointer-events-none ${
                  useResearchAgent
                    ? 'translate-x-6'
                    : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="web-search-source" className="text-base font-medium">
                🌐 Web Search
              </Label>
              <p className="text-sm text-muted-foreground">
                Include real-time web search results (SearXNG)
              </p>
            </div>
            <button
              type="button"
              id="web-search-source"
              data-testid="settings-web-search"
              onClick={(e) => {
                e.preventDefault();
                console.log('🔍 Web Search toggle clicked');
                toggleFeature('useWebSearch');
              }}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors cursor-pointer ${
                useWebSearch
                  ? 'bg-primary'
                  : 'bg-muted'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-background transition-transform pointer-events-none ${
                  useWebSearch
                    ? 'translate-x-6'
                    : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="knowledge-graph-source" className="text-base font-medium">
                🕸️ Knowledge Graph
              </Label>
              <p className="text-sm text-muted-foreground">
                Include related entities from knowledge graph
              </p>
            </div>
            <button
              type="button"
              id="knowledge-graph-source"
              onClick={(e) => {
                e.preventDefault();
                console.log('🔍 Knowledge Graph toggle clicked');
                toggleFeature('useGraph');
              }}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors cursor-pointer ${
                useGraph
                  ? 'bg-primary'
                  : 'bg-muted'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-background transition-transform pointer-events-none ${
                  useGraph
                    ? 'translate-x-6'
                    : 'translate-x-1'
                }`}
              />
            </button>
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

