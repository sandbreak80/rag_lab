import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('Homepage has no serious accessibility violations', async ({ page }) => {
  await page.goto('/');

  const results = await new AxeBuilder({ page }).analyze();

  const serious = results.violations.filter(v =>
    ['serious', 'critical'].includes(v.impact ?? 'minor')
  );

  if (serious.length > 0) {
    console.log(`❌ Found ${serious.length} serious accessibility violations:`);
    serious.forEach(v => {
      console.log(`   - ${v.id}: ${v.description}`);
      console.log(`     Impact: ${v.impact}, Nodes: ${v.nodes.length}`);
    });
  } else {
    console.log('✅ No serious accessibility violations found');
  }

  expect(serious, JSON.stringify(serious, null, 2)).toHaveLength(0);
});

test('Chat page has no serious accessibility violations', async ({ page }) => {
  await page.goto('/');

  // Send a message to populate the chat
  await page.locator('[data-testid="chat-input"], textarea').first().fill('Test message');
  await page.locator('[data-testid="chat-send"], button:has-text("Send")').first().click();

  await expect(page.locator('[data-testid="answer"]')).toBeVisible({ timeout: 15000 });

  const results = await new AxeBuilder({ page }).analyze();

  const serious = results.violations.filter(v =>
    ['serious', 'critical'].includes(v.impact ?? 'minor')
  );

  if (serious.length > 0) {
    console.log(`❌ Found ${serious.length} serious accessibility violations in chat:`);
    serious.forEach(v => {
      console.log(`   - ${v.id}: ${v.description}`);
    });
  } else {
    console.log('✅ No serious accessibility violations in chat');
  }

  expect(serious, JSON.stringify(serious, null, 2)).toHaveLength(0);
});

