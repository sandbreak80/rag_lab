import { create } from 'zustand';
import { RAGConfig, MetadataFilters } from '../types/config';
import { saveToLocalStorage, loadFromLocalStorage } from '../utils/localStorage';

const DEFAULT_CONFIG: RAGConfig = {
  model: 'llama3.2:3b',
  temperature: 0.7,
  topK: 5,
  contextWindow: 4096,
  useQueryExpansion: false,
  useBM25: false,
  useHybrid: false,
  useGraph: false,
  useReranking: false,
  useWebSearch: false,
  useAgenticChunking: false,
  webSearchDocs: 5,
  webSearchPages: 1,
  rerankTopK: 10,
};

interface ConfigStore extends RAGConfig {
  // Current preset name (for highlighting)
  currentPreset?: string;

  // Actions
  setModel: (model: string) => void;
  setTemperature: (temperature: number) => void;
  setTopK: (topK: number) => void;
  setContextWindow: (contextWindow: number) => void;
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
  // Load initial config from localStorage (including currentPreset)
  const savedConfig = loadFromLocalStorage<RAGConfig & { currentPreset?: string }>('rag_config', DEFAULT_CONFIG);

  // DEBUG: Log what config is being loaded
  console.log('🔍 ConfigStore initialized with:', {
    topK: savedConfig.topK,
    useWebSearch: savedConfig.useWebSearch,
    webSearchDocs: savedConfig.webSearchDocs,
    currentPreset: savedConfig.currentPreset,
    source: savedConfig === DEFAULT_CONFIG ? 'DEFAULT' : 'LOCALSTORAGE'
  });

  return {
    ...savedConfig,
    currentPreset: savedConfig.currentPreset, // Restore active preset

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
        // Map snake_case to camelCase
        useQueryExpansion: config.use_query_expansion !== undefined ? config.use_query_expansion : get().useQueryExpansion,
        useBM25: config.use_bm25 !== undefined ? config.use_bm25 : get().useBM25,
        useHybrid: config.use_hybrid !== undefined ? config.use_hybrid : get().useHybrid,
        useGraph: config.use_graph !== undefined ? config.use_graph : get().useGraph,
        useReranking: config.use_reranking !== undefined ? config.use_reranking : get().useReranking,
        useWebSearch: config.use_web_search !== undefined ? config.use_web_search : get().useWebSearch,
        useAgenticChunking: config.use_agentic_chunking !== undefined ? config.use_agentic_chunking : get().useAgenticChunking,
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
        useQueryExpansion: state.useQueryExpansion,
        useBM25: state.useBM25,
        useHybrid: state.useHybrid,
        useGraph: state.useGraph,
        useReranking: state.useReranking,
        useWebSearch: state.useWebSearch,
        useAgenticChunking: state.useAgenticChunking,
        webSearchDocs: state.webSearchDocs,
        webSearchPages: state.webSearchPages,
        rerankTopK: state.rerankTopK,
        metadataFilters: state.metadataFilters,
        currentPreset: state.currentPreset, // Include currentPreset in config
      };
    },
  };
});

