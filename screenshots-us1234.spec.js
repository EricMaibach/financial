const { test } = require('@playwright/test');
const fs = require('fs');

const outputDir = 'screenshots/us1234';
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

test.describe('US-123.4 Credit Stub, Nav Dropdown & Regime Implications Dollar Tab', () => {

  // ── /credit stub page ──────────────────────────────────────────────────────

  test('credit-mobile-375', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('http://localhost:5000/credit');
    await page.waitForLoadState('networkidle');
    await page.screenshot({
      path: `${outputDir}/credit-mobile-375.png`,
      fullPage: true,
    });
  });

  test('credit-tablet-768', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('http://localhost:5000/credit');
    await page.waitForLoadState('networkidle');
    await page.screenshot({
      path: `${outputDir}/credit-tablet-768.png`,
      fullPage: true,
    });
  });

  test('credit-desktop-1280', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto('http://localhost:5000/credit');
    await page.waitForLoadState('networkidle');
    await page.screenshot({
      path: `${outputDir}/credit-desktop-1280.png`,
      fullPage: true,
    });
  });

  // ── Markets nav dropdown — open state (desktop 1280px) ────────────────────

  test('nav-dropdown-open-desktop-1280', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto('http://localhost:5000/');
    await page.waitForLoadState('networkidle');
    // Click the Markets dropdown toggle to open it
    await page.locator('.nav-item.dropdown .dropdown-toggle').first().click();
    await page.waitForTimeout(300); // let dropdown animate open
    // Screenshot the open dropdown
    const dropdownMenu = page.locator('.nav-item.dropdown .dropdown-menu').first();
    const box = await dropdownMenu.boundingBox();
    // Include the toggle button in the clip (so context is clear)
    const toggleBox = await page.locator('.nav-item.dropdown .dropdown-toggle').first().boundingBox();
    if (box && toggleBox) {
      await page.screenshot({
        path: `${outputDir}/nav-dropdown-open-desktop-1280.png`,
        fullPage: false,
        clip: {
          x: Math.max(0, toggleBox.x - 8),
          y: Math.max(0, toggleBox.y - 8),
          width: Math.max(box.width, toggleBox.width) + 16,
          height: (box.y + box.height) - toggleBox.y + 16,
        },
      });
    } else {
      await page.screenshot({ path: `${outputDir}/nav-dropdown-open-desktop-1280.png` });
    }
  });

  // ── Regime Implications Panel — all 6 asset class cards (tab row) ─────────

  // Mobile 375px — expand panel, show all 6 chips in switcher + card grid
  test('regime-panel-mobile-375-all-6-cards', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('http://localhost:5000/');
    await page.waitForLoadState('networkidle');
    await page.locator('#regime-implications').scrollIntoViewIfNeeded();
    // Expand the panel
    await page.locator('#regime-implications-toggle').click();
    await page.waitForTimeout(300);
    await page.screenshot({
      path: `${outputDir}/regime-panel-mobile-375-all-6-cards.png`,
      fullPage: false,
      clip: await clipToSection(page, '#regime-implications'),
    });
  });

  // Tablet 768px — tab bar visible, showing all 4 regime tabs + 6 asset class cards
  test('regime-panel-tablet-768-all-6-cards', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('http://localhost:5000/');
    await page.waitForLoadState('networkidle');
    await page.locator('#regime-implications').scrollIntoViewIfNeeded();
    await page.waitForTimeout(300);
    await page.screenshot({
      path: `${outputDir}/regime-panel-tablet-768-all-6-cards.png`,
      fullPage: false,
      clip: await clipToSection(page, '#regime-implications'),
    });
  });

  // Desktop 1280px — full section with all 6 asset class cards
  test('regime-panel-desktop-1280-all-6-cards', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto('http://localhost:5000/');
    await page.waitForLoadState('networkidle');
    await page.locator('#regime-implications').scrollIntoViewIfNeeded();
    await page.waitForTimeout(300);
    await page.screenshot({
      path: `${outputDir}/regime-panel-desktop-1280-all-6-cards.png`,
      fullPage: false,
      clip: await clipToSection(page, '#regime-implications'),
    });
  });

  // ── Regime Implications Panel — Dollar card close-up in Bull regime ────────

  // Desktop 1280px — Dollar card (6th) in Bull regime panel
  test('regime-dollar-card-bull-desktop-1280', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto('http://localhost:5000/');
    await page.waitForLoadState('networkidle');
    await page.locator('#regime-implications').scrollIntoViewIfNeeded();
    await page.waitForTimeout(300);
    // Find the Bull regime panel and get the 6th implication card (Dollar)
    const dollarCard = page.locator('#regime-panel-bull .implication-card').nth(5);
    await dollarCard.scrollIntoViewIfNeeded();
    const box = await dollarCard.boundingBox();
    if (box) {
      await page.screenshot({
        path: `${outputDir}/regime-dollar-card-bull-desktop-1280.png`,
        fullPage: false,
        clip: {
          x: Math.max(0, box.x - 8),
          y: Math.max(0, box.y - 8),
          width: box.width + 16,
          height: box.height + 16,
        },
      });
    } else {
      // Fallback: full panel
      await page.screenshot({
        path: `${outputDir}/regime-dollar-card-bull-desktop-1280.png`,
        fullPage: false,
        clip: await clipToSection(page, '#regime-panel-bull'),
      });
    }
  });

  // Mobile 375px — Dollar card close-up after expanding panel in Bull regime
  test('regime-dollar-card-bull-mobile-375', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('http://localhost:5000/');
    await page.waitForLoadState('networkidle');
    await page.locator('#regime-implications').scrollIntoViewIfNeeded();
    await page.locator('#regime-implications-toggle').click();
    await page.waitForTimeout(300);
    // Find the 6th implication card (Dollar) in the active Bull panel
    const dollarCard = page.locator('#regime-panel-bull .implication-card').nth(5);
    await dollarCard.scrollIntoViewIfNeeded();
    const box = await dollarCard.boundingBox();
    if (box) {
      await page.screenshot({
        path: `${outputDir}/regime-dollar-card-bull-mobile-375.png`,
        fullPage: false,
        clip: {
          x: Math.max(0, box.x - 8),
          y: Math.max(0, box.y - 8),
          width: box.width + 16,
          height: box.height + 16,
        },
      });
    } else {
      await page.screenshot({
        path: `${outputDir}/regime-dollar-card-bull-mobile-375.png`,
        fullPage: false,
        clip: await clipToSection(page, '#regime-panel-bull'),
      });
    }
  });

});
