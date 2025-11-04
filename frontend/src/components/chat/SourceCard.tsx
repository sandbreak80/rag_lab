import React from 'react';
import { Source } from '../../types/chat';
import { Card, CardContent } from '../ui/card';
import { FileText, Globe, ExternalLink } from 'lucide-react';

interface SourceCardProps {
  source: Source;
  index: number;
}

export function SourceCard({ source, index }: SourceCardProps) {
  const isWebSource = source.source === 'web_search';
  const url = source.metadata?.url;
  const title = source.metadata?.title || source.file_name;
  const engine = source.metadata?.engine;

  return (
    <Card className="bg-background">
      <CardContent className="p-3">
        <div className="flex items-start gap-3">
          <div className={`flex-shrink-0 w-8 h-8 rounded flex items-center justify-center ${
            isWebSource ? 'bg-blue-500/10' : 'bg-primary/10'
          }`}>
            {isWebSource ? (
              <Globe className="h-4 w-4 text-blue-500" />
            ) : (
              <FileText className="h-4 w-4 text-primary" />
            )}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-medium text-muted-foreground">
                {isWebSource ? 'Web' : 'RAG'} {index}
              </span>
              <span className="text-xs text-muted-foreground">•</span>
              <span className="text-xs font-medium text-primary">
                Score: {source.score.toFixed(3)}
              </span>
              {engine && (
                <>
                  <span className="text-xs text-muted-foreground">•</span>
                  <span className="text-xs text-muted-foreground capitalize">
                    {engine}
                  </span>
                </>
              )}
            </div>

            {isWebSource && url ? (
              <a
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 flex items-center gap-1 mb-1 group"
              >
                <span className="truncate">{title}</span>
                <ExternalLink className="h-3 w-3 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" />
              </a>
            ) : (
              <h4 className="text-sm font-medium truncate mb-1">
                {title}
              </h4>
            )}

            <p className="text-xs text-muted-foreground line-clamp-2">
              {source.chunk_text}
            </p>

            {source.metadata && Object.keys(source.metadata).length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {Array.isArray(source.metadata.tags) && source.metadata.tags.map((tag, i) => (
                  <span
                    key={i}
                    className="px-2 py-0.5 text-xs rounded-full bg-secondary/20 text-secondary-foreground"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

