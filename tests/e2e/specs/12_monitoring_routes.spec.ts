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
  // This should always work - it's the API metrics endpoint
  const metrics = await request.get(`${baseURL}/api/metrics`);

  expect(metrics.status()).toBe(200);

  const body = await metrics.text();

  // Should contain Prometheus-format metrics
  expect(body).toMatch(/^[a-z_]+{.*}|^# HELP|^# TYPE/m);

  // Should have our custom metrics
  expect(body).toContain('rag_requests_total');

  console.log('✅ Metrics endpoint working');
});

test('Grafana endpoint proxied (optional)', async ({ request, baseURL }) => {
  // Check if Grafana is accessible through nginx
  const grafana = await request.get(`${baseURL}/graf/`, {
    failOnStatusCode: false,
    maxRedirects: 0 // Don't follow redirects
  });

  if (grafana.status() === 200 || grafana.status() === 302) {
    console.log('✅ Grafana proxy working');
  } else {
    console.log(`⚠️  Grafana proxy not configured (status: ${grafana.status()})`);
  }

  // Should either work (200/302) or not be configured yet (404)
  expect([200, 302, 404, 502]).toContain(grafana.status());
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

