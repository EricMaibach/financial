const { test } = require('@playwright/test');
const fs = require('fs');

const outputDir = 'screenshots/us173';
fs.mkdirSync(outputDir, { recursive: true });

// Take a screenshot of just the collapsible section header element (collapsed state)
async function screenshotHeader(page, sectionId, path) {
  const locator = page.locator(`[data-section-id="${sectionId}"] .collapsible-section__header`);
  await locator.waitFor({ state: 'visible', timeout: 15000 });
  await locator.screenshot({ path });
}

test.describe('US-173 Descriptive Collapsible Section Labels', () => {

  // ── /equity ────────────────────────────────────────────────────────────────

  test('equity-collapsed-header-mobile-375', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('http://localhost:5000/equity');
    await page.waitForLoadState('networkidle');
    await screenshotHeader(page, 'additional-charts', `${outputDir}/equity-collapsed-header-mobile-375.png`);
  });

  test('equity-collapsed-header-desktop-1280', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto('http://localhost:5000/equity');
    await page.waitForLoadState('networkidle');
    await screenshotHeader(page, 'additional-charts', `${outputDir}/equity-collapsed-header-desktop-1280.png`);
  });

  // ── /rates ─────────────────────────────────────────────────────────────────

  test('rates-collapsed-header-mobile-375', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('http://localhost:5000/rates');
    await page.waitForLoadState('networkidle');
    await screenshotHeader(page, 'additional-charts', `${outputDir}/rates-collapsed-header-mobile-375.png`);
  });

  test('rates-collapsed-header-desktop-1280', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto('http://localhost:5000/rates');
    await page.waitForLoadState('networkidle');
    await screenshotHeader(page, 'additional-charts', `${outputDir}/rates-collapsed-header-desktop-1280.png`);
  });

  // ── /safe-havens ───────────────────────────────────────────────────────────

  test('safe-havens-collapsed-header-mobile-375', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('http://localhost:5000/safe-havens');
    await page.waitForLoadState('networkidle');
    await screenshotHeader(page, 'additional-charts', `${outputDir}/safe-havens-collapsed-header-mobile-375.png`);
  });

  test('safe-havens-collapsed-header-desktop-1280', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto('http://localhost:5000/safe-havens');
    await page.waitForLoadState('networkidle');
    await screenshotHeader(page, 'additional-charts', `${outputDir}/safe-havens-collapsed-header-desktop-1280.png`);
  });

  // ── /crypto ────────────────────────────────────────────────────────────────

  test('crypto-collapsed-header-mobile-375', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('http://localhost:5000/crypto');
    await page.waitForLoadState('networkidle');
    await screenshotHeader(page, 'additional-charts', `${outputDir}/crypto-collapsed-header-mobile-375.png`);
  });

  test('crypto-collapsed-header-desktop-1280', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto('http://localhost:5000/crypto');
    await page.waitForLoadState('networkidle');
    await screenshotHeader(page, 'additional-charts', `${outputDir}/crypto-collapsed-header-desktop-1280.png`);
  });

  // ── /dollar ────────────────────────────────────────────────────────────────

  test('dollar-collapsed-header-mobile-375', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('http://localhost:5000/dollar');
    await page.waitForLoadState('networkidle');
    await screenshotHeader(page, 'additional-charts', `${outputDir}/dollar-collapsed-header-mobile-375.png`);
  });

  test('dollar-collapsed-header-desktop-1280', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto('http://localhost:5000/dollar');
    await page.waitForLoadState('networkidle');
    await screenshotHeader(page, 'additional-charts', `${outputDir}/dollar-collapsed-header-desktop-1280.png`);
  });

});
