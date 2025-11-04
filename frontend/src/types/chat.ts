// Chat Message Types
import { PerformanceMetrics } from './performance';

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

