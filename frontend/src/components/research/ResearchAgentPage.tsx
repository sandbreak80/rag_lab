import React, { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Slider } from '../ui/slider';
import { Badge } from '../ui/badge';
import { Play, RefreshCw, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { useToast } from '../ui/toast';
import { TID } from '../../testids';

interface ResearchAgentStats {
  active_sources: number;
  items_ingested: number;
  success_rate: number;
  last_fetch: string | null;
}

export function ResearchAgentPage() {
  const [sourceLimit, setSourceLimit] = useState(10);
  const [daysBack, setDaysBack] = useState(7);
  const { showToast } = useToast();

  // Check if research feature is enabled
  const researchEnabled = import.meta.env.VITE_RESEARCH_ENABLED !== 'false';

  // Fetch research agent status
  const { data: stats, refetch: refetchStats } = useQuery<ResearchAgentStats>({
    queryKey: ['research-agent-stats'],
    queryFn: async () => {
      const response = await fetch('/api/research-agent/status');
      if (!response.ok) throw new Error('Failed to fetch stats');
      const data = await response.json();
      return data.stats;
    },
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  // Trigger fetch mutation
  const triggerFetch = useMutation({
    mutationFn: async () => {
      const response = await fetch('/api/research-agent/trigger/custom', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_limit: sourceLimit,
          days_back: daysBack,
          rebuild_kg: true,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to trigger fetch');
      }

      return response.json();
    },
    onSuccess: (data) => {
      showToast('success', `✅ Research Agent Started!\n\nFetching from ${data.sources_selected} sources\nLast ${data.days_back} days of content\nKnowledge graph will rebuild automatically`);
      // Start polling for updates
      setTimeout(() => refetchStats(), 2000);
    },
    onError: (error) => {
      showToast('error', `❌ Failed to start: ${error}`);
    },
  });

  const handleTrigger = () => {
    triggerFetch.mutate();
  };

  // Feature flag guard
  if (!researchEnabled) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] p-8">
        <Card className="max-w-2xl w-full" data-testid="research-disabled">
          <CardContent className="p-12 text-center space-y-6">
            <div className="flex justify-center">
              <div className="rounded-full bg-muted p-6">
                <AlertCircle className="h-16 w-16 text-muted-foreground" />
              </div>
            </div>
            
            <div className="space-y-2">
              <h2 className="text-2xl font-bold">Research Agent Coming Soon</h2>
              <p className="text-muted-foreground">
                The Research Agent feature is currently in development and will be available in a future release.
              </p>
            </div>

            <div className="bg-muted rounded-lg p-4 space-y-2">
              <div className="flex items-center gap-2 text-sm font-medium">
                <AlertCircle className="h-4 w-4" />
                <span>Feature Status: Development</span>
              </div>
              <p className="text-xs text-muted-foreground text-left">
                The Research Agent will enable multi-step reasoning, web research, and knowledge synthesis
                for complex queries that require gathering information from multiple sources.
              </p>
            </div>

            <div className="pt-4">
              <a
                href="/"
                className="inline-flex items-center gap-2 px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
              >
                Return to Chat
              </a>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid={TID.Research.Panel}>
      {/* Header Card */}
      <Card className="border-blue-500/50 bg-blue-500/5">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <RefreshCw className="h-5 w-5 text-blue-500" />
            🤖 Research Agent Control Panel
          </CardTitle>
          <CardDescription>
            Automatically discover and ingest AI research content from 31 sources
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Current Status */}
      {stats && (
        <Card data-testid={TID.Research.Status}>
          <CardHeader>
            <CardTitle>Current Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <div className="text-sm text-muted-foreground">Active Sources</div>
                <div className="text-2xl font-bold">{stats.active_sources}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Items Ingested</div>
                <div className="text-2xl font-bold">{stats.items_ingested.toLocaleString()}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Success Rate</div>
                <div className="text-2xl font-bold">{stats.success_rate.toFixed(1)}%</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Last Fetch</div>
                <div className="text-sm font-medium">
                  {stats.last_fetch ? new Date(stats.last_fetch).toLocaleString() : 'Never'}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Control Panel */}
      <Card>
        <CardHeader>
          <CardTitle>Fetch Configuration</CardTitle>
          <CardDescription>
            Adjust parameters and trigger a custom fetch
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-8">
          {/* Source Limit Slider */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">Number of Sources</label>
              <Badge variant="outline" className="text-base px-3 py-1">
                {sourceLimit} {sourceLimit === stats?.active_sources ? '(All)' : 'sources'}
              </Badge>
            </div>
            <Slider
              value={sourceLimit}
              onValueChange={setSourceLimit}
              min={1}
              max={stats?.active_sources || 31}
              step={1}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>1 source</span>
              <span>All {stats?.active_sources || 31} sources</span>
            </div>
          </div>

          {/* Days Back Slider */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">Lookback Period</label>
              <Badge variant="outline" className="text-base px-3 py-1">
                {daysBack} {daysBack === 1 ? 'day' : 'days'}
              </Badge>
            </div>
            <Slider
              value={daysBack}
              onValueChange={setDaysBack}
              min={1}
              max={90}
              step={1}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>1 day</span>
              <span>90 days</span>
            </div>
            <div className="text-xs text-muted-foreground">
              💡 Tip: Higher values may find more content but take longer to process
            </div>
          </div>

          {/* Estimated Impact */}
          <div className="p-4 bg-muted rounded-lg space-y-2">
            <div className="text-sm font-medium">Estimated Fetch</div>
            <div className="grid grid-cols-2 gap-2 text-sm text-muted-foreground">
              <div>Sources: {sourceLimit}</div>
              <div>Days: {daysBack}</div>
              <div>Max Articles: ~{sourceLimit * 100}</div>
              <div>Est. Time: ~{Math.ceil(sourceLimit / 5) * 30}s</div>
            </div>
            <div className="text-xs text-amber-600 dark:text-amber-400 mt-2">
              ⚡ Knowledge graph will automatically rebuild after fetch
            </div>
          </div>

          {/* Trigger Button */}
          <Button
            onClick={handleTrigger}
            disabled={triggerFetch.isPending}
            className="w-full"
            size="lg"
            data-testid={TID.Research.Run}
          >
            {triggerFetch.isPending ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                Fetching in Progress...
              </>
            ) : (
              <>
                <Play className="mr-2 h-5 w-5" />
                Start Research Agent
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* How It Works */}
      <Card>
        <CardHeader>
          <CardTitle>How It Works</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-500/10 flex items-center justify-center text-blue-500 font-bold">
              1
            </div>
            <div>
              <div className="font-medium">Discover Content</div>
              <div className="text-sm text-muted-foreground">
                Fetch articles from selected sources using RSS feeds and web scraping
              </div>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-500/10 flex items-center justify-center text-blue-500 font-bold">
              2
            </div>
            <div>
              <div className="font-medium">Extract Full Text</div>
              <div className="text-sm text-muted-foreground">
                Use Trafilatura to extract full article content (not just summaries)
              </div>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-500/10 flex items-center justify-center text-blue-500 font-bold">
              3
            </div>
            <div>
              <div className="font-medium">Ingest & Index</div>
              <div className="text-sm text-muted-foreground">
                Generate embeddings and store in vector database for semantic search
              </div>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-purple-500/10 flex items-center justify-center text-purple-500 font-bold">
              4
            </div>
            <div>
              <div className="font-medium">Rebuild Knowledge Graph</div>
              <div className="text-sm text-muted-foreground">
                Automatically extract entities and relationships for enhanced retrieval
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Sources Info */}
      <Card>
        <CardHeader>
          <CardTitle>Available Sources ({stats?.active_sources || 31})</CardTitle>
          <CardDescription>
            High-quality AI research feeds from academia and industry
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-sm">
            <div>📄 arXiv AI/ML</div>
            <div>🤗 Hugging Face Papers</div>
            <div>📰 TechCrunch AI</div>
            <div>📰 VentureBeat AI</div>
            <div>📰 The Verge AI</div>
            <div>📰 Wired AI</div>
            <div>📰 Ars Technica AI</div>
            <div>🔬 ScienceDaily AI</div>
            <div>📰 AI News</div>
            <div>📰 The Guardian AI</div>
            <div>📊 Analytics Vidhya</div>
            <div>📊 KDnuggets</div>
            <div>📚 ML Mastery</div>
            <div>🎓 Berkeley AI Research</div>
            <div>🏢 Google AI Blog</div>
            <div>🏢 Microsoft AI Blog</div>
            <div>🏢 AWS AI Blog</div>
            <div>🏢 DeepMind Blog</div>
            <div>🏢 OpenAI Blog</div>
            <div>🏢 Anthropic</div>
            <div className="text-muted-foreground">+ 11 more...</div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

