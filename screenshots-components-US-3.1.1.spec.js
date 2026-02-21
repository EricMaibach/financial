const { test } = require('@playwright/test');

/**
 * Playwright Screenshot Script for US-3.1.1 Components
 *
 * Generates screenshots of the mobile-first component test page
 * at three responsive breakpoints for designer review.
 *
 * Usage: npx playwright test screenshots-components-US-3.1.1.spec.js
 */

const viewports = [
  { name: 'mobile', width: 375, height: 667 },      // iPhone SE
  { name: 'tablet', width: 768, height: 1024 },     // iPad Portrait
  { name: 'desktop', width: 1920, height: 1080 }    // Desktop
];

test.describe('US-3.1.1 Component Screenshots', () => {
  for (const viewport of viewports) {
    test(`Components Test Page - ${viewport.name}`, async ({ page }) => {
      // Set viewport size
      await page.setViewportSize({ width: viewport.width, height: viewport.height });

      // Navigate to component test page
      // Note: Assumes the test HTML is served via the Flask app or a local server
      // Adjust URL based on actual serving method
      await page.goto('file://' + __dirname + '/signaltrackers/static/components-test.html', {
        waitUntil: 'networkidle'
      });

      // Wait for components to initialize
      await page.waitForTimeout(500);

      // Take full page screenshot
      await page.screenshot({
        path: `screenshots/US-3.1.1-components-${viewport.name}.png`,
        fullPage: true
      });
    });

    // Individual component screenshots for detailed review
    test(`CollapsibleSection - ${viewport.name}`, async ({ page }) => {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.goto('file://' + __dirname + '/signaltrackers/static/components-test.html');
      await page.waitForTimeout(500);

      // Screenshot just the CollapsibleSection test section
      const section = await page.locator('.test-section').first();
      await section.screenshot({
        path: `screenshots/US-3.1.1-collapsible-section-${viewport.name}.png`
      });
    });

    test(`StickyMetricSelector - ${viewport.name}`, async ({ page }) => {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.goto('file://' + __dirname + '/signaltrackers/static/components-test.html');
      await page.waitForTimeout(500);

      // Scroll to sticky selector section
      await page.locator('.test-section').nth(1).scrollIntoViewIfNeeded();

      // Screenshot the sticky selector section
      const section = await page.locator('.test-section').nth(1);
      await section.screenshot({
        path: `screenshots/US-3.1.1-sticky-selector-${viewport.name}.png`
      });
    });

    test(`ResponsiveChartContainer - ${viewport.name}`, async ({ page }) => {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.goto('file://' + __dirname + '/signaltrackers/static/components-test.html');
      await page.waitForTimeout(500);

      // Scroll to chart container section
      await page.locator('.test-section').nth(2).scrollIntoViewIfNeeded();

      // Screenshot the chart container section
      const section = await page.locator('.test-section').nth(2);
      await section.screenshot({
        path: `screenshots/US-3.1.1-chart-container-${viewport.name}.png`
      });
    });

    test(`KeyStatsPanel - ${viewport.name}`, async ({ page }) => {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.goto('file://' + __dirname + '/signaltrackers/static/components-test.html');
      await page.waitForTimeout(500);

      // Scroll to key stats panel section
      await page.locator('.test-section').nth(3).scrollIntoViewIfNeeded();

      // Screenshot the key stats panel section
      const section = await page.locator('.test-section').nth(3);
      await section.screenshot({
        path: `screenshots/US-3.1.1-key-stats-panel-${viewport.name}.png`
      });
    });

    // Test collapsible section in expanded state
    test(`CollapsibleSection Expanded - ${viewport.name}`, async ({ page }) => {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.goto('file://' + __dirname + '/signaltrackers/static/components-test.html');
      await page.waitForTimeout(500);

      // Click first collapsible section to expand
      await page.locator('.collapsible-section__header').first().click();
      await page.waitForTimeout(300); // Wait for animation

      // Screenshot
      const section = await page.locator('.test-section').first();
      await section.screenshot({
        path: `screenshots/US-3.1.1-collapsible-expanded-${viewport.name}.png`
      });
    });

    // Test sticky selector in stuck state (desktop/tablet only)
    if (viewport.name !== 'mobile') {
      test(`StickySelector Stuck State - ${viewport.name}`, async ({ page }) => {
        await page.setViewportSize({ width: viewport.width, height: viewport.height });
        await page.goto('file://' + __dirname + '/signaltrackers/static/components-test.html');
        await page.waitForTimeout(500);

        // Scroll down to make sticky selector stick
        await page.locator('.test-section').nth(2).scrollIntoViewIfNeeded();
        await page.waitForTimeout(300);

        // Screenshot showing sticky selector at top
        await page.screenshot({
          path: `screenshots/US-3.1.1-sticky-stuck-${viewport.name}.png`,
          fullPage: false // Viewport screenshot to show sticky at top
        });
      });
    }
  }
});
