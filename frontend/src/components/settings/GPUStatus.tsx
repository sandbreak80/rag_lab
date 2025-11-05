import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../services/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Cpu, Zap, AlertTriangle, CheckCircle2 } from 'lucide-react';

export function GPUStatus() {
  const { data: gpuStatus, isLoading, isError } = useQuery({
    queryKey: ['gpuStatus'],
    queryFn: () => api.getGPUStatus(),
    refetchInterval: 30000, // Refresh every 30 seconds
    retry: 2,
  });

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Cpu className="h-5 w-5" />
            GPU Status
          </CardTitle>
          <CardDescription>Checking GPU availability...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-muted-foreground">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
            <span>Loading...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (isError || !gpuStatus) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Cpu className="h-5 w-5" />
            GPU Status
          </CardTitle>
          <CardDescription>Unable to detect GPU status</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-destructive">
            <AlertTriangle className="h-4 w-4" />
            <span>Error checking GPU status</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  const isGPU = gpuStatus.mode === 'GPU';
  const statusColor = isGPU ? 'text-green-600 dark:text-green-400' : 'text-orange-600 dark:text-orange-400';
  const StatusIcon = isGPU ? Zap : Cpu;

  return (
    <Card className={isGPU ? 'border-green-500/50' : 'border-orange-500/50'}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <StatusIcon className={`h-5 w-5 ${statusColor}`} />
          GPU Status
        </CardTitle>
        <CardDescription>
          {isGPU ? 'Ollama is using GPU acceleration' : 'Ollama is running on CPU'}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Mode Badge */}
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-muted-foreground">Mode:</span>
          <Badge variant={isGPU ? 'default' : 'secondary'} className={isGPU ? 'bg-green-600' : 'bg-orange-600'}>
            {gpuStatus.mode}
          </Badge>
        </div>

        {/* GPU Info */}
        {isGPU && gpuStatus.gpu_info && gpuStatus.gpu_info !== 'Unknown' && (
          <div className="space-y-2">
            <span className="text-sm font-medium text-muted-foreground">GPU Details:</span>
            <div className="bg-secondary/20 p-3 rounded-md">
              <pre className="text-xs font-mono whitespace-pre-wrap break-all">
                {gpuStatus.gpu_info}
              </pre>
            </div>
          </div>
        )}

        {/* Ollama Status */}
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-muted-foreground">Ollama:</span>
          {gpuStatus.ollama_accessible ? (
            <div className="flex items-center gap-1 text-green-600 dark:text-green-400">
              <CheckCircle2 className="h-4 w-4" />
              <span className="text-sm">Accessible</span>
            </div>
          ) : (
            <div className="flex items-center gap-1 text-destructive">
              <AlertTriangle className="h-4 w-4" />
              <span className="text-sm">Not accessible</span>
            </div>
          )}
        </div>

        {/* Recommendation */}
        <div className={`p-3 rounded-md ${isGPU ? 'bg-green-500/10 border border-green-500/20' : 'bg-orange-500/10 border border-orange-500/20'}`}>
          <div className="flex items-start gap-2">
            {isGPU ? (
              <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
            ) : (
              <AlertTriangle className="h-5 w-5 text-orange-600 dark:text-orange-400 flex-shrink-0 mt-0.5" />
            )}
            <div>
              <p className={`text-sm font-medium ${isGPU ? 'text-green-600 dark:text-green-400' : 'text-orange-600 dark:text-orange-400'}`}>
                {isGPU ? 'Optimal Performance' : 'Performance Warning'}
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                {gpuStatus.recommendation}
              </p>
              {!isGPU && (
                <p className="text-xs text-muted-foreground mt-2">
                  To enable GPU: Uncomment the <code className="px-1 py-0.5 bg-secondary rounded text-xs">deploy.resources</code> section in <code className="px-1 py-0.5 bg-secondary rounded text-xs">docker-compose.yml</code> and restart Ollama.
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Performance Impact */}
        {!isGPU && (
          <div className="bg-secondary/20 p-3 rounded-md">
            <p className="text-sm font-medium mb-2">Expected Performance Impact:</p>
            <ul className="text-xs text-muted-foreground space-y-1">
              <li>• LLM inference: <span className="text-orange-600 dark:text-orange-400">10-20x slower</span></li>
              <li>• Query decomposition: <span className="text-orange-600 dark:text-orange-400">4-5s vs &lt;1s</span></li>
              <li>• Answer generation: <span className="text-orange-600 dark:text-orange-400">5-10s vs &lt;1s</span></li>
              <li>• CPU usage: <span className="text-orange-600 dark:text-orange-400">High (300-400%)</span></li>
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

