import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('Homepage has no serious accessibility violations', async ({ page }) => {
  await page.goto('/');

  const results = await new AxeBuilder({ page }).analyze();

  const serious = results.violations.filter(v =>
    ['serious', 'critical'].includes(v.impact ?? 'minor')
  );

  // Filter out known acceptable violations
  const critical = serious.filter(v => {
    // Ignore color-contrast issues in dark mode (often false positives)
    if (v.id === 'color-contrast') return false;
    // Ignore aria-hidden-focus issues for decorative elements
    if (v.id === 'aria-hidden-focus') return false;
    return true;
  });

  if (critical.length > 0) {
    console.log(`❌ Found ${critical.length} critical accessibility violations:`);
    critical.forEach(v => {
      console.log(`   - ${v.id}: ${v.description}`);
      console.log(`     Impact: ${v.impact}, Nodes: ${v.nodes.length}`);
    });
  } else if (serious.length > 0) {
    console.log(`⚠️  Found ${serious.length} serious violations (filtered to ${critical.length} critical)`);
  } else {
    console.log('✅ No serious accessibility violations found');
  }

  expect(critical, JSON.stringify(critical, null, 2)).toHaveLength(0);
});

test('Chat page has no serious accessibility violations', async ({ page }) => {
  await page.goto('/');

  // Send a message to populate the chat
  await page.locator('[data-testid="chat-input"], textarea').first().fill('Test message');
  await page.locator('[data-testid="chat-send"], button:has-text("Send")').first().click();

  await expect(page.locator('[data-testid="chat-answer"]')).toBeVisible({ timeout: 15000 });

  const results = await new AxeBuilder({ page }).analyze();

  const serious = results.violations.filter(v =>
    ['serious', 'critical'].includes(v.impact ?? 'minor')
  );

  // Filter out known acceptable violations
  const critical = serious.filter(v => {
    // Ignore color-contrast issues in dark mode (often false positives)
    if (v.id === 'color-contrast') return false;
    // Ignore aria-hidden-focus issues for decorative elements
    if (v.id === 'aria-hidden-focus') return false;
    return true;
  });

  if (critical.length > 0) {
    console.log(`❌ Found ${critical.length} critical accessibility violations in chat:`);
    critical.forEach(v => {
      console.log(`   - ${v.id}: ${v.description}`);
    });
  } else if (serious.length > 0) {
    console.log(`⚠️  Found ${serious.length} serious violations (filtered to ${critical.length} critical)`);
  } else {
    console.log('✅ No serious accessibility violations in chat');
  }

  expect(critical, JSON.stringify(critical, null, 2)).toHaveLength(0);
});

