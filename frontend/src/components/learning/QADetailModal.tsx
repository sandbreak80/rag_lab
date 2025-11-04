import React from 'react';
import { X, Clock, Tag, ExternalLink, Code, BookOpen } from 'lucide-react';
import type { QAItem } from '../../data/qaData';
import { QA_CATEGORIES, QA_DATA } from '../../data/qaData';
import ReactMarkdown from 'react-markdown';

interface QADetailModalProps {
  qa: QAItem;
  onClose: () => void;
  onSelectRelated: (qa: QAItem) => void;
}

export function QADetailModal({ qa, onClose, onSelectRelated }: QADetailModalProps) {
  const category = QA_CATEGORIES.find(c => c.id === qa.category);
  const relatedQuestions = qa.relatedQuestions
    ? QA_DATA.filter(q => qa.relatedQuestions?.includes(q.id))
    : [];

  // Difficulty badge
  const getDifficultyBadge = () => {
    const badges = {
      beginner: { color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200', icon: '🟢', label: 'Beginner' },
      intermediate: { color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200', icon: '🟡', label: 'Intermediate' },
      advanced: { color: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200', icon: '🔴', label: 'Advanced' },
    };
    
    return badges[qa.difficulty];
  };

  const difficultyBadge = getDifficultyBadge();

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative min-h-screen flex items-center justify-center p-4">
        <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
          {/* Header */}
          <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-6 z-10">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <span className="text-3xl">{category?.icon}</span>
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    {category?.name}
                  </span>
                </div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
                  {qa.question}
                </h2>
                <div className="flex flex-wrap items-center gap-3">
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${difficultyBadge.color}`}>
                    {difficultyBadge.icon} {difficultyBadge.label}
                  </span>
                  <div className="flex items-center gap-1 text-sm text-gray-600 dark:text-gray-400">
                    <Clock className="w-4 h-4" />
                    {qa.estimatedReadTime} min read
                  </div>
                  {qa.codeExample && (
                    <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded-full text-sm flex items-center gap-1">
                      <Code className="w-4 h-4" />
                      Code Example
                    </span>
                  )}
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                <X className="w-6 h-6 text-gray-500 dark:text-gray-400" />
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="p-6 space-y-6">
            {/* Answer */}
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown
                components={{
                  // Custom code block styling
                  code: ({ node, inline, className, children, ...props }) => {
                    if (inline) {
                      return (
                        <code className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-sm" {...props}>
                          {children}
                        </code>
                      );
                    }
                    return (
                      <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto">
                        <code className={className} {...props}>
                          {children}
                        </code>
                      </pre>
                    );
                  },
                }}
              >
                {qa.answer}
              </ReactMarkdown>
            </div>

            {/* Code Example */}
            {qa.codeExample && (
              <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Code className="w-5 h-5 text-primary-600" />
                  <h3 className="font-semibold text-gray-900 dark:text-white">
                    Code Example
                  </h3>
                </div>
                <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm">
                  <code>{qa.codeExample}</code>
                </pre>
              </div>
            )}

            {/* External Links */}
            {qa.externalLinks && qa.externalLinks.length > 0 && (
              <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-3">
                  <ExternalLink className="w-5 h-5 text-primary-600" />
                  <h3 className="font-semibold text-gray-900 dark:text-white">
                    External Resources
                  </h3>
                </div>
                <ul className="space-y-2">
                  {qa.externalLinks.map((link, index) => (
                    <li key={index}>
                      <a
                        href={link.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary-600 dark:text-primary-400 hover:underline flex items-center gap-2"
                      >
                        {link.title}
                        <ExternalLink className="w-4 h-4" />
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Tags */}
            {qa.tags.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <Tag className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                  <h3 className="font-semibold text-gray-900 dark:text-white">
                    Tags
                  </h3>
                </div>
                <div className="flex flex-wrap gap-2">
                  {qa.tags.map(tag => (
                    <span
                      key={tag}
                      className="px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300
                               text-sm rounded-full"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Related Questions */}
            {relatedQuestions.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <BookOpen className="w-5 h-5 text-primary-600" />
                  <h3 className="font-semibold text-gray-900 dark:text-white">
                    Related Questions
                  </h3>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {relatedQuestions.map(relatedQA => {
                    const relatedCategory = QA_CATEGORIES.find(c => c.id === relatedQA.category);
                    return (
                      <button
                        key={relatedQA.id}
                        onClick={() => onSelectRelated(relatedQA)}
                        className="p-3 border border-gray-200 dark:border-gray-700 rounded-lg
                                 hover:border-primary-500 hover:bg-primary-50 dark:hover:bg-primary-900/20
                                 transition-all text-left group"
                      >
                        <div className="flex items-start gap-2 mb-1">
                          <span className="text-lg">{relatedCategory?.icon}</span>
                          <h4 className="font-medium text-sm text-gray-900 dark:text-white line-clamp-2
                                       group-hover:text-primary-600 dark:group-hover:text-primary-400">
                            {relatedQA.question}
                          </h4>
                        </div>
                        <p className="text-xs text-gray-600 dark:text-gray-400">
                          {relatedCategory?.name}
                        </p>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="sticky bottom-0 bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 p-4">
            <button
              onClick={onClose}
              className="w-full px-4 py-2 bg-primary-600 text-white rounded-lg
                       hover:bg-primary-700 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

