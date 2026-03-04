/**
 * Screenshots for US-183.1: Homepage Narrative Cohesion — Frontend Implementation
 * Captures: section order, regime-thread border accents, navbar pill,
 *           §1.5 bridge sentence, §2 anchor line, §3 context note
 */
const { test } = require('@playwright/test');

const viewports = [
  { name: 'mobile', width: 375, height: 667 },
  { name: 'tablet', width: 768, height: 1024 },
  { name: 'desktop', width: 1280, height: 900 },
];

test.describe('US-183.1 Screenshots', () => {
  for (const vp of viewports) {
    test(`homepage full-page - ${vp.name}`, async ({ page }) => {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.goto('http://localhost:5000/');
      await page.waitForLoadState('networkidle');
      await page.screenshot({
        path: `screenshots/us184/homepage-full-${vp.name}.png`,
        fullPage: true,
      });
    });
  }

  test('navbar regime pill close-up', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 200 });
    await page.goto('http://localhost:5000/');
    await page.waitForLoadState('networkidle');
    const navbar = page.locator('nav.navbar');
    await navbar.screenshot({ path: 'screenshots/us184/navbar-pill.png' });
  });

  test('navbar regime pill mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 100 });
    await page.goto('http://localhost:5000/');
    await page.waitForLoadState('networkidle');
    const navbar = page.locator('nav.navbar');
    await navbar.screenshot({ path: 'screenshots/us184/navbar-pill-mobile.png' });
  });

  test('section 0 - no regime-thread border', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto('http://localhost:5000/');
    await page.waitForLoadState('networkidle');
    const sec0 = page.locator('#macro-regime-section');
    await sec0.screenshot({ path: 'screenshots/us184/sec0-no-thread-border.png' });
  });

  test('section 1.5 with bridge sentence', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto('http://localhost:5000/');
    await page.waitForLoadState('networkidle');
    const sec = page.locator('#sector-tone-section');
    await sec.screenshot({ path: 'screenshots/us184/sec15-bridge-sentence.png' });
  });

  test('section 2 with compact anchor', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto('http://localhost:5000/');
    await page.waitForLoadState('networkidle');
    const sec = page.locator('section.hero-briefing');
    await sec.screenshot({ path: 'screenshots/us184/sec2-regime-anchor.png' });
  });

  test('section 3 with context note', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto('http://localhost:5000/');
    await page.waitForLoadState('networkidle');
    const sec = page.locator('section.whats-moving-section');
    await sec.screenshot({ path: 'screenshots/us184/sec3-context-note.png' });
  });
});
