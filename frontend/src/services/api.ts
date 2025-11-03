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
  }> {
    const response = await this.client.post('/ask', {
      query,
      ...config,
    }, { signal });
    return response.data;
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
}

export const api = new ApiClient();

