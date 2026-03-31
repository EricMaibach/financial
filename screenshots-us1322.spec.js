// Screenshot spec for US-13.2.2: Remove Anonymous AI Trial
// Captures anonymous vs logged-in UI to verify AI elements are hidden/shown correctly
// Run: npx playwright test screenshots-us1322.spec.js --reporter=line
const { test, expect } = require('@playwright/test');
const path = require('path');
const fs = require('fs');

const BASE_URL = 'http://localhost:5000';
const OUT_DIR = path.join(__dirname, 'screenshots', 'us1322');

test.beforeAll(() => {
  fs.mkdirSync(OUT_DIR, { recursive: true });
});

// --- Anonymous user screenshots (not logged in) ---

test.describe('Anonymous user — no AI elements', () => {

  test('homepage-anonymous-desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(`${BASE_URL}/`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);
    // Verify no chatbot FAB visible
    const chatBtn = page.locator('#ai-chat-button');
    if (await chatBtn.count() > 0) {
      await expect(chatBtn).not.toBeVisible();
    }
    await page.screenshot({
      path: path.join(OUT_DIR, 'homepage-anonymous-desktop.png'),
      fullPage: false,
    });
  });

  test('equity-anonymous-desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(`${BASE_URL}/equity`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);
    await page.screenshot({
      path: path.join(OUT_DIR, 'equity-anonymous-desktop.png'),
      fullPage: false,
    });
  });

  test('portfolio-anonymous-desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(`${BASE_URL}/portfolio`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);
    await page.screenshot({
      path: path.join(OUT_DIR, 'portfolio-anonymous-desktop.png'),
      fullPage: false,
    });
  });

});

// --- Logged-in user screenshots (AI elements visible) ---

test.describe('Logged-in user — AI elements present', () => {

  test('homepage-loggedin-desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    // Login
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name=username]', 'testuser');
    await page.fill('input[name=password]', 'testpassword');
    await page.click('button[type=submit]');
    await page.waitForURL(`${BASE_URL}/`);
    // Navigate to homepage
    await page.goto(`${BASE_URL}/`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);
    await page.screenshot({
      path: path.join(OUT_DIR, 'homepage-loggedin-desktop.png'),
      fullPage: false,
    });
  });

  test('equity-loggedin-desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    // Login
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name=username]', 'testuser');
    await page.fill('input[name=password]', 'testpassword');
    await page.click('button[type=submit]');
    await page.waitForURL(`${BASE_URL}/`);
    // Navigate to equity category page
    await page.goto(`${BASE_URL}/equity`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);
    await page.screenshot({
      path: path.join(OUT_DIR, 'equity-loggedin-desktop.png'),
      fullPage: false,
    });
  });

});
