const { test } = require('@playwright/test');
const path = require('path');
const fs = require('fs');

const BASE_URL = 'http://localhost:5000';
const OUT_DIR = path.join(__dirname, 'screenshots', 'us246');

const VIEWPORTS = [
  { name: 'mobile-375', width: 375, height: 812 },
  { name: 'tablet-768', width: 768, height: 1024 },
  { name: 'desktop-1280', width: 1280, height: 900 },
];

test.beforeAll(() => {
  fs.mkdirSync(OUT_DIR, { recursive: true });
});

for (const vp of VIEWPORTS) {
  test(`screenshots at ${vp.name}`, async ({ page }) => {
    await page.setViewportSize({ width: vp.width, height: vp.height });

    // Login
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name=username]', 'testuser');
    await page.fill('input[name=password]', 'testpassword');
    await page.click('button[type=submit]');
    await page.waitForURL(`${BASE_URL}/`);

    // Portfolio page overview
    await page.goto(`${BASE_URL}/portfolio`, { waitUntil: 'networkidle' });
    await page.screenshot({
      path: path.join(OUT_DIR, `${vp.name}-portfolio-page.png`),
      fullPage: true,
    });

    // Open Add Holding modal
    await page.click('button:has-text("Add Holding")');
    await page.waitForSelector('#holdingModal.show', { timeout: 5000 });
    await page.screenshot({
      path: path.join(OUT_DIR, `${vp.name}-add-holding-modal.png`),
    });

    // Select Farmland — symbol hidden, name auto-populated
    await page.selectOption('#asset-type', 'farmland');
    await page.screenshot({
      path: path.join(OUT_DIR, `${vp.name}-farmland-selected.png`),
    });

    // Select Commercial Real Estate
    await page.selectOption('#asset-type', 'commercial_real_estate');
    await page.screenshot({
      path: path.join(OUT_DIR, `${vp.name}-commercial-re-selected.png`),
    });
  });
}
