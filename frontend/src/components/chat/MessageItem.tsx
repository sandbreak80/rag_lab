import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { ChatMessage } from '../../types/chat';
import { SourceCard } from './SourceCard';
import { WaterfallChart } from '../metrics/WaterfallChart';
import { formatDate } from '../../utils/formatting';
import { User, Bot, BarChart3 } from 'lucide-react';

interface MessageItemProps {
  message: ChatMessage;
}

export function MessageItem({ message }: MessageItemProps) {
  const isUser = message.role === 'user';
  const [showPerformance, setShowPerformance] = useState(false);
  
  const hasPerformanceData = !isUser && message.metadata?.performance;

  return (
    <div className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary flex items-center justify-center">
          <Bot className="h-5 w-5 text-primary-foreground" />
        </div>
      )}

      <div className={`flex-1 max-w-3xl ${isUser ? 'flex justify-end' : ''}`}>
        <div
          className={`rounded-lg p-4 ${
            isUser
              ? 'bg-primary text-primary-foreground'
              : 'bg-muted'
          }`}
        >
          {/* Message content */}
          <div className="prose prose-invert max-w-none">
            {isUser ? (
              <p className="whitespace-pre-wrap">{message.content}</p>
            ) : (
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code({ node, className, children, ...props }: any) {
                    const match = /language-(\w+)/.exec(className || '');
                    const inline = props.inline;
                    return !inline && match ? (
                      <SyntaxHighlighter
                        style={vscDarkPlus as any}
                        language={match[1]}
                        PreTag="div"
                        {...props}
                      >
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    ) : (
                      <code className={className} {...props}>
                        {children}
                      </code>
                    );
                  },
                }}
              >
                {message.content}
              </ReactMarkdown>
            )}
          </div>

          {/* Metadata */}
          <div className="mt-2 flex items-center gap-2 text-xs opacity-70">
            <span>{formatDate(message.timestamp)}</span>
            {message.metadata?.latency && (
              <>
                <span>•</span>
                <span>{message.metadata.latency}ms</span>
              </>
            )}
            {message.metadata?.model && (
              <>
                <span>•</span>
                <span>{message.metadata.model}</span>
              </>
            )}
          </div>
        </div>

        {/* Sources */}
        {message.sources && message.sources.length > 0 && (
          <div className="mt-4 space-y-2">
            <h4 className="text-sm font-medium text-muted-foreground">
              Sources ({message.sources.length})
            </h4>
            <div className="grid gap-2">
              {message.sources.map((source, index) => (
                <SourceCard key={index} source={source} index={index + 1} />
              ))}
            </div>
          </div>
        )}

        {/* Performance Waterfall */}
        {hasPerformanceData && (
          <div className="mt-4 border border-border rounded-lg bg-background/50 overflow-hidden">
            <button
              onClick={() => setShowPerformance(!showPerformance)}
              className="w-full px-4 py-2 flex items-center justify-between hover:bg-muted/50 transition-colors"
            >
              <div className="flex items-center gap-2 text-sm font-medium">
                <BarChart3 className="h-4 w-4 text-primary" />
                <span>Performance Breakdown</span>
              </div>
              <span className="text-xs text-muted-foreground">
                {showPerformance ? '▼ Hide' : '▶ Show'}
              </span>
            </button>
            
            {showPerformance && (
              <div className="p-4 border-t border-border">
                <WaterfallChart metrics={message.metadata!.performance!} compact />
              </div>
            )}
          </div>
        )}
      </div>

      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-secondary flex items-center justify-center">
          <User className="h-5 w-5 text-secondary-foreground" />
        </div>
      )}
    </div>
  );
}

