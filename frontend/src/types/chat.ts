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

