/**
 * Design-review screenshots for US-171.2: Mobile FAB + bottom sheet section navigator
 *
 * Captures:
 *  1. mobile-375-fab-visible   — FAB visible at bottom-right; strip absent
 *  2. mobile-375-fab-closeup   — FAB button close-up
 *  3. mobile-375-sheet-open    — Bottom sheet fully open, all 9 items listed
 *  4. mobile-375-sheet-active  — Bottom sheet with active item highlighted
 *  5. desktop-1280-fab-hidden  — FAB absent; desktop sticky strip visible
 */
const { test, expect } = require('@playwright/test');

const BASE = 'http://localhost:5000/';
const DIR  = 'screenshots/us1962/';

test.describe('US-171.2 Design Review Screenshots', () => {

  test('mobile-375 — FAB visible, strip hidden', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto(BASE);
    await page.waitForLoadState('networkidle');
    // FAB must be visible
    const fab = page.locator('#section-nav-fab');
    await expect(fab).toBeVisible();
    // Take full viewport screenshot to show FAB in context
    await page.screenshot({ path: DIR + 'mobile-375-fab-visible.png' });
  });

  test('mobile-375 — FAB close-up', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto(BASE);
    await page.waitForLoadState('networkidle');
    const fab = page.locator('#section-nav-fab');
    await expect(fab).toBeVisible();
    await fab.screenshot({ path: DIR + 'mobile-375-fab-closeup.png' });
  });

  test('mobile-375 — bottom sheet open', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto(BASE);
    await page.waitForLoadState('networkidle');
    // Open the sheet
    await page.locator('#section-nav-fab').click();
    // Wait for sheet to slide into view, then let transition complete (250ms)
    await page.locator('#section-quick-nav-sheet.is-open').waitFor({ timeout: 2000 });
    await page.waitForTimeout(400);
    await page.screenshot({ path: DIR + 'mobile-375-sheet-open.png' });
  });

  test('mobile-375 — sheet with active section highlighted', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto(BASE);
    await page.waitForLoadState('networkidle');
    // Scroll to the Briefing section to change active item
    await page.evaluate(() => {
      const el = document.querySelector('#briefing-section');
      if (el) el.scrollIntoView({ behavior: 'instant' });
    });
    await page.waitForTimeout(400);
    // Open the sheet
    await page.locator('#section-nav-fab').click();
    await page.locator('#section-quick-nav-sheet.is-open').waitFor({ timeout: 2000 });
    await page.waitForTimeout(400);
    await page.screenshot({ path: DIR + 'mobile-375-sheet-active.png' });
  });

  test('desktop-1280 — FAB hidden, sticky strip visible', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(BASE);
    await page.waitForLoadState('networkidle');
    // FAB must be hidden
    const fab = page.locator('#section-nav-fab');
    await expect(fab).toBeHidden();
    // Strip must be visible
    const strip = page.locator('nav.section-quick-nav');
    await expect(strip).toBeVisible();
    await strip.screenshot({ path: DIR + 'desktop-1280-strip-with-fab-hidden.png' });
  });

});
