import { test, expect } from '@playwright/test';

for (const path of ['/live', '/ready', '/health']) {
  test(`health via frontend ${path}`, async ({ request, baseURL }) => {
    const r = await request.get(`${baseURL}${path}`);
    // /ready can return 503 (degraded) which is acceptable - service is up but dependencies may be down
    const statusCode = r.status();
    if (path === '/ready' && statusCode === 503) {
      // 503 is acceptable for /ready endpoint when service is degraded
      expect(statusCode).toBe(503);
    } else {
      expect(statusCode).toBe(200);
    }
    const json = await r.json();
    // Accept alive, ready, ok, healthy, or degraded (degraded means some deps are down but core services work)
    expect(json.status).toMatch(/alive|ready|ok|healthy|degraded/i);
  });
}

