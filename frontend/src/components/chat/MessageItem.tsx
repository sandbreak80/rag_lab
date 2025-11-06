import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { ChatMessage } from '../../types/chat';
import { SourceCard } from './SourceCard';
import { WaterfallChart } from '../metrics/WaterfallChart';
import { SecurityStatus } from '../security/SecurityStatus';
import { formatDate } from '../../utils/formatting';
import { User, Bot, BarChart3, Copy, Check } from 'lucide-react';

interface MessageItemProps {
  message: ChatMessage;
}

export function MessageItem({ message }: MessageItemProps) {
  const isUser = message.role === 'user';
  const [showPerformance, setShowPerformance] = useState(false);
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  const hasPerformanceData = !isUser && message.metadata?.performance;

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedCode(id);
    setTimeout(() => setCopiedCode(null), 2000);
  };

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
          <div className={`prose max-w-none ${isUser ? 'prose-invert' : 'prose-slate dark:prose-invert'}`}>
            {isUser ? (
              <p className="whitespace-pre-wrap">{message.content}</p>
            ) : (
              <ReactMarkdown
                remarkPlugins={[remarkGfm, remarkMath]}
                rehypePlugins={[rehypeKatex]}
                components={{
                  // Enhanced code blocks with copy button
                  code({ node, className, children, ...props }: any) {
                    const match = /language-(\w+)/.exec(className || '');
                    const inline = props.inline;
                    const codeString = String(children).replace(/\n$/, '');
                    const codeId = `code-${Math.random().toString(36).substr(2, 9)}`;
                    
                    return !inline && match ? (
                      <div className="relative group my-4">
                        <div className="absolute right-2 top-2 z-10">
                          <button
                            onClick={() => copyToClipboard(codeString, codeId)}
                            className="opacity-0 group-hover:opacity-100 transition-opacity px-2 py-1 bg-slate-700 hover:bg-slate-600 rounded text-xs text-slate-200 flex items-center gap-1"
                            title="Copy code"
                          >
                            {copiedCode === codeId ? (
                              <>
                                <Check className="h-3 w-3" />
                                Copied!
                              </>
                            ) : (
                              <>
                                <Copy className="h-3 w-3" />
                                Copy
                              </>
                            )}
                          </button>
                        </div>
                        <SyntaxHighlighter
                          style={vscDarkPlus as any}
                          language={match[1]}
                          PreTag="div"
                          className="rounded-lg !my-0"
                          showLineNumbers={codeString.split('\n').length > 3}
                          {...props}
                        >
                          {codeString}
                        </SyntaxHighlighter>
                      </div>
                    ) : (
                      <code className="px-1.5 py-0.5 rounded bg-slate-200 dark:bg-slate-800 text-sm font-mono" {...props}>
                        {children}
                      </code>
                    );
                  },
                  // Enhanced headings
                  h1: ({ children }) => (
                    <h1 className="text-2xl font-bold mt-6 mb-4 pb-2 border-b border-border">{children}</h1>
                  ),
                  h2: ({ children }) => (
                    <h2 className="text-xl font-semibold mt-5 mb-3 pb-1 border-b border-border/50">{children}</h2>
                  ),
                  h3: ({ children }) => (
                    <h3 className="text-lg font-semibold mt-4 mb-2">{children}</h3>
                  ),
                  // Enhanced lists
                  ul: ({ children }) => (
                    <ul className="list-disc list-outside ml-6 my-3 space-y-1">{children}</ul>
                  ),
                  ol: ({ children }) => (
                    <ol className="list-decimal list-outside ml-6 my-3 space-y-1">{children}</ol>
                  ),
                  li: ({ children }) => (
                    <li className="pl-1">{children}</li>
                  ),
                  // Enhanced blockquotes
                  blockquote: ({ children }) => (
                    <blockquote className="border-l-4 border-primary pl-4 py-2 my-4 italic bg-muted/30 rounded-r">
                      {children}
                    </blockquote>
                  ),
                  // Enhanced tables
                  table: ({ children }) => (
                    <div className="overflow-x-auto my-4">
                      <table className="min-w-full divide-y divide-border border border-border rounded-lg">
                        {children}
                      </table>
                    </div>
                  ),
                  thead: ({ children }) => (
                    <thead className="bg-muted">{children}</thead>
                  ),
                  th: ({ children }) => (
                    <th className="px-4 py-2 text-left text-sm font-semibold">{children}</th>
                  ),
                  td: ({ children }) => (
                    <td className="px-4 py-2 text-sm border-t border-border">{children}</td>
                  ),
                  // Enhanced links
                  a: ({ href, children }) => (
                    <a
                      href={href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:text-primary/80 underline underline-offset-2 transition-colors"
                    >
                      {children}
                    </a>
                  ),
                  // Enhanced paragraphs
                  p: ({ children }) => (
                    <p className="my-3 leading-7">{children}</p>
                  ),
                  // Enhanced horizontal rules
                  hr: () => (
                    <hr className="my-6 border-t-2 border-border" />
                  ),
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

        {/* Security Status */}
        {!isUser && message.metadata?.security && (
          <div className="mt-4">
            <SecurityStatus
              violations={message.metadata.security.violations}
              cleanedQueryUsed={message.metadata.security.cleaned_query_used}
              enabled={true}
            />
          </div>
        )}

        {/* Query Decomposition */}
        {!isUser && message.metadata?.decomposition?.needs_decomposition && (
          <div className="mt-4 p-4 border border-border rounded-lg bg-background/30">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-lg">🧩</span>
              <h4 className="text-sm font-medium">
                Query Decomposition
                <span className="ml-2 text-xs px-2 py-0.5 bg-primary/20 text-primary rounded-full">
                  {message.metadata.decomposition.complexity}
                </span>
              </h4>
            </div>
            <p className="text-sm text-muted-foreground mb-3">
              Your complex question was broken into simpler sub-queries for better results:
            </p>
            <div className="space-y-2">
              {message.metadata.decomposition.sub_queries.map((subQuery, idx) => (
                <div key={idx} className="flex items-start gap-2 text-sm">
                  <span className="flex-shrink-0 w-5 h-5 rounded-full bg-primary/20 text-primary flex items-center justify-center text-xs font-medium">
                    {idx + 1}
                  </span>
                  <span className="flex-1 py-0.5">{subQuery}</span>
                </div>
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

