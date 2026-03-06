/**
 * Design-review screenshots for US-169.1: Credit Page — Data Layer, Charts, and Percentile Engine
 *
 * Captures:
 *  1. desktop-1280-top         — Full page header + regime strip + hero chart + key stats
 *  2. desktop-1280-percentile  — Percentile gauge bars (HY + IG)
 *  3. tablet-768-top           — Tablet view, stacked layout
 *  4. mobile-375-top           — Mobile view header and chart
 */
const { test, expect } = require('@playwright/test');

const BASE = 'http://localhost:5000/credit';
const DIR  = 'screenshots/us1911/';

test.describe('US-169.1 Credit Page Screenshots', () => {

  test('desktop-1280 — page header, regime strip, hero chart, key stats', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(BASE);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await page.screenshot({ path: DIR + 'desktop-1280-top.png', fullPage: false });
  });

  test('desktop-1280 — percentile gauge bars visible', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(BASE);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    // Scroll down to percentile bars if present
    const pctRow = page.locator('.percentile-row').first();
    if (await pctRow.count() > 0) {
      await pctRow.scrollIntoViewIfNeeded();
      await page.waitForTimeout(300);
      await pctRow.screenshot({ path: DIR + 'desktop-1280-percentile-bars.png' });
    } else {
      // Fallback: full-page screenshot
      await page.screenshot({ path: DIR + 'desktop-1280-percentile-bars.png' });
    }
  });

  test('tablet-768 — stacked layout', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto(BASE);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await page.screenshot({ path: DIR + 'tablet-768-top.png', fullPage: false });
  });

  test('mobile-375 — header and chart', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto(BASE);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await page.screenshot({ path: DIR + 'mobile-375-top.png', fullPage: false });
  });

});
