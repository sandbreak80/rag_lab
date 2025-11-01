import React, { useState, KeyboardEvent } from 'react';
import { Textarea } from '../ui/textarea';
import { Button } from '../ui/button';
import { Send, Sparkles } from 'lucide-react';

interface InputBarProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

const SUGGESTED_QUERIES = [
  "What are the key features of RAG?",
  "How does hybrid search work?",
  "Explain agentic chunking",
  "What is the difference between vector and keyword search?",
];

export function InputBar({ onSend, disabled }: InputBarProps) {
  const [input, setInput] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(true);

  const handleSend = () => {
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
      setShowSuggestions(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion);
    setShowSuggestions(false);
  };

  return (
    <div className="space-y-3">
      {/* Suggestions */}
      {showSuggestions && input.length === 0 && (
        <div className="flex flex-wrap gap-2">
          {SUGGESTED_QUERIES.map((query, index) => (
            <button
              key={index}
              onClick={() => handleSuggestionClick(query)}
              className="px-3 py-1.5 text-sm bg-secondary/20 hover:bg-secondary/30 rounded-full transition-colors flex items-center gap-1"
              disabled={disabled}
            >
              <Sparkles className="h-3 w-3" />
              {query}
            </button>
          ))}
        </div>
      )}

      {/* Input area */}
      <div className="flex gap-2">
        <Textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question... (Shift+Enter for new line)"
          className="min-h-[60px] max-h-[200px] resize-none"
          disabled={disabled}
        />
        <Button
          onClick={handleSend}
          disabled={!input.trim() || disabled}
          size="icon"
          className="h-[60px] w-[60px] flex-shrink-0"
        >
          <Send className="h-5 w-5" />
        </Button>
      </div>

      <p className="text-xs text-muted-foreground">
        Press Enter to send, Shift+Enter for new line
      </p>
    </div>
  );
}

