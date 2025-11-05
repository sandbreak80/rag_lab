import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../services/api';
import { useConfigStore } from '../../stores/configStore';
import { formatNumber } from '../../utils/formatting';
import { Badge } from '../ui/badge';
import { UserMenu } from '../auth/UserMenu';

export function Header() {
  const model = useConfigStore((state) => state.model);

  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: () => api.getStats(),
    refetchInterval: 30000, // Refetch every 30 seconds
    retry: 1, // Only retry once
    retryDelay: 5000, // Wait 5 seconds before retry
    staleTime: 60000, // Consider data fresh for 1 minute
  });

  return (
    <header className="border-b bg-card">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              Neural Vault
            </h1>
            <Badge variant="secondary" className="text-xs">
              Educational RAG Lab
            </Badge>
          </div>

          <div className="flex items-center gap-6 text-sm">
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground">Model:</span>
              <span className="font-medium">{model}</span>
            </div>

            {stats && (
              <>
                <div className="h-4 w-px bg-border" />
                <div className="flex items-center gap-2">
                  <span className="text-muted-foreground">Chunks:</span>
                  <span className="font-medium">{formatNumber((stats as any).chunks)}</span>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-muted-foreground">Documents:</span>
                  <span className="font-medium">{(stats as any).documents?.length || 0}</span>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-muted-foreground">Graph Nodes:</span>
                  <span className="font-medium">{formatNumber((stats as any).knowledge_graph_nodes)}</span>
                </div>
              </>
            )}

            <div className="h-4 w-px bg-border" />
            <UserMenu />
          </div>
        </div>
      </div>
    </header>
  );
}

