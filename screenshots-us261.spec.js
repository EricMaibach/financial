const { test, expect } = require('@playwright/test');
const path = require('path');
const fs = require('fs');

const BASE_URL = 'http://localhost:5000';
const OUT_DIR = path.join(__dirname, 'screenshots', 'us261');

const VIEWPORTS = [
  { name: 'mobile-375', width: 375, height: 812 },
  { name: 'tablet-768', width: 768, height: 1024 },
  { name: 'desktop-1280', width: 1280, height: 900 },
];

test.beforeAll(() => {
  fs.mkdirSync(OUT_DIR, { recursive: true });
});

for (const vp of VIEWPORTS) {
  test(`AI icon migration screenshots at ${vp.name}`, async ({ page }) => {
    await page.setViewportSize({ width: vp.width, height: vp.height });

    // Login
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name=username]', 'testuser');
    await page.fill('input[name=password]', 'testpassword');
    await page.click('button[type=submit]');
    await page.waitForURL(`${BASE_URL}/`);

    // --- Homepage: chatbot FAB (bottom-right corner) ---
    await page.goto(`${BASE_URL}/`, { waitUntil: 'networkidle' });
    const fab = page.locator('#chatbot-fab');
    await fab.screenshot({
      path: path.join(OUT_DIR, `${vp.name}-chatbot-fab.png`),
    });

    // --- Homepage: open chatbot panel, screenshot header ---
    await fab.click();
    await page.waitForSelector('#chatbot-panel:not([aria-hidden="true"])', { timeout: 5000 }).catch(() => {});
    const panel = page.locator('#chatbot-panel');
    await panel.screenshot({
      path: path.join(OUT_DIR, `${vp.name}-chatbot-panel.png`),
    });

    // --- Homepage: AI provenance badge below daily briefing ---
    // Close the chatbot first
    await page.keyboard.press('Escape');
    await page.goto(`${BASE_URL}/`, { waitUntil: 'networkidle' });
    const badge = page.locator('#briefing-attribution');
    await badge.screenshot({
      path: path.join(OUT_DIR, `${vp.name}-ai-provenance-badge.png`),
    });

    // --- Full homepage to see chatbot FAB in context ---
    await page.screenshot({
      path: path.join(OUT_DIR, `${vp.name}-homepage-full.png`),
      fullPage: false,
    });
  });
}
