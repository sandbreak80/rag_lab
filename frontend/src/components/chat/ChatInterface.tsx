import React, { useRef, useEffect, useMemo } from 'react';
import { useMutation } from '@tanstack/react-query';
import { api } from '../../services/api';
import { useConfigStore } from '../../stores/configStore';
import { useMetricsStore } from '../../stores/metricsStore';
import { useChatStore } from '../../stores/chatStore';
import { ChatMessage } from '../../types/chat';
import { MessageList } from './MessageList';
import { InputBar } from './InputBar';
import { generateId } from '../../utils/formatting';

export function ChatInterface() {
  const messages = useChatStore((state) => state.messages);
  const isLoading = useChatStore((state) => state.isLoading);
  const addMessage = useChatStore((state) => state.addMessage);
  const setLoading = useChatStore((state) => state.setLoading);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Cancel token for aborting requests
  const abortControllerRef = useRef<AbortController | null>(null);

  // Select individual properties to avoid creating new objects
  const model = useConfigStore((state) => state.model);
  const temperature = useConfigStore((state) => state.temperature);
  const topK = useConfigStore((state) => state.topK);
  const contextWindow = useConfigStore((state) => state.contextWindow);
  const useQueryExpansion = useConfigStore((state) => state.useQueryExpansion);
  const useBM25 = useConfigStore((state) => state.useBM25);
  const useHybrid = useConfigStore((state) => state.useHybrid);
  const useGraph = useConfigStore((state) => state.useGraph);
  const useReranking = useConfigStore((state) => state.useReranking);
  const useWebSearch = useConfigStore((state) => state.useWebSearch);
  const useAgenticChunking = useConfigStore((state) => state.useAgenticChunking);
  const webSearchDocs = useConfigStore((state) => state.webSearchDocs);
  const webSearchPages = useConfigStore((state) => state.webSearchPages);
  const rerankTopK = useConfigStore((state) => state.rerankTopK);
  const metadataFilters = useConfigStore((state) => state.metadataFilters);

  // Memoize config object - only recreates when values actually change
  const config = useMemo(() => ({
    model,
    temperature,
    topK,
    contextWindow,
    useQueryExpansion,
    useBM25,
    useHybrid,
    useGraph,
    useReranking,
    useWebSearch,
    useAgenticChunking,
    webSearchDocs,
    webSearchPages,
    rerankTopK,
    metadataFilters,
  }), [
    model,
    temperature,
    topK,
    contextWindow,
    useQueryExpansion,
    useBM25,
    useHybrid,
    useGraph,
    useReranking,
    useWebSearch,
    useAgenticChunking,
    webSearchDocs,
    webSearchPages,
    rerankTopK,
    metadataFilters,
  ]);

  const addMetric = useMetricsStore((state) => state.addQuery);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const chatMutation = useMutation({
    mutationFn: (query: string) => {
      // Create new abort controller for this request
      abortControllerRef.current = new AbortController();
      return api.sendMessage(query, config, abortControllerRef.current.signal);
    },
    onSuccess: (data, query) => {
      const assistantMessage: ChatMessage = {
        id: generateId(),
        role: 'assistant',
        content: data.answer,
        timestamp: new Date(),
        sources: data.sources,
        metadata: {
          model: config.model,
          temperature: config.temperature,
          topK: config.topK,
          latency: data.metrics?.total_latency_ms,
          performance: data.metrics ? {
            // Search Service Components
            query_expansion_ms: data.metrics.query_expansion_ms,
            vector_search_ms: data.metrics.vector_search_ms,
            bm25_search_ms: data.metrics.bm25_search_ms,
            hybrid_fusion_ms: data.metrics.fusion_ms,
            graph_enhancement_ms: data.metrics.graph_enhancement_ms,
            reranking_ms: data.metrics.reranking_ms,
            web_search_ms: data.metrics.web_search_ms,
            // LLM Components
            llm_generation_ms: data.metrics.llm_generation_ms,
            llm_prompt_eval_duration_ms: data.metrics.llm_prompt_eval_duration_ms,
            llm_eval_duration_ms: data.metrics.llm_eval_duration_ms,
            llm_tokens_generated: data.metrics.llm_tokens_generated,
            llm_tokens_prompt: data.metrics.llm_tokens_prompt,
            llm_tokens_per_second: data.metrics.llm_tokens_per_second,
            // Service Latencies
            search_service_latency_ms: data.metrics.search_service_latency_ms,
            chat_service_overhead_ms: data.metrics.chat_service_overhead_ms,
            // Total
            total_latency_ms: data.metrics.total_latency_ms,
          } : undefined,
        },
      };

      addMessage(assistantMessage);
      setLoading(false);

      // Log metric
      if (data.metrics) {
        addMetric({
          id: generateId(),
          timestamp: new Date(),
          query,
          config,
          results: {
            total_results: data.sources?.length || 0,
            sources_count: data.sources?.length || 0,
          },
          performance: {
            total_latency_ms: data.metrics.total_latency_ms || 0,
            query_expansion_ms: data.metrics.query_expansion_ms,
            vector_search_ms: data.metrics.vector_search_ms,
            bm25_search_ms: data.metrics.bm25_search_ms,
            hybrid_fusion_ms: data.metrics.fusion_ms,
            graph_enhancement_ms: data.metrics.graph_enhancement_ms,
            reranking_ms: data.metrics.reranking_ms,
            web_search_ms: data.metrics.web_search_ms,
            llm_generation_ms: data.metrics.llm_generation_ms,
            llm_prompt_eval_duration_ms: data.metrics.llm_prompt_eval_duration_ms,
            llm_eval_duration_ms: data.metrics.llm_eval_duration_ms,
            llm_tokens_generated: data.metrics.llm_tokens_generated,
            llm_tokens_prompt: data.metrics.llm_tokens_prompt,
            llm_tokens_per_second: data.metrics.llm_tokens_per_second,
            search_service_latency_ms: data.metrics.search_service_latency_ms,
            chat_service_overhead_ms: data.metrics.chat_service_overhead_ms,
          },
          tokens: {
            prompt_tokens: data.metrics.prompt_tokens || 0,
            completion_tokens: data.metrics.completion_tokens || 0,
            total_tokens: data.metrics.total_tokens || 0,
          },
        });
      }

      setLoading(false);
    },
    onError: (error: any) => {
      console.error('Chat error:', error);

      // Check if request was cancelled by user
      if (error.name === 'CanceledError' || error.code === 'ERR_CANCELED') {
        // Message already added by handleCancelRequest
        setLoading(false);
        return;
      }

      // Check if request timed out
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        const timeoutMessage: ChatMessage = {
          id: generateId(),
          role: 'assistant',
          content: '⏱️ **Request Timed Out (30 minutes)**\n\nThe Maximum preset exceeded the 30-minute timeout. This can happen on slower hardware or when Ollama is heavily loaded.\n\n**What Maximum does:**\n- Query Expansion (~100ms)\n- Hybrid Search (~200ms)\n- Knowledge Graph (~100ms)\n- **Re-ranking with LLM** (~3-5 seconds per batch)\n- **Web Search** (10 docs × 5 pages = 50 requests, ~30-60s)\n- **LLM Generation with llama3.1:8b** (5-15 minutes for 1500 tokens with 20 context chunks)\n\n🎓 **Key Learning**: Maximum demonstrates the extreme end of the quality/latency spectrum. Start this preset during a break and return to see the high-quality results!\n\n💡 **Tip**: For interactive use, try Balanced (< 1s) or Production (< 5s) presets. Maximum is designed for quality benchmarking on your specific hardware.',
          timestamp: new Date(),
        };
        addMessage(timeoutMessage);
        setLoading(false);
        return;
      }

      // Extract detailed error information
      let errorContent = 'An error occurred while processing your request.';
      let errorDetails = '';

      if (error.response?.data) {
        const errorData = error.response.data;
        errorContent = errorData.error || errorData.message || errorContent;

        // Add error type if available
        if (errorData.type) {
          errorDetails = `\n\n**Error Type:** ${errorData.type}`;
        }

        // Add status code
        errorDetails += `\n\n**Status Code:** ${error.response.status}`;

        // Add helpful suggestions based on error type
        if (errorData.type === 'timeout') {
          errorDetails += '\n\n**Suggestion:** The system is processing your request but taking longer than expected. This usually happens when Ollama is busy with other requests. Please try again in a moment.';
        } else if (errorData.type === 'connection_error') {
          errorDetails += '\n\n**Suggestion:** Cannot connect to the backend services. Please ensure all Docker containers are running.';
        } else if (error.response.status === 503) {
          errorDetails += '\n\n**Suggestion:** One or more backend services are currently unavailable. Please wait a moment and try again.';
        }
      } else if (error.message) {
        errorContent = error.message;
      }

      const errorMessage: ChatMessage = {
        id: generateId(),
        role: 'assistant',
        content: `❌ **Error**\n\n${errorContent}${errorDetails}`,
        timestamp: new Date(),
      };
      addMessage(errorMessage);
      setLoading(false);
    },
  });

  const handleSendMessage = (query: string) => {
    if (!query.trim() || isLoading) return;

    // Add user message
    const userMessage: ChatMessage = {
      id: generateId(),
      role: 'user',
      content: query,
      timestamp: new Date(),
    };

    addMessage(userMessage);
    setLoading(true);

    // Send to API
    chatMutation.mutate(query);
  };

  const handleClearChat = () => {
    const clearMessages = useChatStore.getState().clearMessages;
    clearMessages();
  };

  const handleCancelRequest = async () => {
    // Abort the frontend request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }

    // Restart Ollama container to cancel backend processing
    try {
      await api.cancelRequest();
      const cancelMessage: ChatMessage = {
        id: generateId(),
        role: 'assistant',
        content: '🛑 **Request Cancelled** - Ollama restarted.',
        timestamp: new Date(),
      };
      addMessage(cancelMessage);
    } catch (error) {
      console.error('Failed to cancel request:', error);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-200px)] bg-card rounded-lg border">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <div>
          <h2 className="text-lg font-semibold">Chat</h2>
          <p className="text-sm text-muted-foreground">
            Ask questions about your documents
          </p>
        </div>
        <div className="flex gap-2">
          {isLoading && (
            <button
              onClick={handleCancelRequest}
              className="px-3 py-1 text-sm bg-destructive text-destructive-foreground hover:bg-destructive/90 rounded transition-colors"
            >
              Cancel Request
            </button>
          )}
          <button
            onClick={handleClearChat}
            className="px-3 py-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
            disabled={messages.length === 0}
          >
            Clear Chat
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-center">
            <div>
              <div className="text-6xl mb-4">💬</div>
              <h3 className="text-xl font-semibold mb-2">Start a conversation</h3>
              <p className="text-muted-foreground">
                Ask questions about your uploaded documents
              </p>
            </div>
          </div>
        ) : (
          <>
            <MessageList messages={messages} />
            {isLoading && (
              <div className="flex items-center gap-2 text-muted-foreground">
                <div className="animate-spin h-4 w-4 border-2 border-primary border-t-transparent rounded-full" />
                <span>Thinking...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input */}
      <div className="border-t p-4">
        <InputBar onSend={handleSendMessage} disabled={isLoading} />
      </div>
    </div>
  );
}

