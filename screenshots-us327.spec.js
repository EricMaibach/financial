const { test, expect } = require('@playwright/test');
const path = require('path');
const fs = require('fs');
const { execSync } = require('child_process');

const BASE_URL = 'http://localhost:5000';
const OUT_DIR = path.join(__dirname, 'screenshots', 'us327');
const CONTAINER = 'signaltrackers-dev';

/** Write a mock market_conditions_cache.json into the Docker container. */
function writeMockCache(cacheObj) {
  const json = JSON.stringify(cacheObj);
  execSync(
    `echo '${json.replace(/'/g, "'\\''")}' | docker exec -i ${CONTAINER} python3 -c "import sys,json; data=json.load(sys.stdin); f=open('/app/data/market_conditions_cache.json','w'); json.dump(data, f, indent=2); f.close()"`,
  );
}

/** Remove the mock cache file so the strip falls back to unavailable. */
function removeMockCache() {
  execSync(
    `docker exec ${CONTAINER} rm -f /app/data/market_conditions_cache.json`,
  );
}

/** Standard Goldilocks cache with expanding liquidity and calm risk. */
function goldilocksCache() {
  return {
    quadrant: 'Goldilocks',
    dimensions: {
      liquidity: { state: 'Expanding' },
      quadrant: { state: 'Goldilocks' },
      risk: { state: 'Calm' },
      policy: { stance: 'Neutral', direction: 'Paused' },
    },
    asset_expectations: {},
    as_of: '2026-03-17',
    updated_at: new Date().toISOString(),
  };
}

test.beforeAll(() => {
  fs.mkdirSync(OUT_DIR, { recursive: true });
});

// 1. Desktop 1280 — standard page (Credit) — quadrant leads
test('Desktop 1280 — standard page (Credit)', async ({ page }) => {
  writeMockCache(goldilocksCache());
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto(`${BASE_URL}/credit`, { waitUntil: 'networkidle' });

  // Capture just the conditions strip area (top of page, below navbar)
  const strip = await page.locator('.conditions-strip').first();
  await expect(strip).toBeVisible();

  // Full-width clip of the strip with some padding
  const box = await strip.boundingBox();
  await page.screenshot({
    path: path.join(OUT_DIR, 'desktop-1280-standard-credit.png'),
    clip: {
      x: 0,
      y: box.y,
      width: 1280,
      height: box.height + 4,
    },
  });
});

// 2. Desktop 1280 — Crypto page (Liquidity-leads variant)
test('Desktop 1280 — Crypto page liquidity-leads', async ({ page }) => {
  writeMockCache(goldilocksCache());
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto(`${BASE_URL}/crypto`, { waitUntil: 'networkidle' });

  const strip = await page.locator('.conditions-strip').first();
  await expect(strip).toBeVisible();

  const box = await strip.boundingBox();
  await page.screenshot({
    path: path.join(OUT_DIR, 'desktop-1280-crypto-liquidity-leads.png'),
    clip: {
      x: 0,
      y: box.y,
      width: 1280,
      height: box.height + 4,
    },
  });
});

// 3. Mobile 375 — collapsed (standard page)
test('Mobile 375 — collapsed', async ({ page }) => {
  writeMockCache(goldilocksCache());
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto(`${BASE_URL}/credit`, { waitUntil: 'networkidle' });

  const strip = await page.locator('.conditions-strip').first();
  await expect(strip).toBeVisible();

  // Ensure collapsed
  const toggle = await page.locator('.conditions-strip__toggle');
  const expanded = await toggle.getAttribute('aria-expanded');
  if (expanded === 'true') {
    await toggle.click();
    await page.waitForTimeout(300);
  }

  const box = await strip.boundingBox();
  await page.screenshot({
    path: path.join(OUT_DIR, 'mobile-375-collapsed.png'),
    clip: {
      x: 0,
      y: box.y,
      width: 375,
      height: box.height + 4,
    },
  });
});

// 4. Mobile 375 — expanded (standard page)
test('Mobile 375 — expanded', async ({ page }) => {
  writeMockCache(goldilocksCache());
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto(`${BASE_URL}/credit`, { waitUntil: 'networkidle' });

  const strip = await page.locator('.conditions-strip').first();
  await expect(strip).toBeVisible();

  // Expand
  const toggle = await page.locator('.conditions-strip__toggle');
  const expanded = await toggle.getAttribute('aria-expanded');
  if (expanded !== 'true') {
    await toggle.click();
    await page.waitForTimeout(300);
  }

  const box = await strip.boundingBox();
  await page.screenshot({
    path: path.join(OUT_DIR, 'mobile-375-expanded.png'),
    clip: {
      x: 0,
      y: box.y,
      width: 375,
      height: box.height + 4,
    },
  });
});

// 5. Mobile 375 — Crypto collapsed (liquidity-leads variant)
test('Mobile 375 — Crypto collapsed', async ({ page }) => {
  writeMockCache(goldilocksCache());
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto(`${BASE_URL}/crypto`, { waitUntil: 'networkidle' });

  const strip = await page.locator('.conditions-strip').first();
  await expect(strip).toBeVisible();

  // Ensure collapsed
  const toggle = await page.locator('.conditions-strip__toggle');
  const expanded = await toggle.getAttribute('aria-expanded');
  if (expanded === 'true') {
    await toggle.click();
    await page.waitForTimeout(300);
  }

  const box = await strip.boundingBox();
  await page.screenshot({
    path: path.join(OUT_DIR, 'mobile-375-crypto-collapsed.png'),
    clip: {
      x: 0,
      y: box.y,
      width: 375,
      height: box.height + 4,
    },
  });
});

// 6. Desktop — fallback state (CONDITIONS UNAVAILABLE)
test('Desktop 1280 — fallback unavailable', async ({ page }) => {
  removeMockCache();
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto(`${BASE_URL}/credit`, { waitUntil: 'networkidle' });

  const strip = await page.locator('.conditions-strip').first();
  await expect(strip).toBeVisible();

  const box = await strip.boundingBox();
  await page.screenshot({
    path: path.join(OUT_DIR, 'desktop-1280-fallback-unavailable.png'),
    clip: {
      x: 0,
      y: box.y,
      width: 1280,
      height: box.height + 4,
    },
  });
});

// Cleanup: restore cache for other tests
test.afterAll(() => {
  try {
    writeMockCache(goldilocksCache());
  } catch (_) {
    // noop
  }
});
