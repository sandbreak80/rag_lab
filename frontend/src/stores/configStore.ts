import { create } from 'zustand';
import { RAGConfig, MetadataFilters } from '../types/config';
import { saveToLocalStorage, loadFromLocalStorage } from '../utils/localStorage';

const DEFAULT_CONFIG: RAGConfig = {
  model: 'llama3.2:3b',
  temperature: 0.7,
  topK: 5,
  contextWindow: 4096,
  maxTokens: 512,  // Default max tokens for LLM response
  useQueryExpansion: false,
  useBM25: false,
  useHybrid: false,
  useGraph: false,
  useReranking: false,
  useWebSearch: false,
  useAgenticChunking: false,
  useSecurity: true, // Security enabled by default
  webSearchDocs: 20,  // Increased from 5 to 20
  webSearchPages: 5,  // Increased from 1 to 5
  rerankTopK: 10,

  // New intelligence features (Nov 5, 2025) - All optional, off by default for now
  usePromptEnhancement: false,
  useAutoModelRouting: false,
  useQueryDecomposition: false,
  useSelfRAG: false,
  showReasoningProcess: true,  // Show reasoning by default for transparency

  // Data source toggles - All enabled by default
  useVectorDB: true,
  useResearchAgent: true,
};

interface ConfigStore extends RAGConfig {
  // Current preset name (for highlighting)
  currentPreset?: string;

  // Actions
  setModel: (model: string) => void;
  setTemperature: (temperature: number) => void;
  setTopK: (topK: number) => void;
  setContextWindow: (contextWindow: number) => void;
  setMaxTokens: (maxTokens: number) => void;
  toggleFeature: (feature: keyof RAGConfig) => void;
  setWebSearchDocs: (docs: number) => void;
  setWebSearchPages: (pages: number) => void;
  setRerankTopK: (topK: number) => void;
  setMetadataFilters: (filters: MetadataFilters) => void;
  updateConfig: (config: Partial<RAGConfig>) => void;
  loadPreset: (config: Partial<RAGConfig>) => void;
  reset: () => void;
  getConfig: () => RAGConfig;
}

export const useConfigStore = create<ConfigStore>((set, get) => {
  // CONFIG VERSION CHECK - Force reset if localStorage is outdated
  const CONFIG_VERSION = 3; // Increment this when adding new config properties (Added useQueryDecomposition)
  const savedVersion = localStorage.getItem('rag_config_version');

  if (savedVersion !== String(CONFIG_VERSION)) {
    console.log('🔄 Config version mismatch. Resetting to defaults with new features...');
    localStorage.removeItem('rag_config');
    localStorage.setItem('rag_config_version', String(CONFIG_VERSION));
  }

  // Load initial config from localStorage (including currentPreset)
  const savedConfig = loadFromLocalStorage<RAGConfig & { currentPreset?: string }>('rag_config', DEFAULT_CONFIG);

  // CRITICAL: Merge with DEFAULT_CONFIG to ensure new properties exist
  // This handles when localStorage has old config without new intelligence features
  const mergedConfig = {
    ...DEFAULT_CONFIG,
    ...savedConfig,
  };

  // DEBUG: Log what config is being loaded
  console.log('🔍 ConfigStore initialized with:', {
    topK: mergedConfig.topK,
    useWebSearch: mergedConfig.useWebSearch,
    webSearchDocs: mergedConfig.webSearchDocs,
    usePromptEnhancement: mergedConfig.usePromptEnhancement,
    useAutoModelRouting: mergedConfig.useAutoModelRouting,
    useQueryDecomposition: mergedConfig.useQueryDecomposition,
    currentPreset: mergedConfig.currentPreset,
    source: savedConfig === DEFAULT_CONFIG ? 'DEFAULT' : 'LOCALSTORAGE_MERGED'
  });

  return {
    ...mergedConfig,
    currentPreset: mergedConfig.currentPreset, // Restore active preset

    setModel: (model) => {
      set({ model, currentPreset: undefined }); // Clear preset when manually changed
      saveToLocalStorage('rag_config', { ...get().getConfig(), currentPreset: undefined });
    },

    setTemperature: (temperature) => {
      set({ temperature, currentPreset: undefined }); // Clear preset when manually changed
      saveToLocalStorage('rag_config', { ...get().getConfig(), currentPreset: undefined });
    },

    setTopK: (topK) => {
      console.log('🔍 setTopK called with:', topK);
      set({ topK, currentPreset: undefined }); // Clear preset when manually changed
      const newConfig = { ...get().getConfig(), currentPreset: undefined };
      console.log('🔍 Saving config to localStorage:', { topK: newConfig.topK });
      saveToLocalStorage('rag_config', newConfig);
    },

    setContextWindow: (contextWindow) => {
      set({ contextWindow, currentPreset: undefined }); // Clear preset when manually changed
      saveToLocalStorage('rag_config', { ...get().getConfig(), currentPreset: undefined });
    },

    setMaxTokens: (maxTokens) => {
      set({ maxTokens, currentPreset: undefined }); // Clear preset when manually changed
      saveToLocalStorage('rag_config', { ...get().getConfig(), currentPreset: undefined });
    },

    toggleFeature: (feature) => {
      console.log('🔍 toggleFeature called for:', feature);
      set((state) => {
        const currentValue = state[feature];
        if (typeof currentValue === 'boolean') {
          console.log(`🔍 Toggling ${feature} from ${currentValue} to ${!currentValue}`);
          return { [feature]: !currentValue, currentPreset: undefined }; // Clear preset
        }
        return state;
      });
      // Save immediately after state update
      const newConfig = { ...get().getConfig(), currentPreset: undefined };
      console.log('🔍 Saving config to localStorage:', { [feature]: newConfig[feature as keyof RAGConfig] });
      saveToLocalStorage('rag_config', newConfig);
    },

    setWebSearchDocs: (webSearchDocs) => {
      set({ webSearchDocs, currentPreset: undefined }); // Clear preset when manually changed
      saveToLocalStorage('rag_config', { ...get().getConfig(), currentPreset: undefined });
    },

    setWebSearchPages: (webSearchPages) => {
      set({ webSearchPages, currentPreset: undefined }); // Clear preset when manually changed
      saveToLocalStorage('rag_config', { ...get().getConfig(), currentPreset: undefined });
    },

    setRerankTopK: (rerankTopK) => {
      set({ rerankTopK, currentPreset: undefined }); // Clear preset when manually changed
      saveToLocalStorage('rag_config', { ...get().getConfig(), currentPreset: undefined });
    },

    setMetadataFilters: (metadataFilters) => {
      set({ metadataFilters, currentPreset: undefined }); // Clear preset when manually changed
      saveToLocalStorage('rag_config', { ...get().getConfig(), currentPreset: undefined });
    },

    updateConfig: (config) => {
      set({ ...config, currentPreset: undefined }); // Clear preset when manually changed
      saveToLocalStorage('rag_config', { ...get().getConfig(), currentPreset: undefined });
    },

    loadPreset: (presetData: any) => {
      // Combine RAG config and LLM config
      const config = presetData.config || {};
      const llmConfig = presetData.llm_config || {};

      const newConfig = {
        ...config,
        model: llmConfig.model || get().model,
        temperature: llmConfig.temperature || get().temperature,
        contextWindow: llmConfig.context_window || get().contextWindow,
        maxTokens: llmConfig.max_tokens || get().maxTokens,  // Load max_tokens from preset
        // Map snake_case to camelCase
        useQueryExpansion: config.use_query_expansion !== undefined ? config.use_query_expansion : get().useQueryExpansion,
        useBM25: config.use_bm25 !== undefined ? config.use_bm25 : get().useBM25,
        useHybrid: config.use_hybrid !== undefined ? config.use_hybrid : get().useHybrid,
        useGraph: config.use_graph !== undefined ? config.use_graph : get().useGraph,
        useReranking: config.use_reranking !== undefined ? config.use_reranking : get().useReranking,
        useWebSearch: config.use_web_search !== undefined ? config.use_web_search : get().useWebSearch,
        useAgenticChunking: config.use_agentic_chunking !== undefined ? config.use_agentic_chunking : get().useAgenticChunking,
        useSecurity: config.use_security !== undefined ? config.use_security : get().useSecurity,
        // Intelligence features
        usePromptEnhancement: config.use_prompt_enhancement !== undefined ? config.use_prompt_enhancement : get().usePromptEnhancement,
        useAutoModelRouting: config.use_auto_model_routing !== undefined ? config.use_auto_model_routing : get().useAutoModelRouting,
        useQueryDecomposition: config.use_query_decomposition !== undefined ? config.use_query_decomposition : get().useQueryDecomposition,
        useSelfRAG: config.use_self_rag !== undefined ? config.use_self_rag : get().useSelfRAG,
        showReasoningProcess: config.show_reasoning_process !== undefined ? config.show_reasoning_process : get().showReasoningProcess,
        topK: config.top_k || get().topK,
        rerankTopK: config.rerank_top_k || get().rerankTopK,
        webSearchDocs: config.web_search_docs || get().webSearchDocs,
        webSearchPages: config.web_search_pages_per_doc || get().webSearchPages,
        currentPreset: presetData.name,  // Track which preset is active
      };

      set(newConfig);
      // Save with currentPreset included
      saveToLocalStorage('rag_config', { ...get().getConfig(), currentPreset: presetData.name });
    },

    reset: () => {
      set(DEFAULT_CONFIG);
      saveToLocalStorage('rag_config', DEFAULT_CONFIG);
    },

    getConfig: () => {
      const state = get();
      return {
        model: state.model,
        temperature: state.temperature,
        topK: state.topK,
        contextWindow: state.contextWindow,
        maxTokens: state.maxTokens,  // CRITICAL: Include maxTokens in getConfig()
        useQueryExpansion: state.useQueryExpansion,
        useBM25: state.useBM25,
        useHybrid: state.useHybrid,
        useGraph: state.useGraph,
        useReranking: state.useReranking,
        useWebSearch: state.useWebSearch,
        useAgenticChunking: state.useAgenticChunking,
        useSecurity: state.useSecurity,
        webSearchDocs: state.webSearchDocs,
        webSearchPages: state.webSearchPages,
        rerankTopK: state.rerankTopK,
        metadataFilters: state.metadataFilters,
        currentPreset: state.currentPreset, // Include currentPreset in config

        // New intelligence features
        usePromptEnhancement: state.usePromptEnhancement,
        useAutoModelRouting: state.useAutoModelRouting,
        useQueryDecomposition: state.useQueryDecomposition,
        useSelfRAG: state.useSelfRAG,
        showReasoningProcess: state.showReasoningProcess,

        // Data source toggles (ensure all are included)
        useVectorDB: state.useVectorDB,
        useResearchAgent: state.useResearchAgent,
        // Note: useWebSearch and useGraph already included above in legacy location
      };
    },
  };
});

