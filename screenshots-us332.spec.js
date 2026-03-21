// Screenshot spec for US-324.1: Category page conditions migration
// Run: npx playwright test screenshots-us332.spec.js --reporter=line
const { test, expect } = require('@playwright/test');

const BASE = 'http://localhost:5000';
const DIR = 'screenshots/us332';

// Mock conditions cache — Goldilocks + Expanding liquidity
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
  '2026-03-18': { quadrant: 'Goldilocks', dimensions: { quadrant: { state: 'Goldilocks' }, liquidity: { state: 'Expanding', score: 0.82 }, risk: { state: 'Calm', score: 1 }, policy: { stance: 'Neutral', direction: 'Easing' } }, asset_expectations: [] },
  '2026-03-11': { quadrant: 'Goldilocks', dimensions: { quadrant: { state: 'Goldilocks' }, liquidity: { state: 'Expanding', score: 0.78 }, risk: { state: 'Calm', score: 1 }, policy: { stance: 'Neutral', direction: 'Easing' } }, asset_expectations: [] },
  '2026-03-04': { quadrant: 'Goldilocks', dimensions: { quadrant: { state: 'Goldilocks' }, liquidity: { state: 'Expanding', score: 0.72 }, risk: { state: 'Calm', score: 1 }, policy: { stance: 'Neutral', direction: 'Easing' } }, asset_expectations: [] },
});

test.describe('US-324.1 Category Conditions Screenshots', () => {

  test.beforeAll(async () => {
    const { execSync } = require('child_process');
    execSync(`docker exec -i signaltrackers-dev bash -c "cat > /app/data/market_conditions_cache.json"`, { input: MOCK_CACHE, stdio: ['pipe', 'pipe', 'pipe'] });
    execSync(`docker exec -i signaltrackers-dev bash -c "cat > /app/data/market_conditions_history.json"`, { input: MOCK_HISTORY, stdio: ['pipe', 'pipe', 'pipe'] });
  });

  // 1. Credit page — desktop: strip + context sentence + recession panel
  test('credit-desktop-1280', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(BASE + '/credit', { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);
    // Capture from top of content through recession panel
    await page.screenshot({ path: `${DIR}/credit-desktop-1280.png`, fullPage: false });
  });

  // 2. Credit page — mobile: strip + context sentence wrapping
  test('credit-mobile-375', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto(BASE + '/credit', { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);
    await page.screenshot({ path: `${DIR}/credit-mobile-375.png`, fullPage: false });
  });

  // 3. Credit page — recession panel section (desktop)
  test('credit-desktop-1280-recession-panel', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(BASE + '/credit', { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);
    const panel = page.locator('#recession-panel-section');
    if (await panel.count() > 0) {
      await panel.scrollIntoViewIfNeeded();
      await panel.screenshot({ path: `${DIR}/credit-desktop-1280-recession-panel.png` });
    } else {
      // If no recession data, capture the area where it would be
      await page.screenshot({ path: `${DIR}/credit-desktop-1280-recession-panel.png`, fullPage: false });
    }
  });

  // 4. Equities page — desktop: strip + context sentence + sector tone + trade pulse
  test('equities-desktop-1280', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(BASE + '/equity', { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);
    await page.screenshot({ path: `${DIR}/equities-desktop-1280.png`, fullPage: false });
  });

  // 5. Equities page — mobile
  test('equities-mobile-375', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto(BASE + '/equity', { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);
    await page.screenshot({ path: `${DIR}/equities-mobile-375.png`, fullPage: false });
  });

  // 6. Equities — sector tone + trade pulse relocated sections (desktop)
  test('equities-desktop-1280-relocated-sections', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(BASE + '/equity', { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);
    const sectorTone = page.locator('#sector-tone-section');
    if (await sectorTone.count() > 0) {
      await sectorTone.scrollIntoViewIfNeeded();
      await sectorTone.screenshot({ path: `${DIR}/equities-desktop-1280-sector-tone.png` });
    }
    const tradePulse = page.locator('#trade-pulse-section');
    if (await tradePulse.count() > 0) {
      await tradePulse.scrollIntoViewIfNeeded();
      await tradePulse.screenshot({ path: `${DIR}/equities-desktop-1280-trade-pulse.png` });
    }
  });

  // 7. Crypto page — desktop: liquidity-led strip + context sentence
  test('crypto-desktop-1280', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(BASE + '/crypto', { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);
    await page.screenshot({ path: `${DIR}/crypto-desktop-1280.png`, fullPage: false });
  });

  // 8. Crypto page — mobile
  test('crypto-mobile-375', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto(BASE + '/crypto', { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);
    await page.screenshot({ path: `${DIR}/crypto-mobile-375.png`, fullPage: false });
  });

  // 9. Metric card with "Conditions Context" annotation (visible on desktop without toggle)
  test('credit-desktop-1280-conditions-annotation', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(BASE + '/credit', { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);
    // Expand the Market Statistics collapsible section first
    const sectionBtn = page.locator('[data-section-id="market-stats"] .collapsible-section__header');
    await sectionBtn.scrollIntoViewIfNeeded();
    await sectionBtn.click();
    await page.waitForTimeout(500);
    // Now screenshot the first stat-item that has a conditions-annotation
    const statItem = page.locator('.stat-item:has(.conditions-annotation)').first();
    await statItem.scrollIntoViewIfNeeded();
    await statItem.screenshot({ path: `${DIR}/credit-desktop-1280-conditions-annotation.png` });
  });

  // 10. Homepage — confirm relocated sections are removed
  test('homepage-desktop-1280-no-relocated', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(BASE + '/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);
    await page.screenshot({ path: `${DIR}/homepage-desktop-1280.png`, fullPage: false });
  });

});
