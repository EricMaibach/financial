const { test, expect } = require('@playwright/test');
const path = require('path');
const fs = require('fs');

const BASE_URL = 'http://localhost:5000';
const OUT_DIR = path.join(__dirname, 'screenshots', 'us262');

const VIEWPORTS = [
  { name: 'mobile-375', width: 375, height: 812 },
  { name: 'tablet-768', width: 768, height: 1024 },
  { name: 'desktop-1280', width: 1280, height: 900 },
];

test.beforeAll(() => {
  fs.mkdirSync(OUT_DIR, { recursive: true });
});

for (const vp of VIEWPORTS) {
  test(`AI section buttons screenshots at ${vp.name}`, async ({ page }) => {
    await page.setViewportSize({ width: vp.width, height: vp.height });
    await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' });

    // Full homepage overview
    await page.screenshot({
      path: path.join(OUT_DIR, `${vp.name}-homepage-ai-buttons.png`),
      fullPage: false,
    });

    // Macro Regime Score section button
    const macroSection = page.locator('#macro-regime-section');
    if (await macroSection.count() > 0) {
      await macroSection.scrollIntoViewIfNeeded();
      await page.screenshot({
        path: path.join(OUT_DIR, `${vp.name}-macro-regime-ai-btn.png`),
        fullPage: false,
      });
    }

    // Market Conditions section button
    const marketSection = page.locator('#market-conditions');
    if (await marketSection.count() > 0) {
      await marketSection.scrollIntoViewIfNeeded();
      await page.screenshot({
        path: path.join(OUT_DIR, `${vp.name}-market-conditions-ai-btn.png`),
        fullPage: false,
      });
    }
  });

  test(`AI section button chatbot open at ${vp.name}`, async ({ page }) => {
    await page.setViewportSize({ width: vp.width, height: vp.height });
    await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' });

    // Click first AI section button
    const firstBtn = page.locator('.ai-section-btn').first();
    if (await firstBtn.count() > 0) {
      await firstBtn.scrollIntoViewIfNeeded();
      await firstBtn.click();
      await page.waitForTimeout(400); // Allow panel animation + opening message
      await page.screenshot({
        path: path.join(OUT_DIR, `${vp.name}-chatbot-preloaded.png`),
        fullPage: false,
      });
    }
  });

  test(`Credit page AI button at ${vp.name}`, async ({ page }) => {
    await page.setViewportSize({ width: vp.width, height: vp.height });
    await page.goto(`${BASE_URL}/credit`, { waitUntil: 'domcontentloaded' });

    await page.screenshot({
      path: path.join(OUT_DIR, `${vp.name}-credit-ai-btn.png`),
      fullPage: false,
    });
  });
}
