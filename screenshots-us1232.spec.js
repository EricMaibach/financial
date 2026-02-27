const { test } = require('@playwright/test');
const fs = require('fs');

const outputDir = 'screenshots/us1232';
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

test.describe('US-123.2 Sector Management Tone Panel Screenshots', () => {

  // 1. Mobile 375px — collapsed (default state)
  test('mobile-375-collapsed', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('http://localhost:5000/');
    await page.waitForLoadState('networkidle');
    await page.locator('#sector-tone-section').scrollIntoViewIfNeeded();
    await page.waitForTimeout(300);
    await page.screenshot({
      path: `${outputDir}/mobile-375-collapsed.png`,
      fullPage: false,
      clip: await clipToSection(page, '#sector-tone-section'),
    });
  });

  // 2. Mobile 375px — expanded, 2-col grid visible
  test('mobile-375-expanded', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('http://localhost:5000/');
    await page.waitForLoadState('networkidle');
    await page.locator('#sector-tone-section').scrollIntoViewIfNeeded();
    // Click the toggle to expand
    await page.locator('#sector-tone-toggle').click();
    await page.waitForTimeout(300); // let transition finish
    await page.screenshot({
      path: `${outputDir}/mobile-375-expanded.png`,
      fullPage: false,
      clip: await clipToSection(page, '#sector-tone-section'),
    });
  });

  // 3. Tablet 768px — 3-col grid, expanded by default
  test('tablet-768', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('http://localhost:5000/');
    await page.waitForLoadState('networkidle');
    await page.locator('#sector-tone-section').scrollIntoViewIfNeeded();
    await page.waitForTimeout(300);
    await page.screenshot({
      path: `${outputDir}/tablet-768.png`,
      fullPage: false,
      clip: await clipToSection(page, '#sector-tone-section'),
    });
  });

  // 4. Desktop 1280px — 4-col grid, full section visible
  test('desktop-1280', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto('http://localhost:5000/');
    await page.waitForLoadState('networkidle');
    await page.locator('#sector-tone-section').scrollIntoViewIfNeeded();
    await page.waitForTimeout(300);
    await page.screenshot({
      path: `${outputDir}/desktop-1280.png`,
      fullPage: false,
      clip: await clipToSection(page, '#sector-tone-section'),
    });
  });

  // 5. Mobile 375px — card detail: positive, neutral, negative cards close-up
  test('mobile-375-card-detail', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('http://localhost:5000/');
    await page.waitForLoadState('networkidle');
    await page.locator('#sector-tone-section').scrollIntoViewIfNeeded();
    // Expand to show cards
    await page.locator('#sector-tone-toggle').click();
    await page.waitForTimeout(300);

    // Grab first positive card, first neutral card, first negative card
    const positiveCard = page.locator('.sector-card--positive').first();
    const neutralCard = page.locator('.sector-card--neutral').first();
    const negativeCard = page.locator('.sector-card--negative').first();

    await positiveCard.scrollIntoViewIfNeeded();
    const posBox = await positiveCard.boundingBox();
    const neuBox = await neutralCard.boundingBox();
    const negBox = await negativeCard.boundingBox();

    if (posBox && neuBox && negBox) {
      // Bounding box that covers all three cards
      const x = Math.min(posBox.x, neuBox.x, negBox.x);
      const y = Math.min(posBox.y, neuBox.y, negBox.y);
      const right = Math.max(posBox.x + posBox.width, neuBox.x + neuBox.width, negBox.x + negBox.width);
      const bottom = Math.max(posBox.y + posBox.height, neuBox.y + neuBox.height, negBox.y + negBox.height);
      await page.screenshot({
        path: `${outputDir}/mobile-375-card-detail.png`,
        fullPage: false,
        clip: {
          x: Math.max(0, x - 8),
          y: Math.max(0, y - 8),
          width: right - x + 16,
          height: bottom - y + 16,
        },
      });
    } else {
      // Fallback: screenshot the full grid
      await page.screenshot({
        path: `${outputDir}/mobile-375-card-detail.png`,
        fullPage: false,
        clip: await clipToSection(page, '.sector-card-grid'),
      });
    }
  });

});
