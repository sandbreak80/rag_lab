import React, { useState, KeyboardEvent, useEffect } from 'react';
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

const DRAFT_KEY = 'chat_draft_message';

export function InputBar({ onSend, disabled }: InputBarProps) {
  // Load draft from localStorage on mount
  const [input, setInput] = useState(() => {
    try {
      return localStorage.getItem(DRAFT_KEY) || '';
    } catch {
      return '';
    }
  });
  const [showSuggestions, setShowSuggestions] = useState(true);

  // Save draft to localStorage whenever it changes
  useEffect(() => {
    try {
      if (input) {
        localStorage.setItem(DRAFT_KEY, input);
      } else {
        localStorage.removeItem(DRAFT_KEY);
      }
    } catch (error) {
      console.error('Failed to save draft:', error);
    }
  }, [input]);

  const handleSend = () => {
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
      setShowSuggestions(false);
      // Clear draft from localStorage
      try {
        localStorage.removeItem(DRAFT_KEY);
      } catch (error) {
        console.error('Failed to clear draft:', error);
      }
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

