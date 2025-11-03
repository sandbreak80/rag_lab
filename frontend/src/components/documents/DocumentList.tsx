import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../services/api';
import { Card, CardContent } from '../ui/card';
import { Badge } from '../ui/badge';
import { FileText, FileImage, FileSpreadsheet, File as FileIcon, RefreshCw, AlertTriangle } from 'lucide-react';

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
  const queryClient = useQueryClient();

  const { data: response, isLoading, error } = useQuery({
    queryKey: ['documents'],
    queryFn: () => api.getDocuments(),
    refetchInterval: 10000, // Refetch every 10 seconds
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

