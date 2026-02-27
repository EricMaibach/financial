const { test } = require('@playwright/test');
const fs = require('fs');

const outputDir = 'screenshots/us1452';
fs.mkdirSync(outputDir, { recursive: true });

// Helper: clip screenshot to section bounds with padding
async function clipToSection(page, selector, padX = 8, padY = 8) {
  const box = await page.locator(selector).boundingBox();
  if (!box) return undefined;
  return {
    x: Math.max(0, box.x - padX),
    y: Math.max(0, box.y - padY),
    width: box.width + padX * 2,
    height: box.height + padY * 2,
  };
}

test.describe('US-145.2 Regime Implications Panel Screenshots', () => {

  // 1. Mobile 375px — collapsed (default state)
  test('mobile-375-collapsed', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('http://localhost:5000/');
    await page.waitForLoadState('networkidle');
    await page.locator('#regime-implications').scrollIntoViewIfNeeded();
    await page.screenshot({
      path: `${outputDir}/mobile-375-collapsed.png`,
      fullPage: false,
      clip: await clipToSection(page, '#regime-implications'),
    });
  });

  // 2. Mobile 375px — expanded, Bull regime cards visible
  test('mobile-375-expanded-bull', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('http://localhost:5000/');
    await page.waitForLoadState('networkidle');
    await page.locator('#regime-implications').scrollIntoViewIfNeeded();
    // Click the toggle to expand
    await page.locator('#regime-implications-toggle').click();
    await page.waitForTimeout(300); // let 200ms transition finish
    await page.screenshot({
      path: `${outputDir}/mobile-375-expanded-bull.png`,
      fullPage: false,
      clip: await clipToSection(page, '#regime-implications'),
    });
  });

  // 3. Mobile 375px — after tapping Neutral chip, subtitle + cards update
  test('mobile-375-chip-switch', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('http://localhost:5000/');
    await page.waitForLoadState('networkidle');
    await page.locator('#regime-implications').scrollIntoViewIfNeeded();
    // Expand first
    await page.locator('#regime-implications-toggle').click();
    await page.waitForTimeout(300);
    // Tap the Neutral chip (not current = Bull, so Neutral chip is visible)
    await page.locator('.regime-switcher-chip[data-regime="neutral"]').click();
    await page.waitForTimeout(100);
    await page.screenshot({
      path: `${outputDir}/mobile-375-chip-switch.png`,
      fullPage: false,
      clip: await clipToSection(page, '#regime-implications'),
    });
  });

  // 4. Mobile 375px — close-up of Equities card (Bull regime, so expanded)
  test('mobile-375-equities-card', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('http://localhost:5000/');
    await page.waitForLoadState('networkidle');
    await page.locator('#regime-implications').scrollIntoViewIfNeeded();
    // Expand to show cards
    await page.locator('#regime-implications-toggle').click();
    await page.waitForTimeout(300);
    // Screenshot the first implication-card (Equities) in the Bull panel
    const equitiesCard = page.locator('#regime-panel-bull .implication-card').first();
    await equitiesCard.scrollIntoViewIfNeeded();
    const box = await equitiesCard.boundingBox();
    if (box) {
      await page.screenshot({
        path: `${outputDir}/mobile-375-equities-card.png`,
        fullPage: false,
        clip: {
          x: Math.max(0, box.x - 8),
          y: Math.max(0, box.y - 8),
          width: box.width + 16,
          height: box.height + 16,
        },
      });
    }
  });

  // 5. Tablet 768px — tab bar visible, Bull tab active, 3-column grid
  test('tablet-768-bull', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('http://localhost:5000/');
    await page.waitForLoadState('networkidle');
    await page.locator('#regime-implications').scrollIntoViewIfNeeded();
    await page.screenshot({
      path: `${outputDir}/tablet-768-bull.png`,
      fullPage: false,
      clip: await clipToSection(page, '#regime-implications'),
    });
  });

  // 6. Tablet 768px — after clicking Bear tab
  test('tablet-768-tab-switch', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('http://localhost:5000/');
    await page.waitForLoadState('networkidle');
    await page.locator('#regime-implications').scrollIntoViewIfNeeded();
    // Click the Bear tab
    await page.locator('#regime-tab-bear').click();
    await page.waitForTimeout(100);
    await page.screenshot({
      path: `${outputDir}/tablet-768-tab-switch.png`,
      fullPage: false,
      clip: await clipToSection(page, '#regime-implications'),
    });
  });

  // 7. Desktop 1280px — full section
  test('desktop-1280-bull', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto('http://localhost:5000/');
    await page.waitForLoadState('networkidle');
    await page.locator('#regime-implications').scrollIntoViewIfNeeded();
    await page.screenshot({
      path: `${outputDir}/desktop-1280-bull.png`,
      fullPage: false,
      clip: await clipToSection(page, '#regime-implications'),
    });
  });

});
