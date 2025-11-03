// Chat Message Types
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  sources?: Source[];
  metadata?: MessageMetadata;
}

export interface Source {
  file_name: string;
  chunk_text: string;
  score: number;
  metadata?: {
    tags?: string[];
    page?: number;
    section?: string;
  };
}

export interface MessageMetadata {
  model?: string;
  temperature?: number;
  topK?: number;
  features_used?: string[];
  latency?: number;
  token_count?: number;
  performance?: PerformanceMetrics;
}

export interface PerformanceMetrics {
  query_expansion_ms?: number;
  vector_search_ms?: number;
  bm25_search_ms?: number;
  hybrid_fusion_ms?: number;
  graph_expansion_ms?: number;
  reranking_ms?: number;
  web_search_ms?: number;
  llm_generation_ms?: number;
  total_latency_ms?: number;
}

// Chat Session
export interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  created_at: Date;
  updated_at: Date;
}

// Streaming Response
export interface StreamChunk {
  type: 'content' | 'sources' | 'metadata' | 'error' | 'done';
  data: any;
}

