// Screenshot spec for US-323.2: §2 Portfolio Implications + Today's Movers footer
// Run: npx playwright test screenshots-us331.spec.js --reporter=line

const { test, expect } = require('@playwright/test');

const BASE = 'http://localhost:5000';
const SCREENSHOTS_DIR = 'screenshots/us331';

// Mock conditions cache with implications data
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

// History with multiple Goldilocks+Expanding entries for historical context sentence
const MOCK_HISTORY = JSON.stringify({
  '2026-03-18': { quadrant: 'Goldilocks', dimensions: { quadrant: { state: 'Goldilocks' }, liquidity: { state: 'Expanding', score: 0.82 }, risk: { state: 'Calm', score: 1 }, policy: { stance: 'Neutral', direction: 'Easing' } }, asset_expectations: [] },
  '2026-03-11': { quadrant: 'Goldilocks', dimensions: { quadrant: { state: 'Goldilocks' }, liquidity: { state: 'Expanding', score: 0.78 }, risk: { state: 'Calm', score: 1 }, policy: { stance: 'Neutral', direction: 'Easing' } }, asset_expectations: [] },
  '2026-03-04': { quadrant: 'Goldilocks', dimensions: { quadrant: { state: 'Goldilocks' }, liquidity: { state: 'Expanding', score: 0.72 }, risk: { state: 'Calm', score: 1 }, policy: { stance: 'Neutral', direction: 'Easing' } }, asset_expectations: [] },
  '2026-02-25': { quadrant: 'Goldilocks', dimensions: { quadrant: { state: 'Goldilocks' }, liquidity: { state: 'Expanding', score: 0.68 }, risk: { state: 'Calm', score: 1 }, policy: { stance: 'Neutral', direction: 'Easing' } }, asset_expectations: [] },
  '2026-02-18': { quadrant: 'Goldilocks', dimensions: { quadrant: { state: 'Goldilocks' }, liquidity: { state: 'Expanding', score: 0.60 }, risk: { state: 'Calm', score: 1 }, policy: { stance: 'Neutral', direction: 'Easing' } }, asset_expectations: [] },
  '2026-02-11': { quadrant: 'Goldilocks', dimensions: { quadrant: { state: 'Goldilocks' }, liquidity: { state: 'Neutral', score: 0.48 }, risk: { state: 'Normal', score: 2 }, policy: { stance: 'Neutral', direction: 'Paused' } }, asset_expectations: [] },
  '2026-02-04': { quadrant: 'Reflation', dimensions: { quadrant: { state: 'Reflation' }, liquidity: { state: 'Neutral', score: 0.35 }, risk: { state: 'Normal', score: 2 }, policy: { stance: 'Neutral', direction: 'Paused' } }, asset_expectations: [] },
  '2026-01-28': { quadrant: 'Reflation', dimensions: { quadrant: { state: 'Reflation' }, liquidity: { state: 'Neutral', score: 0.25 }, risk: { state: 'Normal', score: 2 }, policy: { stance: 'Neutral', direction: 'Paused' } }, asset_expectations: [] },
  '2026-01-21': { quadrant: 'Reflation', dimensions: { quadrant: { state: 'Reflation' }, liquidity: { state: 'Neutral', score: 0.18 }, risk: { state: 'Normal', score: 2 }, policy: { stance: 'Neutral', direction: 'Paused' } }, asset_expectations: [] },
  '2026-01-18': { quadrant: 'Reflation', dimensions: { quadrant: { state: 'Reflation' }, liquidity: { state: 'Neutral', score: 0.10 }, risk: { state: 'Normal', score: 2 }, policy: { stance: 'Neutral', direction: 'Paused' } }, asset_expectations: [] },
  '2026-01-11': { quadrant: 'Reflation', dimensions: { quadrant: { state: 'Reflation' }, liquidity: { state: 'Neutral', score: 0.05 }, risk: { state: 'Normal', score: 2 }, policy: { stance: 'Neutral', direction: 'Paused' } }, asset_expectations: [] },
  '2026-01-04': { quadrant: 'Reflation', dimensions: { quadrant: { state: 'Reflation' }, liquidity: { state: 'Neutral', score: -0.02 }, risk: { state: 'Normal', score: 2 }, policy: { stance: 'Neutral', direction: 'Paused' } }, asset_expectations: [] },
  '2025-12-28': { quadrant: 'Reflation', dimensions: { quadrant: { state: 'Reflation' }, liquidity: { state: 'Contracting', score: -0.10 }, risk: { state: 'Normal', score: 3 }, policy: { stance: 'Restrictive', direction: 'Paused' } }, asset_expectations: [] },
  '2025-12-21': { quadrant: 'Reflation', dimensions: { quadrant: { state: 'Reflation' }, liquidity: { state: 'Contracting', score: -0.15 }, risk: { state: 'Normal', score: 3 }, policy: { stance: 'Restrictive', direction: 'Paused' } }, asset_expectations: [] },
});

test.describe('US-323.2 Implications & Movers Screenshots', () => {

  test.beforeAll(async () => {
    const { execSync } = require('child_process');
    execSync(`docker exec -i signaltrackers-dev bash -c "cat > /app/data/market_conditions_cache.json"`, { input: MOCK_CACHE, stdio: ['pipe', 'pipe', 'pipe'] });
    execSync(`docker exec -i signaltrackers-dev bash -c "cat > /app/data/market_conditions_history.json"`, { input: MOCK_HISTORY, stdio: ['pipe', 'pipe', 'pipe'] });
  });

  test('mobile-375-implications', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto(BASE + '/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);
    const section = page.locator('#implications-section');
    await section.screenshot({ path: `${SCREENSHOTS_DIR}/mobile-375-implications.png` });
  });

  test('desktop-1280-implications', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(BASE + '/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);
    const section = page.locator('#implications-section');
    await section.screenshot({ path: `${SCREENSHOTS_DIR}/desktop-1280-implications.png` });
  });

  test('mobile-375-movers-footer', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto(BASE + '/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1500); // Wait for movers AJAX
    const strip = page.locator('#movers-strip');
    await strip.screenshot({ path: `${SCREENSHOTS_DIR}/mobile-375-movers-footer.png` });
  });

  test('desktop-1280-movers-footer', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(BASE + '/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1500); // Wait for movers AJAX
    const strip = page.locator('#movers-strip');
    await strip.screenshot({ path: `${SCREENSHOTS_DIR}/desktop-1280-movers-footer.png` });
  });

});
