import React, { useRef, useEffect, useMemo } from 'react';
import { useMutation } from '@tanstack/react-query';
import { api } from '../../services/api';
import { useConfigStore } from '../../stores/configStore';
import { useMetricsStore } from '../../stores/metricsStore';
import { useChatStore } from '../../stores/chatStore';
import { ChatMessage } from '../../types/chat';
import { MessageList } from './MessageList';
import { InputBar } from './InputBar';
import { FilterPanel } from '../filters/FilterPanel';
import { generateId } from '../../utils/formatting';

export function ChatInterface() {
  const messages = useChatStore((state) => state.messages);
  const isLoading = useChatStore((state) => state.isLoading);
  const addMessage = useChatStore((state) => state.addMessage);
  const setLoading = useChatStore((state) => state.setLoading);
  const metadataFilters = useChatStore((state) => state.metadataFilters);
  const setMetadataFilters = useChatStore((state) => state.setMetadataFilters);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Cancel token for aborting requests
  const abortControllerRef = useRef<AbortController | null>(null);

  // Track if component is mounted to prevent error messages on page refresh
  const isMountedRef = useRef(true);

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
  const useSecurity = useConfigStore((state) => state.useSecurity);
  const webSearchDocs = useConfigStore((state) => state.webSearchDocs);
  const webSearchPages = useConfigStore((state) => state.webSearchPages);
  const rerankTopK = useConfigStore((state) => state.rerankTopK);

  // New intelligence features
  const usePromptEnhancement = useConfigStore((state) => state.usePromptEnhancement);
  const useAutoModelRouting = useConfigStore((state) => state.useAutoModelRouting);
  const useQueryDecomposition = useConfigStore((state) => state.useQueryDecomposition);
  const useVectorDB = useConfigStore((state) => state.useVectorDB);
  const useResearchAgent = useConfigStore((state) => state.useResearchAgent);

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
    useSecurity,
    webSearchDocs,
    webSearchPages,
    rerankTopK,
    metadataFilters: metadataFilters, // Use filters from chatStore
    usePromptEnhancement,
    useAutoModelRouting,
    useVectorDB,
    useResearchAgent,
    useQueryDecomposition,
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
    useSecurity,
    webSearchDocs,
    webSearchPages,
    rerankTopK,
    metadataFilters, // Include chatStore filters in deps
    usePromptEnhancement,
    useAutoModelRouting,
    useVectorDB,
    useResearchAgent,
    useQueryDecomposition,
  ]);

  useEffect(() => {
    // Force loading state to false on mount (in case of page refresh during request)
    setLoading(false);

    const { getPendingRequests, removePendingRequest } = useChatStore.getState();

    // Poll for ALL pending requests (not just the last one)
    // This ensures responses appear even if user navigated away
    const pollPendingRequests = async () => {
      const pendingRequestIds = getPendingRequests();
      if (pendingRequestIds.length === 0) return;

      console.log(`🔍 Polling for ${pendingRequestIds.length} pending request(s):`, pendingRequestIds);

      // Poll all pending requests in parallel
      const pollPromises = pendingRequestIds.map(async (requestId) => {
        try {
          const response = await api.getResponse(requestId);

          // Check if we already have this response in messages
          const currentMessages = useChatStore.getState().messages;
          const alreadyExists = currentMessages.some(
            msg => msg.metadata?.request_id === requestId && msg.role === 'assistant'
          );

          if (!alreadyExists) {
            // Response found! Add it to messages
            const assistantMessage: ChatMessage = {
              id: generateId(),
              role: 'assistant',
              content: response.answer,
              timestamp: new Date(),
              sources: response.sources,
              metadata: {
                model: config.model,
                temperature: config.temperature,
                topK: config.topK,
                latency: response.metrics?.total_latency_ms,
                trace_id: response.trace_id,
                request_id: response.request_id,
                tokens_in: response.tokens_in,
                tokens_out: response.tokens_out,
                cost_usd: response.cost_usd,
                stage_timings: response.stage_timings,
              },
            };
            addMessage(assistantMessage);
            removePendingRequest(requestId);
            console.log(`✅ Retrieved response for request: ${requestId}`);
            return true; // Success
          } else {
            // Already have response, remove from pending
            removePendingRequest(requestId);
            return true;
          }
        } catch (error: any) {
          // 404 means not ready yet or expired - that's okay, continue polling
          if (error.response?.status === 404) {
            return false; // Not ready yet
          } else {
            console.error(`Error polling for request ${requestId}:`, error.message);
            // For other errors, remove from pending to avoid infinite polling
            removePendingRequest(requestId);
            return false;
          }
        }
      });

      const results = await Promise.all(pollPromises);
      const successCount = results.filter(r => r === true).length;
      if (successCount > 0) {
        console.log(`✅ Retrieved ${successCount} response(s) from pending requests`);
      }
    };

    // Poll immediately on mount, then every 2 seconds
    // Continue polling for up to 30 minutes (allows for long-running queries)
    pollPendingRequests();
    const pollInterval = setInterval(pollPendingRequests, 2000);
    const timeout = setTimeout(() => {
      clearInterval(pollInterval);
      const remaining = getPendingRequests();
      if (remaining.length > 0) {
        console.warn(`⚠️  Stopped polling after 30 minutes. ${remaining.length} request(s) still pending:`, remaining);
      }
    }, 30 * 60 * 1000); // 30 minutes

    return () => {
      clearInterval(pollInterval);
      clearTimeout(timeout);
      isMountedRef.current = false;
      // Abort any pending requests on unmount (page refresh/navigation)
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      // Force loading state to false on unmount
      setLoading(false);
    };
  }, [setLoading, addMessage, config]);

  const addMetric = useMetricsStore((state) => state.addQuery);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const chatMutation = useMutation({
    mutationFn: ({ query, requestId }: { query: string; requestId: string }) => {
      // Create new abort controller for this request
      abortControllerRef.current = new AbortController();
      // Pass requestId to API so backend uses it for caching
      return api.sendMessage(query, config, abortControllerRef.current.signal, requestId);
    },
    onSuccess: (data, variables) => {
      const { removePendingRequest } = useChatStore.getState();
      const query = typeof variables === 'string' ? variables : variables.query;
      const requestId = typeof variables === 'string' ? undefined : variables.requestId;

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
          // RAG API v1 observability fields
          trace_id: data.trace_id,
          request_id: data.request_id || requestId, // Store request_id for reference
          tokens_in: data.tokens_in,
          tokens_out: data.tokens_out,
          cost_usd: data.cost_usd,
          // Stage timings
          stage_timings: data.stage_timings,
          performance: data.metrics ? {
            // Search Service Components
            query_expansion_ms: data.metrics.query_expansion_ms,
            vector_search_ms: data.metrics.vector_search_ms,
            bm25_search_ms: data.metrics.bm25_search_ms,
            hybrid_fusion_ms: data.metrics.fusion_ms,
            graph_expansion_ms: data.metrics.graph_enhancement_ms,
            reranking_ms: data.metrics.reranking_ms,
            web_search_ms: data.metrics.web_search_ms,
            // LLM Components (from Ollama)
            llm_generation_ms: data.metrics.llm_generation_ms,
            llm_prompt_eval_duration_ms: data.metrics.llm_prompt_eval_duration_ms,
            llm_eval_duration_ms: data.metrics.llm_eval_duration_ms,
            llm_tokens_generated: data.metrics.llm_tokens_generated,
            llm_tokens_prompt: data.metrics.llm_tokens_prompt,
            llm_tokens_per_second: data.metrics.llm_tokens_per_second,
            // Service Latencies
            search_service_latency_ms: data.metrics.search_service_latency_ms,
            chat_service_overhead_ms: data.metrics.chat_service_overhead_ms,
            // Intelligence Features
            query_decomposition_ms: data.metrics.query_decomposition_ms,
            // Total
            total_latency_ms: data.metrics.total_latency_ms,
          } : undefined,
          // Security Information
          security: data.security ? {
            violations: data.security.violations,
            cleaned_query_used: data.security.cleaned_query_used,
          } : undefined,
          // Query Decomposition
          decomposition: data.decomposition,
        },
      };

      addMessage(assistantMessage);

      // Remove from pending requests since we got the response
      const finalRequestId = data.request_id || requestId;
      if (finalRequestId) {
        removePendingRequest(finalRequestId);
      }

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
            graph_expansion_ms: data.metrics.graph_enhancement_ms,
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
      // Only log non-cancellation errors to avoid test failures
      if (error.name !== 'CanceledError' && error.code !== 'ERR_CANCELED') {
        console.error('Chat error:', error);
      }

      // Don't add error messages if component is unmounting (page refresh/navigation)
      if (!isMountedRef.current) {
        setLoading(false);
        return;
      }

      // Check if request was cancelled by user
      if (error.name === 'CanceledError' || error.code === 'ERR_CANCELED') {
        // Message already added by handleCancelRequest
        setLoading(false);
        return;
      }

      // Check if request timed out
      // DON'T show error - backend is still processing and will store in Redis
      // Polling will retrieve the response when ready
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        console.log('⏱️ Frontend request timed out, but backend is still processing. Polling will retrieve response from Redis when ready.');
        setLoading(false);
        // Keep request_id in pending list - polling will retrieve it
        // Don't add error message - response will appear via polling
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

    const { addPendingRequest } = useChatStore.getState();

    // Generate request_id for tracking
    const requestId = `client-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    // Add user message with request_id in metadata
    const userMessage: ChatMessage = {
      id: generateId(),
      role: 'user',
      content: query,
      timestamp: new Date(),
      metadata: {
        request_id: requestId, // Store request_id for polling after refresh
      },
    };

    addMessage(userMessage);

    // Add to pending requests list (persisted in localStorage)
    // This ensures we poll for it even after page refresh/navigation
    addPendingRequest(requestId);

    setLoading(true);

    // Send to API (request_id is passed in the request body)
    chatMutation.mutate({ query, requestId });
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
      // Silently fail - request might already be completed
      // console.error('Failed to cancel request:', error);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-40px)] bg-card rounded-lg border">
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

      {/* Filters */}
      <div className="p-4 pb-0">
        <FilterPanel
          filters={metadataFilters}
          onFiltersChange={setMetadataFilters}
        />
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

