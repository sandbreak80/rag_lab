// Document Types
export interface Document {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  uploaded_at: Date;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  chunks?: number;
  tags?: string[];
  metadata?: {
    title?: string;
    author?: string;
    created_date?: string;
  };
}

export interface UploadProgress {
  filename: string;
  progress: number;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  error?: string;
}

