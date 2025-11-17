import axios, { AxiosInstance } from 'axios';
import { RAGConfig, ConfigPreset, SystemStats, OllamaModel } from '../types/config';
import { ChatMessage, Source } from '../types/chat';
import { QueryMetric } from '../types/metrics';
import { Document, UploadProgress } from '../types/documents';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: '/api',
      timeout: 1800000, // 30 minutes timeout - allows Maximum preset to complete (lunch break testing)
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  // Chat endpoints
  async getResponse(requestId: string): Promise<{
    answer: string;
    sources: Source[];
    metrics: any;
    security?: {
      violations: any[];
      cleaned_query_used: boolean;
    };
    decomposition?: {
      needs_decomposition: boolean;
      complexity: 'simple' | 'moderate' | 'complex';
      sub_queries: string[];
      original_query: string;
    };
    trace_id?: string;
    request_id?: string;
    tokens_in?: number;
    tokens_out?: number;
    cost_usd?: number;
    stage_timings?: any;
  }> {
    const response = await this.client.get(`/v1/rag/response/${requestId}`);
    // Transform API response to match expected format
    return {
      answer: response.data.answer,
      sources: (response.data.citations || []).map((c: any, idx: number) => ({
        file_name: c.doc_id || `Document ${idx + 1}`,
        chunk_text: c.content || `Citation from ${c.doc_id || c.source_uri || 'unknown source'}`,
        score: c.score || 0.95,
        source: c.origin_tool as 'rag' | 'web_search' || 'rag',
        metadata: {
          tags: c.tags || [],
          url: c.source_uri,
          title: c.doc_id,
        },
      })),
      metrics: {
        total_latency_ms: response.data.metrics?.latency_ms || 0,
        llm_tokens_generated: response.data.metrics?.tokens_out || 0,
        llm_tokens_prompt: response.data.metrics?.tokens_in || 0,
        vector_search_ms: response.data.artifacts?.retrieval_log?.timing_ms || 0,
        reranking_ms: response.data.artifacts?.reranking_ms || 0,
        llm_generation_ms: response.data.metrics?.latency_ms || 0,
      },
      trace_id: response.data.trace_id,
      request_id: response.data.request_id,
      tokens_in: response.data.metrics?.tokens_in,
      tokens_out: response.data.metrics?.tokens_out,
      cost_usd: response.data.metrics?.cost_usd,
      stage_timings: response.data.artifacts?.stage_timings,
    };
  }

  async sendMessage(query: string, config: RAGConfig, signal?: AbortSignal, requestId?: string): Promise<{
    answer: string;
    sources: Source[];
    metrics: any;
    security?: {
      violations: any[];
      cleaned_query_used: boolean;
    };
    decomposition?: {
      needs_decomposition: boolean;
      complexity: 'simple' | 'moderate' | 'complex';
      sub_queries: string[];
      original_query: string;
    };
    trace_id?: string;
    request_id?: string;
    tokens_in?: number;
    tokens_out?: number;
    cost_usd?: number;
    stage_timings?: any;
  }> {
    // Convert camelCase to snake_case for backend
    const backendConfig = {
      query,
      model: config.model,
      temperature: config.temperature,
      top_k: config.topK,
      context_window: config.contextWindow,
      use_query_expansion: config.useQueryExpansion,
      use_bm25: config.useBM25,
      use_hybrid: config.useHybrid,
      use_graph: config.useGraph,
      use_reranking: config.useReranking,
      use_web_search: config.useWebSearch,
      use_agentic_chunking: config.useAgenticChunking,
      use_security: config.useSecurity,
      web_search_docs: config.webSearchDocs,
      web_search_pages_per_doc: config.webSearchPages,
      rerank_top_k: config.rerankTopK,
      metadata_filters: config.metadataFilters,
      // Intelligence features
      use_enhancement: config.usePromptEnhancement,
      use_auto_routing: config.useAutoModelRouting,
      use_query_decomposition: config.useQueryDecomposition,
      // Data source toggles
      use_vector_db: config.useVectorDB,
      use_research_agent: config.useResearchAgent,
    };

    console.log('🔍 API sending request with config:', {
      top_k: backendConfig.top_k,
      use_web_search: backendConfig.use_web_search,
      web_search_docs: backendConfig.web_search_docs,
      use_enhancement: backendConfig.use_enhancement,
      use_auto_routing: backendConfig.use_auto_routing,
      use_query_decomposition: backendConfig.use_query_decomposition,
      use_vector_db: backendConfig.use_vector_db,
      use_research_agent: backendConfig.use_research_agent,
    });

    // Use NEW RAG API v1 (with observability) instead of OLD broken pipeline
    const payload: any = {
      query,
      user_id: 'demo', // TODO: Get from auth
      groups: [], // TODO: Get from auth
      top_k: backendConfig.top_k, // CRITICAL: Send top_k from config
      web_search_enabled: backendConfig.use_web_search,
      use_graph: backendConfig.use_graph,
      enable_research: backendConfig.use_research_agent,
    };

    // If request_id provided, use it (for response caching after refresh)
    if (requestId) {
      payload.request_id = requestId;
    }

    const response = await this.client.post('/v1/rag/query', payload, { signal });

    // Transform new API response to match old format
    return {
      answer: response.data.answer,
      // Use sources instead of citations - sources contains ALL retrieved results
      sources: (response.data.sources || []).map((s: any, idx: number) => ({
        file_name: s.doc_id || `Document ${idx + 1}`,
        chunk_text: s.content || s.snippet || `Source from ${s.doc_id || s.url || 'unknown source'}`,
        score: s.score || 0.95,
        source: s.origin_tool as 'rag' | 'web_search' || 'rag',
        metadata: {
          tags: s.tags || [],
          url: s.url || s.source_uri,
          title: s.title || s.doc_id,
        },
      })),
      metrics: {
        // Map API metrics to expected format
        total_latency_ms: response.data.metrics?.latency_ms || 0,
        llm_tokens_generated: response.data.metrics?.tokens_out || 0,
        llm_tokens_prompt: response.data.metrics?.tokens_in || 0,
        // Add stage timings if available (from artifacts)
        vector_search_ms: response.data.artifacts?.retrieval_log?.timing_ms || 0,
        reranking_ms: response.data.artifacts?.reranking_ms || 0,
        llm_generation_ms: response.data.metrics?.latency_ms || 0,
      },
      // Include RAG API v1 observability fields
      trace_id: response.data.trace_id,
      request_id: response.data.request_id,
      tokens_in: response.data.metrics?.tokens_in,
      tokens_out: response.data.metrics?.tokens_out,
      cost_usd: response.data.metrics?.cost_usd,
      // Stage timings from artifacts
      stage_timings: response.data.artifacts?.stage_timings,
    };
  }

  async cancelRequest(): Promise<{ success: boolean; message: string }> {
    const response = await this.client.post('/cancel');
    return response.data;
  }

  async searchDocuments(query: string, config: Partial<RAGConfig>): Promise<{
    results: Source[];
    metrics: any;
  }> {
    const response = await this.client.post('/search', {
      query,
      ...config,
    });
    return response.data;
  }

  // Document endpoints
  async getDocuments(): Promise<{ documents: string[]; count: number }> {
    const response = await this.client.get('/v1/documents');
    return response.data;
  }

  async uploadDocument(
    file: File,
    onProgress?: (progress: UploadProgress) => void
  ): Promise<{ success: boolean; message: string }> {
    const formData = new FormData();
    formData.append('files', file);  // Backend expects 'files' (plural)
    formData.append('perms_tag', 'public');  // Default to public

    const response = await this.client.post('/v1/documents', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress({
            filename: file.name,
            progress: percentCompleted,
            status: percentCompleted === 100 ? 'processing' : 'uploading',
          });
        }
      },
    });

    return response.data;
  }

  async getStats(): Promise<SystemStats> {
    const response = await this.client.get('/stats');
    return response.data;
  }

  async getVersions(): Promise<any> {
    const response = await this.client.get('/version');
    return response.data;
  }

  // Settings endpoints
  async getPresets(): Promise<ConfigPreset[]> {
    const response = await this.client.get('/presets');
    return response.data;
  }

  async getModels(): Promise<OllamaModel[]> {
    const response = await this.client.get('/models');
    return response.data.models || [];
  }

  // Metrics endpoints
  async getMetrics(): Promise<QueryMetric[]> {
    const response = await this.client.get('/metrics');
    return response.data.metrics || [];
  }

  async logMetric(metric: QueryMetric): Promise<void> {
    await this.client.post('/metrics', metric);
  }

  async clearMetrics(): Promise<void> {
    await this.client.delete('/metrics');
  }

  // Lab endpoints
  async getLabProgress(): Promise<{ [key: string]: boolean }> {
    const response = await this.client.get('/lab/progress');
    return response.data.progress || {};
  }

  async updateLabProgress(exerciseId: string, completed: boolean): Promise<void> {
    await this.client.post('/lab/progress', {
      exercise_id: exerciseId,
      completed,
    });
  }

  // Admin endpoints
  async resetDatabase(): Promise<{ status: string; message: string }> {
    const response = await this.client.post('/admin/reset');
    return response.data;
  }

  async resetKnowledgeGraph(): Promise<{ status: string; message: string }> {
    const response = await this.client.post('/admin/reset-kg');
    return response.data;
  }

  async getKGAlgorithms(): Promise<{ algorithms: any; default: string }> {
    const response = await this.client.get('/kg/algorithms');
    return response.data;
  }

  async buildKnowledgeGraph(algorithm: string): Promise<{ success: boolean; stats: any }> {
    const response = await this.client.post('/kg/build', { algorithm });
    return response.data;
  }

  // Feedback endpoint
  async submitFeedback(feedback: {
    rating: number;
    categories: string[];
    comments: string;
  }): Promise<{ success: boolean }> {
    const response = await this.client.post('/feedback', feedback);
    return response.data;
  }

  // GPU status endpoint
  async getGPUStatus(): Promise<{
    gpu_available: boolean;
    gpu_enabled: boolean;
    gpu_info: string;
    ollama_accessible: boolean;
    mode: string;
    recommendation: string;
  }> {
    const response = await this.client.get('/gpu_status');
    return response.data;
  }
}

export const api = new ApiClient();

