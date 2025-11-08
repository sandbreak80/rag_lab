import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Download } from 'lucide-react';

interface JSONInspectorProps {
  artifacts: Record<string, any>;
}

export const JSONInspector: React.FC<JSONInspectorProps> = ({ artifacts }) => {
  const [isOpen, setIsOpen] = useState(false);

  const downloadJSON = () => {
    const blob = new Blob([JSON.stringify(artifacts, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `rag-artifacts-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const artifactLabels: Record<string, string> = {
    planner: 'A: Planner',
    retrieval_log: 'B: Retrieval Log',
    evidence_map: 'C: Evidence Map',
    kg_log: 'D: KG Log',
    chunking_report: 'E: Chunking Report',
    guardrail_report: 'F: Guardrail Report',
    ab_eval: 'G: A/B Evaluation',
    recency: 'Recency Gate',
  };

  return (
    <div className="mt-4 rounded-lg border border-gray-200">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex w-full items-center justify-between rounded-t-lg bg-gray-50 p-3 text-sm font-medium hover:bg-gray-100"
      >
        <span>Artifacts (Schemas A–G)</span>
        <div className="flex items-center gap-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              downloadJSON();
            }}
            className="rounded p-1 hover:bg-gray-200"
            title="Download JSON"
          >
            <Download className="h-4 w-4" />
          </button>
          {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </div>
      </button>

      {isOpen && (
        <div className="max-h-96 overflow-auto p-3">
          {Object.entries(artifacts).map(([key, value]) => (
            <details key={key} className="mb-2">
              <summary className="cursor-pointer rounded bg-gray-100 p-2 text-sm font-medium hover:bg-gray-200">
                {artifactLabels[key] || key}
              </summary>
              <pre className="mt-1 overflow-auto rounded bg-gray-50 p-2 text-xs">
                {JSON.stringify(value, null, 2)}
              </pre>
            </details>
          ))}
        </div>
      )}
    </div>
  );
};

