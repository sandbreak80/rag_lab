import React, { useMemo, useState } from 'react';
import { useMetricsStore } from '../../stores/metricsStore';
import { QueryMetric } from '../../types/metrics';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { FileText, Download, Filter, AlertTriangle, TrendingUp } from 'lucide-react';
import { formatDate } from '../../utils/formatting';

export function PromptLoggingPage() {
  const queries = useMetricsStore((state) => state.queries);
  const [selectedQuery, setSelectedQuery] = useState<QueryMetric | null>(null);
  const [filterRisky, setFilterRisky] = useState(false);

  // Analyze queries for patterns
  const analysis = useMemo(() => {
    const totalQueries = queries.length;
    const uniqueQueries = new Set(queries.map(q => q.query.toLowerCase().trim())).size;
    
    // Detect potentially risky queries
    const riskyPatterns = [
      /password/i,
      /secret/i,
      /api[_\s]?key/i,
      /token/i,
      /confidential/i,
      /private/i,
      /ssn|social security/i,
      /credit card/i,
    ];
    
    const riskyQueries = queries.filter(q => 
      riskyPatterns.some(pattern => pattern.test(q.query))
    );
    
    // Query length analysis
    const avgLength = queries.length > 0
      ? queries.reduce((sum, q) => sum + q.query.length, 0) / queries.length
      : 0;
    
    // Time-based patterns
    const queryTimes = queries.map(q => new Date(q.timestamp).getHours());
    const peakHour = queryTimes.length > 0
      ? queryTimes.reduce((a, b, i, arr) => 
          arr.filter(v => v === a).length >= arr.filter(v => v === b).length ? a : b
        )
      : 0;
    
    return {
      totalQueries,
      uniqueQueries,
      repetitionRate: totalQueries > 0 ? ((totalQueries - uniqueQueries) / totalQueries * 100) : 0,
      riskyQueries: riskyQueries.length,
      avgLength: Math.round(avgLength),
      peakHour,
    };
  }, [queries]);

  const displayQueries = filterRisky 
    ? queries.filter(q => 
        (/password|secret|api.*key|token|confidential|private|ssn|credit/i).test(q.query)
      )
    : queries;

  const handleExportLogs = () => {
    // Export in Splunk-compatible JSON format
    const logs = queries.map(q => ({
      timestamp: new Date(q.timestamp).toISOString(),
      query: q.query,
      user: 'demo-user', // In production, this would be actual user ID
      model: q.config.model,
      temperature: q.config.temperature,
      latency_ms: q.performance.total_latency_ms,
      tokens: q.tokens.total_tokens,
      prompt_tokens: q.tokens.prompt_tokens,
      completion_tokens: q.tokens.completion_tokens,
      results_count: q.results.total_results,
      features_enabled: {
        query_expansion: q.config.useQueryExpansion,
        bm25: q.config.useBM25,
        hybrid: q.config.useHybrid,
        knowledge_graph: q.config.useGraph,
        reranking: q.config.useReranking,
        web_search: q.config.useWebSearch,
      },
      // Splunk fields
      sourcetype: 'rag:query',
      source: 'rag-lab',
      host: 'localhost',
    }));

    const blob = new Blob([JSON.stringify(logs, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `rag-prompt-logs-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2">📝 Prompt Logging & Analysis</h1>
          <p className="text-muted-foreground">
            Enterprise-grade prompt tracking for security, compliance, and quality analysis
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setFilterRisky(!filterRisky)}>
            <Filter className="h-4 w-4 mr-2" />
            {filterRisky ? 'Show All' : 'Show Risky'}
          </Button>
          <Button variant="outline" onClick={handleExportLogs}>
            <Download className="h-4 w-4 mr-2" />
            Export to Splunk
          </Button>
        </div>
      </div>

      {/* Splunk Integration Info */}
      <Card className="border-blue-500/50 bg-blue-500/5">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-blue-500" />
            🔵 Splunk Observability Integration
          </CardTitle>
          <CardDescription>
            This is what enterprise AI systems log and send to Splunk for monitoring
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <p>
            <strong>What We Capture:</strong> Every query, user, model, config, latency, tokens, results
          </p>
          <p>
            <strong>Why It Matters:</strong> Security (detect abuse), Quality (identify failing queries), Cost (attribution)
          </p>
          <p>
            <strong>Splunk Use Cases:</strong>
          </p>
          <ul className="list-disc list-inside ml-4 space-y-1 text-muted-foreground">
            <li>Alert on risky queries (passwords, PII)</li>
            <li>Dashboard: Queries/min, Latency p95, Cost/user</li>
            <li>Anomaly detection: Unusual query patterns</li>
            <li>Compliance: Audit trail for all AI interactions</li>
            <li>Quality: Track which configs produce best results</li>
          </ul>
        </CardContent>
      </Card>

      {/* Analysis Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <FileText className="h-8 w-8 text-blue-500" />
              <div>
                <p className="text-sm text-muted-foreground">Total Queries</p>
                <p className="text-2xl font-bold">{analysis.totalQueries}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <TrendingUp className="h-8 w-8 text-green-500" />
              <div>
                <p className="text-sm text-muted-foreground">Unique Queries</p>
                <p className="text-2xl font-bold">{analysis.uniqueQueries}</p>
                <p className="text-xs text-muted-foreground">
                  {analysis.repetitionRate.toFixed(0)}% repeated
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <AlertTriangle className="h-8 w-8 text-yellow-500" />
              <div>
                <p className="text-sm text-muted-foreground">Risky Queries</p>
                <p className="text-2xl font-bold">{analysis.riskyQueries}</p>
                <p className="text-xs text-muted-foreground">
                  {analysis.totalQueries > 0 
                    ? ((analysis.riskyQueries / analysis.totalQueries) * 100).toFixed(1)
                    : 0}% of total
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <FileText className="h-8 w-8 text-purple-500" />
              <div>
                <p className="text-sm text-muted-foreground">Avg Length</p>
                <p className="text-2xl font-bold">{analysis.avgLength}</p>
                <p className="text-xs text-muted-foreground">characters</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Query Log Table */}
      <Card>
        <CardHeader>
          <CardTitle>Query Log</CardTitle>
          <CardDescription>
            All prompts with metadata - Click to see full details
          </CardDescription>
        </CardHeader>
        <CardContent>
          {displayQueries.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No queries logged yet</p>
              <p className="text-sm">Start chatting to see prompt logs appear here</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-[600px] overflow-y-auto">
              {displayQueries.slice().reverse().map((query, index) => {
                const isRisky = /password|secret|api.*key|token|confidential|private|ssn|credit/i.test(query.query);
                
                return (
                  <div
                    key={query.id}
                    onClick={() => setSelectedQuery(query)}
                    className={`p-4 border rounded-lg cursor-pointer transition-colors hover:bg-muted/50 ${
                      isRisky ? 'border-yellow-500/50 bg-yellow-500/5' : ''
                    }`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 space-y-1">
                        <div className="flex items-center gap-2">
                          {isRisky && (
                            <AlertTriangle className="h-4 w-4 text-yellow-500" />
                          )}
                          <span className="font-medium line-clamp-1">{query.query}</span>
                        </div>
                        <div className="flex items-center gap-3 text-xs text-muted-foreground">
                          <span>{formatDate(query.timestamp)}</span>
                          <span>•</span>
                          <span>{query.config.model}</span>
                          <span>•</span>
                          <span>{query.tokens.total_tokens} tokens</span>
                          <span>•</span>
                          <span>{query.performance.total_latency_ms.toFixed(0)}ms</span>
                        </div>
                      </div>
                      <Button variant="ghost" size="sm">
                        View →
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Detail Modal */}
      {selectedQuery && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setSelectedQuery(null)}>
          <Card className="max-w-3xl w-full max-h-[80vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <CardTitle>Query Details</CardTitle>
                  <CardDescription className="mt-2">
                    {formatDate(selectedQuery.timestamp)}
                  </CardDescription>
                </div>
                <Button variant="ghost" size="icon" onClick={() => setSelectedQuery(null)}>
                  ✕
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Query */}
              <div>
                <h4 className="text-sm font-medium mb-2">Query</h4>
                <p className="text-sm bg-muted p-3 rounded">{selectedQuery.query}</p>
              </div>

              {/* Metadata */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="text-sm font-medium mb-2">Configuration</h4>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between"><span className="text-muted-foreground">Model:</span> <span>{selectedQuery.config.model}</span></div>
                    <div className="flex justify-between"><span className="text-muted-foreground">Temperature:</span> <span>{selectedQuery.config.temperature}</span></div>
                    <div className="flex justify-between"><span className="text-muted-foreground">Top-K:</span> <span>{selectedQuery.config.topK}</span></div>
                  </div>
                </div>

                <div>
                  <h4 className="text-sm font-medium mb-2">Performance</h4>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between"><span className="text-muted-foreground">Latency:</span> <span>{selectedQuery.performance.total_latency_ms.toFixed(0)}ms</span></div>
                    <div className="flex justify-between"><span className="text-muted-foreground">Tokens:</span> <span>{selectedQuery.tokens.total_tokens}</span></div>
                    <div className="flex justify-between"><span className="text-muted-foreground">Results:</span> <span>{selectedQuery.results.total_results}</span></div>
                  </div>
                </div>
              </div>

              {/* Features */}
              <div>
                <h4 className="text-sm font-medium mb-2">Features Enabled</h4>
                <div className="flex flex-wrap gap-2">
                  {selectedQuery.config.useQueryExpansion && <span className="px-2 py-1 bg-green-500/20 text-green-500 text-xs rounded">Query Expansion</span>}
                  {selectedQuery.config.useBM25 && <span className="px-2 py-1 bg-blue-500/20 text-blue-500 text-xs rounded">BM25</span>}
                  {selectedQuery.config.useHybrid && <span className="px-2 py-1 bg-purple-500/20 text-purple-500 text-xs rounded">Hybrid</span>}
                  {selectedQuery.config.useGraph && <span className="px-2 py-1 bg-pink-500/20 text-pink-500 text-xs rounded">Knowledge Graph</span>}
                  {selectedQuery.config.useReranking && <span className="px-2 py-1 bg-red-500/20 text-red-500 text-xs rounded">Reranking</span>}
                  {selectedQuery.config.useWebSearch && <span className="px-2 py-1 bg-cyan-500/20 text-cyan-500 text-xs rounded">Web Search</span>}
                </div>
              </div>

              {/* Splunk Export Preview */}
              <div>
                <h4 className="text-sm font-medium mb-2">Splunk JSON Format</h4>
                <pre className="text-xs bg-muted p-3 rounded overflow-x-auto">
{JSON.stringify({
  timestamp: new Date(selectedQuery.timestamp).toISOString(),
  query: selectedQuery.query,
  user: 'demo-user',
  model: selectedQuery.config.model,
  latency_ms: selectedQuery.performance.total_latency_ms,
  tokens: selectedQuery.tokens.total_tokens,
  sourcetype: 'rag:query',
  source: 'rag-lab',
}, null, 2)}
                </pre>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

