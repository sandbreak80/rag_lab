import React from 'react';
import { AlertCircle, Beaker } from 'lucide-react';
import { Card, CardContent } from '../ui/card';

export function ResearchPage() {
  // Check if research feature is enabled
  const researchEnabled = import.meta.env.VITE_RESEARCH_ENABLED === 'true';

  if (!researchEnabled) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] p-8">
        <Card className="max-w-2xl w-full" data-testid="research-disabled">
          <CardContent className="p-12 text-center space-y-6">
            <div className="flex justify-center">
              <div className="rounded-full bg-muted p-6">
                <Beaker className="h-16 w-16 text-muted-foreground" />
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

  // When enabled, render the actual research interface
  return (
    <div className="space-y-6" data-testid="research-enabled">
      <div>
        <h1 className="text-3xl font-bold mb-2">🔬 Research Agent</h1>
        <p className="text-muted-foreground">
          Multi-step reasoning and knowledge synthesis for complex queries
        </p>
      </div>

      <Card>
        <CardContent className="p-6">
          <p className="text-muted-foreground">
            Research agent interface will be implemented here.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

