import React from 'react';
import { useConfigStore } from '../../stores/configStore';
import { Switch } from '../ui/switch';
import { Label } from '../ui/label';

const RAG_FEATURES = [
  {
    key: 'useQueryExpansion' as const,
    label: 'Query Expansion',
    description: 'Expand queries with synonyms and related terms',
    impact: '+5-10% recall',
  },
  {
    key: 'useBM25' as const,
    label: 'BM25 Search',
    description: 'Keyword-based search algorithm',
    impact: '+10-15% precision for exact matches',
  },
  {
    key: 'useHybrid' as const,
    label: 'Hybrid Search',
    description: 'Combine vector and BM25 results',
    impact: '+15% overall performance',
  },
  {
    key: 'useGraph' as const,
    label: 'Knowledge Graph',
    description: 'Expand results using document relationships',
    impact: '+25% on multi-hop questions',
  },
  {
    key: 'useReranking' as const,
    label: 'LLM Re-ranking',
    description: 'Use LLM to re-rank search results',
    impact: '+12% precision',
  },
  {
    key: 'useWebSearch' as const,
    label: 'Web Search',
    description: 'Include web results via SearXNG',
    impact: 'External knowledge integration',
  },
  {
    key: 'useAgenticChunking' as const,
    label: 'Agentic Chunking',
    description: 'LLM-powered intelligent chunking',
    impact: '+12% recall',
  },
];

export function RAGToggles() {
  const store = useConfigStore();

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-medium mb-3">RAG Features</h3>
        <p className="text-xs text-muted-foreground mb-4">
          Enable or disable features to see their impact on response quality
        </p>
      </div>

      <div className="space-y-3">
        {RAG_FEATURES.map((feature) => (
          <div
            key={feature.key}
            className="flex items-start justify-between p-3 rounded-lg bg-muted/50"
          >
            <div className="flex-1 mr-4">
              <Label htmlFor={feature.key} className="cursor-pointer">
                {feature.label}
              </Label>
              <p className="text-xs text-muted-foreground mt-0.5">
                {feature.description}
              </p>
              <p className="text-xs text-primary mt-1 font-medium">
                {feature.impact}
              </p>
            </div>
            <Switch
              id={feature.key}
              checked={store[feature.key] as boolean}
              onCheckedChange={() => store.toggleFeature(feature.key)}
            />
          </div>
        ))}
      </div>
    </div>
  );
}

