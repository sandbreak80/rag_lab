import React, { useState } from 'react';
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { DocumentUpload } from './DocumentUpload';
import { DocumentList } from './DocumentList';
import { api } from '../../services/api';
import { Network, RefreshCw } from 'lucide-react';

export function DocumentsPage() {
  const [selectedAlgorithm, setSelectedAlgorithm] = useState(() => {
    return localStorage.getItem('kg-algorithm') || 'wikilinks';
  });
  const [showKGResetConfirm, setShowKGResetConfirm] = useState(false);
  const queryClient = useQueryClient();

  // Save algorithm to localStorage when it changes
  const handleAlgorithmChange = (algo: string) => {
    setSelectedAlgorithm(algo);
    localStorage.setItem('kg-algorithm', algo);
  };

  // Get available KG algorithms
  const { data: algorithmsData } = useQuery({
    queryKey: ['kg-algorithms'],
    queryFn: () => api.getKGAlgorithms(),
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

  const handleUploadComplete = () => {
    // Refetch documents list and stats
    queryClient.invalidateQueries({ queryKey: ['documents'] });
    queryClient.invalidateQueries({ queryKey: ['stats'] });
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>📁 Upload Documents</CardTitle>
          <CardDescription>
            Upload PDF, Word, PowerPoint, Excel, Text, or Markdown files to add them to your knowledge base
          </CardDescription>
        </CardHeader>
        <CardContent>
          <DocumentUpload onUploadComplete={handleUploadComplete} />
        </CardContent>
      </Card>

      {/* Knowledge Graph Rebuild Card */}
      <Card className="border-blue-500/50 bg-blue-500/5">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Network className="h-5 w-5 text-blue-500" />
            🔵 Knowledge Graph: Rebuild with Algorithm
          </CardTitle>
          <CardDescription>
            Compare different graph construction methods and their impact on retrieval quality
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex gap-3 items-center">
              {/* Algorithm Selector */}
              <select
                value={selectedAlgorithm}
                onChange={(e) => handleAlgorithmChange(e.target.value)}
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
              <div className="text-xs text-muted-foreground bg-background/50 p-3 rounded border">
                <p className="font-medium mb-1">{algorithmsData.algorithms[selectedAlgorithm]?.description}</p>
                <p>
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

      <Card>
        <CardHeader>
          <CardTitle>📚 Your Documents</CardTitle>
          <CardDescription>
            Files you've uploaded for RAG processing
          </CardDescription>
        </CardHeader>
        <CardContent>
          <DocumentList />
        </CardContent>
      </Card>
    </div>
  );
}
