import React, { useState, useMemo, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../services/api';
import { Card, CardContent } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { FileText, FileImage, FileSpreadsheet, File as FileIcon, RefreshCw, AlertTriangle, ChevronLeft, ChevronRight } from 'lucide-react';
import { useToast } from '../ui/toast';

const DOCUMENTS_PER_PAGE = 20;

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
  const [currentPage, setCurrentPage] = useState(1);
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  const { data: response, isLoading, error } = useQuery({
    queryKey: ['documents'],
    queryFn: () => api.getDocuments(),
    refetchInterval: 10000, // Refetch every 10 seconds
    retry: 1,
    staleTime: 5000, // Consider data fresh for 5 seconds
  });

  const resetMutation = useMutation({
    mutationFn: () => api.resetDatabase(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
      setShowResetConfirm(false);
      showToast('success', '✅ Database reset successfully! System docs will be re-ingested automatically.');
    },
    onError: (error) => {
      showToast('error', `❌ Reset failed: ${error}`);
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
  const documents = Array.isArray(response?.documents) ? response.documents : [];

  // Filter out only test/debug documents (show everything else including lab docs)
  const userDocuments = useMemo(() => {
    if (!Array.isArray(documents) || documents.length === 0) {
      return [];
    }
    return documents.filter((doc: string) => {
      if (!doc || typeof doc !== 'string') return false;
      const lower = doc.toLowerCase();
      // Only exclude test/debug files
      return !(
        doc.startsWith('test_') ||
        lower.includes('_summary') ||
        lower.includes('archive/')
      );
    });
  }, [documents]);

  // Early return for empty documents
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

  // Calculate pagination (only when we have documents)
  const totalPages = Math.max(1, Math.ceil(userDocuments.length / DOCUMENTS_PER_PAGE));
  const startIndex = Math.max(0, (currentPage - 1) * DOCUMENTS_PER_PAGE);
  const endIndex = Math.min(startIndex + DOCUMENTS_PER_PAGE, userDocuments.length);
  const paginatedDocuments = userDocuments.slice(startIndex, endIndex);

  // Reset to page 1 if current page is out of bounds
  useEffect(() => {
    if (totalPages > 0 && currentPage > totalPages) {
      setCurrentPage(1);
    }
  }, [currentPage, totalPages]);

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
      <div className="space-y-4">
        <div className="grid gap-3">
          {paginatedDocuments.map((filename: string, index: number) => {
            if (!filename || typeof filename !== 'string') {
              return null;
            }
            const Icon = getFileIcon(filename);
            const colorClass = getFileColor(filename);
            const globalIndex = startIndex + index;

            return (
              <Card key={`doc-${globalIndex}-${filename}`} data-testid="doc-row">
                <CardContent className="p-4">
                  <div className="flex items-center gap-4">
                    <div className={`flex-shrink-0 ${colorClass}`}>
                      <Icon className="h-8 w-8" />
                    </div>

                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium truncate" data-testid="doc-filename">{filename}</h4>
                      <p className="text-sm text-muted-foreground">
                        User uploaded
                      </p>
                    </div>

                    <Badge variant="secondary">#{globalIndex + 1}</Badge>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Pagination Controls */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between pt-4 border-t">
            <div className="text-sm text-muted-foreground">
              Showing {startIndex + 1} to {Math.min(endIndex, userDocuments.length)} of {userDocuments.length} documents
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
              >
                <ChevronLeft className="h-4 w-4 mr-1" />
                Previous
              </Button>

              <div className="flex items-center gap-1">
                {totalPages > 0 && Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => {
                  // Show first page, last page, current page, and pages around current
                  const showPage =
                    page === 1 ||
                    page === totalPages ||
                    (page >= Math.max(1, currentPage - 1) && page <= Math.min(totalPages, currentPage + 1));

                  if (!showPage) {
                    // Show ellipsis
                    if (page === Math.max(1, currentPage - 2) || page === Math.min(totalPages, currentPage + 2)) {
                      return (
                        <span key={`ellipsis-${page}`} className="px-2 text-muted-foreground">
                          ...
                        </span>
                      );
                    }
                    return null;
                  }

                  return (
                    <Button
                      key={page}
                      variant={currentPage === page ? "default" : "outline"}
                      size="sm"
                      onClick={() => setCurrentPage(page)}
                      className="min-w-[2.5rem]"
                    >
                      {page}
                    </Button>
                  );
                })}
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                disabled={currentPage === totalPages}
              >
                Next
                <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

