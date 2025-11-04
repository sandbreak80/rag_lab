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
  source?: 'rag' | 'web_search';  // Source type
  metadata?: {
    tags?: string[];
    page?: number;
    section?: string;
    url?: string;  // For web sources
    engine?: string;  // Search engine (google, bing, etc.)
    title?: string;  // Web page title
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
  // Search Service Components
  query_expansion_ms?: number;
  vector_search_ms?: number;
  bm25_search_ms?: number;
  hybrid_fusion_ms?: number;
  graph_expansion_ms?: number;
  reranking_ms?: number;
  web_search_ms?: number;
  
  // LLM Components (from Ollama)
  llm_generation_ms?: number;
  llm_prompt_eval_duration_ms?: number;  // Time to process prompt
  llm_eval_duration_ms?: number;         // Time to generate tokens
  llm_tokens_generated?: number;
  llm_tokens_prompt?: number;
  llm_tokens_per_second?: number;
  
  // Service Latencies
  search_service_latency_ms?: number;
  chat_service_overhead_ms?: number;
  
  // Total
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

