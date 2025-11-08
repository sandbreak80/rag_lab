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
  async sendMessage(query: string, config: RAGConfig, signal?: AbortSignal): Promise<{
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
    const response = await this.client.post('/v1/rag/query', {
      query,
      user_id: 'demo', // TODO: Get from auth
      groups: [], // TODO: Get from auth
    }, { signal });

    // Transform new API response to match old format
    return {
      answer: response.data.answer,
      sources: response.data.citations.map((c: any) => ({
        content: c.content || '',
        document_id: c.doc_id || c.document_id,
        score: 1.0,
        metadata: {
          version: c.version,
          chunk_id: c.chunk_id,
          source_uri: c.source_uri,
        },
      })),
      metrics: response.data.metrics,
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
    const response = await this.client.get('/documents');
    return response.data;
  }

  async uploadDocument(
    file: File,
    onProgress?: (progress: UploadProgress) => void
  ): Promise<{ success: boolean; message: string }> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.client.post('/upload', formData, {
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

