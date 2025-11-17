import React from 'react';
import { ExternalLink, Activity, Database, Cpu, Gauge } from 'lucide-react';
import { TID } from '../../testids';

export function MonitoringPage() {
  // Use proxied paths through nginx (port 3000) for Grafana and Prometheus
  // Grafana is configured with GF_SERVER_SERVE_FROM_SUB_PATH=true and GF_SERVER_ROOT_URL=http://...:3000/graf
  // Access /graf/login directly to avoid redirect loop from /graf/ to /graf/login
  const baseUrl = window.location.origin; // Use current origin (works in dev and prod)
  const grafanaUrl = import.meta.env.VITE_GRAFANA_URL || `${baseUrl}/graf/login`;
  const prometheusUrl = import.meta.env.VITE_PROMETHEUS_URL || `${baseUrl}/prom/`;

  return (
    <div className="flex flex-col w-full">
      {/* Header */}
      <div className="bg-card border-b p-6 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-3">
              <Activity className="h-8 w-8 text-primary" />
              System Monitoring
            </h1>
            <p className="text-muted-foreground mt-2">
              Real-time system metrics powered by Prometheus + Grafana
            </p>
          </div>
          <div className="flex gap-3">
            <a
              href={grafanaUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
              data-testid="grafana-link"
            >
              <ExternalLink className="h-4 w-4" />
              Open Grafana
            </a>
            <a
              href={prometheusUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 transition-colors"
            >
              <Database className="h-4 w-4" />
              Prometheus
            </a>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-4 gap-4 mt-6" data-testid={TID.Monitoring.Panel}>
          <div className="bg-background border rounded-lg p-4" data-testid={TID.Monitoring.CpuChart}>
            <div className="flex items-center gap-3">
              <Cpu className="h-8 w-8 text-blue-500" />
              <div>
                <div className="text-sm text-muted-foreground">Container Metrics</div>
                <div className="text-lg font-semibold">CPU, Memory, Network</div>
              </div>
            </div>
          </div>

          <div className="bg-background border rounded-lg p-4" data-testid={TID.Monitoring.GpuChart}>
            <div className="flex items-center gap-3">
              <Gauge className="h-8 w-8 text-green-500" />
              <div>
                <div className="text-sm text-muted-foreground">GPU Stats</div>
                <div className="text-lg font-semibold">Utilization & Temp</div>
              </div>
            </div>
          </div>

          <div className="bg-background border rounded-lg p-4" data-testid={TID.Monitoring.HealthChart}>
            <div className="flex items-center gap-3">
              <Activity className="h-8 w-8 text-purple-500" />
              <div>
                <div className="text-sm text-muted-foreground">Service Health</div>
                <div className="text-lg font-semibold">All Services</div>
              </div>
            </div>
          </div>

          <div className="bg-background border rounded-lg p-4">
            <div className="flex items-center gap-3">
              <Database className="h-8 w-8 text-orange-500" />
              <div>
                <div className="text-sm text-muted-foreground">Data Retention</div>
                <div className="text-lg font-semibold">30 Days</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Grafana Dashboard - Open in New Tab */}
      <div className="w-full p-12 bg-background flex flex-col items-center justify-center gap-6">
        <div className="text-center max-w-2xl">
          <h2 className="text-2xl font-semibold mb-4">Open Dashboards in New Tab</h2>
          <p className="text-muted-foreground mb-6">
            Grafana dashboards are best viewed in their native interface. Click the buttons above to open
            Grafana or Prometheus in a new tab with full functionality.
          </p>
        </div>

        <div className="flex gap-4">
          <a
            href={grafanaUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors text-lg font-medium"
            data-testid="monitoring-open-grafana"
          >
            <ExternalLink className="h-5 w-5" />
            Open Grafana Dashboard
          </a>
          <a
            href={prometheusUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-6 py-3 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 transition-colors text-lg font-medium"
            data-testid="monitoring-open-prometheus"
          >
            <Database className="h-5 w-5" />
            Open Prometheus
          </a>
        </div>

        <div className="mt-8 p-4 bg-muted rounded-lg max-w-xl">
          <p className="text-sm text-muted-foreground">
            <strong>Note:</strong> Embedding Grafana under a subpath can cause rendering issues.
            Direct access provides the best experience with full dashboard functionality.
          </p>
        </div>
      </div>

      {/* Footer Help */}
      <div className="bg-card border-t p-4 flex-shrink-0">
        <div className="text-sm text-muted-foreground flex items-center justify-between">
          <div>
            <strong>Tips:</strong> Click any panel to zoom • Use time range picker (top right) • Refresh: 10s
          </div>
          <div className="flex gap-4">
            <a href="/docs/monitoring" className="text-primary hover:underline">
              Documentation
            </a>
            <a href="https://grafana.com/docs/" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
              Grafana Docs
            </a>
            <a href="https://prometheus.io/docs/" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
              Prometheus Docs
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}

