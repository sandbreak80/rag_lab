import React, { useState } from 'react';
import { MetadataFilters } from '../../types/config';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Label } from '../ui/label';
import { Filter, X } from 'lucide-react';

interface FilterPanelProps {
  filters: MetadataFilters;
  onFiltersChange: (filters: MetadataFilters) => void;
  availableOptions?: {
    documentTypes?: string[];
    tags?: string[];
    sources?: string[];
  };
}

const DEFAULT_DOCUMENT_TYPES = ['pdf', 'markdown', 'txt', 'docx', 'html'];
const DEFAULT_TAGS = ['AI', 'RAG', 'LLM', 'Machine Learning', 'Deep Learning', 'NLP'];
const DEFAULT_SOURCES = ['research-agent', 'upload', 'web-search'];

const DATE_RANGES = [
  { label: 'All Time', value: null },
  { label: 'Last 7 Days', days: 7 },
  { label: 'Last 30 Days', days: 30 },
  { label: 'Last 3 Months', days: 90 },
  { label: 'Last Year', days: 365 },
];

export function FilterPanel({ filters, onFiltersChange, availableOptions }: FilterPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const documentTypes = availableOptions?.documentTypes || DEFAULT_DOCUMENT_TYPES;
  const tags = availableOptions?.tags || DEFAULT_TAGS;
  const sources = availableOptions?.sources || DEFAULT_SOURCES;

  const hasActiveFilters =
    (filters.documentTypes && filters.documentTypes.length > 0) ||
    (filters.tags && filters.tags.length > 0) ||
    (filters.sources && filters.sources.length > 0) ||
    filters.dateRange?.start ||
    filters.dateRange?.end;

  const activeFilterCount = [
    filters.documentTypes?.length || 0,
    filters.tags?.length || 0,
    filters.sources?.length || 0,
    filters.dateRange?.start || filters.dateRange?.end ? 1 : 0,
  ].reduce((a, b) => a + b, 0);

  const toggleDocumentType = (type: string) => {
    const current = filters.documentTypes || [];
    const updated = current.includes(type)
      ? current.filter(t => t !== type)
      : [...current, type];
    onFiltersChange({ ...filters, documentTypes: updated.length > 0 ? updated : undefined });
  };

  const toggleTag = (tag: string) => {
    const current = filters.tags || [];
    const updated = current.includes(tag)
      ? current.filter(t => t !== tag)
      : [...current, tag];
    onFiltersChange({ ...filters, tags: updated.length > 0 ? updated : undefined });
  };

  const toggleSource = (source: string) => {
    const current = filters.sources || [];
    const updated = current.includes(source)
      ? current.filter(s => s !== source)
      : [...current, source];
    onFiltersChange({ ...filters, sources: updated.length > 0 ? updated : undefined });
  };

  const setDateRange = (days: number | null) => {
    if (days === null) {
      onFiltersChange({ ...filters, dateRange: undefined });
    } else {
      const end = new Date().toISOString().split('T')[0];
      const start = new Date(Date.now() - days * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
      onFiltersChange({ ...filters, dateRange: { start, end } });
    }
  };

  const clearFilters = () => {
    onFiltersChange({});
  };

  return (
    <Card className="mb-4">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-primary" />
            <CardTitle className="text-base">Filters</CardTitle>
            {activeFilterCount > 0 && (
              <span className="px-2 py-0.5 text-xs bg-primary text-primary-foreground rounded-full">
                {activeFilterCount}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            {hasActiveFilters && (
              <button
                onClick={clearFilters}
                className="text-xs text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
              >
                <X className="h-3 w-3" />
                Clear
              </button>
            )}
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-xs text-primary hover:underline"
            >
              {isExpanded ? 'Hide' : 'Show'}
            </button>
          </div>
        </div>
        {!isExpanded && hasActiveFilters && (
          <CardDescription className="text-xs mt-1">
            {activeFilterCount} filter{activeFilterCount !== 1 ? 's' : ''} active
          </CardDescription>
        )}
      </CardHeader>

      {isExpanded && (
        <CardContent className="space-y-4 pt-0">
          {/* Date Range */}
          <div className="space-y-2">
            <Label className="text-sm font-medium">Date Range</Label>
            <div className="flex flex-wrap gap-2">
              {DATE_RANGES.map((range) => {
                const isActive = range.value === null
                  ? !filters.dateRange
                  : !!filters.dateRange;
                return (
                  <button
                    key={range.label}
                    onClick={() => setDateRange(range.days || null)}
                    className={`px-3 py-1 text-xs rounded-md transition-colors ${
                      isActive
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted hover:bg-muted/80'
                    }`}
                  >
                    {range.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Document Types */}
          <div className="space-y-2">
            <Label className="text-sm font-medium">Document Types</Label>
            <div className="flex flex-wrap gap-2">
              {documentTypes.map((type) => {
                const isActive = filters.documentTypes?.includes(type);
                return (
                  <button
                    key={type}
                    onClick={() => toggleDocumentType(type)}
                    className={`px-3 py-1 text-xs rounded-md transition-colors ${
                      isActive
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted hover:bg-muted/80'
                    }`}
                  >
                    {type.toUpperCase()}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Sources */}
          <div className="space-y-2">
            <Label className="text-sm font-medium">Sources</Label>
            <div className="flex flex-wrap gap-2">
              {sources.map((source) => {
                const isActive = filters.sources?.includes(source);
                const label = source.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase());
                return (
                  <button
                    key={source}
                    onClick={() => toggleSource(source)}
                    className={`px-3 py-1 text-xs rounded-md transition-colors ${
                      isActive
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted hover:bg-muted/80'
                    }`}
                  >
                    {label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Tags */}
          <div className="space-y-2">
            <Label className="text-sm font-medium">Tags</Label>
            <div className="flex flex-wrap gap-2">
              {tags.map((tag) => {
                const isActive = filters.tags?.includes(tag);
                return (
                  <button
                    key={tag}
                    onClick={() => toggleTag(tag)}
                    className={`px-3 py-1 text-xs rounded-md transition-colors ${
                      isActive
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted hover:bg-muted/80'
                    }`}
                  >
                    {tag}
                  </button>
                );
              })}
            </div>
          </div>
        </CardContent>
      )}
    </Card>
  );
}

