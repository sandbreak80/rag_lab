import React from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { DocumentUpload } from './DocumentUpload';
import { DocumentList } from './DocumentList';

export function DocumentsPage() {
  const queryClient = useQueryClient();

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
