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
  useQueryDecomposition?: boolean; // Break complex queries into sub-queries
  useSelfRAG?: boolean;            // Self-reflective RAG with quality assessment
  showReasoningProcess?: boolean;  // Show/hide ReAct framework scaffolding

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
  documentTypes?: string[];  // ['pdf', 'markdown', 'txt', etc.]
  dateRange?: {
    start?: string;          // ISO date string
    end?: string;            // ISO date string
  };
  tags?: string[];           // ['AI', 'RAG', 'LLM', etc.]
  sources?: string[];        // ['research-agent', 'upload', 'web-search']
  authors?: string[];        // Author names
}

// Available filter options
export interface FilterOptions {
  documentTypes: string[];
  tags: string[];
  sources: string[];
  authors: string[];
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

