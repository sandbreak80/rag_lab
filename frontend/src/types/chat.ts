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
  source?: 'rag' | 'web_search' | 'research';  // Source type
  origin_tool?: string;  // 'rag' | 'web' | 'research' - from API
  title?: string;  // Title (for web/research sources)
  url?: string;  // URL (for web/research sources)
  metadata?: {
    tags?: string[];
    page?: number;
    section?: string;
    url?: string;  // For web sources
    engine?: string;  // Search engine (google, bing, etc.)
    title?: string;  // Web page title
  };
}

export interface SecurityViolation {
  type: string;
  severity: string;
  details: string;
}

export interface SecurityInfo {
  violations?: SecurityViolation[];
  cleaned_query_used?: boolean;
}

export interface QueryDecomposition {
  needs_decomposition: boolean;
  complexity: 'simple' | 'moderate' | 'complex';
  sub_queries: string[];
  original_query: string;
}

export interface StageTimings {
  vector_ms?: number;
  web_ms?: number;
  llm_ms?: number;
  total_ms?: number;
  retrieve_parallel_ms?: number;
  web_skipped?: boolean;
  web_reason?: 'disabled' | 'early_stop' | 'timeout' | 'ok';
  web_enabled?: boolean;
}

export interface MessageMetadata {
  model?: string;
  temperature?: number;
  topK?: number;
  features_used?: string[];
  latency?: number;
  token_count?: number;
  performance?: PerformanceMetrics;
  stage_timings?: StageTimings;  // New stage timings format
  security?: SecurityInfo;
  decomposition?: QueryDecomposition;
}

export interface PerformanceMetrics {
  // Search Service Components
  query_expansion_ms?: number;
  vector_search_ms?: number;
  bm25_search_ms?: number;
  fusion_ms?: number;
  hybrid_fusion_ms?: number;
  graph_enhancement_ms?: number;
  graph_expansion_ms?: number;
  reranking_ms?: number;
  web_search_ms?: number;
  // LLM Components
  llm_generation_ms?: number;
  llm_prompt_eval_duration_ms?: number;
  llm_eval_duration_ms?: number;
  llm_tokens_generated?: number;
  llm_tokens_prompt?: number;
  llm_tokens_per_second?: number;
  // Service Latencies
  search_service_latency_ms?: number;
  chat_service_overhead_ms?: number;
  // Security & Enhancement (NEW - for learning lab visibility)
  security_validation_ms?: number;
  prompt_enhancement_ms?: number;
  query_decomposition_ms?: number;
  // Infrastructure (NEW - API Gateway overhead)
  rate_limit_check_ms?: number;
  api_gateway_overhead_ms?: number;
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

