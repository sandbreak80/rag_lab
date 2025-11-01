import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Card, CardContent } from '../ui/card';
import { ChevronDown, ChevronRight } from 'lucide-react';

interface LabSectionProps {
  title: string;
  content: string;
  defaultOpen?: boolean;
}

export function LabSection({ title, content, defaultOpen = false }: LabSectionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <Card>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full p-4 flex items-center justify-between hover:bg-muted/50 transition-colors"
      >
        <h3 className="text-lg font-semibold text-left">{title}</h3>
        {isOpen ? (
          <ChevronDown className="h-5 w-5 text-muted-foreground" />
        ) : (
          <ChevronRight className="h-5 w-5 text-muted-foreground" />
        )}
      </button>
      
      {isOpen && (
        <CardContent className="pt-0 pb-4 px-4">
          <div className="prose prose-invert max-w-none text-sm">
            <ReactMarkdown>{content}</ReactMarkdown>
          </div>
        </CardContent>
      )}
    </Card>
  );
}

