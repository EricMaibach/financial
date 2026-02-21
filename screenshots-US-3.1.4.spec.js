const { test } = require('@playwright/test');

/**
 * Playwright Screenshot Script for US-3.1.4
 *
 * Captures screenshots for 4 asset class pages refactored to mobile-first:
 * - Dollar (/dollar)
 * - Equities (/equity)
 * - Crypto (/crypto)
 * - Safe Havens (/safe-havens)
 *
 * 3 viewports per page = 12 total screenshots
 */

const viewports = [
  { name: 'mobile', width: 375, height: 667 },      // iPhone SE
  { name: 'tablet', width: 768, height: 1024 },     // iPad portrait
  { name: 'desktop', width: 1920, height: 1080 }    // Desktop
];

const pages = [
  { path: '/dollar', name: 'dollar' },
  { path: '/equity', name: 'equity' },
  { path: '/crypto', name: 'crypto' },
  { path: '/safe-havens', name: 'safe-havens' }
];

test.describe('US-3.1.4: Mobile-First Asset Class Pages', () => {
  for (const page of pages) {
    for (const viewport of viewports) {
      test(`${page.name} - ${viewport.name} (${viewport.width}x${viewport.height})`, async ({ page: p }) => {
        // Set viewport size
        await p.setViewportSize({ width: viewport.width, height: viewport.height });

        // Navigate to page
        await p.goto(`http://localhost:5000${page.path}`);

        // Wait for chart to render (give it a moment)
        await p.waitForTimeout(1500);

        // Take screenshot
        await p.screenshot({
          path: `screenshots/US-3.1.4-${page.name}-${viewport.name}.png`,
          fullPage: true
        });

        console.log(`✓ Screenshot captured: ${page.name} at ${viewport.width}x${viewport.height}`);
      });
    }
  }
});
