const { test } = require('@playwright/test');

const viewports = [
  { name: 'mobile', width: 375, height: 667 },      // iPhone SE
  { name: 'tablet', width: 768, height: 1024 },     // iPad
  { name: 'desktop', width: 1920, height: 1080 }    // Desktop
];

const pages = [
  '/',
  '/credit',
  '/equities',
  '/rates',
  '/portfolio',
  '/explorer'
];

test.describe('Screenshot Generation', () => {
  for (const viewport of viewports) {
    for (const page of pages) {
      test(`${page} - ${viewport.name}`, async ({ page: p }) => {
        await p.setViewportSize({ width: viewport.width, height: viewport.height });
        await p.goto(`http://localhost:5000${page}`);
        await p.screenshot({ 
          path: `screenshots/${page.replace('/', 'home')}-${viewport.name}.png`,
          fullPage: true 
        });
      });
    }
  }
});
