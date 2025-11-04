import React from 'react';
import { Clock, Tag, ChevronRight } from 'lucide-react';
import type { QAItem } from '../../data/qaData';
import { QA_CATEGORIES } from '../../data/qaData';

interface QACardProps {
  qa: QAItem;
  onClick: () => void;
  compact?: boolean;
  searchQuery?: string;
}

export function QACard({ qa, onClick, compact = false, searchQuery = '' }: QACardProps) {
  const category = QA_CATEGORIES.find(c => c.id === qa.category);

  // Highlight search terms
  const highlightText = (text: string) => {
    if (!searchQuery.trim()) return text;
    
    const regex = new RegExp(`(${searchQuery})`, 'gi');
    const parts = text.split(regex);
    
    return parts.map((part, i) => 
      regex.test(part) ? (
        <mark key={i} className="bg-yellow-200 dark:bg-yellow-800">{part}</mark>
      ) : (
        part
      )
    );
  };

  // Difficulty badge
  const getDifficultyBadge = () => {
    const badges = {
      beginner: { color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200', icon: '🟢', label: 'Beginner' },
      intermediate: { color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200', icon: '🟡', label: 'Intermediate' },
      advanced: { color: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200', icon: '🔴', label: 'Advanced' },
    };
    
    const badge = badges[qa.difficulty];
    
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${badge.color}`}>
        {badge.icon} {badge.label}
      </span>
    );
  };

  if (compact) {
    return (
      <button
        onClick={onClick}
        className="w-full p-4 border border-gray-200 dark:border-gray-700 rounded-lg
                 hover:border-primary-500 hover:shadow-md transition-all text-left group"
      >
        <div className="flex items-start justify-between gap-2 mb-2">
          <span className="text-xl">{category?.icon}</span>
          {getDifficultyBadge()}
        </div>
        <h3 className="font-medium text-gray-900 dark:text-white mb-2 line-clamp-2
                     group-hover:text-primary-600 dark:group-hover:text-primary-400">
          {qa.question}
        </h3>
        <div className="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
          <div className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {qa.estimatedReadTime} min
          </div>
          {qa.tags.length > 0 && (
            <div className="flex items-center gap-1">
              <Tag className="w-3 h-3" />
              {qa.tags.length} tags
            </div>
          )}
        </div>
      </button>
    );
  }

  return (
    <button
      onClick={onClick}
      className="w-full p-6 border border-gray-200 dark:border-gray-700 rounded-lg
               hover:border-primary-500 hover:shadow-md transition-all text-left group"
    >
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{category?.icon}</span>
          <div>
            <h3 className="font-semibold text-lg text-gray-900 dark:text-white mb-1
                         group-hover:text-primary-600 dark:group-hover:text-primary-400">
              {highlightText(qa.question)}
            </h3>
            <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
              <span>{category?.name}</span>
              <span>•</span>
              {getDifficultyBadge()}
            </div>
          </div>
        </div>
        <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-primary-600 
                                dark:group-hover:text-primary-400 flex-shrink-0" />
      </div>

      {/* Answer Preview */}
      <p className="text-gray-600 dark:text-gray-400 text-sm mb-3 line-clamp-2">
        {highlightText(qa.answer.substring(0, 150))}...
      </p>

      {/* Tags */}
      {qa.tags.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-3">
          {qa.tags.slice(0, 5).map(tag => (
            <span
              key={tag}
              className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300
                       text-xs rounded-full"
            >
              {highlightText(tag)}
            </span>
          ))}
          {qa.tags.length > 5 && (
            <span className="px-2 py-1 text-gray-500 dark:text-gray-400 text-xs">
              +{qa.tags.length - 5} more
            </span>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {qa.estimatedReadTime} min read
          </div>
          {qa.codeExample && (
            <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded">
              Code Example
            </span>
          )}
          {qa.externalLinks && qa.externalLinks.length > 0 && (
            <span className="px-2 py-1 bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300 rounded">
              External Links
            </span>
          )}
        </div>
        {qa.relatedQuestions && qa.relatedQuestions.length > 0 && (
          <span>{qa.relatedQuestions.length} related</span>
        )}
      </div>
    </button>
  );
}

