/**
 * OpenTelemetry Web Instrumentation
 * Enables distributed tracing and RUM (Real User Monitoring) for the frontend
 */

import { WebTracerProvider } from '@opentelemetry/sdk-trace-web';
import { Resource } from '@opentelemetry/resources';
import { ATTR_SERVICE_NAME, ATTR_SERVICE_VERSION } from '@opentelemetry/semantic-conventions';
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-web';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { ZoneContextManager } from '@opentelemetry/context-zone';
import { registerInstrumentations } from '@opentelemetry/instrumentation';
import { FetchInstrumentation } from '@opentelemetry/instrumentation-fetch';
import { XMLHttpRequestInstrumentation } from '@opentelemetry/instrumentation-xml-http-request';
import { DocumentLoadInstrumentation } from '@opentelemetry/instrumentation-document-load';
import { UserInteractionInstrumentation } from '@opentelemetry/instrumentation-user-interaction';
import { onCLS, onFID, onLCP, onFCP, onTTFB, Metric } from 'web-vitals';

/**
 * Initialize OpenTelemetry for the frontend
 * This should be called as early as possible in the app lifecycle
 */
export function initializeOpenTelemetry(): void {
  // Create resource with service metadata
  const resource = Resource.default().merge(
    new Resource({
      [ATTR_SERVICE_NAME]: 'rag-lab-frontend',
      [ATTR_SERVICE_VERSION]: '1.2.4',
      'service.namespace': 'rag-lab',
      'deployment.environment': 'production',
    })
  );

  // Create tracer provider
  const provider = new WebTracerProvider({
    resource,
  });

  // Configure OTLP exporter to send traces to OTel Collector via Nginx
  const exporter = new OTLPTraceExporter({
    url: import.meta.env.VITE_OTEL_EXPORT_URL || '/api/v1/traces',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Add batch span processor
  provider.addSpanProcessor(new BatchSpanProcessor(exporter, {
    maxQueueSize: 100,
    maxExportBatchSize: 10,
    scheduledDelayMillis: 5000,
  }));

  // Register the provider
  provider.register({
    contextManager: new ZoneContextManager(),
  });

  // Register auto-instrumentations
  registerInstrumentations({
    instrumentations: [
      // Instrument fetch API calls
      new FetchInstrumentation({
        propagateTraceHeaderCorsUrls: [
          /^http:\/\/.*:3000\/api\/.*/,  // Local API calls
          /^http:\/\/16\.146\.148\.184:3000\/api\/.*/,  // Production API calls
        ],
        clearTimingResources: true,
        applyCustomAttributesOnSpan: (span, request, result) => {
          if (request instanceof Request) {
            span.setAttribute('http.url', request.url);
            span.setAttribute('http.method', request.method);
          }
          if (result instanceof Response) {
            span.setAttribute('http.status_code', result.status);
          }
        },
      }),
      // Instrument XMLHttpRequest
      new XMLHttpRequestInstrumentation({
        propagateTraceHeaderCorsUrls: [
          /^http:\/\/.*:3000\/api\/.*/,
          /^http:\/\/16\.146\.148\.184:3000\/api\/.*/,
        ],
      }),
      // Instrument document load
      new DocumentLoadInstrumentation(),
      // Instrument user interactions (clicks, etc.)
      new UserInteractionInstrumentation({
        eventNames: ['click', 'submit'],
      }),
    ],
  });

  console.log('✅ OpenTelemetry initialized for frontend');
}

/**
 * Initialize Web Vitals monitoring
 * Sends Core Web Vitals as custom spans
 */
export function initializeWebVitals(): void {
  const sendToAnalytics = (metric: Metric) => {
    // Get the tracer
    const tracer = (globalThis as any).__tracer__;
    if (!tracer) return;

    // Create a span for the web vital
    const span = tracer.startSpan(`web_vital.${metric.name}`, {
      startTime: metric.entries[0]?.startTime || Date.now(),
    });

    span.setAttribute('web_vital.name', metric.name);
    span.setAttribute('web_vital.value', metric.value);
    span.setAttribute('web_vital.rating', metric.rating);
    span.setAttribute('web_vital.delta', metric.delta);
    span.setAttribute('web_vital.id', metric.id);

    span.end();
  };

  // Register Web Vitals callbacks
  onCLS(sendToAnalytics);  // Cumulative Layout Shift
  onFID(sendToAnalytics);  // First Input Delay
  onLCP(sendToAnalytics);  // Largest Contentful Paint
  onFCP(sendToAnalytics);  // First Contentful Paint
  onTTFB(sendToAnalytics); // Time to First Byte

  console.log('✅ Web Vitals monitoring initialized');
}

/**
 * Check if OpenTelemetry is ready
 */
export function isRUMReady(): boolean {
  return typeof (globalThis as any).__tracer__ !== 'undefined';
}

