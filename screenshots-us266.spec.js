const { test, expect } = require('@playwright/test');
const path = require('path');
const fs = require('fs');

const BASE_URL = 'http://localhost:5000';
const OUT_DIR = path.join(__dirname, 'screenshots', 'us266');

const VIEWPORTS = [
  { name: 'mobile-375', width: 375, height: 812 },
  { name: 'tablet-768', width: 768, height: 1024 },
  { name: 'desktop-1280', width: 1280, height: 900 },
];

test.beforeAll(() => {
  fs.mkdirSync(OUT_DIR, { recursive: true });
});

for (const vp of VIEWPORTS) {
  test(`News page screenshots at ${vp.name}`, async ({ page }) => {
    await page.setViewportSize({ width: vp.width, height: vp.height });

    // Homepage: verify News nav link is present in navbar
    await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' });
    await page.screenshot({
      path: path.join(OUT_DIR, `${vp.name}-homepage-navbar-news-link.png`),
      fullPage: false,
    });

    // News page: empty state (no pipeline data yet)
    await page.goto(`${BASE_URL}/news`, { waitUntil: 'domcontentloaded' });
    await page.screenshot({
      path: path.join(OUT_DIR, `${vp.name}-news-empty-state.png`),
      fullPage: true,
    });
  });
}
