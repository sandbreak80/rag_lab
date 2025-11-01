import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../services/api';
import { Card, CardContent } from '../ui/card';
import { Badge } from '../ui/badge';
import { FileText, FileImage, FileSpreadsheet, File as FileIcon } from 'lucide-react';

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
  const { data: documents, isLoading, error } = useQuery({
    queryKey: ['documents'],
    queryFn: () => api.getDocuments(),
    refetchInterval: 10000, // Refetch every 10 seconds
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

  // Filter out system/lab documents
  const userDocuments = (documents || []).filter((doc: string) => {
    const lower = doc.toLowerCase();
    return (
      !doc.includes('_SUMMARY') &&
      !doc.includes('lab/') &&
      !doc.includes('docs/') &&
      !doc.includes('LAB_') &&
      !doc.includes('AI_FUNDAMENTALS') &&
      !doc.includes('ARCHITECTURE') &&
      !doc.includes('PERFORMANCE') &&
      !doc.includes('RAG_') &&
      !lower.includes('readme') &&
      (lower.endsWith('.pdf') ||
        lower.endsWith('.docx') ||
        lower.endsWith('.pptx') ||
        lower.endsWith('.xlsx') ||
        lower.endsWith('.txt') ||
        lower.endsWith('.rtf'))
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
  );
}

