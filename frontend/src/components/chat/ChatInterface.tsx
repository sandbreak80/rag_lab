import React, { useState, useRef, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { api } from '../../services/api';
import { useConfigStore } from '../../stores/configStore';
import { useMetricsStore } from '../../stores/metricsStore';
import { ChatMessage } from '../../types/chat';
import { MessageList } from './MessageList';
import { InputBar } from './InputBar';
import { generateId } from '../../utils/formatting';

export function ChatInterface() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const config = useConfigStore((state) => state.getConfig());
  const addMetric = useMetricsStore((state) => state.addQuery);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const chatMutation = useMutation({
    mutationFn: (query: string) => api.sendMessage(query, config),
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
        },
      };

      setMessages((prev) => [...prev, assistantMessage]);

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
            hybrid_fusion_ms: data.metrics.hybrid_fusion_ms,
            graph_expansion_ms: data.metrics.graph_expansion_ms,
            reranking_ms: data.metrics.reranking_ms,
            web_search_ms: data.metrics.web_search_ms,
            llm_generation_ms: data.metrics.llm_generation_ms,
          },
          tokens: {
            prompt_tokens: data.metrics.prompt_tokens || 0,
            completion_tokens: data.metrics.completion_tokens || 0,
            total_tokens: data.metrics.total_tokens || 0,
          },
        });
      }

      setIsLoading(false);
    },
    onError: (error) => {
      const errorMessage: ChatMessage = {
        id: generateId(),
        role: 'assistant',
        content: `Error: ${error.message}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
      setIsLoading(false);
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

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    // Send to API
    chatMutation.mutate(query);
  };

  const handleClearChat = () => {
    setMessages([]);
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
        <button
          onClick={handleClearChat}
          className="px-3 py-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
          disabled={messages.length === 0}
        >
          Clear Chat
        </button>
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

