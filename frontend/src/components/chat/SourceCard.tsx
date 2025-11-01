import React from 'react';
import { Source } from '../../types/chat';
import { Card, CardContent } from '../ui/card';
import { FileText } from 'lucide-react';

interface SourceCardProps {
  source: Source;
  index: number;
}

export function SourceCard({ source, index }: SourceCardProps) {
  return (
    <Card className="bg-background">
      <CardContent className="p-3">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 w-8 h-8 rounded bg-primary/10 flex items-center justify-center">
            <FileText className="h-4 w-4 text-primary" />
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-medium text-muted-foreground">
                Source {index}
              </span>
              <span className="text-xs text-muted-foreground">•</span>
              <span className="text-xs font-medium text-primary">
                Score: {source.score.toFixed(3)}
              </span>
            </div>

            <h4 className="text-sm font-medium truncate mb-1">
              {source.file_name}
            </h4>

            <p className="text-xs text-muted-foreground line-clamp-2">
              {source.chunk_text}
            </p>

            {source.metadata && Object.keys(source.metadata).length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {source.metadata.tags?.map((tag, i) => (
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

