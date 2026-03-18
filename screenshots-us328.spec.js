// Screenshot spec for US-323.1: Homepage §0 Briefing + §1 Market Conditions
// Run: npx playwright test screenshots-us328.spec.js --reporter=line

const { test, expect } = require('@playwright/test');

const BASE = 'http://localhost:5000';

// Mock conditions cache to inject into Docker before screenshotting
const MOCK_CACHE = JSON.stringify({
  quadrant: 'Goldilocks',
  dimensions: {
    liquidity: { state: 'Expanding', score: 0.82 },
    quadrant: { state: 'Goldilocks', growth_composite: 0.6, inflation_composite: -0.4 },
    risk: { state: 'Calm', score: 1, vix_level: 14.8, vix_ratio: 0.88, stock_bond_corr: -0.35 },
    policy: { stance: 'Neutral', direction: 'Easing', taylor_gap: -0.30, actual_rate: 4.25, taylor_prescribed: 4.55 },
  },
  asset_expectations: [
    { asset: 'S&P 500', direction: 'positive', magnitude: 'strong' },
    { asset: 'Treasuries', direction: 'positive', magnitude: 'moderate' },
    { asset: 'Gold', direction: 'neutral', magnitude: 'weak' },
    { asset: 'Bitcoin', direction: 'positive', magnitude: 'moderate' },
    { asset: 'Credit', direction: 'positive', magnitude: 'moderate' },
    { asset: 'Commodities', direction: 'neutral', magnitude: 'weak' },
  ],
  as_of: '2026-03-18',
  updated_at: new Date().toISOString(),
});

const MOCK_HISTORY = JSON.stringify({
  '2026-03-18': {
    quadrant: 'Goldilocks',
    dimensions: {
      quadrant: { state: 'Goldilocks', growth_composite: 0.6, inflation_composite: -0.4 },
      liquidity: { state: 'Expanding', score: 0.82 },
      risk: { state: 'Calm', score: 1 },
      policy: { stance: 'Neutral', direction: 'Easing' },
    },
    asset_expectations: [],
  },
  '2026-02-18': {
    quadrant: 'Goldilocks',
    dimensions: {
      quadrant: { state: 'Goldilocks', growth_composite: 0.45, inflation_composite: -0.25 },
      liquidity: { state: 'Expanding', score: 0.6 },
      risk: { state: 'Calm', score: 1 },
      policy: { stance: 'Neutral', direction: 'Easing' },
    },
    asset_expectations: [],
  },
  '2026-01-18': {
    quadrant: 'Reflation',
    dimensions: {
      quadrant: { state: 'Reflation', growth_composite: 0.3, inflation_composite: 0.1 },
      liquidity: { state: 'Neutral', score: 0.1 },
      risk: { state: 'Normal', score: 2 },
      policy: { stance: 'Neutral', direction: 'Paused' },
    },
    asset_expectations: [],
  },
});

const SCREENSHOTS_DIR = 'screenshots/us328';

test.describe('US-323.1 Homepage Screenshots', () => {

  test.beforeAll(async () => {
    // Write mock cache files into Docker container via stdin pipe
    const { execSync } = require('child_process');
    execSync(`docker exec -i signaltrackers-dev bash -c "cat > /app/data/market_conditions_cache.json"`, { input: MOCK_CACHE, stdio: ['pipe', 'pipe', 'pipe'] });
    execSync(`docker exec -i signaltrackers-dev bash -c "cat > /app/data/market_conditions_history.json"`, { input: MOCK_HISTORY, stdio: ['pipe', 'pipe', 'pipe'] });
  });

  test('desktop-1280-homepage', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(BASE + '/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);
    await page.screenshot({ path: `${SCREENSHOTS_DIR}/desktop-1280-homepage.png`, fullPage: true });
  });

  test('desktop-1280-conditions-section', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(BASE + '/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);
    const section = page.locator('#conditions-section');
    await section.screenshot({ path: `${SCREENSHOTS_DIR}/desktop-1280-conditions-section.png` });
  });

  test('desktop-1280-quadrant-hero', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(BASE + '/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);
    const hero = page.locator('.quadrant-hero');
    await hero.screenshot({ path: `${SCREENSHOTS_DIR}/desktop-1280-quadrant-hero.png` });
  });

  test('mobile-375-homepage', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto(BASE + '/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);
    await page.screenshot({ path: `${SCREENSHOTS_DIR}/mobile-375-homepage.png`, fullPage: true });
  });

  test('mobile-375-dimension-grid', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto(BASE + '/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);
    const grid = page.locator('.dimension-grid');
    await grid.screenshot({ path: `${SCREENSHOTS_DIR}/mobile-375-dimension-grid.png` });
  });

  test('desktop-1280-liquidity-expanded', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(BASE + '/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);
    // Click to expand liquidity card
    await page.click('#dim-liquidity-toggle');
    await page.waitForTimeout(400);
    const card = page.locator('#dim-liquidity');
    await card.screenshot({ path: `${SCREENSHOTS_DIR}/desktop-1280-liquidity-expanded.png` });
  });

  test('desktop-1280-movers-strip', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(BASE + '/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1500); // Wait for movers AJAX
    const strip = page.locator('#movers-strip');
    await strip.screenshot({ path: `${SCREENSHOTS_DIR}/desktop-1280-movers-strip.png` });
  });

});
