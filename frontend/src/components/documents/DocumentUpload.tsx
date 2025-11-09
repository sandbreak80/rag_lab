import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useMutation } from '@tanstack/react-query';
import { api } from '../../services/api';
import { UploadProgress } from '../../types/documents';
import { Button } from '../ui/button';
import { Card, CardContent } from '../ui/card';
import { Upload, File, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { formatBytes } from '../../utils/formatting';
import { TID } from '../../testids';

const ALLOWED_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation',
  'application/vnd.ms-powerpoint',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/vnd.ms-excel',
  'text/plain',
  'text/markdown',
  'application/rtf',
];

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

interface DocumentUploadProps {
  onUploadComplete?: () => void;
}

export function DocumentUpload({ onUploadComplete }: DocumentUploadProps) {
  const [uploads, setUploads] = useState<UploadProgress[]>([]);

  const uploadMutation = useMutation({
    mutationFn: (file: File) => {
      return api.uploadDocument(file, (progress) => {
        setUploads((prev) =>
          prev.map((u) =>
            u.filename === file.name ? progress : u
          )
        );
      });
    },
    onSuccess: (data, file) => {
      setUploads((prev) =>
        prev.map((u) =>
          u.filename === file.name
            ? { ...u, status: 'completed' }
            : u
        )
      );
      setTimeout(() => {
        setUploads((prev) => prev.filter((u) => u.filename !== file.name));
        onUploadComplete?.();
      }, 2000);
    },
    onError: (error: any, file) => {
      const errorMsg = error?.response?.data?.message 
        || error?.message 
        || 'Upload failed';
      
      setUploads((prev) =>
        prev.map((u) =>
          u.filename === file.name
            ? { ...u, status: 'error', error: errorMsg }
            : u
        )
      );
    },
  });

  const onDrop = useCallback((acceptedFiles: File[]) => {
    acceptedFiles.forEach((file) => {
      // Add to uploads list
      setUploads((prev) => [
        ...prev,
        {
          filename: file.name,
          progress: 0,
          status: 'uploading',
        },
      ]);

      // Start upload
      uploadMutation.mutate(file);
    });
  }, [uploadMutation]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ALLOWED_TYPES.reduce((acc, type) => ({ ...acc, [type]: [] }), {}),
    maxSize: MAX_FILE_SIZE,
    multiple: true,
  });

  return (
    <div className="space-y-4">
      {/* Drop zone */}
      <Card
        {...getRootProps()}
        className={`cursor-pointer transition-colors ${
          isDragActive ? 'border-primary bg-primary/5' : 'border-dashed'
        }`}
        data-testid={TID.Upload.Zone}
      >
        <CardContent className="p-8">
          <input {...getInputProps()} data-testid={TID.Upload.Input} />
          <div className="flex flex-col items-center text-center">
            <Upload
              className={`h-12 w-12 mb-4 ${
                isDragActive ? 'text-primary' : 'text-muted-foreground'
              }`}
            />
            {isDragActive ? (
              <p className="text-lg font-medium">Drop files here...</p>
            ) : (
              <>
                <p className="text-lg font-medium mb-2">
                  Drag & drop files here, or click to select
                </p>
                <p className="text-sm text-muted-foreground mb-4">
                  Supports PDF, Word, PowerPoint, Excel, Text, Markdown, RTF
                </p>
                <p className="text-xs text-muted-foreground">
                  Maximum file size: {formatBytes(MAX_FILE_SIZE)}
                </p>
              </>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Upload progress */}
      {uploads.length > 0 && (
        <div className="space-y-2" data-testid={TID.Upload.List}>
          <h3 className="text-sm font-medium">Uploading files</h3>
          {uploads.map((upload) => (
            <Card key={upload.filename} data-testid={TID.Upload.Item(upload.filename)}>
              <CardContent className="p-3">
                <div className="flex items-center gap-3">
                  <File className="h-5 w-5 flex-shrink-0 text-muted-foreground" />

                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">
                      {upload.filename}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      {upload.status === 'uploading' && (
                        <>
                          <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                            <div
                              className="h-full bg-primary transition-all"
                              style={{ width: `${upload.progress}%` }}
                            />
                          </div>
                          <span className="text-xs text-muted-foreground">
                            {upload.progress}%
                          </span>
                        </>
                      )}
                      {upload.status === 'processing' && (
                        <>
                          <Loader2 className="h-4 w-4 animate-spin text-primary" />
                          <span className="text-xs text-muted-foreground">
                            Processing...
                          </span>
                        </>
                      )}
                      {upload.status === 'completed' && (
                        <>
                          <CheckCircle className="h-4 w-4 text-green-500" />
                          <span className="text-xs text-green-500">
                            Complete
                          </span>
                        </>
                      )}
                      {upload.status === 'error' && (
                        <>
                          <XCircle className="h-4 w-4 text-destructive" />
                          <span className="text-xs text-destructive" data-testid={TID.Upload.Error}>
                            {upload.error || 'Upload failed'}
                          </span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

