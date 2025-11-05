// RAG Configuration Types
export interface RAGConfig {
  model: string;
  temperature: number;
  topK: number;
  contextWindow: number;
  useQueryExpansion: boolean;
  useBM25: boolean;
  useHybrid: boolean;
  useGraph: boolean;
  useReranking: boolean;
  useWebSearch: boolean;
  useAgenticChunking: boolean;
  useSecurity: boolean;
  webSearchDocs: number;
  webSearchPages: number;
  rerankTopK: number;
  metadataFilters?: MetadataFilters;

  // New intelligence features (Nov 5, 2025)
  usePromptEnhancement?: boolean;  // Enable intelligent prompt enhancement
  useAutoModelRouting?: boolean;   // Enable automatic model selection

  // Data source toggles
  useVectorDB?: boolean;           // Search uploaded/ingested documents
  useResearchAgent?: boolean;      // Include research agent discoveries
}

export interface DataSourceFilters {
  vectorDB: boolean;       // Uploaded documents
  researchAgent: boolean;  // Auto-discovered research
  webSearch: boolean;      // Web search results
  knowledgeGraph: boolean; // Knowledge graph entities
}

export interface MetadataFilters {
  documentTypes?: string[];
  dateRange?: {
    start?: string;
    end?: string;
  };
  tags?: string[];
  authors?: string[];
}

export interface ConfigPreset {
  name: string;
  description: string;
  config: Partial<RAGConfig>;
  feature_impacts: {
    [key: string]: {
      latency_ms: number;
      quality_boost: string;
      cost: string;
    };
  };
}

// System Stats
export interface SystemStats {
  chunks: number;
  documents: string[];
  unique_tags: number;
  bm25_index_size: number;
  knowledge_graph_nodes: number;
  knowledge_graph_edges: number;
}

// Model Information
export interface OllamaModel {
  name: string;
  model: string;
  modified_at: string;
  size: number;
  digest: string;
  details: {
    parent_model: string;
    format: string;
    family: string;
    families: string[];
    parameter_size: string;
    quantization_level: string;
  };
}

