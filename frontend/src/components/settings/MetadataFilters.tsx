import React from 'react';
import { useConfigStore } from '../../stores/configStore';
import { MetadataFilters as MetadataFiltersType } from '../../types/config';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Select } from '../ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';

const DOCUMENT_TYPES = [
  'All Types',
  'PDF',
  'Word Document',
  'PowerPoint',
  'Excel',
  'Text File',
  'Markdown',
];

export function MetadataFilters() {
  const filters = useConfigStore((state) => state.metadataFilters);
  const setMetadataFilters = useConfigStore((state) => state.setMetadataFilters);

  const updateFilters = (updates: Partial<MetadataFiltersType>) => {
    setMetadataFilters({
      ...filters,
      ...updates,
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Metadata Filters</CardTitle>
        <CardDescription className="text-xs">
          Filter documents by type, date, tags, and author
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Document Type */}
        <div className="space-y-2">
          <Label htmlFor="doc-type">Document Type</Label>
          <Select
            id="doc-type"
            value={filters?.documentTypes?.[0] || 'All Types'}
            onChange={(e) => {
              const value = e.target.value;
              updateFilters({
                documentTypes: value === 'All Types' ? undefined : [value],
              });
            }}
          >
            {DOCUMENT_TYPES.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </Select>
        </div>

        {/* Date Range */}
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-2">
            <Label htmlFor="date-start">Date From</Label>
            <Input
              id="date-start"
              type="date"
              value={filters?.dateRange?.start || ''}
              onChange={(e) =>
                updateFilters({
                  dateRange: {
                    ...filters?.dateRange,
                    start: e.target.value,
                  },
                })
              }
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="date-end">Date To</Label>
            <Input
              id="date-end"
              type="date"
              value={filters?.dateRange?.end || ''}
              onChange={(e) =>
                updateFilters({
                  dateRange: {
                    ...filters?.dateRange,
                    end: e.target.value,
                  },
                })
              }
            />
          </div>
        </div>

        {/* Tags */}
        <div className="space-y-2">
          <Label htmlFor="tags">Tags</Label>
          <Input
            id="tags"
            placeholder="e.g., technical, documentation"
            value={filters?.tags?.join(', ') || ''}
            onChange={(e) =>
              updateFilters({
                tags: e.target.value
                  ? e.target.value.split(',').map((t) => t.trim())
                  : undefined,
              })
            }
          />
          <p className="text-xs text-muted-foreground">
            Comma-separated list of tags
          </p>
        </div>

        {/* Author */}
        <div className="space-y-2">
          <Label htmlFor="authors">Authors</Label>
          <Input
            id="authors"
            placeholder="e.g., John Doe, Jane Smith"
            value={filters?.authors?.join(', ') || ''}
            onChange={(e) =>
              updateFilters({
                authors: e.target.value
                  ? e.target.value.split(',').map((a) => a.trim())
                  : undefined,
              })
            }
          />
          <p className="text-xs text-muted-foreground">
            Comma-separated list of authors
          </p>
        </div>

        {/* Clear Filters */}
        {(filters?.documentTypes ||
          filters?.dateRange?.start ||
          filters?.dateRange?.end ||
          filters?.tags ||
          filters?.authors) && (
          <button
            onClick={() => setMetadataFilters({})}
            className="text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            Clear all filters
          </button>
        )}
      </CardContent>
    </Card>
  );
}

