import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { PromptLibraryItem } from '../../../data/promptLibrary';
import { Search, Filter } from 'lucide-react';

interface PromptLibraryBrowserProps {
  prompts: PromptLibraryItem[];
  selectedPrompt: PromptLibraryItem | null;
  onSelect: (prompt: PromptLibraryItem) => void;
}

export function PromptLibraryBrowser({
  prompts,
  selectedPrompt,
  onSelect
}: PromptLibraryBrowserProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [complexityFilter, setComplexityFilter] = useState<string>('all');
  const [difficultyFilter, setDifficultyFilter] = useState<string>('all');

  const categories = ['all', ...Array.from(new Set(prompts.map(p => p.category)))];
  const complexities = ['all', ...Array.from(new Set(prompts.map(p => p.complexity)))];
  const difficulties = ['all', ...Array.from(new Set(prompts.map(p => p.difficulty)))];

  const filteredPrompts = prompts.filter(p => {
    const matchesSearch =
      p.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.prompt.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesCategory = categoryFilter === 'all' || p.category === categoryFilter;
    const matchesComplexity = complexityFilter === 'all' || p.complexity === complexityFilter;
    const matchesDifficulty = difficultyFilter === 'all' || p.difficulty === difficultyFilter;

    return matchesSearch && matchesCategory && matchesComplexity && matchesDifficulty;
  });

  return (
    <div>
      {/* Filters */}
      <div className="mb-4 space-y-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search prompts..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>

        <div className="flex flex-wrap gap-2">
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-3 py-1 border rounded-md text-sm"
          >
            {categories.map(cat => (
              <option key={cat} value={cat}>
                {cat === 'all' ? 'All Categories' : cat.charAt(0).toUpperCase() + cat.slice(1)}
              </option>
            ))}
          </select>

          <select
            value={complexityFilter}
            onChange={(e) => setComplexityFilter(e.target.value)}
            className="px-3 py-1 border rounded-md text-sm"
          >
            {complexities.map(comp => (
              <option key={comp} value={comp}>
                {comp === 'all' ? 'All Complexities' : comp.charAt(0).toUpperCase() + comp.slice(1)}
              </option>
            ))}
          </select>

          <select
            value={difficultyFilter}
            onChange={(e) => setDifficultyFilter(e.target.value)}
            className="px-3 py-1 border rounded-md text-sm"
          >
            {difficulties.map(diff => (
              <option key={diff} value={diff}>
                {diff === 'all' ? 'All Difficulties' : diff.charAt(0).toUpperCase() + diff.slice(1)}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Prompt Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-96 overflow-y-auto">
        {filteredPrompts.map((prompt) => (
          <Card
            key={prompt.id}
            className={`cursor-pointer transition-all ${
              selectedPrompt?.id === prompt.id
                ? 'ring-2 ring-primary border-primary'
                : 'hover:border-primary/50'
            }`}
            onClick={() => onSelect(prompt)}
          >
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">{prompt.title}</CardTitle>
              <CardDescription className="text-xs">
                {prompt.category} • {prompt.complexity} • {prompt.difficulty}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground line-clamp-2">
                {prompt.prompt}
              </p>
              <div className="mt-2 flex flex-wrap gap-1">
                {prompt.tags.slice(0, 3).map(tag => (
                  <span
                    key={tag}
                    className="px-1.5 py-0.5 bg-muted text-xs rounded"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredPrompts.length === 0 && (
        <div className="text-center py-8 text-muted-foreground">
          No prompts match your filters
        </div>
      )}

      {/* Selected Prompt Preview */}
      {selectedPrompt && (
        <Card className="mt-4">
          <CardHeader>
            <CardTitle>Selected: {selectedPrompt.title}</CardTitle>
            <CardDescription>{selectedPrompt.description}</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm">{selectedPrompt.prompt}</p>
            <div className="mt-2 text-xs text-muted-foreground">
              Expected: {selectedPrompt.expectedSources} sources • {selectedPrompt.expectedLatency}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

