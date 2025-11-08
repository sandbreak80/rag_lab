import { test, expect } from '@playwright/test';

for (const path of ['/live', '/ready', '/health']) {
  test(`health via frontend ${path}`, async ({ request, baseURL }) => {
    const r = await request.get(`${baseURL}${path}`);
    expect(r.status()).toBe(200);
    const json = await r.json();
    expect(json.status).toMatch(/alive|ready|ok|healthy/i);
  });
}

