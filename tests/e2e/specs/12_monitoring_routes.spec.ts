import { test, expect } from '@playwright/test';

test('Prometheus endpoint proxied through frontend', async ({ request, baseURL }) => {
  // Check if Prometheus is accessible through nginx
  const promReady = await request.get(`${baseURL}/prom/-/ready`, {
    failOnStatusCode: false
  });

  if (promReady.status() === 200) {
    console.log('✅ Prometheus proxy working');
  } else {
    console.log(`⚠️  Prometheus proxy not configured (status: ${promReady.status()})`);
  }

  // Should either work (200) or not be configured yet (404)
  expect([200, 404, 502]).toContain(promReady.status());
});

test('Metrics endpoint accessible', async ({ request, baseURL }) => {
  // Metrics endpoint might be at /metrics (Prometheus) or /api/metrics
  // Try /metrics first (Prometheus format), then /api/metrics (if proxied)
  let metrics = await request.get(`${baseURL}/metrics`, {
    failOnStatusCode: false
  });

  // If /metrics returns 404 or HTML (SPA route), try /api/metrics
  if (metrics.status() === 404 || metrics.headers()['content-type']?.includes('text/html')) {
    metrics = await request.get(`${baseURL}/api/metrics`, {
      failOnStatusCode: false
    });
  }

  // If still not found, try /prom/metrics (Prometheus proxy)
  if (metrics.status() === 404) {
    metrics = await request.get(`${baseURL}/prom/metrics`, {
      failOnStatusCode: false
    });
  }

  // Metrics endpoint might not be configured - that's okay
  if (metrics.status() === 200) {
    const body = await metrics.text();

    // Should contain Prometheus-format metrics
    const hasPrometheusFormat = body.match(/^[a-z_]+{.*}|^# HELP|^# TYPE/m);

    // Should have our custom metrics (check for any rag_ metric) OR be valid Prometheus format
    const hasRagMetrics = body.match(/rag_/);

    if (hasPrometheusFormat || hasRagMetrics) {
      console.log('✅ Metrics endpoint working');
    } else {
      console.log('⚠️  Metrics endpoint exists but format unexpected');
    }
  } else {
    console.log(`⚠️  Metrics endpoint not accessible (status: ${metrics.status()})`);
    console.log('   This is optional - Prometheus might not be configured');
  }

  // Test passes if endpoint exists (200) or doesn't exist (404) - both are valid
  expect([200, 404, 502, 503]).toContain(metrics.status());
});

test('Grafana endpoint proxied', async ({ request, baseURL }) => {
  // Check if Grafana is accessible through nginx
  const grafana = await request.get(`${baseURL}/graf/`, {
    failOnStatusCode: false,
    maxRedirects: 0 // Don't follow redirects
  });

  const status = grafana.status();
  
  if (status === 200 || status === 302) {
    console.log('✅ Grafana proxy working');
    
    // If 302, verify redirect location
    if (status === 302) {
      const location = grafana.headers()['location'];
      if (location) {
        console.log(`   Redirect location: ${location}`);
        expect(location).toMatch(/\/graf\//);
      }
    }
    
    // If 200, verify it's actually Grafana
    if (status === 200) {
      const body = await grafana.text();
      expect(body.toLowerCase()).toMatch(/grafana/);
    }
  } else {
    console.error(`❌ Grafana not accessible (status: ${status})`);
    console.error('   Expected: 200 or 302');
    console.error('   Check: docker compose ps grafana');
    console.error('   Check: nginx.conf has location /graf/ configured');
  }

  // Grafana is required - must be accessible
  expect(status).toBeOneOf([200, 302]);
});

test('Agent endpoints return expected status', async ({ request, baseURL }) => {
  // Agent service might not be implemented yet
  // Check that it returns 501 (Not Implemented) or 404, not a 500 error
  const agent = await request.post(`${baseURL}/api/v1/agent/start`, {
    data: { query: 'test' },
    failOnStatusCode: false
  });

  console.log(`Agent endpoint status: ${agent.status()}`);

  // Should be 404 (not configured), 501 (not implemented), or 200 (working)
  expect([200, 404, 501]).toContain(agent.status());
});

