import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../services/api';
import { Card, CardContent } from '../ui/card';
import { Badge } from '../ui/badge';
import { FileText, FileImage, FileSpreadsheet, File as FileIcon, RefreshCw, AlertTriangle, Network } from 'lucide-react';

const getFileIcon = (filename: string) => {
  const ext = filename.split('.').pop()?.toLowerCase();
  switch (ext) {
    case 'pdf':
      return FileText;
    case 'doc':
    case 'docx':
      return FileText;
    case 'ppt':
    case 'pptx':
      return FileImage;
    case 'xls':
    case 'xlsx':
      return FileSpreadsheet;
    default:
      return FileIcon;
  }
};

const getFileColor = (filename: string) => {
  const ext = filename.split('.').pop()?.toLowerCase();
  switch (ext) {
    case 'pdf':
      return 'text-red-500';
    case 'doc':
    case 'docx':
      return 'text-blue-500';
    case 'ppt':
    case 'pptx':
      return 'text-orange-500';
    case 'xls':
    case 'xlsx':
      return 'text-green-500';
    default:
      return 'text-muted-foreground';
  }
};

export function DocumentList() {
  const [showResetConfirm, setShowResetConfirm] = useState(false);
  const [showKGResetConfirm, setShowKGResetConfirm] = useState(false);
  const [selectedAlgorithm, setSelectedAlgorithm] = useState('wikilinks');
  const queryClient = useQueryClient();
  
  const { data: response, isLoading, error } = useQuery({
    queryKey: ['documents'],
    queryFn: () => api.getDocuments(),
    refetchInterval: 10000, // Refetch every 10 seconds
  });

  // Get available KG algorithms
  const { data: algorithmsData } = useQuery({
    queryKey: ['kg-algorithms'],
    queryFn: () => api.getKGAlgorithms(),
  });

  const resetMutation = useMutation({
    mutationFn: () => api.resetDatabase(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
      setShowResetConfirm(false);
      alert('✅ Database reset successfully! System docs will be re-ingested automatically.');
    },
    onError: (error) => {
      alert(`❌ Reset failed: ${error}`);
      setShowResetConfirm(false);
    },
  });

  const resetKGMutation = useMutation({
    mutationFn: () => api.resetKnowledgeGraph(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stats'] });
      setShowKGResetConfirm(false);
      alert('✅ Knowledge Graph reset successfully!');
    },
    onError: (error) => {
      alert(`❌ KG Reset failed: ${error}`);
      setShowKGResetConfirm(false);
    },
  });

  const buildKGMutation = useMutation({
    mutationFn: (algorithm: string) => api.buildKnowledgeGraph(algorithm),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['stats'] });
      const stats = data.stats || {};
      alert(`✅ Knowledge Graph built successfully!\n\nNodes: ${stats.nodes}\nEdges: ${stats.edges}\nAlgorithm: ${stats.algorithm}`);
    },
    onError: (error) => {
      alert(`❌ KG Build failed: ${error}`);
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full" />
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-6 text-center">
          <p className="text-destructive">Failed to load documents</p>
        </CardContent>
      </Card>
    );
  }

  // Extract documents array from response
  const documents = response?.documents || [];

  // Filter out only test/debug documents (show everything else including lab docs)
  const userDocuments = documents.filter((doc: string) => {
    const lower = doc.toLowerCase();
    // Only exclude test/debug files
    return !(
      doc.startsWith('test_') ||
      lower.includes('_summary') ||
      lower.includes('archive/')
    );
  });

  if (userDocuments.length === 0) {
    return (
      <Card>
        <CardContent className="p-12 text-center">
          <FileIcon className="h-16 w-16 mx-auto mb-4 text-muted-foreground" />
          <h3 className="text-lg font-semibold mb-2">No documents yet</h3>
          <p className="text-muted-foreground">
            Upload your first document to get started
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Admin Reset Button */}
      <Card className="border-orange-500/50 bg-orange-500/5">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-5 w-5 text-orange-500" />
              <div>
                <h4 className="font-semibold text-sm">Admin: Reset Database</h4>
                <p className="text-xs text-muted-foreground">
                  For LLM poisoning & competitive intelligence labs. Clears all documents and resets to system docs only.
                </p>
              </div>
            </div>
            {!showResetConfirm ? (
              <button
                onClick={() => setShowResetConfirm(true)}
                className="px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded text-sm font-medium transition-colors flex items-center gap-2"
              >
                <RefreshCw className="h-4 w-4" />
                Reset DB
              </button>
            ) : (
              <div className="flex gap-2">
                <button
                  onClick={() => resetMutation.mutate()}
                  disabled={resetMutation.isPending}
                  className="px-3 py-2 bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white rounded text-sm font-medium transition-colors"
                >
                  {resetMutation.isPending ? 'Resetting...' : 'Confirm Reset'}
                </button>
                <button
                  onClick={() => setShowResetConfirm(false)}
                  disabled={resetMutation.isPending}
                  className="px-3 py-2 bg-gray-600 hover:bg-gray-700 disabled:opacity-50 text-white rounded text-sm font-medium transition-colors"
                >
                  Cancel
                </button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Knowledge Graph Rebuild */}
      <Card className="border-blue-500/50 bg-blue-500/5">
        <CardContent className="p-4">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Network className="h-5 w-5 text-blue-500" />
                <div>
                  <h4 className="font-semibold text-sm">Knowledge Graph: Rebuild with Algorithm</h4>
                  <p className="text-xs text-muted-foreground">
                    Compare different graph construction methods and their impact on retrieval quality.
                  </p>
                </div>
              </div>
            </div>

            <div className="flex gap-3 items-center">
              {/* Algorithm Selector */}
              <select
                value={selectedAlgorithm}
                onChange={(e) => setSelectedAlgorithm(e.target.value)}
                disabled={buildKGMutation.isPending}
                className="flex-1 px-3 py-2 bg-background border rounded text-sm disabled:opacity-50"
              >
                {algorithmsData?.algorithms && Object.entries(algorithmsData.algorithms).map(([key, algo]: [string, any]) => (
                  <option key={key} value={key}>
                    {algo.name} - {algo.speed}
                  </option>
                ))}
              </select>

              {/* Build Button */}
              <button
                onClick={() => buildKGMutation.mutate(selectedAlgorithm)}
                disabled={buildKGMutation.isPending}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded text-sm font-medium transition-colors flex items-center gap-2"
              >
                <Network className="h-4 w-4" />
                {buildKGMutation.isPending ? 'Building...' : 'Rebuild KG'}
              </button>

              {/* Reset KG Button */}
              {!showKGResetConfirm ? (
                <button
                  onClick={() => setShowKGResetConfirm(true)}
                  className="px-3 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded text-sm font-medium transition-colors"
                  title="Reset Knowledge Graph"
                >
                  <RefreshCw className="h-4 w-4" />
                </button>
              ) : (
                <div className="flex gap-1">
                  <button
                    onClick={() => resetKGMutation.mutate()}
                    disabled={resetKGMutation.isPending}
                    className="px-2 py-2 bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white rounded text-xs font-medium"
                    title="Confirm Reset KG"
                  >
                    ✓
                  </button>
                  <button
                    onClick={() => setShowKGResetConfirm(false)}
                    disabled={resetKGMutation.isPending}
                    className="px-2 py-2 bg-gray-600 hover:bg-gray-700 disabled:opacity-50 text-white rounded text-xs font-medium"
                    title="Cancel"
                  >
                    ✗
                  </button>
                </div>
              )}
            </div>

            {/* Algorithm Info */}
            {algorithmsData?.algorithms && selectedAlgorithm && (
              <div className="text-xs text-muted-foreground bg-background/50 p-2 rounded">
                <p className="font-medium">{algorithmsData.algorithms[selectedAlgorithm]?.description}</p>
                <p className="mt-1">
                  <span className="font-medium">Best for:</span> {algorithmsData.algorithms[selectedAlgorithm]?.best_for}
                </p>
                <p>
                  <span className="font-medium">Speed:</span> {algorithmsData.algorithms[selectedAlgorithm]?.speed} | 
                  <span className="font-medium"> Accuracy:</span> {algorithmsData.algorithms[selectedAlgorithm]?.accuracy}
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Document List */}
      <div className="grid gap-3">
        {userDocuments.map((filename: string, index: number) => {
          const Icon = getFileIcon(filename);
          const colorClass = getFileColor(filename);

          return (
            <Card key={index}>
              <CardContent className="p-4">
                <div className="flex items-center gap-4">
                  <div className={`flex-shrink-0 ${colorClass}`}>
                    <Icon className="h-8 w-8" />
                  </div>

                  <div className="flex-1 min-w-0">
                    <h4 className="font-medium truncate">{filename}</h4>
                    <p className="text-sm text-muted-foreground">
                      User uploaded
                    </p>
                  </div>

                  <Badge variant="secondary">#{index + 1}</Badge>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}

