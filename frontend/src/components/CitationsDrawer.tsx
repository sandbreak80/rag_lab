import React from 'react';
import { Citation } from '../services/ragApiV1';
import { ExternalLink, FileText } from 'lucide-react';

interface CitationsDrawerProps {
  citations: Citation[];
}

export const CitationsDrawer: React.FC<CitationsDrawerProps> = ({ citations }) => {
  if (!citations || citations.length === 0) {
    return null;
  }

  const copyLink = (uri: string) => {
    navigator.clipboard.writeText(uri);
  };

  return (
    <div className="mt-4 rounded-lg border border-gray-200 bg-white p-4">
      <div className="mb-3 flex items-center gap-2">
        <FileText className="h-5 w-5 text-blue-600" />
        <h3 className="text-sm font-semibold text-gray-900">
          Citations ({citations.length})
        </h3>
      </div>
      <ul className="space-y-2">
        {citations.map((citation, idx) => (
          <li
            key={idx}
            className="rounded border border-gray-100 bg-gray-50 p-2 text-xs"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1">
                <div className="mb-1 flex items-center gap-2">
                  <span className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${
                    citation.origin_tool === 'rag' ? 'bg-blue-100 text-blue-700' :
                    citation.origin_tool === 'web_search' ? 'bg-green-100 text-green-700' :
                    'bg-purple-100 text-purple-700'
                  }`}>
                    {citation.origin_tool.toUpperCase().replace('_', ' ')}
                  </span>
                  <span className="font-mono text-gray-600">
                    {citation.doc_id}@{citation.version}
                  </span>
                </div>
                <div className="text-gray-500">
                  Chunk: {citation.chunk_id} • Range: [{citation.char_range[0]}–{citation.char_range[1]}]
                </div>
              </div>
              {citation.source_uri && (
                <div className="flex gap-1">
                  <button
                    onClick={() => window.open(citation.source_uri, '_blank')}
                    className="rounded p-1 hover:bg-gray-200"
                    title="Open source"
                  >
                    <ExternalLink className="h-3.5 w-3.5" />
                  </button>
                  <button
                    onClick={() => copyLink(citation.source_uri)}
                    className="rounded p-1 hover:bg-gray-200"
                    title="Copy link"
                  >
                    📋
                  </button>
                </div>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

