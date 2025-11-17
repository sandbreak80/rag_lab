import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { RAGConfig } from '@/types/config';
import { useConfigStore } from '@/stores/configStore';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/services/api';

interface ConfigurationSelectorProps {
  label: string;
  value: RAGConfig | null;
  onChange: (config: RAGConfig) => void;
}

// Helper function to convert preset data to RAGConfig without modifying global store
function presetToRAGConfig(preset: any, currentConfig: RAGConfig): RAGConfig {
  const config = preset.config || {};
  const llmConfig = preset.llm_config || {};

  return {
    ...currentConfig, // Start with current config as base
    // Map LLM config
    model: llmConfig.model || currentConfig.model,
    temperature: llmConfig.temperature !== undefined ? llmConfig.temperature : currentConfig.temperature,
    contextWindow: llmConfig.context_window || currentConfig.contextWindow,
    maxTokens: llmConfig.max_tokens || currentConfig.maxTokens,  // CRITICAL: Map max_tokens from preset
    // Map RAG config (snake_case to camelCase)
    useQueryExpansion: config.use_query_expansion !== undefined ? config.use_query_expansion : currentConfig.useQueryExpansion,
    useBM25: config.use_bm25 !== undefined ? config.use_bm25 : currentConfig.useBM25,
    useHybrid: config.use_hybrid !== undefined ? config.use_hybrid : currentConfig.useHybrid,
    useGraph: config.use_graph !== undefined ? config.use_graph : currentConfig.useGraph,
    useReranking: config.use_reranking !== undefined ? config.use_reranking : currentConfig.useReranking,
    useWebSearch: config.use_web_search !== undefined ? config.use_web_search : currentConfig.useWebSearch,
    useAgenticChunking: config.use_agentic_chunking !== undefined ? config.use_agentic_chunking : currentConfig.useAgenticChunking,
    useSecurity: config.use_security !== undefined ? config.use_security : currentConfig.useSecurity,
    // Intelligence features
    usePromptEnhancement: config.use_prompt_enhancement !== undefined ? config.use_prompt_enhancement : currentConfig.usePromptEnhancement,
    useAutoModelRouting: config.use_auto_model_routing !== undefined ? config.use_auto_model_routing : currentConfig.useAutoModelRouting,
    useQueryDecomposition: config.use_query_decomposition !== undefined ? config.use_query_decomposition : currentConfig.useQueryDecomposition,
    useSelfRAG: config.use_self_rag !== undefined ? config.use_self_rag : currentConfig.useSelfRAG,
    showReasoningProcess: config.show_reasoning_process !== undefined ? config.show_reasoning_process : currentConfig.showReasoningProcess,
    // Numeric configs
    topK: config.top_k !== undefined ? config.top_k : currentConfig.topK,
    rerankTopK: config.rerank_top_k !== undefined ? config.rerank_top_k : currentConfig.rerankTopK,
    webSearchDocs: config.web_search_docs !== undefined ? config.web_search_docs : currentConfig.webSearchDocs,
    webSearchPages: config.web_search_pages_per_doc !== undefined ? config.web_search_pages_per_doc : currentConfig.webSearchPages,
    // Data source toggles
    useVectorDB: config.use_vector_db !== undefined ? config.use_vector_db : currentConfig.useVectorDB,
    useResearchAgent: config.enable_research !== undefined ? config.enable_research : currentConfig.useResearchAgent,
  };
}

export function ConfigurationSelector({
  label,
  value,
  onChange
}: ConfigurationSelectorProps) {
  const getConfig = useConfigStore((state) => state.getConfig);
  const defaultConfig = getConfig();

  const { data: presets } = useQuery({
    queryKey: ['presets'],
    queryFn: () => api.getPresets(),
  });

  // Determine if we're showing custom based on whether value matches a preset
  const isCustomConfig = React.useMemo(() => {
    if (!value || !presets) return false;
    // Check if current config matches any preset
    const matchingPreset = presets.find((p: any) => {
      const presetConfig = p.config || {};
      const llmConfig = p.llm_config || {};
      return (
        value.model === llmConfig.model &&
        value.topK === presetConfig.top_k &&
        value.contextWindow === llmConfig.context_window &&
        value.useWebSearch === presetConfig.use_web_search &&
        value.useReranking === presetConfig.use_reranking &&
        value.useGraph === presetConfig.use_graph
      );
    });
    return !matchingPreset;
  }, [value, presets]);

  const [showCustom, setShowCustom] = React.useState(isCustomConfig);
  const [selectedPresetName, setSelectedPresetName] = React.useState<string | null>(null);

  const handlePresetSelect = (presetName: string) => {
    const preset = presets?.find((p: any) => p.name?.toLowerCase() === presetName.toLowerCase());
    if (preset) {
      // Convert preset to RAGConfig WITHOUT modifying global store
      const presetConfig = presetToRAGConfig(preset, value || defaultConfig);
      onChange(presetConfig);
      setShowCustom(false);
      setSelectedPresetName(preset.name);
    }
  };

  const handleUseCustom = () => {
    // Get current config and set it as custom
    const currentConfig = getConfig();
    onChange(currentConfig);
    setShowCustom(true);
    setSelectedPresetName(null);
  };

  if (!value) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{label}</CardTitle>
          <CardDescription>Select a configuration</CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={() => onChange(defaultConfig)}>
            Use Current Settings
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{label}</CardTitle>
        <CardDescription>
          {showCustom ? 'Custom Configuration' : 'Select Preset or Custom'}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {!showCustom ? (
          <div className="space-y-2">
            <div className="grid grid-cols-2 gap-2">
              {presets?.map((preset: any) => {
                const enabledFeatures = [];
                if (preset.config?.use_reranking) enabledFeatures.push('Rerank');
                if (preset.config?.use_web_search) enabledFeatures.push('Web');
                if (preset.config?.use_graph) enabledFeatures.push('KG');
                if (preset.config?.use_prompt_enhancement) enabledFeatures.push('Prompt+');
                if (preset.config?.use_auto_model_routing) enabledFeatures.push('AutoRoute');
                if (preset.config?.use_query_decomposition) enabledFeatures.push('Decomp');
                if (preset.config?.use_self_rag) enabledFeatures.push('Self-RAG');

                return (
                  <div key={preset.name} className="space-y-1">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handlePresetSelect(preset.name)}
                      className="text-xs w-full"
                    >
                      {preset.name}
                    </Button>
                    {enabledFeatures.length > 0 && (
                      <div className="text-xs text-muted-foreground px-1">
                        {enabledFeatures.join(', ')}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
            <Button
              variant="outline"
              onClick={handleUseCustom}
              className="w-full"
            >
              Use Custom Configuration
            </Button>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="text-sm space-y-1">
              <div><strong>Model:</strong> {value.model}</div>
              <div><strong>Top-K:</strong> {value.topK}</div>
              <div><strong>Context Window:</strong> {value.contextWindow}</div>
              <div><strong>Web Search:</strong> {value.useWebSearch ? 'Yes' : 'No'}</div>
              <div><strong>Reranking:</strong> {value.useReranking ? 'Yes' : 'No'}</div>
              <div><strong>Knowledge Graph:</strong> {value.useGraph ? 'Yes' : 'No'}</div>
              <div><strong>Research Agent:</strong> {value.useResearchAgent ? 'Yes' : 'No'}</div>
            </div>
            <p className="text-xs text-muted-foreground">
              Using current settings from main configuration panel. Adjust settings there and click "Use Current Settings" to update.
            </p>
            <Button
              variant="outline"
              onClick={() => {
                const updatedConfig = getConfig();
                onChange(updatedConfig);
                setSelectedPresetName(null);
              }}
              className="w-full"
            >
              Refresh from Current Settings
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                setShowCustom(false);
                setSelectedPresetName(null);
              }}
              className="w-full"
            >
              Select Preset Instead
            </Button>
          </div>
        )}

        {/* Configuration Preview */}
        {value && (
          <div className="mt-4 p-3 bg-muted rounded-md text-xs">
            <div className="font-semibold mb-2">
              Current Configuration:
              {selectedPresetName && !isCustomConfig && (
                <span className="ml-2 px-2 py-0.5 bg-primary/20 text-primary rounded text-xs font-normal">
                  {selectedPresetName}
                </span>
              )}
              {isCustomConfig && (
                <span className="ml-2 px-2 py-0.5 bg-orange-100 text-orange-800 rounded text-xs font-normal">
                  Custom
                </span>
              )}
            </div>
            <div className="grid grid-cols-2 gap-x-4 gap-y-1">
              <div><strong>Model:</strong> {value.model}</div>
              <div><strong>Temperature:</strong> {value.temperature}</div>
              <div><strong>Top-K:</strong> {value.topK}</div>
              <div><strong>Rerank Top-K:</strong> {value.rerankTopK}</div>
              <div><strong>Context Window:</strong> {value.contextWindow}</div>
              <div><strong>Max Tokens:</strong> {value.contextWindow}</div>
              <div><strong>Web Search:</strong> {value.useWebSearch ? 'Yes' : 'No'}</div>
              {value.useWebSearch && (
                <>
                  <div><strong>Web Docs:</strong> {value.webSearchDocs}</div>
                  <div><strong>Web Pages:</strong> {value.webSearchPages}</div>
                </>
              )}
              <div><strong>Reranking:</strong> {value.useReranking ? 'Yes' : 'No'}</div>
              <div><strong>Knowledge Graph:</strong> {value.useGraph ? 'Yes' : 'No'}</div>
              <div><strong>Research Agent:</strong> {value.useResearchAgent ? 'Yes' : 'No'}</div>
              <div><strong>Vector DB:</strong> {value.useVectorDB ? 'Yes' : 'No'}</div>
              <div><strong>Query Expansion:</strong> {value.useQueryExpansion ? 'Yes' : 'No'}</div>
              <div><strong>BM25:</strong> {value.useBM25 ? 'Yes' : 'No'}</div>
              <div><strong>Hybrid Search:</strong> {value.useHybrid ? 'Yes' : 'No'}</div>
              <div><strong>Prompt Enhancement:</strong> {value.usePromptEnhancement ? 'Yes' : 'No'}</div>
              <div><strong>Auto Model Routing:</strong> {value.useAutoModelRouting ? 'Yes' : 'No'}</div>
              <div><strong>Query Decomposition:</strong> {value.useQueryDecomposition ? 'Yes' : 'No'}</div>
              <div><strong>Self-RAG:</strong> {value.useSelfRAG ? 'Yes' : 'No'}</div>
              <div><strong>Show Reasoning:</strong> {value.showReasoningProcess ? 'Yes' : 'No'}</div>
              <div><strong>Security:</strong> {value.useSecurity ? 'Yes' : 'No'}</div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

