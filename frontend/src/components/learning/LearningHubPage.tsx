import React, { useState } from 'react';
import { BookOpen, Search, TrendingUp, Filter, X } from 'lucide-react';
import { QA_CATEGORIES, QA_DATA, searchQA, getQAByCategory, getQAByDifficulty, getPopularQuestions } from '../../data/qaData';
import { QACard } from './QACard';
import { QADetailModal } from './QADetailModal';
import type { QAItem } from '../../data/qaData';

export function LearningHubPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('all');
  const [selectedQA, setSelectedQA] = useState<QAItem | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  // Get filtered Q&A
  const getFilteredQA = (): QAItem[] => {
    let filtered = QA_DATA;

    // Search filter
    if (searchQuery.trim()) {
      filtered = searchQA(searchQuery);
    }

    // Category filter
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(qa => qa.category === selectedCategory);
    }

    // Difficulty filter
    if (selectedDifficulty !== 'all') {
      filtered = filtered.filter(qa => qa.difficulty === selectedDifficulty);
    }

    return filtered;
  };

  const filteredQA = getFilteredQA();
  const popularQuestions = getPopularQuestions(6);

  // Clear all filters
  const clearFilters = () => {
    setSearchQuery('');
    setSelectedCategory('all');
    setSelectedDifficulty('all');
  };

  const hasActiveFilters = searchQuery || selectedCategory !== 'all' || selectedDifficulty !== 'all';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-700 rounded-lg p-8 text-white">
        <div className="flex items-center gap-3 mb-3">
          <BookOpen className="w-8 h-8" />
          <h1 className="text-3xl font-bold">Learning Hub</h1>
        </div>
        <p className="text-primary-100 text-lg">
          Comprehensive knowledge base with 100+ questions covering RAG fundamentals, 
          advanced techniques, troubleshooting, and best practices.
        </p>
      </div>

      {/* Search Bar */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
        <div className="flex gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search questions, answers, or tags..."
              className="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg 
                       bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                       focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`px-4 py-3 rounded-lg flex items-center gap-2 transition-colors
                       ${showFilters 
                         ? 'bg-primary-600 text-white' 
                         : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                       }`}
          >
            <Filter className="w-5 h-5" />
            Filters
          </button>
        </div>

        {/* Filters */}
        {showFilters && (
          <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Category Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Category
                </label>
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg
                           bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                           focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  <option value="all">All Categories</option>
                  {QA_CATEGORIES.map(cat => (
                    <option key={cat.id} value={cat.id}>
                      {cat.icon} {cat.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Difficulty Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Difficulty
                </label>
                <select
                  value={selectedDifficulty}
                  onChange={(e) => setSelectedDifficulty(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg
                           bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                           focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  <option value="all">All Levels</option>
                  <option value="beginner">🟢 Beginner</option>
                  <option value="intermediate">🟡 Intermediate</option>
                  <option value="advanced">🔴 Advanced</option>
                </select>
              </div>
            </div>

            {/* Clear Filters */}
            {hasActiveFilters && (
              <button
                onClick={clearFilters}
                className="mt-4 px-4 py-2 text-sm text-gray-600 dark:text-gray-400 
                         hover:text-gray-900 dark:hover:text-white flex items-center gap-2"
              >
                <X className="w-4 h-4" />
                Clear all filters
              </button>
            )}
          </div>
        )}
      </div>

      {/* Popular Questions */}
      {!hasActiveFilters && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-5 h-5 text-primary-600" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Popular Questions
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {popularQuestions.map(qa => (
              <QACard
                key={qa.id}
                qa={qa}
                onClick={() => setSelectedQA(qa)}
                compact
              />
            ))}
          </div>
        </div>
      )}

      {/* Categories Grid (when no search/filters) */}
      {!hasActiveFilters && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Browse by Category
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {QA_CATEGORIES.map(category => {
              const count = getQAByCategory(category.id).length;
              return (
                <button
                  key={category.id}
                  onClick={() => {
                    setSelectedCategory(category.id);
                    setShowFilters(true);
                  }}
                  className="p-4 border-2 border-gray-200 dark:border-gray-700 rounded-lg
                           hover:border-primary-500 hover:bg-primary-50 dark:hover:bg-primary-900/20
                           transition-all text-left group"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-3xl">{category.icon}</span>
                    <span className="text-sm font-medium text-gray-500 dark:text-gray-400
                                   group-hover:text-primary-600 dark:group-hover:text-primary-400">
                      {count} Q&A
                    </span>
                  </div>
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                    {category.name}
                  </h3>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Search Results */}
      {hasActiveFilters && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              {filteredQA.length} {filteredQA.length === 1 ? 'Result' : 'Results'}
            </h2>
            {selectedCategory !== 'all' && (
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {QA_CATEGORIES.find(c => c.id === selectedCategory)?.icon}{' '}
                {QA_CATEGORIES.find(c => c.id === selectedCategory)?.name}
              </span>
            )}
          </div>

          {filteredQA.length === 0 ? (
            <div className="text-center py-12">
              <Search className="w-12 h-12 text-gray-400 mx-auto mb-3" />
              <p className="text-gray-600 dark:text-gray-400 mb-2">
                No results found
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-500">
                Try adjusting your search or filters
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {filteredQA.map(qa => (
                <QACard
                  key={qa.id}
                  qa={qa}
                  onClick={() => setSelectedQA(qa)}
                  searchQuery={searchQuery}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Q&A Detail Modal */}
      {selectedQA && (
        <QADetailModal
          qa={selectedQA}
          onClose={() => setSelectedQA(null)}
          onSelectRelated={(qa) => setSelectedQA(qa)}
        />
      )}
    </div>
  );
}

