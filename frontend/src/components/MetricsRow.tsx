import React from 'react';
import { Activity, Coins, Zap } from 'lucide-react';

interface MetricsRowProps {
  traceId: string;
  tokensIn: number;
  tokensOut: number;
  costUsd: number;
  latencyMs: number;
  abBucket?: 'A' | 'B';
  grafanaUrl?: string;
}

export const MetricsRow: React.FC<MetricsRowProps> = ({
  traceId,
  tokensIn,
  tokensOut,
  costUsd,
  latencyMs,
  abBucket,
  grafanaUrl = 'http://16.146.148.184:3001',
}) => {
  const traceUrl = `${grafanaUrl}/explore?left={"queries":[{"expr":"${traceId}"}]}`;

  return (
    <div className="mt-3 flex flex-wrap items-center gap-3 rounded-lg border border-gray-200 bg-gray-50 p-2 text-xs text-gray-600">
      {/* Trace ID */}
      <a
        href={traceUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="flex items-center gap-1 hover:text-blue-600"
        title="View trace in Grafana"
      >
        <Activity className="h-3.5 w-3.5" />
        <span className="font-mono">{traceId.slice(0, 8)}...</span>
      </a>

      {/* Latency */}
      <div className="flex items-center gap-1">
        <Zap className="h-3.5 w-3.5" />
        <span>{latencyMs.toFixed(0)}ms</span>
      </div>

      {/* Tokens */}
      <div>
        <span className="text-gray-400">Tokens:</span> {tokensIn}→{tokensOut}
      </div>

      {/* Cost */}
      <div className="flex items-center gap-1">
        <Coins className="h-3.5 w-3.5" />
        <span>${costUsd.toFixed(6)}</span>
      </div>

      {/* A/B Bucket */}
      {abBucket && (
        <div className="rounded bg-indigo-100 px-2 py-0.5 font-medium text-indigo-700">
          {abBucket}
        </div>
      )}
    </div>
  );
};

